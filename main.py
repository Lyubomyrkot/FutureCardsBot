import telebot
import json
import os
from telebot import types
import random

bot = telebot.TeleBot('8326718314:AAHo0QDvdlLKiQnA6kIpEQWGoxU9a1iNGXk')

USERS_FILE = "users.json"

# завантаження існуючих користувачів
users_data = {}
if os.path.exists(USERS_FILE):
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:  # якщо файл не порожній
                users_data = json.loads(content)
    except json.JSONDecodeError:
        users_data = {}  # якщо файл пошкоджений або порожній, починаємо з пустого словника

# функція для збереження користувачів
def save_user(user_id, first_name, last_name, lang):
    users_data[str(user_id)] = {
        "first_name": first_name,
        "last_name": last_name,
        "language": lang
    }
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users_data, f, ensure_ascii=False, indent=4)

# завантажуємо карти з JSON
with open("cards.json", "r", encoding="utf-8") as f:
    cards_data = json.load(f)

# створюємо 36 карт (ключі такі ж, як у JSON: "6♥", "7♥" і т.д.)
suits = ["♥", "♠", "♦", "♣"]
ranks = ["6", "7", "8", "9", "10", "J", "Q", "K", "A"]
deck = [f"{r}{s}" for s in suits for r in ranks]

# тут зберігається вибрана мова для кожного юзера
user_langs = {}

# тексти для різних мов
texts = {
    "uk": {
        "choose_theme": "Тепер можеш витягувати карти!",
        "buttons": ["🎴 Витягнути карту (Кохання)", "🎴 Витягнути карту (Майбутнє)", "🎴 Витягнути карту (Багатство)", "🎴 Витягнути карту (Дружба)"],
        "your_card": "Твоя карта"
    },
    "en": {
        "choose_theme": "Now you can draw cards!",
        "buttons": ["🎴 Draw a card (Love)", "🎴 Draw a card (Future)", "🎴 Draw a card (Wealth)", "🎴 Draw a card (Friendship)"],
        "your_card": "Your card"
    }
}

# функція для створення клавіатури
def get_main_keyboard(lang):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for btn in texts[lang]["buttons"]:
        markup.add(types.KeyboardButton(btn))
    return markup

#Обробляємо командку старт де зразу даємо вибір мови
@bot.message_handler(commands=['start'])
def start(message):
    #перевіряємо чи юзер вже вибрав мову
    user_id = message.chat.id
    if user_id not in user_langs:
        # Створюємо клавіатуру для вибору мови
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Українська 🇺🇦")
        btn2 = types.KeyboardButton("English 🇬🇧")
        markup.add(btn1, btn2)

        bot.send_message(
            message.chat.id, 
            "Оберіть мову / Choose your language", 
            reply_markup=markup)
    else:
        # якщо мова вже вибрана, відразу показуємо меню карт
        lang = user_langs[user_id]
        markup_card = get_main_keyboard(lang)
        bot.send_message(
            user_id,
            texts[lang]["choose_theme"],
            reply_markup=markup_card
        )
    
#Обробляємо вибір мови
@bot.message_handler(func=lambda message: message.text in ["Українська 🇺🇦", "English 🇬🇧"])
def choose_language(message):
    user_id = message.chat.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    if message.text == "Українська 🇺🇦":
        user_langs[message.chat.id] = 'uk'
        bot.send_message(message.chat.id, "Ви обрали українську мову. Введіть /help для отримання списку команд.")
    else:
        user_langs[message.chat.id] = 'en'
        bot.send_message(message.chat.id, "You have chosen English. Type /help to get the list of commands.")

    lang = user_langs[message.chat.id]
    save_user(user_id, first_name, last_name, lang)

    markup_card = get_main_keyboard(lang)
    
    bot.send_message(message.chat.id, texts[lang]["choose_theme"], reply_markup=markup_card)

@bot.message_handler(func=lambda m: any(m.text in texts[lang]["buttons"] for lang in texts))
def draw_card(message):
    chat_id = message.chat.id
    lang = user_langs.get(chat_id, "en")  # мова за замовчуванням

    # визначаємо тему
    if message.text in [texts["uk"]["buttons"][0], texts["en"]["buttons"][0]]:
        theme = "love"
    elif message.text in [texts["uk"]["buttons"][1], texts["en"]["buttons"][1]]:
        theme = "future"
    elif message.text in [texts["uk"]["buttons"][2], texts["en"]["buttons"][2]]:
        theme = "wealth"
    elif message.text in [texts["uk"]["buttons"][3], texts["en"]["buttons"][3]]:
        theme = "friendship"

    # вибираємо випадкову карту
    card = random.sample(deck, 4)

    # дістаємо передбачення з JSON
    msg = ""
    for card in card:
        predictions = cards_data[card][theme][lang]
        prediction = random.choice(predictions)
        msg += f"{texts[lang]['your_card']}: {card}\n{prediction}\n\n"

    bot.send_message(chat_id, msg)


@bot.message_handler(commands=['lang'])
def change_language(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_uk"))
    markup.add(types.InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"))
    bot.send_message(
        message.chat.id, 
        "Оберіть мову / Choose language:", 
        reply_markup=markup)
    
# коли змінюємо мову через /lang    
@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def set_language(call):
    user_id = call.from_user.id
    lang = call.data.split("_")[1]
    user_langs[user_id] = lang

    # 🔄 оновлюємо дані в users.json
    first_name = call.from_user.first_name
    last_name = call.from_user.last_name
    save_user(user_id, first_name, last_name, lang)

    if lang == "uk":
        bot.answer_callback_query(call.id, "Мову змінено на українську 🇺🇦")
        bot.edit_message_text("✅ Тепер бот працює українською.", call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "Language switched to English 🇬🇧")
        bot.edit_message_text("✅ Bot now works in English.", call.message.chat.id, call.message.message_id)

    # кнопки для витягування карти
    markup_card = get_main_keyboard(lang)
    bot.send_message(call.message.chat.id, texts[lang]["choose_theme"], reply_markup=markup_card)

@bot.message_handler(commands=['help'])
def help_command(message):
    lang = user_langs.get(message.chat.id, "en")
    if lang == "uk":
        help_text = (
            "📖 *Довідка по боту*\n\n"
            "✨ Основні команди:\n"
            "▫️ /start – Почати спілкування з ботом\n"
            "▫️ /help – Показати це повідомлення\n"
            "▫️ /lang – Змінити мову бота\n\n"
            "🎴 *Як користуватись*: \n"
            "Після вибору мови ти можеш витягувати карти на тему кохання 💕, фінансів 💰, дружби 🤝 або майбутнього 🔮."
        )
    else:
        help_text = (
            "📖 *Bot Guide*\n\n"
            "✨ Main commands:\n"
            "▫️ /start – Start interaction with the bot\n"
            "▫️ /help – Show this message\n"
            "▫️ /lang – Change bot language\n\n"
            "🎴 *How to use*: \n"
            "After choosing a language, you can draw cards on the theme of love 💕, wealth 💰, friendship 🤝, or future 🔮."
        )
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown")

bot.polling(none_stop=True)