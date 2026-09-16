"""Greeting command — Hinatav2-style module (CONFIG + on_start)."""

CONFIG = {
    "name": "hi",
    "aliases": ["hello", "hey"],
    "category": "info",
    "cooldown": 2,
    "role": 0,
    "no_prefix": True,       # can be said bare, no "." needed
    "no_prefix_role": 0,     # ...by anyone, not just the bot admin
    "description": {"en": "Say hello to the bot"},
    "usage": {"en": "{p}hi"},
}


def on_start(ctx):
    username = ctx["legacy_ctx"].get("username", "Friend")
    return f"👋 Hello {username}!\n🐐 {ctx['config'].get('botName', 'InstaBOT')} is here!"
