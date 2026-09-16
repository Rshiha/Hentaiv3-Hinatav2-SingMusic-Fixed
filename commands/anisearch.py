"""Hinatav2 anisearch port: search TikTok anime clips and send one."""
import os, random, tempfile, requests

API_BASE = os.getenv("ANISEARCH_API", "https://alldl.neokex.xyz/api")
MAX_BYTES = int(os.getenv("IG_MAX_MEDIA_BYTES", str(5 * 1024 * 1024)))

CONFIG = {
    "name": "anisearch",
    "aliases": ["anivid", "animevid"],
    "category": "media",
    "cooldown": 5,
    "role": 0,
    "description": {"en": "Find and send a random anime video"},
    "usage": {"en": "{p}anisearch <anime or character>"},
}

def _json(url):
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "*/*"}, timeout=45)
    r.raise_for_status()
    return r.json()

def on_start(ctx):
    q = " ".join(ctx["args"]).strip()
    if not q:
        return "Usage: .anisearch <anime or character>"
    try:
        payload = _json(f"{API_BASE}/tik-sr?q={requests.utils.quote(q)}")
        results = payload.get("results") or payload.get("data", {}).get("results", [])
        urls = [x.get("url") for x in results if isinstance(x, dict) and x.get("url")]
        # Same retry strategy as Hinatav2: randomize candidates so a dead
        # first TikTok result does not make the whole command fail.
        if not urls:
            return "❌ No matching anime videos found."
        random.shuffle(urls)
        last = None
        for src in urls[:4]:
            try:
                data = _json(f"{API_BASE}/alldl?url={requests.utils.quote(src, safe='')}")
                meta = data.get("metadata", {}).get("data") or data.get("data") or data
                downloads = meta.get("downloads") or []
                item = next((x for x in downloads if x.get("url") and str(x.get("ext","")) == "mp4" and "audio" not in str(x.get("label","")).lower()), None)
                if not item:
                    item = next((x for x in downloads if x.get("url") and "audio" not in str(x.get("label","")).lower()), None)
                if not item:
                    continue
                r = requests.get(item["url"], headers={"User-Agent":"Mozilla/5.0"}, timeout=60, stream=True)
                r.raise_for_status()
                length = int(r.headers.get("content-length") or 0)
                if length > MAX_BYTES:
                    continue
                fd, path = tempfile.mkstemp(suffix=".mp4", prefix="anisearch_")
                os.close(fd)
                total = 0
                with open(path, "wb") as f:
                    for chunk in r.iter_content(65536):
                        if chunk:
                            total += len(chunk)
                            if total > MAX_BYTES:
                                raise ValueError("video too large")
                            f.write(chunk)
                ctx["send"](str(meta.get("title") or "Here is your anime video.")[:200])
                ctx["message"].send_video(path)
                return None
            except Exception as e:
                last = e
        return f"❌ Could not send an anime video: {last or 'unknown error'}"
    except Exception as e:
        return f"❌ Anime search failed: {e}"
