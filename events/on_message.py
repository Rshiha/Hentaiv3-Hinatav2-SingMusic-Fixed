"""
Runs before command dispatch on every incoming DM, same order as the
original main.py's process_message(): AI follow-up on a reply to the bot's
own message, digit song-picks, ".bby teach", taught replies, auto link
detection/download, and finally free-text AI chat for anything left over
that wasn't prefixed with a command.

Returns True to tell the dispatcher the message was fully handled (so it
won't also try to run it as a command), False to fall through.
"""

from src.message import BOT_MSG_IDS

try:
    from ai import get_ai_reply
except Exception as e:
    print(f"AI LOAD ERR: {e}", flush=True)
    get_ai_reply = None

try:
    from commands.legacy.downloader import auto_detect, download_video
except Exception as e:
    print(f"DOWNLOADER LOAD ERR: {e}", flush=True)
    auto_detect = None
    download_video = None

try:
    from commands.legacy.media import select_song, download_selected_song
except Exception as e:
    print(f"MEDIA LOAD ERR: {e}", flush=True)
    select_song = None
    download_selected_song = None

from src.teachings import teach, taught_reply

CONFIG = {
    "name": "onMessage",
    "eventType": "message",
    "category": "system",
}


def _handle_song_number(ctx):
    if not select_song or not download_selected_song:
        return False
    text = ctx["text"]
    if not text.isdigit():
        return False
    number = int(text)
    if number < 1 or number > 10:
        return False

    try:
        result = select_song(number, ctx["legacy_ctx"])
    except Exception as e:
        print(f"SONG SELECT ERR: {e}", flush=True)
        return False
    if result is None:
        return False

    if isinstance(result, str):
        ctx["send"](result)
        return True

    if not isinstance(result, dict):
        ctx["send"]("❌ Song selection failed!")
        return True

    ctx["send"]("⏳ গান download হচ্ছে... 🎵")
    try:
        result = download_selected_song(result)
    except Exception as e:
        print(f"SONG DOWNLOAD ERR: {e}", flush=True)
        ctx["send"]("❌ গান download করা যায়নি!")
        return True

    ctx["send"](result if isinstance(result, dict) and result.get("type") == "audio"
                else (result or "❌ গান download করা যায়নি!"))
    return True


def on_event(ctx):
    text = ctx["text"]
    lower = text.lower()
    prefix = ctx["config"].get("prefix", ".")

    # 1) A reply to the bot's own message is treated as an AI follow-up.
    replied_id = getattr(ctx["raw_message"], "reply_to_id", None)
    if replied_id and replied_id in BOT_MSG_IDS:
        if not get_ai_reply:
            ctx["send"]("❌ AI ফিচার এখন unavailable!")
            return True
        try:
            answer = get_ai_reply(text)
        except Exception as e:
            print(f"AI REPLY ERR: {e}", flush=True)
            answer = "❌ AI reply দেওয়া যায়নি!"
        ctx["message"].send_and_remember(answer)
        return True

    # 2) A bare number replies to a pending song search.
    if text.isdigit() and _handle_song_number(ctx):
        return True

    # 3) ".bby teach <q> - <a>"
    if lower.startswith(".bby teach "):
        ctx["send"](teach(text))
        return True

    # 4) A learned reply.
    reply = taught_reply(text)
    if reply is not None:
        ctx["send"](reply)
        return True

    # Everything below only applies to messages that are NOT a bot command
    # (i.e. don't start with the configured prefix) — a prefixed message
    # falls through to normal command dispatch instead.
    if text.startswith(prefix):
        return False

    # 5) A bare link: auto-download it.
    if auto_detect and download_video:
        try:
            url = auto_detect(text)
        except Exception:
            url = None
        if url:
            try:
                ctx["send"](f"⏳ Downloading...\n🔗 {url}")
                path = download_video(url, client=ctx["client"])
                ctx["message"].send_video(path)
            except Exception as e:
                print(f"AUTO DL ERR: {e}", flush=True)
                ctx["send"]("❌ Download failed!")
            return True

    # 6) Greetings/menu are left for the command registry's no-prefix
    # aliases (commands/hi.py, commands/help.py) to answer.
    if lower in ("hi", "hello", "hey", "menu", "help"):
        return False

    # 7) Free-text AI chat fallback.
    if get_ai_reply:
        try:
            answer = get_ai_reply(text)
        except Exception as e:
            print(f"AI AUTO REPLY ERR: {e}", flush=True)
            return True
        if answer:
            ctx["message"].send_and_remember(answer)
        return True

    return False
