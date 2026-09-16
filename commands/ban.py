from commands.admin import ban
CONFIG={"name":"ban","aliases":[],"category":"admin","cooldown":2,"role":2,"no_prefix":True,"description":{"en":"Ban or unban a user"},"usage":{"en":"{p}ban <userID> | {p}unban <userID>"}}
def on_start(ctx):
    if ctx.get("invoked_as")=="unban": return __import__('commands.admin',fromlist=['unban']).unban(ctx)
    return ban(ctx)
