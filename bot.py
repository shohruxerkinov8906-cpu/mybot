import telebot
from telebot import types
import sqlite3
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL = "@SATR_cha"
PRIVATE_LINK = "https://t.me/+HYv_RRO_SOVjNTdi"
REQUIRED = 3
ADMIN_ID = 6014260224

bot = telebot.TeleBot(BOT_TOKEN)

conn = sqlite3.connect('bot.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    ref_count INTEGER DEFAULT 0,
    invited_by INTEGER DEFAULT NULL,
    rewarded INTEGER DEFAULT 0,
    blocked INTEGER DEFAULT 0,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')
conn.commit()

def is_subscribed(user_id):
    try:
        m = bot.get_chat_member(CHANNEL, user_id)
        return m.status in ['member', 'administrator', 'creator']
    except:
        return False

def user_exists(user_id):
    c.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    return c.fetchone() is not None

def add_user(user_id, invited_by=None):
    if user_exists(user_id):
        c.execute("UPDATE users SET blocked=0 WHERE user_id=?", (user_id,))
        conn.commit()
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
                    f"Tabriklaymiz 🥳 Siz 3 ta do'stingizni taklif qildingiz!\n\n"
                    f"Yopiq kanal havolasi:\n{PRIVATE_LINK}")
            except:
                pass
    return True

def get_progress_bar(count, total):
    filled = int((count / total) * 10)
    empty = 10 - filled
    percent = int((count / total) * 100)
    bar = "🟩" * filled + "⬜" * empty
    return bar, percent

def show_subscribe(uid):
    try:
        name = bot.get_chat(uid).first_name or "Foydalanuvchi"
    except:
        name = "Foydalanuvchi"
    mention = f'<a href="tg://user?id={uid}">{name}</a>'
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Kanalga obuna bo'lish📢", url="https://t.me/SATR_cha"))
    kb.add(types.InlineKeyboardButton("Obunani tekshirish✅", callback_data="check"))
    bot.send_message(uid,
        f"Assalomu alaykum {mention} 🙂!\n\n"
        f"Bot ishlashi uchun quyidagi kanalga obuna bo'ling👇",
        reply_markup=kb,
        parse_mode="HTML")

def show_main(uid):
    c.execute("SELECT ref_count, rewarded FROM users WHERE user_id=?", (uid,))
    row = c.fetchone()
    count = row[0] if row else 0
    rewarded = row[1] if row else 0
    me = bot.get_me()
    link = f"https://t.me/{me.username}?start={uid}"
    kb_reply = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb_reply.add(types.KeyboardButton("Taklif havolam 🔗"))
    if uid == ADMIN_ID:
        kb_reply.add(types.KeyboardButton("📊 Statistika"))
    remaining = max(0, REQUIRED - count)
    if rewarded:
        bot.send_message(uid,
            f"Tabriklaymiz 🥳 Siz 3 ta do'stingizni taklif qildingiz!\n\n"
            f"Yopiq kanal havolasi:\n{PRIVATE_LINK}",
            reply_markup=kb_reply)
    else:
        kb_inline = types.InlineKeyboardMarkup()
        kb_inline.add(types.InlineKeyboardButton("Do'stlarga ulashish♻️",
            url=f"https://t.me/share/url?url={link}&text=Botga+qo%27shiling+va+yopiq+kanalga+kiring!"))
        bot.send_message(uid,
            f"Eng yuqori sifatli musiqalar joylangan yopiq kanalga qo'shilish uchun "
            f"botga {remaining} ta do'stingizni taklif qiling!",
            reply_markup=kb_reply)
        bot.send_message(uid, "👇", reply_markup=kb_inline)

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
    is_new = not user_exists(uid)
    add_user(uid, invited_by)
    if not is_subscribed(uid):
        show_subscribe(uid)
    else:
        show_main(uid)

@bot.callback_query_handler(func=lambda c: c.data == "check")
def check_cb(call):
    uid = call.from_user.id
    if is_subscribed(uid):
        bot.answer_callback_query(call.id, "✅ Tasdiqlandi!")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_main(uid)
    else:
        bot.answer_callback_query(call.id, "❌ Hali obuna bo'lmadingiz!", show_alert=True)

@bot.message_handler(func=lambda msg: msg.text == "Taklif havolam 🔗")
def my_referral(msg):
    uid = msg.from_user.id
    if not is_subscribed(uid):
        show_subscribe(uid)
        return
    c.execute("SELECT ref_count FROM users WHERE user_id=?", (uid,))
    row = c.fetchone()
    count = row[0] if row else 0
    me = bot.get_me()
    link = f"https://t.me/{me.username}?start={uid}"
    bar, percent = get_progress_bar(min(count, REQUIRED), REQUIRED)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Do'stlarga ulashish♻️",
        url=f"https://t.me/share/url?url={link}&text=Botga+qo%27shiling+va+yopiq+kanalga+kiring!"))
    bot.send_message(uid,
        f"🔗 SIZNING SHAXSIY TAKLIF HAVOLANGIZ:\n\n"
        f"{link}\n\n"
        f"📊 Siz taklif qilganlar: {count} / {REQUIRED}\n"
        f"{bar} {percent}%\n\n"
        f"🎯 Yopiq kanalga qo'shilish uchun yana {max(0, REQUIRED - count)} ta faol do'stingiz ulanishi kerak.",
        reply_markup=kb)

@bot.message_handler(func=lambda msg: msg.text == "📊 Statistika" and msg.from_user.id == ADMIN_ID)
def statistics(msg):
    c.execute("SELECT COUNT(*) FROM users")
    total = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM users WHERE blocked=1")
    blocked = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM users WHERE rewarded=1")
    rewarded = c.fetchone()[0]

    active = total - blocked

    # Kanalda hali borlar
    in_channel = 0
    left_channel = 0
    c.execute("SELECT user_id FROM users")
    all_users = c.fetchall()
    for (user_id,) in all_users:
        if is_subscribed(user_id):
            in_channel += 1
        else:
            left_channel += 1

    bot.send_message(ADMIN_ID,
        f"📊 BOT STATISTIKASI\n\n"
        f"👥 Jami foydalanuvchilar: {total} ta\n"
        f"✅ Faol foydalanuvchilar: {active} ta\n"
        f"🚫 Botni bloklаganlar: {blocked} ta\n\n"
        f"📢 Kanalda borlar: {in_channel} ta\n"
        f"🚪 Kanaldan chiqqanlar: {left_channel} ta\n\n"
        f"🎁 Yopiq kanalga qo'shilganlar: {rewarded} ta")

@bot.my_chat_member_handler()
def chat_member_update(update):
    if update.new_chat_member.status == "kicked":
        uid = update.from_user.id
        c.execute("UPDATE users SET blocked=1 WHERE user_id=?", (uid,))
        conn.commit()

print("Bot ishlamoqda...")
bot.infinity_polling()
