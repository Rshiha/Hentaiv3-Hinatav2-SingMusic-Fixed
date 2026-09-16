"""
Command + event script loader/registry.
Python port of Hinatav2's src/commandLoader.js.

Two module styles are supported so nothing from the original Instagoat-render
codebase had to be thrown away:

1. "Modern" command modules (the Hinatav2 style) — a file in commands/ that
   defines a CONFIG dict (name, aliases, category, cooldown, role,
   description, usage) and an on_start(ctx) function. New commands should be
   written this way; see commands/ping.py or commands/help.py for examples.

2. "Legacy" command modules — a file in commands/legacy/ that exports one or
   more dicts named like SOMETHING_COMMANDS mapping "name" -> func(args, ctx).
   This is the original Instagoat-render command style. The loader wraps each
   entry into the same Command object automatically, with a generated CONFIG
   (category = filename, cooldown = default, role = 0) — so existing command
   logic (economy, media, downloader, pinterest, tiktok, ...) keeps working
   unchanged, it's just discovered and dispatched the modern way.

Event scripts (events/*.py) define CONFIG + on_event(ctx) and are fanned out
to on every message, same as Hinatav2's events/*.js.
"""

import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMMANDS_DIR = os.path.join(ROOT, "commands")
LEGACY_DIR = os.path.join(COMMANDS_DIR, "legacy")
EVENTS_DIR = os.path.join(ROOT, "events")

REQUIRED_LEGACY_SUFFIX = "_COMMANDS"


class Command:
    def __init__(self, config, on_start, location):
        self.config = config
        self.on_start = on_start
        self.location = location


class EventScript:
    def __init__(self, config, on_event, location):
        self.config = config
        self.on_event = on_event
        self.location = location


class Registry:
    def __init__(self):
        self.commands = {}   # canonical name -> Command
        self.aliases = {}    # alias (incl. canonical) -> canonical name
        self.events = []     # list[EventScript]

    def register_command(self, command):
        name = command.config["name"].lower()
        # Block on either a canonical-name collision or a collision with an
        # alias someone else already claimed (e.g. a legacy "menu" command
        # would otherwise silently steal the "menu" alias away from the
        # modern "help" command that already claims it).
        if name in self.commands or name in self.aliases:
            return f'command "{name}" already exists (skipped duplicate from {command.location})'
        self.commands[name] = command
        self.aliases[name] = name
        for alias in command.config.get("aliases", []):
            key = str(alias).lower()
            self.aliases.setdefault(key, name)
        return None

    def resolve(self, name):
        if not name:
            return None
        canonical = self.aliases.get(str(name).lower())
        return self.commands.get(canonical) if canonical else None


def _load_module(path, module_name):
    # Reuse an already-imported module. This is important for modules such
    # as commands.legacy.media that keep shared state (PENDING_SEARCH).
    # Modern commands can import it before the legacy loader reaches it;
    # creating a second module instance would split that state and make a
    # later numeric song selection appear to have no pending search.
    existing = sys.modules.get(module_name)
    if existing is not None:
        return existing

    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _load_modern_commands(registry):
    if not os.path.isdir(COMMANDS_DIR):
        return 0
    count = 0
    for fname in sorted(os.listdir(COMMANDS_DIR)):
        if not fname.endswith(".py") or fname.startswith("_"):
            continue
        path = os.path.join(COMMANDS_DIR, fname)
        try:
            module = _load_module(path, f"commands.{fname[:-3]}")
            config = getattr(module, "CONFIG", None)
            on_start = getattr(module, "on_start", None)
            if not config or not on_start:
                continue  # not a modern-style command module
            command = Command(config=config, on_start=on_start, location=path)
            error = registry.register_command(command)
            if error:
                print(f"LOADER WARN: {error}", flush=True)
                continue
            count += 1
        except Exception as e:
            print(f"LOADER ERR: could not load command {fname}: {e}", flush=True)
    return count


def _wrap_legacy(name, func, category, default_cooldown):
    def on_start(ctx):
        result = func(ctx["args"], ctx["legacy_ctx"])
        ctx["send"](result)
    config = {
        "name": name,
        "aliases": [],
        "category": category,
        "cooldown": default_cooldown,
        "role": 0,
        "description": {"en": f"(legacy) {name}"},
    }
    return Command(config=config, on_start=on_start, location=f"legacy:{category}")


def _load_legacy_commands(registry, default_cooldown=2):
    if not os.path.isdir(LEGACY_DIR):
        return 0
    count = 0
    for fname in sorted(os.listdir(LEGACY_DIR)):
        if not fname.endswith(".py") or fname.startswith("_"):
            continue
        path = os.path.join(LEGACY_DIR, fname)
        category = fname[:-3]
        try:
            module = _load_module(path, f"commands.legacy.{category}")
        except Exception as e:
            print(f"LOADER ERR: could not load legacy module {fname}: {e}", flush=True)
            continue

        for attr in dir(module):
            if not attr.endswith(REQUIRED_LEGACY_SUFFIX):
                continue
            command_dict = getattr(module, attr)
            if not isinstance(command_dict, dict):
                continue
            for cmd_name, func in command_dict.items():
                if not callable(func):
                    continue
                command = _wrap_legacy(cmd_name.lower(), func, category, default_cooldown)
                error = registry.register_command(command)
                if error:
                    continue  # a modern command with the same name wins
                count += 1
    return count


def _load_events(registry):
    if not os.path.isdir(EVENTS_DIR):
        return 0
    count = 0
    for fname in sorted(os.listdir(EVENTS_DIR)):
        if not fname.endswith(".py") or fname.startswith("_"):
            continue
        path = os.path.join(EVENTS_DIR, fname)
        try:
            module = _load_module(path, f"events.{fname[:-3]}")
            config = getattr(module, "CONFIG", None)
            on_event = getattr(module, "on_event", None)
            if not config or not on_event:
                continue
            registry.events.append(EventScript(config=config, on_event=on_event, location=path))
            count += 1
        except Exception as e:
            print(f"LOADER ERR: could not load event {fname}: {e}", flush=True)
    return count


def load_all(config=None):
    """Build a fresh registry: modern commands first (so they win name
    collisions), then legacy-wrapped commands, then event scripts."""
    registry = Registry()
    default_cooldown = (config or {}).get("cooldown", {}).get("default", 2)

    modern_count = _load_modern_commands(registry)
    legacy_count = _load_legacy_commands(registry, default_cooldown)
    event_count = _load_events(registry)

    print(
        f"✅ LOADED — commands: {len(registry.commands)} "
        f"(modern: {modern_count}, legacy: {legacy_count}), events: {event_count}",
        flush=True,
    )
    return registry
           
