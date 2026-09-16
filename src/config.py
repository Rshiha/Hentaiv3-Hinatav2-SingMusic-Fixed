"""
Config loader. Mirrors Hinatav2's config.json + environment-variable override
pattern (env ALWAYS wins over config.json), adapted for InstaGoat.
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT, "config.json")

DEFAULTS = {
    "botName": "Your Father Shihab",
    "prefix": ".",
    "language": "en",
    "cooldown": {"default": 2},
    "adminBot": [],
    "whiteList": {"enable": False, "userIDs": [], "threadIDs": []},
    "hideNotiMessage": {
        "commandNotFound": False,
        "onlyAdminBot": False,
    },
}


def _deep_merge(base, override):
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load():
    cfg = dict(DEFAULTS)

    if os.path.isfile(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = _deep_merge(cfg, json.load(f))
        except Exception as e:
            print(f"CONFIG LOAD ERR: {e}", flush=True)

    # Environment always wins, same rule as Hinatav2.
    if os.getenv("BOT_PREFIX"):
        cfg["prefix"] = os.getenv("BOT_PREFIX")

    if os.getenv("IG_ADMIN_BOT"):
        cfg["adminBot"] = [
            x.strip() for x in os.getenv("IG_ADMIN_BOT").split(",") if x.strip()
        ]

    return cfg


CONFIG = load()
