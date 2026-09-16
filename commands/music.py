"""Hinatav2-style full music search + numbered selection.

`music` searches JioSaavn first and fills missing results from YouTube.
A selected result is downloaded and sent as playable media by MessageContext.
"""
from commands.legacy.media import play, select_song, download_selected_song

CONFIG = {
    "name": "music",
    "aliases": ["m", "song", "stickermusic"],
    "category": "media",
    "cooldown": 5,
    "role": 0,
    "description": {"en": "Search a song and send the full audio"},
    "usage": {"en": "{p}music <song> or {p}music <number>"},
}


def on_start(ctx):
    args = ctx["args"]
    if not args:
        return "Usage: .music <song name>\nExample: .music blinding lights"

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
