"""About command — Hinatav2-style module."""

CONFIG = {
    "name": "about",
    "aliases": [],
    "category": "info",
    "cooldown": 5,
    "role": 0,
    "description": {"en": "About this bot"},
    "usage": {"en": "{p}about"},
}


def on_start(ctx):
    name = ctx["config"].get("botName", "InstaBOT")
    return f"🐐 {name}\n🤖 Instagram DM Bot — modular Python build\nUse {ctx['config'].get('prefix', '.')}help"
