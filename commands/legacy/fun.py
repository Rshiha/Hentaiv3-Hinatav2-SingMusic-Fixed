import random
def joke(a, c):
    return random.choice([
        "😂 Ekjon bollo: Bhai, tui eto chupchap keno?\nArekjon: Mobile-er battery 1%, tai amio low power mode-e achi! 🤣",
        "🤣 Teacher: Homework kothay?\nStudent: Sir, Google Drive-e chilo... net chole jawar por theke khuje pachhi na! 😂",
        "😂 Friend: Tui eto late korli keno?\nAmi: Rastay traffic chilo.\nFriend: Tui to hete ashchis!\nAmi: Hatar traffic chilo re! 🤣",
        "😆 Ma: Phone ta rekhe porashona kor.\nAmi: Ma, phone chara Google-e porashona korbo kivabe? 😂",
        "🤣 Friend: Tor prem kemon cholche?\nAmi: WiFi-er moto.\nFriend: Mane?\nAmi: Password jani na, signal-o pai na! 😂",
        "😂 Doctor: Apnar ki problem?\nPatient: Mobile charge-e dilei amar ghum ashe.\nDoctor: Eta problem na, eta charger-er magic! 🤣",
        "😎 Boss: Tumi office-e eto deri kore asho keno?\nEmployee: Sir, ami punctual... amar alarm punctual na! 😂",
        "🤣 Baba: Tui porashona korchis?\nAmi: Haan baba.\nBaba: Ki porchis?\nAmi: Battery percentage... 5% theke 4% hoye gelo! 😂",
        "😂 Friend: Tui single keno?\nAmi: Ami premium version.\nFriend: Mane?\nAmi: Sobai afford korte pare na! 🤣",
        "😆 Bhai, tor phone eto gorom keno?\nBattery gorom na re, amar ex-er message dekhe phone-o jealous! 😂"
    ])

def quote(a, c):
    return random.choice([
        "✨ Jotoi tough hok, chesta korle ekdin parbei.",
        "🔥 Ajke fail korle kalke aro bhalo kore try kor.",
        "💫 Nijer upor bishash rakh, baki sob aste aste thik hoye jabe.",
        "😎 Life short, tai unnecessary tension komao.",
        "🌸 Choto choto step-ei boro success ashe.",
        "💪 Har mene neya easy, kintu abar try korai real power.",
        "❤️ Nijer value bujho, sobar approval-er dorkar nei."
    ])

def dice(a, c):
    return f"🎲 Dice roll: {random.randint(1, 6)}"

def truth(a, c):
    return random.choice([
        "❤️ Sotti kore bolo, kake shobcheye beshi text koro?",
        "😏 Tomar biggest secret ki?",
        "😂 Tomar jiboner shobcheye funny mistake konta?",
        "🙈 Kake secretly like koro?",
        "🤣 Shesh kobe mithha bole dhora kheyechho?",
        "😎 Tomar shobcheye embarrassing moment konta?",
        "❤️ Ekhon tomar mon-e kar kotha cholche?"
    ])

def dare(a, c):
    return random.choice([
        "😎 Ekhon ekta funny emoji pathao.",
        "😂 Group-e ekta random kotha bolo.",
        "🔥 10 second-er moddhe ekjonke hashao.",
        "🤣 Nijer somporke ekta funny fact bolo.",
        "😏 Jar sathe kotha bolte bhalo lage take 'Hi' bolo.",
        "😂 Ekhon sudhu emoji diye ekta message dao.",
        "🔥 Ekta funny status lekho."
    ])

def ball8(a, c):
    return random.choice([
        "🎱 Haan, definitely!",
        "🎱 Na, chance kom.",
        "🎱 Maybe... dekha jak! 😏",
        "🎱 100% Haan! 🔥",
        "🎱 Amar mone hoy Haan ❤️",
        "🎱 Nope 😂",
        "🎱 Future ekhono secret! 🔮",
        "🎱 Definitely! 😎"
    ])

def slap(a, c):
    target = " ".join(a) if a else "nijeke"
    return random.choice([
        f"👋 {target} ke thappor marse! 💥",
        f"🤜 BAM! {target} uray gelo! 😂",
        f"👋 {target} thappor kheye kede dilo 😭",
        f"💢 {target} ke ekta solid thappor! 🤣"
    ])

def love(a, c):
    if len(a) < 2:
        return "Format:.love Shihab Mim"
    name1 = a[0]
    name2 = a[1]
    seed = (name1.lower() + name2.lower())
    random.seed(seed)
    percent = random.randint(5, 99)
    random.seed()
    if percent > 90:
        return f"❤️ {name1} + {name2} = {percent}%\nBhai biye kobe? 😍💍"
    elif percent > 70:
        return f"💖 {name1} + {name2} = {percent}%\nPrem jombe! 😚"
    elif percent > 40:
        return f"💛 {name1} + {name2} = {percent}%\nChesta korle hobe 😏"
    else:
        return f"💔 {name1} + {name2} = {percent}%\nVule jao, hobe na 😂"

FUN_COMMANDS = {
    "joke": joke,
    "quote": quote,
    "dice": dice,
    "truth": truth,
    "dare": dare,
    "8ball": ball8,
    "slap": slap,
    "love": love
}
