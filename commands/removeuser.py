from commands.admin import removeuser
CONFIG={"name":"removeuser","aliases":["kick","removefromuser","removemember"],"category":"admin","cooldown":2,"role":2,"no_prefix":True,"description":{"en":"Remove a user from the current group thread"},"usage":{"en":"{p}removeuser <userID>"}}
def on_start(ctx): return removeuser(ctx)
