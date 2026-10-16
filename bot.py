import telebot
from telebot import types
import json
import os
import random
import uuid

# --- НАСТРОЙКИ ---
TOKEN = '8671235709:AAHmw_ocfyop75BPScNf725rq5x0O9lb1Zw'
BOYFRIEND_ID = 5205926300  # Впиши сюда свой Telegram ID (без кавычек)

bot = telebot.TeleBot(TOKEN)
DATA_FILE = 'bot_data.json'

# --- СТАНДАРТНЫЕ СПИСКИ ---
DEFAULT_COMPLIMENTS = [
    "Настюшенька, ты самое прекрасное, что случалось в моей жизни! ❤️",
    "Твоя улыбка способна осветить даже самый пасмурный день ✨",
    "Ты невероятно красивая, умная и самая-самая любимая! 🥰",
    "Обнимаю тебя крепко-крепко через экран, моя принцесса 👑",
    "Настюша, ты выглядишь просто потрясающе сегодня (как и всегда)! 💖",
    "Спасибо за то, что ты есть у меня, моё солнышко ☀️"
]

PREDICTIONS = [
    "✨ Сегодня тебя ждёт очень приятный сюрприз!",
    "🌸 День идеально подходит для того, чтобы побаловать себя чем-то вкусным.",
    "💖 Сегодня твоя красота разобьёт минимум одно сердечко (моё уже у тебя!).",
    "☕ Идеальный день для уютного вечера, вкусного чая и обнимашек.",
    "🌟 Все твои дела сегодня получатся легко и красиво, Настюшенька!"
]

FOOD_IDEAS = ["🍣 Роллы!", "🍕 Горячая пицца", "🍔 Сочный бургер и картошка фри", "🍰 Вкусный десерт в кофейне", "🍝 Паста", "🍦 Мороженое и вкусняшки"]
DATE_IDEAS = ["🎬 Смотреть фильм под одним пледом", "🚶‍♀️ Вечерняя прогулка со стаканчиком кофе/чая", "🎮 Поиграть во что-нибудь вместе", "🛋 Просто валяться, обниматься и болтать обо всём"]

# --- БАЗА ДАННЫХ (JSON) ---
def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "nastya_id": None,
            "wishlist": [],
            "compliments": DEFAULT_COMPLIMENTS
        }
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    # Авто-обновление старых текстовых желаний под новый формат с фото
    updated_wishlist = []
    for item in data.get("wishlist", []):
        if isinstance(item, str):
            updated_wishlist.append({"id": str(uuid.uuid4())[:8], "text": item, "photo": None})
        else:
            if "id" not in item:
                item["id"] = str(uuid.uuid4())[:8]
            updated_wishlist.append(item)
    data["wishlist"] = updated_wishlist
    return data

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- КЛАВИАТУРЫ ---
def girl_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton('🎁 Мой Вишлист'),
        types.KeyboardButton('💌 Хочу комплимент'),
        types.KeyboardButton('🥺 Сигнал любимому'),
        types.KeyboardButton('✨ Предсказание на день'),
        types.KeyboardButton('🎲 Рулетка выбора')
    )
    return markup

def boyfriend_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton('📋 Вишлист Настюши'),
        types.KeyboardButton('💌 Отправить послание Насте'),
        types.KeyboardButton('➕ Добавить комплимент в базу')
    )
    return markup

# --- СТАРТ БОТА ---
@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.id == BOYFRIEND_ID:
        bot.send_message(
            message.chat.id,
            "😎 <b>Панель парня активирована!</b>\n\n"
            "Сюда будут приходить все сигналы и карточки новых желаний (с фотками!) от Настюшеньки.",
            parse_mode='HTML',
            reply_markup=boyfriend_menu()
        )
    else:
        data = load_data()
        if data["nastya_id"] != message.chat.id:
            data["nastya_id"] = message.chat.id
            save_data(data)
            try:
                bot.send_message(BOYFRIEND_ID, "🎉 <b>Настюшенька запустила бота!</b> Теперь ты можешь отправлять ей послания.", parse_mode='HTML')
            except Exception:
                pass

        welcome_text = (
            "Привет, моя любимая Настюшенька! 💖\n\n"
            "Я создал этого бота специально для тебя. Здесь ты можешь сохранять свои хотелки (даже с фотографиями и скриншотами!), "
            "получать порцию любви в любой момент и отправлять мне секретные сигналы 🥰\n\n"
            "Выбирай кнопочку внизу 👇"
        )
        bot.send_message(message.chat.id, welcome_text, reply_markup=girl_menu())

