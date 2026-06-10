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
    ever_subscribed INTEGER DEFAULT 0,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')
try:
    c.execute("ALTER TABLE users ADD COLUMN ever_subscribed INTEGER DEFAULT 0")
except:
    pass
conn.commit()

# Broadcast uchun holatlar
broadcast_state = {}
broadcast_msg = {}

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

def share_text(link):
    return (
        f"https://t.me/share/url?url={link}"
        f"&text=Zo%27r+bot+topib+oldim%21+Eng+yuqori+sifatli+"
        f"musiqalar+bor+ekan.+Start+bosib+shartlarni+bajarishda+yordam+kerak"
    )

def get_main_keyboard(uid):
    kb_reply = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb_reply.add(types.KeyboardButton("Taklif havolam 🔗"))
    if uid == ADMIN_ID:
        kb_reply.add(types.KeyboardButton("📊 Statistika"))
        kb_reply.add(types.KeyboardButton("📨 Obunachilarga xabar yuborish"))
    return kb_reply

def show_main(uid):
    c.execute("SELECT ref_count, rewarded FROM users WHERE user_id=?", (uid,))
    row = c.fetchone()
    count = row[0] if row else 0
    rewarded = row[1] if row else 0
    me = bot.get_me()
    link = f"https://t.me/{me.username}?start={uid}"
    kb_reply = get_main_keyboard(uid)
    remaining = max(0, REQUIRED - count)

    if rewarded:
        if is_subscribed(uid):
            bot.send_message(uid,
                f"Siz yopiq kanalga qo'shilgansiz🙂\n\n{PRIVATE_LINK}",
                reply_markup=kb_reply)
        else:
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("@SATR_cha", url="https://t.me/SATR_cha"))
            bot.send_message(uid,
                "Iltimos, obunani tekshiring:",
                reply_markup=kb)
    else:
        kb_inline = types.InlineKeyboardMarkup()
        kb_inline.add(types.InlineKeyboardButton("Do'stlarga ulashish♻️",
            url=share_text(link)))
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
    add_user(uid, invited_by)
    if not is_subscribed(uid):
        c.execute("SELECT rewarded FROM users WHERE user_id=?", (uid,))
        row = c.fetchone()
        rewarded = row[0] if row else 0
        if rewarded:
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("@SATR_cha", url="https://t.me/SATR_cha"))
            bot.send_message(uid, "Iltimos, obunani tekshiring:", reply_markup=kb)
        else:
            show_subscribe(uid)
    else:
        c.execute("UPDATE users SET ever_subscribed=1 WHERE user_id=?", (uid,))
        conn.commit()
        show_main(uid)

@bot.callback_query_handler(func=lambda c: c.data == "check")
def check_cb(call):
    uid = call.from_user.id
    if is_subscribed(uid):
        bot.answer_callback_query(call.id, "✅ Tasdiqlandi!")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        c.execute("UPDATE users SET ever_subscribed=1 WHERE user_id=?", (uid,))
        conn.commit()
        show_main(uid)
    else:
        bot.answer_callback_query(call.id, "❌ Hali obuna bo'lmadingiz!", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data == "broadcast_send")
def broadcast_send(call):
    uid = call.from_user.id
    if uid != ADMIN_ID:
        return
    bot.answer_callback_query(call.id)
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    saved = broadcast_msg.get(uid)
    if not saved:
        bot.send_message(uid, "❌ Xabar topilmadi.")
        return
    c.execute("SELECT user_id FROM users WHERE blocked=0")
    all_users = c.fetchall()
    success = 0
    fail = 0
    for (user_id,) in all_users:
        try:
            fwd_type = saved['type']
            fwd_msg = saved['message']
            if fwd_type == 'text':
                bot.send_message(user_id, fwd_msg.text)
            elif fwd_type == 'photo':
                bot.send_photo(user_id, fwd_msg.photo[-1].file_id, caption=fwd_msg.caption)
            elif fwd_type == 'video':
                bot.send_video(user_id, fwd_msg.video.file_id, caption=fwd_msg.caption)
            elif fwd_type == 'audio':
                bot.send_audio(user_id, fwd_msg.audio.file_id, caption=fwd_msg.caption)
            elif fwd_type == 'document':
                bot.send_document(user_id, fwd_msg.document.file_id, caption=fwd_msg.caption)
            elif fwd_type == 'animation':
                bot.send_animation(user_id, fwd_msg.animation.file_id, caption=fwd_msg.caption)
            elif fwd_type == 'voice':
                bot.send_voice(user_id, fwd_msg.voice.file_id)
            elif fwd_type == 'sticker':
                bot.send_sticker(user_id, fwd_msg.sticker.file_id)
            success += 1
        except:
            fail += 1
    broadcast_state.pop(uid, None)
    broadcast_msg.pop(uid, None)
    bot.send_message(uid, f"✅ Xabar yuborildi!\n\n📤 Muvaffaqiyatli: {success} ta\n❌ Yuborilmadi: {fail} ta")

