from commands.effect_cards import run
CONFIG={"name":"effect","aliases":["fx"],"category":"utility","cooldown":3,"role":0,"description":{"en":"Send an effect card"},"usage":{"en":"{p}effect <love|gift|celebration|fire> <text>"}}
def on_start(ctx): return run(ctx, ["love","gift","celebration","fire"])
