"""AI image generation kept separate from Hinatav2's .img media sender."""
import os
from ai import generate_pic
CONFIG={"name":"aiimg","aliases":["pic","imageai"],"category":"ai","cooldown":5,"role":0,"description":{"en":"Generate an AI image"},"usage":{"en":"{p}aiimg <prompt>"}}
def on_start(ctx):
    p=" ".join(ctx["args"]).strip()
    if not p: return "Usage: .aiimg <prompt>"
    path=generate_pic(p)
    if not path or not os.path.exists(path): return "❌ Image বানানো যায়নি!"
    try:
        with ctx["legacy_ctx"]["ig_lock"]:
            ctx["client"].direct_send_photo(path,thread_ids=[ctx["legacy_ctx"]["thread_id"]])
    finally:
        try: os.remove(path)
        except Exception: pass
    return None
