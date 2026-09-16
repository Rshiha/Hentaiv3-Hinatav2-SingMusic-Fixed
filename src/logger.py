"""
Small colored console logger.
Python port of Hinatav2's src/logger.js style (tags + colors), adapted for InstaGoat.
"""

import sys
from datetime import datetime

COLORS = {
    "info": "\033[36m",     # cyan
    "success": "\033[32m",  # green
    "warn": "\033[33m",     # yellow
    "error": "\033[31m",    # red
    "reset": "\033[0m",
}


def _emit(level, tag, message, error=None):
    ts = datetime.now().strftime("%H:%M:%S")
    color = COLORS.get(level, "")
    reset = COLORS["reset"]
    line = f"{color}[{ts}] [{tag}]{reset} {message}"
    print(line, flush=True, file=sys.stderr if level == "error" else sys.stdout)
    if error is not None:
        print(f"{color}    ↳ {repr(error)}{reset}", flush=True,
              file=sys.stderr if level == "error" else sys.stdout)


def info(tag, message):
    _emit("info", tag, message)


def success(tag, message):
    _emit("success", tag, message)


def warn(tag, message):
    _emit("warn", tag, message)


def error(tag, message, err=None):
    _emit("error", tag, message, err)
