AUTO_REPLIES = {
    "good morning": "🌅 Good morning!",
    "good night": "🌙 Good night!",
    "thank you": "❤️ You're welcome!",
    "thanks": "😊 Anytime!",
    "love you": "❤️ Love you too!",
    "who are you": "🐐 I'm Your Father Shihab."
}


def about(a, c):
    return "🐐 Your Father Shihab\n🤖 Instagram DM Bot\nUse .menu"


import random


def pair(a, c):
    thread = c.get("thread")

    if not thread:
        return "❌ Group information পাওয়া যায়নি।"

    participants = getattr(thread, "users", None) or []

    participants = [
        user for user in participants
        if str(getattr(user, "pk", "")) != str(c.get("client").user_id)
    ]

    if len(participants) < 2:
        return "❌ Pair করার জন্য কমপক্ষে ২ জন member দরকার।"

    user1, user2 = random.sample(participants, 2)

    name1 = getattr(user1, "username", "Unknown")
    name2 = getattr(user2, "username", "Unknown")

    love = random.randint(50, 100)

    if love >= 90:
        message = "🔥 Perfect couple!"
    elif love >= 75:
        message = "💕 Looking good together!"
    elif love >= 60:
        message = "😊 Cute pair!"
    else:
        message = "😂 Try again!"

    return (
        "💞 TODAY'S PERFECT PAIR 💞\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👦 @{name1}\n"
        f"❤️ @{name2}\n\n"
        f"💘 Love Percentage: {love}%\n"
        f"💑 {message}\n"
        "━━━━━━━━━━━━━━━━━━"
    )


def pair2(a, c):
    return pair(a, c)


def pair3(a, c):
    return pair(a, c)


EXTRA_COMMANDS = {
    "about": about,
    "pair": pair,
    "pair2": pair2,
    "pair3": pair3
}
