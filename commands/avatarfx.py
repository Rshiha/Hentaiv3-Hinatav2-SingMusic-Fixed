from commands.effect_cards import run
CONFIG={"name":"avatarfx","aliases":["avfx","avatar-effect"],"category":"utility","cooldown":3,"role":0,"description":{"en":"Send an avatar effect card"},"usage":{"en":"{p}avatarfx <love|angry|laugh|cry> <text>"}}
def on_start(ctx): return run(ctx,["love","angry","laugh","cry"])
