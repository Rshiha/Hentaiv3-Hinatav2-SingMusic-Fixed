import os,tempfile
from PIL import Image,ImageDraw,ImageFont

def run(ctx,effects):
    if not ctx["args"]: return "Pick an effect: "+", ".join(effects)
    effect=ctx["args"][0].lower()
    if effect not in effects:return "Pick an effect: "+", ".join(effects)
    text=" ".join(ctx["args"][1:]) or "✨"
    im=Image.new("RGB",(900,500),(30,30,30)); d=ImageDraw.Draw(im)
    try: font=ImageFont.truetype("DejaVuSans-Bold.ttf",42); small=ImageFont.truetype("DejaVuSans.ttf",28)
    except Exception: font=small=None
    d.text((40,35),f"{effect.upper()} EFFECT",font=font,fill=(255,255,255)); d.text((40,180),text[:300],font=small,fill=(255,255,255))
    fd,path=tempfile.mkstemp(suffix=".jpg",prefix="effect_"); os.close(fd); im.save(path,"JPEG",quality=90)
    try:
        with ctx["legacy_ctx"]["ig_lock"]: ctx["client"].direct_send_photo(path,thread_ids=[ctx["legacy_ctx"]["thread_id"]])
    finally:
        try:os.remove(path)
        except Exception:pass
    return None