# --- ОБРАБОТКА ТЕКСТОВЫХ КНОПОК ---
@bot.message_handler(content_types=['text'])
def handle_text(message):
    data = load_data()

    # === ЛОГИКА ДЛЯ ТЕБЯ (ПАРНЯ) ===
    if message.chat.id == BOYFRIEND_ID:
        if message.text == '📋 Вишлист Настюши':
            show_wishlist_menu(message.chat.id, is_boyfriend=True)
            return

        elif message.text == '💌 Отправить послание Насте':
            if not data["nastya_id"]:
                bot.send_message(message.chat.id, "Настюшенька ещё не нажала /start в боте 🥺")
                return
            msg = bot.send_message(message.chat.id, "Напиши сообщение, и я красиво отправлю его Настюшеньке (или напиши «Отмена»):")
            bot.register_next_step_handler(msg, send_love_note_step)
            return

        elif message.text == '➕ Добавить комплимент в базу':
            msg = bot.send_message(message.chat.id, "Напиши новый комплимент для базы (или «Отмена»):")
            bot.register_next_step_handler(msg, add_compliment_step)
            return

    # === ЛОГИКА ДЛЯ НАСТЮШЕНЬКИ ===
    if message.text == '💌 Хочу комплимент':
        bot.send_message(message.chat.id, random.choice(data["compliments"]))

    elif message.text == '✨ Предсказание на день':
        bot.send_message(message.chat.id, random.choice(PREDICTIONS))

    elif message.text == '🎁 Мой Вишлист':
        show_wishlist_menu(message.chat.id, is_boyfriend=False)

    elif message.text == '🥺 Сигнал любимому':
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton('🤗 Срочно нужны обнимашки!', callback_data='sos_hug'),
            types.InlineKeyboardButton('🍫 Хочу вкусняшку...', callback_data='sos_sweet'),
            types.InlineKeyboardButton('😢 Мне грустно, напиши мне', callback_data='sos_sad'),
            types.InlineKeyboardButton('❤️ Просто напоминаю, что люблю!', callback_data='sos_love')
        )
        bot.send_message(message.chat.id, "Настюшенька, какой сигнал отправим? 📡💕", reply_markup=markup)

    elif message.text == '🎲 Рулетка выбора':
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton('🍕 Что покушать?', callback_data='roll_food'),
            types.InlineKeyboardButton('💑 Чем заняться?', callback_data='roll_date')
        )
        bot.send_message(message.chat.id, "Не можешь выбрать? Давай решу за тебя! 🎲", reply_markup=markup)

# --- ШАГИ ДЛЯ ПАРНЯ ---
def send_love_note_step(message):
    if not message.text or message.text.lower() == 'отмена' or message.text in ['📋 Вишлист Настюши', '💌 Отправить послание Насте', '➕ Добавить комплимент в базу']:
        bot.send_message(message.chat.id, "Отменено 👌", reply_markup=boyfriend_menu())
        return

    data = load_data()
    try:
        bot.send_message(
            data["nastya_id"],
            f"💌 <b>Внезапное послание от твоего любимого:</b>\n\n«{message.text}» ❤️",
            parse_mode='HTML'
        )
        bot.send_message(message.chat.id, "✅ Послание доставлено Настюшеньке!", reply_markup=boyfriend_menu())
    except Exception:
        bot.send_message(message.chat.id, "❌ Не удалось отправить. Возможно, Настя ещё не запустила бота.", reply_markup=boyfriend_menu())

def add_compliment_step(message):
    if not message.text or message.text.lower() == 'отмена' or message.text in ['📋 Вишлист Настюши', '💌 Отправить послание Насте', '➕ Добавить комплимент в базу']:
        bot.send_message(message.chat.id, "Отменено 👌", reply_markup=boyfriend_menu())
        return

    data = load_data()
    data["compliments"].append(message.text)
    save_data(data)
    bot.send_message(message.chat.id, f"✅ Комплимент добавлен! Всего в базе: {len(data['compliments'])}", reply_markup=boyfriend_menu())

