import os
import sqlite3
from datetime import datetime
from flask import Flask, request
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")
CHANNEL_URL = "https://t.me/TedxYazyavan"

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
app = Flask(__name__)

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
    kb.add(KeyboardButton("A1-A2"), KeyboardButton("B1-B2"), KeyboardButton("B2+"))
    return kb

@bot.message_handler(commands=["start"])
def start(message):
    user_state[message.from_user.id] = "WAIT_NAME"
    bot.send_message(message.chat.id, "Ism familiyangizni yozing:")

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    user_id = message.from_user.id
    text = message.text.strip()

    state = user_state.get(user_id)

    if state == "WAIT_NAME":
        temp_name[user_id] = text
        user_state[user_id] = "WAIT_LEVEL"
        bot.send_message(message.chat.id, "Ingliz tili darajangizni tanlang:", reply_markup=levels_keyboard())
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
            bot.send_message(
                ADMIN_CHAT_ID,
                f"Yangi ro'yxat:\nIsm: {full_name}\nLevel: {level}\nID: {user_id}"
            )

        user_state.pop(user_id, None)
        temp_name.pop(user_id, None)

@app.route("/", methods=["GET"])
def home():
    return "Bot ishlayapti", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

if __name__ == "__main__":
    app.run()