"""Admin commands: ban/unban, whitelist, profile bio/avatar and group removal."""
import json, os, tempfile, requests
from src.config import CONFIG_PATH, load

CONFIG={"name":"admin","aliases":[],"category":"admin","cooldown":2,"role":2,"description":{"en":"Administrative controls"},"usage":{"en":"Use .ban/.unban/.whitelist/.bio/.avatar/.removeuser"}}

def _save(cfg):
    with open(CONFIG_PATH,"w",encoding="utf-8") as f: json.dump(cfg,f,ensure_ascii=False,indent=2)

def _target(ctx):
    if ctx["args"] and ctx["args"][0].isdigit(): return ctx["args"][0]
    raw=ctx.get("raw_message")
    rid=getattr(raw,"reply_to_user_id",None) or getattr(raw,"reply_to_sender_id",None)
    return str(rid) if rid else None

def _subcommand(ctx):
    return (ctx["args"][0].lower() if ctx["args"] else "")

def ban(ctx):
    uid=_target(ctx)
    if not uid:return "Usage: .ban <userID> [reason] (or reply)"
    u=ctx["usersData"].ensure(uid,{"userID":uid})
    u["banned"]={"status":True,"reason":" ".join(ctx["args"][1:]) or "—","date":__import__('time').time()}; return f"🚫 Banned: {uid}"

def unban(ctx):
    uid=_target(ctx)
    if not uid:return "Usage: .unban <userID>"
    u=ctx["usersData"].ensure(uid,{"userID":uid}); u["banned"]={"status":False,"reason":None,"date":None}; return f"✅ Unbanned: {uid}"

def whitelist(ctx):
    cfg=ctx["config"]; wl=cfg.setdefault("whiteList",{"enable":False,"userIDs":[],"threadIDs":[]}); a=(ctx["args"][0].lower() if ctx["args"] else "list")
    if a in ("on","off"):
        wl["enable"]=a=="on"; _save(cfg); return f"Whitelist mode: {a.upper()}"
    if a=="list": return f"Whitelist: {'ON' if wl.get('enable') else 'OFF'}\nUsers: {', '.join(wl.get('userIDs',[])) or '—'}\nThreads: {', '.join(wl.get('threadIDs',[])) or '—'}"
    if a in ("add","remove") and len(ctx["args"])>=2:
        kind=ctx["args"][1].lower(); uid=ctx["args"][2] if len(ctx["args"])>=3 else ctx["user_id"]
        key="threadIDs" if kind in ("thread","box") else "userIDs"; arr=wl.setdefault(key,[]); uid=str(uid)
        if a=="add" and uid not in arr: arr.append(uid)
        if a=="remove": wl[key]=[x for x in arr if x!=uid]
        _save(cfg); return f"✅ Whitelist {a}: {uid}"
    return "Usage: .whitelist on|off|list|add user <id>|remove user <id>|add thread <id>|remove thread <id>"

def bio(ctx):
    text=" ".join(ctx["args"]).strip()
    if not text:return "Usage: .bio <text>"
    ctx["client"].account_set_biography(text); return "✅ Bio changed."

def avatar(ctx):
    src=ctx["args"][0] if ctx["args"] else None
    if not src:return "Usage: .avatar <imageURL>"
    r=requests.get(src,timeout=30,headers={"User-Agent":"Mozilla/5.0"}); r.raise_for_status(); fd,path=tempfile.mkstemp(suffix=".jpg",prefix="avatar_"); os.close(fd)
    try:
        with open(path,"wb") as f:f.write(r.content)
        ctx["client"].account_change_picture(path); return "✅ Avatar changed."
    finally:
        try:os.remove(path)
        except Exception:pass

def removeuser(ctx):
    if len(ctx["args"]) < 1:
        return "Usage: .removeuser <userID>"
    uid = str(ctx["args"][0]).strip()
    if not uid.isdigit():
        return "❌ userID must be numeric."
    tid = str(ctx["legacy_ctx"].get("thread_id") or "").strip()
    if not tid:
        return "❌ No thread id."
    client = ctx["client"]
    try:
        # Some newer instagrapi builds may expose a high-level remover.
        method = getattr(client, "direct_thread_remove_users", None)
        if callable(method):
            ok = method(int(tid), [int(uid)])
            if ok is False:
                raise RuntimeError("Instagram rejected the removal")
        else:
            # Current instagrapi has no documented high-level remove method,
            # so use Instagram's direct_v2 endpoint used by the web client.
            data = {"user_ids": json.dumps([int(uid)]), "_uuid": getattr(client, "uuid", "")}
            result = client.private_request(
                f"direct_v2/threads/{tid}/remove_users/",
                data=data,
                with_signature=False,
            )
            if isinstance(result, dict) and result.get("status") not in (None, "ok"):
                raise RuntimeError(str(result))
        return f"✅ Removed {uid} from the thread."
    except Exception as e:
        print(f"REMOVEUSER ERR: {e}", flush=True)
        return f"❌ Remove failed: {e}"

# Registry uses separate command names; this module's CONFIG is only a namespace.