@bot.callback_query_handler(func=lambda c: c.data == "broadcast_cancel")
def broadcast_cancel(call):
    uid = call.from_user.id
    if uid != ADMIN_ID:
        return
    bot.answer_callback_query(call.id)
    broadcast_state.pop(uid, None)
    broadcast_msg.pop(uid, None)
    bot.edit_message_text("❌ Bekor qilindi.", call.message.chat.id, call.message.message_id)

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
        url=share_text(link)))
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
    c.execute("SELECT COUNT(*) FROM users WHERE ever_subscribed=0")
    never_subscribed = c.fetchone()[0]
    currently_in = 0
    left_channel = 0
    c.execute("SELECT user_id FROM users WHERE ever_subscribed=1")
    subscribed_users = c.fetchall()
    for (user_id,) in subscribed_users:
        if is_subscribed(user_id):
            currently_in += 1
        else:
            left_channel += 1
    bot.send_message(ADMIN_ID,
        f"📊 BOT STATISTIKASI\n\n"
        f"👥 Jami foydalanuvchilar: {total} ta\n"
        f"✅ Obuna bo'lganlar: {currently_in} ta\n"
        f"❌ Obuna bo'lmaganlar: {never_subscribed} ta\n"
        f"🚪 Chiqib ketganlar: {left_channel} ta\n"
        f"🚫 Botni bloklаganlar: {blocked} ta\n"
        f"🎁 Yopiq kanalga qo'shilganlar: {rewarded} ta")

@bot.message_handler(func=lambda msg: msg.text == "📨 Obunachilarga xabar yuborish" and msg.from_user.id == ADMIN_ID)
def broadcast_start(msg):
    uid = msg.from_user.id
    broadcast_state[uid] = True
    bot.send_message(uid, "📝 Obunachilarga yo'llash uchun xabar yuboring:")

@bot.message_handler(func=lambda msg: broadcast_state.get(msg.from_user.id) and msg.from_user.id == ADMIN_ID,
                     content_types=['text', 'photo', 'video', 'audio', 'document', 'animation', 'voice', 'sticker'])
def broadcast_preview(msg):
    uid = msg.from_user.id
    if msg.content_type == 'text':
        broadcast_msg[uid] = {'type': 'text', 'message': msg}
    elif msg.content_type == 'photo':
        broadcast_msg[uid] = {'type': 'photo', 'message': msg}
    elif msg.content_type == 'video':
        broadcast_msg[uid] = {'type': 'video', 'message': msg}
    elif msg.content_type == 'audio':
        broadcast_msg[uid] = {'type': 'audio', 'message': msg}
    elif msg.content_type == 'document':
        broadcast_msg[uid] = {'type': 'document', 'message': msg}
    elif msg.content_type == 'animation':
        broadcast_msg[uid] = {'type': 'animation', 'message': msg}
    elif msg.content_type == 'voice':
        broadcast_msg[uid] = {'type': 'voice', 'message': msg}
    elif msg.content_type == 'sticker':
        broadcast_msg[uid] = {'type': 'sticker', 'message': msg}
    broadcast_state.pop(uid)
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("✅ Yuborish", callback_data="broadcast_send"),
        types.InlineKeyboardButton("❌ Bekor qilish", callback_data="broadcast_cancel")
    )
    bot.send_message(uid, "Xabarni barcha obunachilarga yuborasizmi?", reply_markup=kb)

@bot.my_chat_member_handler()
def chat_member_update(update):
    if update.new_chat_member.status == "kicked":
        uid = update.from_user.id
        c.execute("UPDATE users SET blocked=1 WHERE user_id=?", (uid,))
        conn.commit()

print("Bot ishlamoqda...")
bot.infinity_polling()
