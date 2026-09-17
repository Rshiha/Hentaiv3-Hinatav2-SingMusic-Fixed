"""Hinatav2-style full-song command.

Searches the music catalogue, shows numbered options, and allows users
to directly REPLY to the list message with a number to send the full audio.
"""
import requests
import urllib.parse

CONFIG = {
    "name": "sing",
    "aliases": [],
    "author": "Neoaz 🐊",
    "category": "media",
    "cooldown": 10,
    "role": 0,
    "description": {"en": "Search and send a full song as audio"},
    "usage": {"en": "{p}sing <song> or reply to list with <number>"},
}

# মেমোরিতে সাময়িকভাবে সার্চ রেজাল্ট রাখার জন্য গ্লোবাল ক্যাশ
SEARCH_CACHE = {}

def format_duration(ms):
    if not ms or ms < 0: 
        return "0:00"
    total_sec = round(ms / 1000)
    return f"{total_sec // 60}:{str(total_sec % 60).zfill(2)}"

def pick_audio_url(track):
    if not track or not isinstance(track, dict):
        return None
    keys = ["url", "downloadUrl", "download_url", "audioUrl", "audio_url", "previewUrl", "streamUrl", "stream", "link", "src"]
    for k in keys:
        val = track.get(k)
        if isinstance(val, str) and val.startswith("http"): 
            return val
        if isinstance(val, dict):
            nested = val.get("url") or val.get("link") or val.get("src")
            if isinstance(nested, str) and nested.startswith("http"): 
                return nested
    return None

def process_and_send_song(api, thread_id, reply_to_mid, track):
    """গানের নাম টেক্সট আকারে প্রথমে পাঠাবে, তারপর অডিও ভয়েস মেসেজ হিসেবে পাঠাবে"""
    title_text = f"{track['title']} — {track['artist']} ({track['duration']})"
    
    # ১. প্রথমে টেক্সট মেসেজ পাঠানো হচ্ছে (স্ক্রিনশটের মতো)
    if hasattr(api, "send_message"):
        api.send_message(title_text, thread_id, reply_to_message_id=reply_to_mid)
    
    # ২. তারপর অডিও ফাইলটি পাঠানো হচ্ছে
    if hasattr(api, "send_audio"):
        try:
            api.send_audio(track["url"], thread_id, reply_to_message_id=reply_to_mid)
        except Exception as audio_err:
            # যদি সরাসরি ইউআরএল সাপোর্ট না করে তবে ডাউনলোড করে পাঠানো (সেফটি ব্যাকআপ)
            if hasattr(api, "send_file"):
                try:
                    file_name = f"song_{thread_id}.mp4"
                    r = requests.get(track["url"], stream=True)
                    with open(file_name, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=1024):
                            if chunk: f.write(chunk)
                    api.send_file(file_name, thread_id, reply_to_message_id=reply_to_mid)
                    import os
                    os.remove(file_name)
                except:
                    pass

def on_start(ctx):
    args = ctx.get("args", [])
    api = ctx.get("api") or ctx.get("client")
    message = ctx.get("message")
    event = ctx.get("event", {})
    
    thread_id = event.get("thread_id") or event.get("threadID")
    sender_id = event.get("user_id") or event.get("senderID")
    message_id = event.get("message_id") or event.get("messageID")

    # ডাটা ইনপুট চেক
    query = " ".join(args).strip()

    # ————————————————————————————————————————————————————————————————
    # লজিক ১: ইউজার যদি মেসেজে সরাসরি রিপ্লাই দেয় (Reply Handler Simulation)
    # ————————————————————————————————————————————————————————————————
    reply_to = event.get("reply_to") or event.get("message_reply")
    
    # যদি মেসেজটি কোনো রিপ্লাই হয় এবং রিপ্লাই টেক্সটটি একটি নম্বর হয়
    if reply_to or (query.isdigit() and not args):
        pick = query if query.isdigit() else "".join(filter(str.isdigit, query))
        if pick and sender_id in SEARCH_CACHE:
            idx = int(pick) - 1
            cached = SEARCH_CACHE[sender_id]
            if 0 <= idx < len(cached):
                selected_track = cached[idx]
                # সরাসরি সেন্ড ফাংশন রান করে রিটার্ন করা হচ্ছে
                process_and_send_song(api, thread_id, message_id, selected_track)
                return None  # আলাদা করে আর কোনো টেক্সট রিটার্ন করার প্রয়োজন নেই
            else:
                return f"❌ ১ থেকে {len(cached)}-এর মধ্যে নম্বর বেছে নিন।"

    if not args:
        return "Usage: .sing <song name>\nExample: .sing blinding lights"

    # ————————————————————————————————————————————————————————————————
    # লজিক ২: নতুন গান সার্চ করা
    # ————————————————————————————————————————————————————————————————
    config = ctx.get("config", {})
    music = config.get("music", {}) if config else {}
    raw_list = []

    # কাস্টম এপিআই কনফিগ থাকলে
    if music.get("enable") != False and music.get("apiUrl"):
        api_url = music["apiUrl"]
        url = api_url.replace("{query}", urllib.parse.quote(query)) if "{query}" in api_url else f"{api_url}?query={urllib.parse.quote(query)}"
        headers = {"Accept": "application/json"}
        if music.get("apiToken"):
            headers["Authorization"] = f"Bearer {music['apiToken']}"
        try:
            res = requests.get(url, headers=headers)
            if res.status_code == 200:
                data = res.json()
                raw_list = data if isinstance(data, list) else (data.get("tracks") or data.get("results") or data.get("data") or [])
        except:
            pass

    # কাস্টম এপিআই না থাকলে ইন্টারনাল সার্চ
    if not raw_list and message and hasattr(message, "musicSearch"):
        try:
            res = message.musicSearch(query)
            raw_list = res if isinstance(res, list) else (res.get("tracks") or res.get("results") or res.get("data") or [])
        except:
            return "❌ গান সার্চ করতে ব্যর্থ হয়েছে।"

    # ডাটা নরমালইজেশন
    tracks = []
    for item in raw_list:
        if not item: continue
        t = item.get("track") if isinstance(item, dict) and "track" in item else item
        if not isinstance(t, dict): continue
        
        url = pick_audio_url(item) or pick_audio_url(t)
        if url:
            tracks.append({
                "title": t.get("title") or t.get("name") or "Unknown",
                "artist": t.get("artist") or t.get("singer") or "Unknown",
                "duration": format_duration(t.get("duration_ms") or t.get("duration") or 0),
                "url": url
            })

    if not tracks:
        return "❌ কোনো গান খুঁজে পাওয়া যায়নি!"

    top_tracks = tracks[:10]
    SEARCH_CACHE[sender_id] = top_tracks

    # ১টি গান পাওয়া গেলে সরাসরি প্লে হবে
    if len(top_tracks) == 1 or "--top" in args:
        process_and_send_song(api, thread_id, message_id, top_tracks[0])
        return None

    # গানগুলোর তালিকা তৈরি
    lines = [f"{i+1}. {t['title']} — {t['artist']} ({t['duration']})" for i, t in enumerate(top_tracks)]
    reply_text = f"Full songs for \"{query}\"\n" + "\n".join(lines) + "\n\nReply with sing <number> to send one."
    return reply_text
                        
