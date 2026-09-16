import random
def love(a,c): return f"❤️ Love: {random.randint(0,100)}%"
def hug(a,c): return "🤗 Big friendly hug!"
def kiss(a,c): return "💋 Friendly kiss!"
def slap(a,c): return "😂 Playful virtual slap!"
def ship(a,c): return f"💖 Ship: {random.randint(0,100)}%"
def rps(a,c):
 u=a[0].lower() if a and a[0].lower() in ["rock","paper","scissors"] else "rock"; b=random.choice(["rock","paper","scissors"])
 return f"🪨 You: {u}\n🤖 Bot: {b}\n🏆 "+("Draw!" if u==b else "You win! 🎉" if (u,b) in [("rock","scissors"),("paper","rock"),("scissors","paper")] else "Bot wins! 🤖")
SOCIAL_COMMANDS={"love":love,"hug":hug,"kiss":kiss,"slap":slap,"ship":ship,"rps":rps}
