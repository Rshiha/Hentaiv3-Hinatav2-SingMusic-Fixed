import os, json, random, time

FILE = "/tmp/economy.json"
ADMIN_IDS = ["76593286314"] # TU ADMIN ✅
ADMIN_USERNAMES = ["76593286314"]

def load():
    if not os.path.exists(FILE):
        return {}
    try:
        with open(FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save(data):
    try:
        with open(FILE, "w") as f:
            json.dump(data, f)
    except:
        pass

def get_user(data, uid):
    if uid not in data:
        data[uid] = {"wallet": 1000, "bank": 0, "last_daily": 0, "last_work": 0, "last_bank_interest": time.time()}
    if "last_bank_interest" not in data[uid]:
        data[uid]["last_bank_interest"] = time.time()
    if "last_daily" not in data[uid]:
        data[uid]["last_daily"] = 0
    if "last_work" not in data[uid]:
        data[uid]["last_work"] = 0
    return data[uid]

def get_uid(c):
    if isinstance(c, dict):
        return str(c.get("user_id", "0"))
    return str(c)

def is_admin(c):
    uid = get_uid(c)
    if uid in ADMIN_IDS:
        return True
    if isinstance(c, dict):
        uname = str(c.get("username", "")).lower()
        if uname in [x.lower() for x in ADMIN_USERNAMES]:
            return True
        # uid string o check
        if str(uid) == "76593286314":
            return True
    if str(uid) == "76593286314":
        return True
    return False

def apply_interest(u):
    now = time.time()
    last = u.get("last_bank_interest", now)
    hours_passed = (now - last) / 3600
    if hours_passed >= 24 and u["bank"] > 0:
        days = int(hours_passed // 24)
        total_interest = 0
        for _ in range(days):
            interest = int(u["bank"] * 0.05)
            u["bank"] += interest
            total_interest += interest
        u["last_bank_interest"] = now
        return total_interest
    return 0

def balance(a, c):
    uid = get_uid(c)
    data = load()
    u = get_user(data, uid)
    return f"💰 Wallet: {u['wallet']:,} coins\n🏦 Bank: {u['bank']:,} coins"

def bank(a, c):
    uid = get_uid(c)
    data = load()
    u = get_user(data, uid)
    interest = apply_interest(u)
    if interest > 0:
        save(data)
        return f"✨ Interest +{interest:,}!\n🏦 Bank: {u['bank']:,}\n💰 Wallet: {u['wallet']:,}"
    if not a:
        return f"🏦 BANK\n💰 Wallet: {u['wallet']:,}\n🏦 Bank: {u['bank']:,}\n💹 Interest: 5% per 24h\n\n.deposit 500\n.withdraw 500\n.bank add 1000000 (admin)"
    if a[0].lower() == "add":
        if not is_admin(c):
            return "❌ Admin only! Tui admin na!"
        if len(a) == 2 and a[1].isdigit():
            amount = int(a[1])
            u["bank"] += amount
            save(data)
            return f"✅ Bank e +{amount:,} add! New bank: {u['bank']:,}"
        elif len(a) >= 3 and a[2].isdigit():
            target = a[1]
            amount = int(a[2])
            ut = get_user(data, target)
            ut["bank"] += amount
            save(data)
            return f"✅ {target} er bank +{amount:,}! New: {ut['bank']:,}"
        else:
            return "Usage:.bank add 1000000 OR.bank add <uid> 1000"
    return f"🏦 Wallet: {u['wallet']:,} | Bank: {u['bank']:,}"

def deposit(a, c):
    uid = get_uid(c)
    data = load()
    u = get_user(data, uid)
    apply_interest(u)
    if not a or not a[0].isdigit():
        return f"Usage:.deposit 500\nWallet: {u['wallet']:,} | Bank: {u['bank']:,}"
    amount = int(a[0])
    if amount <= 0:
        return "❌ Valid amount de!"
    if u["wallet"] < amount:
        return f"❌ Wallet e {u['wallet']:,} ache!"
    u["wallet"] -= amount
    u["bank"] += amount
    save(data)
    return f"✅ {amount:,} bank e rakhli!\n💰 Wallet: {u['wallet']:,}\n🏦 Bank: {u['bank']:,}"

def withdraw(a, c):
    uid = get_uid(c)
    data = load()
    u = get_user(data, uid)
    apply_interest(u)
    if not a or not a[0].isdigit():
        return f"Usage:.withdraw 500\nBank: {u['bank']:,}"
    amount = int(a[0])
    if u["bank"] < amount:
        return f"❌ Bank e {u['bank']:,} ache!"
    bonus = int(amount * 0.02)
    u["bank"] -= amount
    u["wallet"] += amount + bonus
    save(data)
    return f"✅ Withdraw {amount:,} + bonus {bonus:,}\n💰 Wallet: {u['wallet']:,}\n🏦 Bank: {u['bank']:,}"

def daily(a, c):
    uid = get_uid(c)
    data = load()
    u = get_user(data, uid)
    now = time.time()
    if now - u["last_daily"] < 86400:
        left = int(86400 - (now - u["last_daily"]))
        return f"⏳ Daily already! {left//3600}h por!"
    u["wallet"] += 500
    u["last_daily"] = now
    save(data)
    return "🎁 Daily +500!"

def work(a, c):
    uid = get_uid(c)
    data = load()
    u = get_user(data, uid)
    now = time.time()
    if now - u["last_work"] < 3600:
        return "😴 1h por!"
    earn = random.randint(100, 500)
    u["wallet"] += earn
    u["last_work"] = now
    save(data)
    return f"💼 {earn} coins paili!"

def slot(a, c):
    uid = get_uid(c)
    data = load()
    u = get_user(data, uid)
    bet = 100
    if a and a[0].isdigit():
        bet = int(a[0])
        if bet < 10: bet = 10
        if bet > 10000: bet = 10000
    if u["wallet"] < bet:
        return f"❌ Taka nai! Ache {u['wallet']:,}, bet {bet:,}"
    u["wallet"] -= bet
    sym = ["🍒","🍋","💎","7️⃣","🍉"]
    x = [random.choice(sym) for _ in range(3)]
    res = " | ".join(x)
    if x[0]==x[1]==x[2]:
        win = bet * 10
        u["wallet"] += win
        msg = f"🎰 {res}\n🎉 JACKPOT! +{win:,}!"
    elif x[0]==x[1] or x[1]==x[2] or x[0]==x[2]:
        win = bet * 2
        u["wallet"] += win
        msg = f"🎰 {res}\n😏 Small win +{win:,}!"
    else:
        msg = f"🎰 {res}\n😅 Haraili! -{bet:,}"
    save(data)
    msg += f"\n💰 Bal: {u['wallet']:,}"
    return msg

def shop(a,c):
    return "🛒 SHOP\n1. 🍫 Chocolate — 100\n2. 🎁 Gift — 250\n3. 💎 Diamond — 1000\n.buy 1"

def buy(a,c):
    uid = get_uid(c)
    data = load()
    u = get_user(data, uid)
    prices = {"1":100, "2":250, "3":1000}
    if not a or a[0] not in prices:
        return "🛍️.buy 1 / 2 / 3"
    price = prices[a[0]]
    if u["wallet"] < price:
        return f"❌ Lagbe {price:,}"
    u["wallet"] -= price
    save(data)
    return f"✅ Kinli! -{price:,} | Bal: {u['wallet']:,}"

def badd(a,c):
    if not is_admin(c):
        return "❌ Admin only! Tor UID: " + get_uid(c)
    if not a:
        return "Usage:.badd 1000000 OR.badd <uid> 1000"
    data = load()
    if len(a) == 1 and a[0].lstrip("-").isdigit():
        uid = get_uid(c)
        amount = int(a[0])
        u = get_user(data, uid)
        u["wallet"] += amount
        save(data)
        return f"✅ Wallet +{amount:,}! New: {u['wallet']:,}"
    if len(a) >= 2 and a[1].lstrip("-").isdigit():
        target = a[0]
        amount = int(a[1])
        u = get_user(data, target)
        u["wallet"] += amount
        save(data)
        return f"✅ {target} +{amount:,}! New: {u['wallet']:,}"
    return "Usage:.badd 1000000"

def send(a,c):
    uid = get_uid(c)
    data = load()
    u = get_user(data, uid)
    if not a or len(a) < 2:
        return "Usage:.send <uid> <amount>\nEx:.send 123456 500"
    target_id = a[0].replace("@","").strip()
    if not a[1].isdigit():
        return "❌ Amount de!"
    amount = int(a[1])
    if amount < 10:
        return "❌ Min 10!"
    if target_id == uid:
        return "❌ Nijeke na!"
    tax = int(amount * 0.05)
    total = amount + tax
    if u["wallet"] < total:
        return f"❌ Lagbe {total:,} (tax {tax:,}), ache {u['wallet']:,}"
    ut = get_user(data, target_id)
    u["wallet"] -= total
    ut["wallet"] += amount
    save(data)
    return f"✅ {amount:,} sent to {target_id} (tax {tax:,})\n💰 Bal: {u['wallet']:,}"

def add(a,c):
    return badd(a,c)
def pay(a,c):
    return send(a,c)

ECONOMY_COMMANDS={
    "balance":balance, "bal":balance,
    "daily":daily, "work":work, "shop":shop, "buy":buy,
    "slot":slot, "bank":bank,
    "deposit":deposit, "dep":deposit,
    "withdraw":withdraw, "wd":withdraw,
    "badd":badd, "add":add, "abalance":badd,
    "send":send, "pay":pay, "transfer":send
}
