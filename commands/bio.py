from commands.admin import bio
CONFIG={"name":"bio","aliases":["setbio","biography"],"category":"profile","cooldown":5,"role":2,"no_prefix":True,"description":{"en":"Change bot biography"},"usage":{"en":"{p}bio <text>"}}
def on_start(ctx): return bio(ctx)
