"""Hinatav2-style conversational AI with persistent per-user/thread history."""
import json, os, time
from ai import get_ai_reply

STATE=os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "ai-state.json")
MAX_HISTORY=30
TTL=6*60*60

def _load():
    try:
        with open(STATE,"r",encoding="utf-8") as f: return json.load(f)
    except Exception: return {}

def _save(data):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    try:
        with open(STATE,"w",encoding="utf-8") as f: json.dump(data,f,ensure_ascii=False,indent=2)
    except Exception: pass

CONFIG={"name":"ai","aliases":["chatgpt"],"category":"ai","cooldown":2,"role":0,"description":{"en":"Conversational AI"},"usage":{"en":"{p}ai <question>"}}

def on_start(ctx):
    q=" ".join(ctx["args"]).strip()
    if not q: return "Usage: .ai <question>"
    state=_load(); key=f"{ctx['legacy_ctx']['thread_id']}:{ctx['user_id']}"; now=time.time()
    s=state.get(key,{"history":[],"lastActive":0})
    if now-s.get("lastActive",0)>TTL: s={"history":[],"lastActive":now}
    history=s.get("history",[])
    # get_ai_reply accepts optional history in the upgraded ai.py
    try: answer=get_ai_reply(q, history=history)
    except TypeError: answer=get_ai_reply(q)
    history += [{"role":"user","content":q},{"role":"assistant","content":answer}]
    s={"history":history[-MAX_HISTORY:],"lastActive":now}; state[key]=s
    _save(state)
    return answer