# --- ФУНКЦИИ ВИШЛИСТА С ФОТОГРАФИЯМИ ---
def show_wishlist_menu(chat_id, is_boyfriend=False):
    data = load_data()
    wishlist = data["wishlist"]

    if not wishlist:
        if is_boyfriend:
            bot.send_message(chat_id, "Вишлист Настюшеньки пока пуст 🌸")
        else:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton('➕ Добавить первое желание', callback_data='wish_add'))
            bot.send_message(
                chat_id,
                "Твой вишлист пока пуст, Настюшенька 🌸\nСамое время добавить туда что-нибудь прекрасное!",
                reply_markup=markup
            )
        return

    # Отправляем каждую хотелку отдельной карточкой
    header = "🎁 <b>Вишлист Настюшеньки:</b>" if is_boyfriend else "🎁 <b>Твои сохранённые хотелки:</b>"
    bot.send_message(chat_id, header, parse_mode='HTML')

    for i, item in enumerate(wishlist, 1):
        wish_id = item["id"]
        wish_text = item["text"]
        wish_photo = item.get("photo")

        card_caption = f"✨ <b>Желание #{i}</b>\n\n{wish_text}"
        
        card_markup = types.InlineKeyboardMarkup()
        del_btn_text = "✅ Уже купил (Удалить)" if is_boyfriend else "🗑 Удалить желание"
        card_markup.add(types.InlineKeyboardButton(del_btn_text, callback_data=f"del_wish_{wish_id}"))

        if wish_photo:
            bot.send_photo(chat_id, wish_photo, caption=card_caption, parse_mode='HTML', reply_markup=card_markup)
        else:
            bot.send_message(chat_id, card_caption, parse_mode='HTML', reply_markup=card_markup)

    # Кнопка добавления внизу списка для Насти
    if not is_boyfriend:
        add_markup = types.InlineKeyboardMarkup()
        add_markup.add(types.InlineKeyboardButton('➕ Добавить ещё желание', callback_data='wish_add'))
        bot.send_message(chat_id, "Хочешь пополнить свой список? 🥰👇", reply_markup=add_markup)

def save_new_wish(chat_id, text, photo_id=None):
    data = load_data()
    new_wish = {
        "id": str(uuid.uuid4())[:8],
        "text": text,
        "photo": photo_id
    }
    data["wishlist"].append(new_wish)
    save_data(data)

    bot.send_message(chat_id, "✅ Карточка желания сохранена в твой вишлист, котик! ✨", reply_markup=girl_menu())

    # Уведомление парню (с фото, если оно есть!)
    notify_text = f"🔔 <b>Настюшенька добавила новое желание в вишлист!</b>\n\n👉 {text}"
    try:
        if photo_id:
            bot.send_photo(BOYFRIEND_ID, photo_id, caption=notify_text, parse_mode='HTML')
        else:
            bot.send_message(BOYFRIEND_ID, notify_text, parse_mode='HTML')
    except Exception:
        pass

def add_wish_step(message):
    # Если Настя нажала на кнопку меню вместо ввода желания
    if message.content_type == 'text' and (
        message.text.lower() == 'отмена' or
        message.text in ['🎁 Мой Вишлист', '💌 Хочу комплимент', '🥺 Сигнал любимому', '✨ Предсказание на день', '🎲 Рулетка выбора']
    ):
        if message.text.lower() == 'отмена':
            bot.send_message(message.chat.id, "Отменено 🌸", reply_markup=girl_menu())
        else:
            handle_text(message)
        return

    # 1. Если Настя прислала ФОТО (скриншот)
    if message.content_type == 'photo':
        photo_id = message.photo[-1].file_id  # Берём фото в лучшем качестве
        if message.caption:
            # Если к фото сразу есть подпись/ссылка — сохраняем сразу
            save_new_wish(message.chat.id, message.caption, photo_id)
        else:
            # Если фото без подписи — просим досбросить описание или ссылку
            msg = bot.send_message(
                message.chat.id,
                "Фотку поймал! 📸😍\nА теперь напиши название этой хотелки или скинь ссылку на неё (WB / Ozon / ЗЯ):"
            )
            bot.register_next_step_handler(msg, add_wish_caption_step, photo_id)

    # 2. Если Настя прислала просто ТЕКСТ или ссылку без фото
    elif message.content_type == 'text':
        save_new_wish(message.chat.id, message.text, photo_id=None)

    else:
        bot.send_message(message.chat.id, "Пришли, пожалуйста, фотографию (скриншот) или просто текст 🌸", reply_markup=girl_menu())

