import requests, os, uuid, random

def tik_command(args, ctx):
    if not args:
        return "❌ Usage: .tik funny"
    query = " ".join(args).replace("-", "").strip() or "funny"
    cl = ctx.get("client")
    thread_id = ctx.get("thread_id")
    try:
        cl.direct_send(f"🎵 TikTok search: {query}...", thread_ids=[thread_id])
        
        # Try 1: tikwm with browser headers
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Referer": "https://www.tikwm.com/",
                "Accept": "application/json, text/plain, */*",
                "Origin": "https://www.tikwm.com"
            }
            r = requests.post("https://www.tikwm.com/api/feed/search",
                data={"keywords": query, "count": "10", "cursor": "0"},
                headers=headers, timeout=20)
            if r.status_code == 200:
                j = r.json()
                videos = j.get("data", {}).get("videos", [])
                if videos:
                    v = random.choice(videos)
                    vurl = v.get("play") or v.get("wmplay")
                    if vurl:
                        tmp = f"/tmp/{uuid.uuid4().hex[:8]}.mp4"
                        with requests.get(vurl, headers={"User-Agent": "Mozilla/5.0"}, stream=True, timeout=30) as resp:
                            with open(tmp, "wb") as f:
                                for c in resp.iter_content(1024*64):
                                    if c: f.write(c)
                        cl.direct_send_video(tmp, thread_ids=[thread_id])
                        try: os.remove(tmp)
                        except: pass
                        return f"✅ Done: {query}"
        except Exception as e:
            print(f"TIK wm fail {e}")

        # Try 2: Tell user to use .dl
        return "❌ TikTok API Blocked (Status: 403)\nRender IP block korse. Direct link diye .dl use koro:\n.dl https://www.tiktok.com/@user/video/123"
        
    except Exception as e:
        print(f"TIK ERROR {e}")
        return "❌ TikTok error!"

TIKTOK_COMMANDS = {"tik": tik_command, "tiktok": tik_command}
