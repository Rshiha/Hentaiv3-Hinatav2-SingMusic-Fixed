import os
import nest_asyncio
import requests
try:
    from g4f.client import Client
    client = Client()
except Exception as e:
    Client = None
    client = None
    print(f"g4f unavailable; using fallback AI: {e}", flush=True)

nest_asyncio.apply()

# =========================
# INSTAGRAPI DM CRASH FIX
# =========================
try:
    from instagrapi import Client as _IGClient
    if not getattr(_IGClient, "_dm_url_patch_applied", False):
        _original_private_request = _IGClient.private_request
        def _sanitize_bad_urls(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if (isinstance(v, str) and "url" in k.lower() and "://" in v and not v.startswith(("http://", "https://"))):
                        obj[k] = ""
                    elif isinstance(v, (dict, list)):
                        _sanitize_bad_urls(v)
            elif isinstance(obj, list):
                for item in obj:
                    _sanitize_bad_urls(item)
            return obj
        def _patched_private_request(self, endpoint, *args, **kwargs):
            result = _original_private_request(self, endpoint, *args, **kwargs)
            if isinstance(result, dict):
                _sanitize_bad_urls(result)
            return result
        _IGClient.private_request = _patched_private_request
        _IGClient._dm_url_patch_applied = True
        print("🩹 instagrapi DM url-scheme patch applied", flush=True)
except Exception as e:
    print(f"DM URL PATCH ERR: {e}", flush=True)

# === BANGLISH SYSTEM PROMPT ===
SYSTEM_PROMPT = """Tumi ekta funny Bengali friend, naam tomar BakaBot.
Rule:
- SOB SOMOY Banglish e reply diba (Bangla kotha English okkhor e). Kokhono pure English bolba na like 'Sure thing', 'Of course', 'How can I help'.
- Style: choto, moja kore, friendly, 1-3 line er moddhe. Beshi boro rochona likhba na.
- Emoji majhe majhe use korba 🖤😅
- User ja bolbe tar reply Banglish e diba."""

def get_ai_reply(text: str, history=None) -> str:
    """main.py's.ai command / auto-reply ei function ke call kore."""
    # g4f er jonno system prompt soho message banano
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        messages.extend(history[-30:])
    messages.append({"role": "user", "content": text})

    try:
        if client is None:
            raise RuntimeError("g4f is not installed")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            web_search=False,
        )
        result = response.choices[0].message.content
        if result and result.strip():
            return result.strip()
    except Exception as e:
        print(f"AI TEXT (g4f) ERR: {e}", flush=True)

    # --- backup: Pollinations (key lage na) - prompt er sathe system jure deya ---
    try:
        combined_prompt = f"{SYSTEM_PROMPT}\n\nUser: {text}\nBakaBot:"
        r = requests.get(
            f"https://text.pollinations.ai/{requests.utils.quote(combined_prompt)}",
            timeout=15,
        )
        if r.status_code == 200 and len(r.text.strip()) > 2 and "budget" not in r.text.lower():
            return r.text.strip()
    except Exception as e:
        print(f"AI TEXT (pollinations) ERR: {e}", flush=True)

    return "Areh ektu busy achi re, ektu pore bol 🖤"

def generate_pic(prompt: str):
    """main.py's.img/.pic command ei function ke call kore."""
    try:
        if client is None:
            raise RuntimeError("g4f is not installed")
        response = client.images.generate(model="flux", prompt=prompt)
        image_url = response.data[0].url
        img_data = requests.get(image_url, timeout=20).content
        file_path = f"/tmp/gen_img_{os.getpid()}_{abs(hash(prompt)) % 100000}.jpg"
        with open(file_path, "wb") as f:
            f.write(img_data)
        return file_path
    except Exception as e:
        print(f"AI IMG (g4f) ERR: {e}", flush=True)

    try:
        url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}?width=768&height=768&nologo=true"
        r = requests.get(url, timeout=30)
        if r.status_code == 200 and r.content and len(r.content) > 500:
            file_path = f"/tmp/gen_img_{os.getpid()}_{abs(hash(prompt)) % 100000}.jpg"
            with open(file_path, "wb") as f:
                f.write(r.content)
            return file_path
    except Exception as e:
        print(f"AI IMG (pollinations) ERR: {e}", flush=True)
    return None
