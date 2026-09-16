"""Ping command — Hinatav2-style module."""
import time

CONFIG = {
    "name": "ping",
    "aliases": ["pong"],
    "category": "info",
    "cooldown": 2,
    "role": 0,
    "description": {"en": "Check whether the bot is online"},
    "usage": {"en": "{p}ping"},
}


def on_start(ctx):
    start = time.time()
    ctx["message"].reply("🏓 Pong...")
    ms = int((time.time() - start) * 1000)
    return f"🏓 Pong! ({ms}ms)"
