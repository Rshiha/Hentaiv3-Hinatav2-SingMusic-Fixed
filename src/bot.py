"""
Instagram login + DM polling loop (Optimized for 5 seconds interval).
Python port of the original main.py run_bot()/message_worker(), with
process_message() replaced by src.dispatcher.Dispatcher.
"""

import os
import queue
import threading
import time
import urllib.parse

from instagrapi import Client

from src import logger
from src.config import CONFIG
from src.database import DATABASE
from src.dispatcher import Dispatcher
from src.registry import load_all

SETTINGS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ig_settings.json"
)

# এখানে ইন্টারভ্যাল ৫ সেকেন্ড ফিক্সড করে দেওয়া হলো
POLL_INTERVAL = 5

IG_LOCK = threading.Lock()
MESSAGE_QUEUE = queue.Queue()

START_TIME = time.time()
BOT_RUNNING = False
BOT_USERNAME = "Unknown"

REGISTRY = load_all(CONFIG)
DISPATCHER = Dispatcher(CONFIG, REGISTRY, DATABASE, IG_LOCK)


def is_instagram_403(error):
    text = str(error).lower()
    return (
        "1404006" in text
        or "item_ack" in text
        or "clientforbiddenerror" in text
        or 'status_code":"403' in text
        or "403" in text
    )


def process_message(client, thread, message):
    try:
        user = client.user_info_v1(int(message.user_id))
    except Exception:
        user = None

    try:
        DISPATCHER.handle(client, thread, message, user, START_TIME)
    finally:
        DATABASE.flush()


def message_worker():
    while True:
        client, thread, message = MESSAGE_QUEUE.get()
        try:
            process_message(client, thread, message)
        except Exception as e:
            logger.error("WORKER", "MESSAGE PROCESS ERR", e)
        finally:
            MESSAGE_QUEUE.task_done()


def run_bot():
    global BOT_RUNNING, BOT_USERNAME

    session_id = os.getenv("IG_SESSIONID")
    if not session_id:
        logger.error("LOGIN", "❌ IG_SESSIONID missing")
        return

    session_id = urllib.parse.unquote(session_id.strip().strip('"').strip("'"))
    client = Client()
    
    # রিকোয়েস্টগুলোর মধ্যকার ইন্টারনাল ডিলে রেঞ্জ কমানো হলো যাতে রেসপন্স ফাস্ট হয়
    client.delay_range = [1, 3]

    if os.path.exists(SETTINGS_FILE):
        try:
            client.load_settings(SETTINGS_FILE)
            logger.info("LOGIN", "⚙️ Loaded saved device settings")
        except Exception as e:
            logger.warn("LOGIN", f"SETTINGS LOAD SKIPPED: {e}")

    try:
        logger.info("LOGIN", "🔐 Instagram session login হচ্ছে...")
        client.login_by_sessionid(session_id)

        try:
            client.dump_settings(SETTINGS_FILE)
        except Exception as e:
            logger.warn("LOGIN", f"SETTINGS SAVE ERR: {e}")

        BOT_USERNAME = getattr(client, "username", "Unknown")
        BOT_RUNNING = True
        logger.success("LOGIN", f"🎉 LOGIN SUCCESS: @{BOT_USERNAME}")
        logger.info("LOGIN", f"⏱️ Poll interval set to: {POLL_INTERVAL}s")

    except Exception as e:
        BOT_RUNNING = False
        logger.error("LOGIN", "❌ LOGIN FAIL", e)
        if is_instagram_403(e):
            logger.warn("LOGIN", "⚠️ Instagram session/request rejected (403/1404006).")
        return

    last_messages = {}
    try:
        logger.info("DM", "📨 Loading initial DM threads...")
        with IG_LOCK:
            # ৫ সেকেন্ড পর পর চেক করার জন্য থ্রেড অ্যামাউন্ট কমিয়ে ১০ করা হলো (স্পিড বুস্টের জন্য)
            threads = client.direct_threads(amount=10, thread_message_limit=5)
        for thread in threads:
            try:
                if thread.messages:
                    last_messages[thread.id] = str(thread.messages[0].id)
            except Exception:
                continue
        logger.success("DM", f"✅ Initial DM loaded: {len(last_messages)} threads")
    except Exception as e:
        logger.warn("DM", f"⚠️ INITIAL DM LOAD FAILED: {repr(e)}")
        time.sleep(15)

    errors = 0
    last_403_log = 0

    while True:
        try:
            with IG_LOCK:
                # ৫ সেকেন্ড লুপের জন্য থ্রেডের সংখ্যা অপ্টিমাইজড (amount=10) করা হয়েছে, যাতে সার্ভার ব্লক না করে
                threads = client.direct_threads(amount=10, thread_message_limit=5)
            errors = 0

            for thread in threads:
                try:
                    if not thread.messages:
                        continue
                    message = thread.messages[0]
                    message_id = str(getattr(message, "id", ""))
                    user_id = str(getattr(message, "user_id", ""))
                    if not message_id:
                        continue
                    if user_id == str(client.user_id):
                        continue
                    if last_messages.get(thread.id) == message_id:
                        continue
                    last_messages[thread.id] = message_id

                    text = (getattr(message, "text", "") or "").strip()
                    if not text:
                        continue

                    logger.info("DM", f"📩 {text}")
                    MESSAGE_QUEUE.put((client, thread, message))

                except Exception as message_error:
                    logger.error("DM", "MESSAGE PROCESS ERR", message_error)

        except Exception as e:
            errors += 1
            if is_instagram_403(e):
                now = time.time()
                if now - last_403_log >= 60:
                    logger.warn("DM", f"⚠️ Instagram 403/1404006: {repr(e)}")
                    last_403_log = now
                wait = min(600, 30 * max(1, min(errors, 10)))
                logger.warn("DM", f"⏳ rate limit block - retry in {wait}s")
                time.sleep(wait)
                continue

            logger.error("DM", "FULL ERROR", e)
            wait = min(60, 5 + (errors * 5))
            time.sleep(wait)

        # লুপটি প্রতি ৫ সেকেন্ড পর পর ঘুরবে
        time.sleep(POLL_INTERVAL)


def start():
    """Start the bot + worker threads once, from main.py."""
    threading.Thread(target=run_bot, daemon=True).start()
    threading.Thread(target=message_worker, daemon=True).start()


def status():
    return {
        "running": BOT_RUNNING,
        "username": BOT_USERNAME,
        "start_time": START_TIME,
        "commands": len(REGISTRY.commands),
        "events": len(REGISTRY.events),
    }
    
