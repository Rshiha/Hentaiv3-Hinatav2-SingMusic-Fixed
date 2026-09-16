"""
Message dispatcher: prefix parsing, roles, cooldowns, command lookup + typo
suggestions, and event-script fan-out. Python port of Hinatav2's
src/dispatcher.js, adapted for a single-user-DM (no groups/threads-with-
admins) Instagram bot: role is just "bot admin" (2) or "user" (0).
"""

import time

from src.message import MessageContext

ROLE_USER = 0
ROLE_ADMIN_BOT = 2


class Dispatcher:
    def __init__(self, config, registry, database, ig_lock):
        self.config = config
        self.registry = registry
        self.database = database
        self.ig_lock = ig_lock
        self._cooldowns = {}

    # ---- roles / cooldowns -------------------------------------------

    def is_bot_admin(self, user_id):
        return str(user_id) in [str(a) for a in self.config.get("adminBot", [])]

    def role_of(self, user_id):
        return ROLE_ADMIN_BOT if self.is_bot_admin(user_id) else ROLE_USER

    def _cooldown_remaining(self, command, user_id):
        seconds = command.config.get("cooldown", self.config.get("cooldown", {}).get("default", 2)) or 0
        if seconds <= 0:
            return 0
        key = f"{command.config['name']}:{user_id}"
        last = self._cooldowns.get(key, 0)
        remaining = last + seconds - time.time()
        if remaining > 0:
            return int(remaining) + 1
        self._cooldowns[key] = time.time()
        return 0

    def _suggestion_for(self, name):
        if not name:
            return None
        candidates = set(self.registry.commands.keys()) | set(self.registry.aliases.keys())
        best, best_dist = None, 10 ** 9
        for candidate in candidates:
            dist = _levenshtein(name, candidate)
            if dist < best_dist or (dist == best_dist and best and len(candidate) < len(best)):
                best_dist, best = dist, candidate
        limit = 1 if len(name) <= 3 else 2
        return best if best_dist <= limit else None

    # ---- context ----------------------------------------------------

    def build_legacy_ctx(self, client, user_info, user_id, thread, message, start_time):
        """Same shape as the original main.py's make_context(), for legacy
        command modules that expect (args, ctx)."""
        return {
            "client": client,
            "user": user_info,
            "user_id": str(user_id),
            "username": getattr(user_info, "username", "Unknown") if user_info else "Unknown",
            "full_name": getattr(user_info, "full_name", "Unknown") if user_info else "Unknown",
            "profile_pic_url": str(getattr(user_info, "profile_pic_url", "")) if user_info else "",
            "followers": getattr(user_info, "follower_count", 0) if user_info else 0,
            "following": getattr(user_info, "following_count", 0) if user_info else 0,
            "posts": getattr(user_info, "media_count", 0) if user_info else 0,
            "bio": getattr(user_info, "biography", "") if user_info else "",
            "start_time": start_time,
            "thread_id": thread.id,
            "ig_lock": self.ig_lock,
            "thread": thread,
            "message": message,
        }

    # ---- dispatch -----------------------------------------------------

    def handle(self, client, thread, message, user_info, start_time):
        """Entry point: one incoming DM message. Returns True if it was
        consumed by an event script or a command."""
        text = (getattr(message, "text", "") or "").strip()
        if not text:
            return False

        user_id = str(getattr(message, "user_id", ""))

        # Hinatav2-style ban + whitelist gate. Admins are never blocked by
        # these gates, matching the intended role hierarchy.
        if not self.is_bot_admin(user_id):
            banned = self.database.users.get(user_id) or {}
            if isinstance(banned.get("banned"), dict) and banned["banned"].get("status"):
                return False
            wl = self.config.get("whiteList", {}) or {}
            if wl.get("enable"):
                allowed_users = {str(x) for x in wl.get("userIDs", [])}
                allowed_threads = {str(x) for x in wl.get("threadIDs", [])}
                if user_id not in allowed_users and str(thread.id) not in allowed_threads:
                    return False

        msg_ctx = MessageContext(client, thread.id, self.ig_lock)
        legacy_ctx = self.build_legacy_ctx(client, user_info, user_id, thread, message, start_time)

        base_ctx = {
            "client": client,
            "message": msg_ctx,
            "raw_message": message,
            "thread": thread,
            "text": text,
            "user_id": user_id,
            "role": self.role_of(user_id),
            "config": self.config,
            "registry": self.registry,
            "usersData": self.database.users,
            "threadsData": self.database.threads,
            "legacy_ctx": legacy_ctx,
            "send": msg_ctx.send,
        }

        # 1) Event scripts always run first (teach, taught replies, AI
        #    free-chat, auto link-download, song-number selection...).
        for script in self.registry.events:
            try:
                if script.on_event(dict(base_ctx)):
                    return True  # event claimed the message; stop here
            except Exception as e:
                print(f"EVENT ERR ({script.config.get('name')}): {e}", flush=True)

        # 2) Command dispatch.
        prefix = self.config.get("prefix", ".")
        has_prefix = bool(prefix) and text.startswith(prefix)
        raw_body = text[len(prefix):].strip() if has_prefix else text.strip()
        raw_args = raw_body.split() if raw_body else []
        raw_name = (raw_args[0] if raw_args else "").lower()

        bare_command = self.registry.resolve(raw_name)
        bare_allowed = bool(bare_command) and bare_command.config.get("no_prefix") and (
            self.is_bot_admin(user_id) or bare_command.config.get("no_prefix_role") == 0
        )

        if not has_prefix and not bare_allowed:
            return False

        args = raw_args[1:] if raw_args else []
        name = raw_name
        command = self.registry.resolve(name)

        if not command:
            if not has_prefix or self.config.get("hideNotiMessage", {}).get("commandNotFound"):
                return False
            suggestion = self._suggestion_for(name)
            hint = f' Did you mean "{prefix}{suggestion}"?' if suggestion else ""
            msg_ctx.reply(f"❌ Unknown command: {name}.{hint}")
            return True

        needed_role = command.config.get("role", 0)
        if needed_role > base_ctx["role"]:
            if not self.config.get("hideNotiMessage", {}).get("onlyAdminBot"):
                msg_ctx.reply(f"❌ Only the bot admin can use \"{command.config['name']}\".")
            return True

        wait = self._cooldown_remaining(command, user_id)
        if wait:
            msg_ctx.reply(f"⏳ Wait {wait}s before using \"{command.config['name']}\" again.")
            return True

        ctx = dict(base_ctx)
        ctx["args"] = args
        ctx["command_name"] = command.config["name"]
        ctx["invoked_as"] = name

        try:
            result = command.on_start(ctx)
            if result is not None:
                msg_ctx.send(result)
            print(f"COMMAND | {command.config['name']} | {user_id} | {' '.join(args)}", flush=True)
        except Exception as e:
            print(f"COMMAND ERR ({command.config['name']}): {e}", flush=True)
            msg_ctx.reply(f"❌ Error running \"{command.config['name']}\": {e}")

        return True


def _levenshtein(a, b):
    if a == b:
        return 0
    rows = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        prev = rows[0]
        rows[0] = i
        for j in range(1, len(b) + 1):
            temp = rows[j]
            rows[j] = min(rows[j] + 1, rows[j - 1] + 1, prev + (0 if a[i - 1] == b[j - 1] else 1))
            prev = temp
    return rows[len(b)]
