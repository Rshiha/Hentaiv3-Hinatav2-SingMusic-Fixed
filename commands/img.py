"""Hinatav2-compatible image sender. Use .aiimg for AI image generation."""
import os, tempfile, requests

CONFIG = {
    "name": "img",
    "aliases": ["image", "sendimg"],
    "category": "media",
    "cooldown": 3,
    "role": 0,
    "description": {"en": "Send an image from a URL or replied media"},
    "usage": {"en": "{p}img <imageURL>"},
}

def _urls(obj, depth=0):
    if depth > 5 or obj is None: return []
    if isinstance(obj, str): return [obj] if obj.startswith(("http://", "https://")) else []
    if isinstance(obj, dict):
        out=[]
        for k,v in obj.items():
            if k.lower() in {"url","profile_pic_url","thumbnail_url","preview_url"}: out += _urls(v, depth+1)
            elif isinstance(v,(dict,list)): out += _urls(v, depth+1)
        return out
    if isinstance(obj, (list,tuple,set)):
        out=[]
        for v in obj: out += _urls(v, depth+1)
        return out
    try:
        if hasattr(obj, "model_dump"): return _urls(obj.model_dump(), depth+1)
        if hasattr(obj, "dict"): return _urls(obj.dict(), depth+1)
        if hasattr(obj, "__dict__"): return _urls(vars(obj), depth+1)
    except Exception: pass
    return []

def on_start(ctx):
    urls=[]
    if ctx["args"] and ctx["args"][0].startswith(("http://","https://")):
        urls.append(ctx["args"][0])
    raw=ctx.get("raw_message")
    urls += _urls(raw)
    urls=list(dict.fromkeys(urls))[:4]
    if not urls: return "Give me an image URL, or reply to an image."
    for url in urls:
        try:
            r=requests.get(url, timeout=30, headers={"User-Agent":"Mozilla/5.0"})
            r.raise_for_status()
            if not r.content: continue
            fd,path=tempfile.mkstemp(suffix=".jpg", prefix="img_"); os.close(fd)
            with open(path,"wb") as f: f.write(r.content)
            with ctx["legacy_ctx"]["ig_lock"]:
                ctx["client"].direct_send_photo(path, thread_ids=[ctx["legacy_ctx"]["thread_id"]])
            os.remove(path)
        except Exception as e:
            try: os.remove(path)
            except Exception: pass
            return f"❌ Could not send image: {e}"
    return None
