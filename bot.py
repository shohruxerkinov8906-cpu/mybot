import telebot
from telebot import types
import sqlite3
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL = "@SATR_cha"
PRIVATE_LINK = "https://t.me/+HYv_RRO_SOVjNTdi"
REQUIRED = 5

bot = telebot.TeleBot(BOT_TOKEN)

conn = sqlite3.connect('bot.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    ref_count INTEGER DEFAULT 0,
    invited_by INTEGER DEFAULT NULL,
    rewarded INTEGER DEFAULT 0
)''')
conn.commit()

def is_subscribed(user_id):
    try:
        m = bot.get_chat_member(CHANNEL, user_id)
        return m.status in ['member', 'administrator', 'creator']
    except:
        return False

def add_user(user_id, invited_by=None):
    c.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    if c.fetchone():
        return False
    c.execute("INSERT INTO users (user_id, invited_by) VALUES (?, ?)", (user_id, invited_by))
    conn.commit()
    if invited_by and invited_by != user_id:
        c.execute("UPDATE users SET ref_count = ref_count + 1 WHERE user_id=?", (invited_by,))
        conn.commit()
        c.execute("SELECT ref_count, rewarded FROM users WHERE user_id=?", (invited_by,))
        row = c.fetchone()
        if row and row[0] >= REQUIRED and not row[1]:
            c.execute("UPDATE users SET rewarded=1 WHERE user_id=?", (invited_by,))
            conn.commit()
            try:
                bot.send_message(invited_by,
                    f"🎉 Tabriklaymiz! 5 ta do'stingiz qo'shildi!\n\n"
                    f"🔐 Yopiq kanal havolasi:\n{PRIVATE_LINK}")
            except:
                pass
    return True

@bot.message_handler(commands=['start'])
def start(msg):
    uid = msg.from_user.id
    args = msg.text.split()
    invited_by = None
    if len(args) > 1:
        try:
            invited_by = int(args[1])
        except:
            pass
    add_user(uid, invited_by)
    if not is_subscribed(uid):
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("📢 Kanalga o'tish", url="https://t.me/SATR_cha"))
        kb.add(types.InlineKeyboardButton("✅ Obuna bo'ldim", callback_data="check"))
        bot.send_message(uid,
            "⚠️ Botdan foydalanish uchun avval kanalga obuna bo'ling:\n\n"
            "@SATR_cha\n\nObuna bo'lgach '✅ Obuna bo'ldim' tugmasini bosing.",
            reply_markup=kb)
        return
    show_menu(uid)

@bot.callback_query_handler(func=lambda c: c.data == "check")
def check_cb(call):
    uid = call.from_user.id
    if is_subscribed(uid):
        bot.answer_callback_query(call.id, "✅ Tasdiqlandi!")
        show_menu(uid)
    else:
        bot.answer_callback_query(call.id, "❌ Hali obuna bo'lmadingiz!", show_alert=True)

def show_menu(uid):
    c.execute("SELECT ref_count, rewarded FROM users WHERE user_id=?", (uid,))
    row = c.fetchone()
    count = row[0] if row else 0
    rewarded = row[1] if row else 0
    me = bot.get_me()
    link = f"https://t.me/{me.username}?start={uid}"
    if rewarded:
        text = (f"✅ Siz mukofotni oldingiz!\n\n"
                f"🔐 Yopiq kanal: {PRIVATE_LINK}\n\n"
                f"👥 Taklif qilganlar: {count} ta\n"
                f"🔗 Havolangiz: {link}")
    else:
        left = REQUIRED - count
        text = (f"👋 Xush kelibsiz!\n\n"
                f"👥 Taklif qilganlar: {count}/{REQUIRED}\n"
                f"⏳ Yana {left} ta odam kerak\n\n"
                f"🔗 Sizning havolangiz:\n{link}\n\n"
                f"Do'stlaringizga yuboring. Ular botga kirib kanalga obuna bo'lsa, balingiz oshadi!")
    bot.send_message(uid, text)

print("Bot ishlamoqda...")
bot.infinity_polling()
