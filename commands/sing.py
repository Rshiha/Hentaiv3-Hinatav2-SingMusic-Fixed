"""Hinatav2-style full-song command.

Searches the same music catalogue as `music`; numbered selection downloads
and sends the complete track rather than an Instagram music sticker.
"""
from commands.legacy.media import play, select_song, download_selected_song

CONFIG = {
    "name": "sing",
    "aliases": [],
    "category": "media",
    "cooldown": 10,
    "role": 0,
    "description": {"en": "Search and send a full song as audio"},
    "usage": {"en": "{p}sing <song> or {p}sing <number>"},
}


def on_start(ctx):
    args = ctx["args"]
    if not args:
        return "Usage: .sing <song name>\nExample: .sing blinding lights"

    if len(args) == 1 and args[0].isdigit():
        selected = select_song(int(args[0]), ctx["legacy_ctx"])
        if selected is None:
            return "❌ No pending song search. Search a song first."
        if isinstance(selected, str):
            return selected
        result = download_selected_song(selected)
        if isinstance(result, dict) and result.get("type") == "audio":
            return result
        return result or "❌ গান download করা যায়নি!"

    return play(args, ctx["legacy_ctx"])
