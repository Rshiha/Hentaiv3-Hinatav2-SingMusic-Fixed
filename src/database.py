"""
JSON-file store for per-user and per-thread data — no DB server needed,
same "just JSON files" philosophy as Hinatav2's src/database.js.
"""

import json
import os
import threading

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(DATA_DIR, exist_ok=True)


class JSONStore:
    def __init__(self, filename):
        self.path = os.path.join(DATA_DIR, filename)
        self._lock = threading.Lock()
        self._data = self._read()

    def _read(self):
        if not os.path.isfile(self.path):
            return {}
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def flush(self):
        with self._lock:
            try:
                with open(self.path, "w", encoding="utf-8") as f:
                    json.dump(self._data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"DB SAVE ERR ({self.path}): {e}", flush=True)

    def get(self, key):
        return self._data.get(str(key))

    def ensure(self, key, defaults=None):
        key = str(key)
        if key not in self._data:
            self._data[key] = dict(defaults or {})
        return self._data[key]

    def update(self, key, patch):
        key = str(key)
        entry = self._data.setdefault(key, {})
        entry.update(patch)
        return entry


class Database:
    def __init__(self):
        self.users = JSONStore("users.json")
        self.threads = JSONStore("threads.json")

    def flush(self):
        self.users.flush()
        self.threads.flush()


DATABASE = Database()