def add_wish_caption_step(message, photo_id):
    if message.content_type == 'text':
        if message.text.lower() == 'отмена':
            bot.send_message(message.chat.id, "Добавление отменено 🌸", reply_markup=girl_menu())
            return
        save_new_wish(message.chat.id, message.text, photo_id)
    else:
        save_new_wish(message.chat.id, "Без описания ✨", photo_id)

# --- ОБРАБОТКА INLINE-КНОПОК ---
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    data = load_data()

    # Добавление желания
    if call.data == 'wish_add':
        msg = bot.send_message(
            call.message.chat.id,
            "📸 <b>Отправь мне фото (скриншот)</b> своей хотелки и в подписи укажи ссылку или название!\n\n"
            "<i>(Либо можешь сначала скинуть фото, а следующим сообщением ссылку — или вообще написать просто текстом)</i> 🛍👇",
            parse_mode='HTML'
        )
        bot.register_next_step_handler(msg, add_wish_step)

    # Удаление конкретной карточки желания по кнопке под ней
    elif call.data.startswith('del_wish_'):
        wish_id = call.data.replace('del_wish_', '')
        new_wishlist = [item for item in data["wishlist"] if item["id"] != wish_id]
        
        if len(new_wishlist) < len(data["wishlist"]):
            data["wishlist"] = new_wishlist
            save_data(data)
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass
            bot.answer_callback_query(call.id, "Желание удалено из списка! ✨")
        else:
            bot.answer_callback_query(call.id, "Это желание уже было удалено 🌸")

    # Сигналы от Насти -> Парню
    elif call.data.startswith('sos_'):
        signals = {
            'sos_hug': "🚨 Настюшеньке срочно нужны ТВОИ ОБНИМАШКИ! 🤗",
            'sos_sweet': "🍫 Настюшенька намекает, что очень хочет ВКУСНЯШКУ!",
            'sos_sad': "😢 Настюшеньке ГРУСТНО! Срочно напиши или позвони ей!",
            'sos_love': "❤️ Настюшенька передаёт, что очень сильно тебя любит!"
        }
        reply_markup = types.InlineKeyboardMarkup(row_width=1)
        reply_markup.add(
            types.InlineKeyboardButton('🏃‍♂️ Ответить: «Уже бегу к тебе!»', callback_data='reply_run'),
            types.InlineKeyboardButton('🤗 Ответить: «Крепко-крепко обнимаю!»', callback_data='reply_hug'),
            types.InlineKeyboardButton('💋 Ответить: «Люблю тебя, котёнок!»', callback_data='reply_love')
        )
        try:
            bot.send_message(BOYFRIEND_ID, signals[call.data], reply_markup=reply_markup)
            bot.answer_callback_query(call.id, "Сигнал отправлен любимому! 💌", show_alert=True)
        except Exception:
            bot.answer_callback_query(call.id, "Сигнал отправлен! 💌", show_alert=True)

    # Быстрые ответы от Парня -> Насте
    elif call.data.startswith('reply_'):
        replies = {
            'reply_run': "🏃‍♂️💨 <b>Ответ от любимого:</b> «Уже бегу к тебе, моя хорошая!»",
            'reply_hug': "🤗💖 <b>Ответ от любимого:</b> «Крепко-крепко тебя обнимаю и целую!»",
            'reply_love': "💋❤️ <b>Ответ от любимого:</b> «Я тоже безумно сильно тебя люблю, Настюшенька!»"
        }
        if data["nastya_id"]:
            bot.send_message(data["nastya_id"], replies[call.data], parse_mode='HTML')
            bot.answer_callback_query(call.id, "Ответ улетел Настюшеньке! ✨")
        else:
            bot.answer_callback_query(call.id, "ID Насти ещё не сохранён!", show_alert=True)

    # Рулетка
    elif call.data == 'roll_food':
        bot.send_message(call.message.chat.id, f"Судьба решила: <b>{random.choice(FOOD_IDEAS)}</b> 😋", parse_mode='HTML')
    elif call.data == 'roll_date':
        bot.send_message(call.message.chat.id, f"Идея для нас: <b>{random.choice(DATE_IDEAS)}</b> 🥰", parse_mode='HTML')

    bot.answer_callback_query(call.id)

if __name__ == '__main__':
    print("Бот с фото-вишлистом запущен! 💖📸")
    bot.infinity_polling()