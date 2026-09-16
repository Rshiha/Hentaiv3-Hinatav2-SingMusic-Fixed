import requests, re, random

def pin_command(args, ctx):
    if not args:
        return "❌ Usage: .pin cat"
    query = " ".join(args).replace("-", "").strip() or "cat"
    cl = ctx.get("client")
    thread_id = ctx.get("thread_id")
    try:
        cl.direct_send(f"📌 Searching: {query}...", thread_ids=[thread_id])
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}
        # Bing image search - Render e block hoy na
        url = f"https://www.bing.com/images/search?q={query}&form=HDRSC2&first=1"
        r = requests.get(url, headers=headers, timeout=15)
        # Bing er murl extract
        imgs = re.findall(r'"murl":"(https://[^"]+\.(?:jpg|jpeg|png|webp))"', r.text)
        imgs = list(set(imgs))[:20]
        
        if not imgs:
            return f"❌ '{query}' pic pailam na!"
        
        sent = 0
        for img in imgs[:10]:
            try:
                cl.direct_send_image(img, thread_ids=[thread_id])
                sent += 1
            except:
                pass
        
        return f"✅ {sent} ta {query} pic sent!" if sent else "❌ Send fail"
    except Exception as e:
        print(f"PIN ERROR {e}")
        return "❌ Pinterest error!"

PINTEREST_COMMANDS = {"pin": pin_command, "pinterest": pin_command}
