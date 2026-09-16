from commands.admin import unban
CONFIG={"name":"unban","aliases":[],"category":"admin","cooldown":2,"role":2,"no_prefix":True,"description":{"en":"Unban a user"},"usage":{"en":"{p}unban <userID>"}}
def on_start(ctx): return unban(ctx)
