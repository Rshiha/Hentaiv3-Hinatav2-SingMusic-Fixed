from commands.admin import avatar
CONFIG={"name":"avatar","aliases":["setavatar","setavt"],"category":"profile","cooldown":5,"role":2,"no_prefix":True,"description":{"en":"Change bot profile picture"},"usage":{"en":"{p}avatar <imageURL>"}}
def on_start(ctx): return avatar(ctx)
