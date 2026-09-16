"""
InstaGoat-Py — modular Python port of Instagoat-render, restructured in the
Hinatav2 style (config-driven prefix/roles/cooldowns, a command registry
loaded from commands/, event scripts loaded from events/, a dispatcher that
fans messages out to both).

This file only wires up Flask (health check + the temporary /audio link used
for song downloads) and starts the bot. All the bot logic itself lives in
src/ and commands/ — see README.md for the layout.
"""

import os

from flask import Flask, abort, request, send_from_directory

from src import bot
from src.config import CONFIG

try:
    from commands.legacy.media import DOWNLOAD_DIR
except Exception:
    DOWNLOAD_DIR = "/tmp/downloads"

app = Flask(__name__)

CRAWLER_UA_MARKERS = (
    "facebookexternalhit", "facebookcatalog", "facebookbot",
    "meta-externalagent", "instagram",
)


@app.route("/")
def home():
    s = bot.status()
    return f"🐐 {CONFIG.get('botName', 'InstaBOT')} LIVE! @{s['username']}"


@app.route("/audio/<path:filename>")
def serve_audio(filename):
    # Serves temporarily-downloaded songs as a link, since Instagram DMs
    # only accept JPG/JPEG/PNG/WEBP as raw file uploads. Meta's own
    # link-preview crawler re-fetches any raw link it sees in a DM to build
    # a preview, so it's blocked here to avoid hammering the route / using
    # up the short-lived file before the actual recipient opens the link.
    ua = (request.headers.get("User-Agent") or "").lower()
    if any(marker in ua for marker in CRAWLER_UA_MARKERS):
        abort(403)

    safe_name = os.path.basename(filename)
    if not os.path.isfile(os.path.join(DOWNLOAD_DIR, safe_name)):
        abort(404)

    return send_from_directory(DOWNLOAD_DIR, safe_name, as_attachment=True)


@app.route("/health")
def health():
    s = bot.status()
    return {
        "status": "online",
        "bot": CONFIG.get("botName", "InstaBOT"),
        "username": s["username"],
        "running": s["running"],
        "commands": s["commands"],
        "events": s["events"],
        "poll_interval": bot.POLL_INTERVAL,
    }


# Bot + worker threads start once, at import time (same as the original).
bot.start()

if __name__ == "__main__":
    # Render supplies its own port via the PORT env var.
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "10000")))
