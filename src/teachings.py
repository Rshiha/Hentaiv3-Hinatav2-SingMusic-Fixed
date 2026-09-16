"""
".bby teach <q> - <a>" learned-reply store. Ported unchanged from the
original main.py (load_teachings/save_teachings/teach/taught_reply).
"""

import json
import os
import random

TEACH_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bby_teachings.json"
)


def load_teachings():
    try:
        if not os.path.exists(TEACH_FILE):
            return {}
        with open(TEACH_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
        result = {}
        if isinstance(data, list):
            for item in data:
                if not isinstance(item, dict):
                    continue
                q, a = item.get("question"), item.get("answer")
                if q and a:
                    result[str(q)] = str(a)
        return result
    except Exception as e:
        print(f"TEACH LOAD ERR: {e}", flush=True)
        return {}


TEACHINGS = load_teachings()


def save_teachings():
    try:
        with open(TEACH_FILE, "w", encoding="utf-8") as f:
            json.dump(TEACHINGS, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"TEACH SAVE ERR: {e}", flush=True)
        return False


def normalize(text):
    if not text:
        return ""
    text = " ".join(str(text).strip().lower().split())
    for char in "!?।,.;:'\"“”‘’`~":
        text = text.replace(char, "")
    return text.strip()


def teach(text):
    count = 0
    for line in text.splitlines():
        if not line.lower().startswith(".bby teach "):
            continue
        data = line[11:].strip()
        if " - " not in data:
            continue
        question, answer = data.split(" - ", 1)
        question = normalize(question)
        answer = answer.strip()
        if question and answer:
            existing = TEACHINGS.get(question)
            if existing is None:
                TEACHINGS[question] = answer
            elif isinstance(existing, list):
                if answer not in existing:
                    existing.append(answer)
            elif existing != answer:
                TEACHINGS[question] = [existing, answer]
            count += 1

    if count == 0:
        return "🥹 ঠিকভাবে teach করা হয়নি!\n\nExample:\n.bby teach hi - hello"
    if not save_teachings():
        return "❌ Teach save করা যায়নি!"
    return f"🥹 {count}টা কথা শিখে নিলাম! ❤️"


def pick_answer(answer):
    if isinstance(answer, list):
        return random.choice(answer) if answer else None
    return answer


def taught_reply(text):
    question = normalize(text)
    if not question:
        return None
    if question in TEACHINGS:
        return pick_answer(TEACHINGS[question])
    for key, answer in TEACHINGS.items():
        key_n = normalize(key)
        if len(key_n) >= 3 and key_n in question:
            return pick_answer(answer)
    return None
