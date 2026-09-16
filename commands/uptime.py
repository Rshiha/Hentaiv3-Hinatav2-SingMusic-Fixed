"""Uptime command — Hinatav2-style module."""
import time

CONFIG = {
    "name": "uptime",
    "aliases": [],
    "category": "info",
    "cooldown": 2,
    "role": 0,
    "description": {"en": "How long the bot has been running"},
    "usage": {"en": "{p}uptime"},
}


def on_start(ctx):
    seconds = int(time.time() - ctx["legacy_ctx"].get("start_time", time.time()))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"⏱️ {h}h {m}m {s}s"
