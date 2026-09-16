from commands.admin import whitelist
CONFIG={"name":"whitelist","aliases":["wl"],"category":"admin","cooldown":2,"role":2,"no_prefix":True,"description":{"en":"Manage whitelist"},"usage":{"en":"{p}whitelist on|off|list|add|remove"}}
def on_start(ctx): return whitelist(ctx)
