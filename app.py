import os
import telebot
import sqlite3
from datetime import datetime
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")

bot = telebot.TeleBot(TOKEN)

DB_PATH = "data.db"

def init_db():
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id TEXT,
            username TEXT,
            full_name TEXT,
            level TEXT,
            created_at TEXT
        )
        """)
init_db()

user_state = {}
temp_name = {}

def levels_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add("A1-A2", "B1-B2", "B2+")
    return kb

@bot.message_handler(commands=['start'])
def start(message):
    user_state[message.from_user.id] = "WAIT_NAME"
    bot.send_message(message.chat.id, "Ism familiyangizni yozing:")

@bot.message_handler(func=lambda m: True)
def handle(message):
    user_id = message.from_user.id
    text = message.text.strip()

    state = user_state.get(user_id)

    if state == "WAIT_NAME":
        temp_name[user_id] = text
        user_state[user_id] = "WAIT_LEVEL"
        bot.send_message(message.chat.id, "Ingliz darajangizni tanlang:", reply_markup=levels_keyboard())
        return

    if state == "WAIT_LEVEL":
        full_name = temp_name.get(user_id)
        level = text

        with sqlite3.connect(DB_PATH) as con:
            con.execute(
                "INSERT INTO registrations (telegram_id, username, full_name, level, created_at) VALUES (?,?,?,?,?)",
                (
                    str(user_id),
                    message.from_user.username or "",
                    full_name,
                    level,
                    datetime.utcnow().isoformat()
                )
            )

        bot.send_message(
            message.chat.id,
            "✅ Rahmat, Ro'yxatga olindi.\n"
            "TEDxYazyavan yangiliklari uchun https://t.me/TedxYazyavan shu kanalda qolin."
        )

        if ADMIN_CHAT_ID:
             username = message.from_user.username
             username_text = f"@{username}" if username else "Username yo'q"

             bot.send_message(
                 ADMIN_CHAT_ID,
                 f"🆕 Yangi ro'yxat:\n"
                 f"👤 Ism: {full_name}\n"
                 f"📚 Level: {level}\n"
                 f"🔗 Username: {username_text}\n"
                 f"🆔 ID: {user_id}"
              )

        user_state.pop(user_id, None)
        temp_name.pop(user_id, None)

bot.infinity_polling()
