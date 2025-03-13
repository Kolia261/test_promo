import telebot
import sqlite3
import requests
import logging
from telebot import types
import time
import random, string

# Initialize bot and set up API
API_TOKEN = "7785892216:AAEh7sL6xXfTa7MR8NryYEkaFe1_vSrieg8"
CRYPTO_PAY_API_TOKEN = "352203:AASE7av52X3rkiTCUD4evQuIILeMScmPXxw"
bot = telebot.TeleBot(API_TOKEN)

# Set up logging
logging.basicConfig(level=logging.INFO)

# SQLite for storing user data
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            balance REAL DEFAULT 0.0,
            total_orders REAL DEFAULT 0.0,
            ref_code TEXT UNIQUE,
            used_ref_code TEXT DEFAULT NULL,
            referrer_id INTEGER DEFAULT NULL,
            invited_friends INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()


def generate_ref_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def get_user(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def add_user(user_id, name):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    ref_code = generate_ref_code()
    cursor.execute("""
        INSERT INTO users (user_id, name, ref_code, invited_friends) 
        VALUES (?, ?, ?, ?)
    """, (user_id, name, ref_code, 0))
    conn.commit()
    conn.close()
    return ref_code


# Function to create invoice
def create_invoice(asset, amount, description, retries=3, delay=5):
    url = "https://pay.crypt.bot/api/createInvoice"
    payload = {"asset": asset, "amount": str(amount), "description": description}
    headers = {"Crypto-Pay-API-Token": CRYPTO_PAY_API_TOKEN}

    for attempt in range(retries):
        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                return response.json().get('result', None)
        except requests.exceptions.ConnectionError:
            print(f"Connection error. Retrying in {delay} seconds...")
            time.sleep(delay)
    return None

# Function to check invoice status
def get_invoice(invoice_id):
    url = f"https://pay.crypt.bot/api/getInvoice?invoice_id={invoice_id}"
    headers = {"Crypto-Pay-API-Token": CRYPTO_PAY_API_TOKEN}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        result = response.json().get('result', None)
        print(f"Invoice data: {result}")  # Лог данных
        return result
    else:
        print(f"Error fetching invoice: {response.text}")  # Лог ошибок
    return None


@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if user:
        name = user[1]
        ref_code = user[4]
    else:
        first_name = message.from_user.first_name
        ref_code = generate_ref_code()
        cursor.execute("INSERT INTO users (user_id, name, ref_code) VALUES (?, ?, ?)", (user_id, first_name, ref_code))
        conn.commit()
        name = first_name
    
    conn.close()

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🔑 Enter Referral Code"))
    markup.add(types.KeyboardButton("🏠 Main Menu"))

    bot.send_message(
        user_id,
        f"✨ Thank you for joining our service, {name}!\n"
        "Here you will find promo codes for various cryptocurrencies. Don't worry about security, we sell only guaranteed promo codes.\n\n"
        f"✨ Your unique referral code: `{ref_code}`\n"
        "You can invite friends using this code or by sending them the link below.",
        parse_mode="Markdown",
        reply_markup=markup
    )


@bot.message_handler(func=lambda message: message.text == "🔑 Enter Referral Code")
def ask_for_ref_code(message):
    msg = bot.send_message(message.chat.id, "🔑 Please enter your referral code:")
    bot.register_next_step_handler(msg, process_ref_code)

def process_ref_code(message):
    user_id, ref_code = message.chat.id, message.text.strip().upper()
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM users WHERE ref_code = ?", (ref_code,))
    referrer = cursor.fetchone()

    if referrer:
        referrer_id = referrer[0]

        # Проверяем, чтобы пользователь не использовал рефкод повторно
        cursor.execute("SELECT used_ref_code FROM users WHERE user_id = ?", (user_id,))
        used_ref_code = cursor.fetchone()[0]
        if used_ref_code:
            bot.send_message(user_id, "❌ You have already used a referral code.")
            conn.close()
            return

        # Обновление данных
        cursor.execute("UPDATE users SET used_ref_code = ?, referrer_id = ? WHERE user_id = ?", (ref_code, referrer_id, user_id))
        cursor.execute("UPDATE users SET balance = balance + 1, invited_friends = invited_friends + 1 WHERE user_id = ?", (referrer_id,))
        conn.commit()

        # Уведомление реферера
        bot.send_message(referrer_id, f"🎉 You have a new referral! {message.from_user.first_name} joined using your code.")

        bot.send_message(user_id, "✅ Referral code applied successfully!")
    else:
        bot.send_message(user_id, "❌ Invalid referral code. Try again.")

    conn.close()


@bot.message_handler(func=lambda message: message.text == "🏠 Main Menu")
def main_menu(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("📝 Rules"))
    keyboard.add(types.KeyboardButton("👤 Profile"))
    keyboard.add(types.KeyboardButton("🔍 Find promo code"))
    bot.send_message(message.chat.id, "🏠 Main Menu", reply_markup=keyboard)

# Main menu
def start_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("📝 Rules"))
    keyboard.add(types.KeyboardButton("👤 Profile"))
    keyboard.add(types.KeyboardButton("🔍 Find promo code"))
    logging.info("Main menu keyboard created.")
    return keyboard

# Handler for "Rules" button
@bot.message_handler(func=lambda message: message.text == "📝 Rules")
def show_rules(message):
    logging.info(f"Rules button clicked by {message.chat.id}")
    bot.send_message(message.chat.id, "📌 All promo codes come with a 72-hour guarantee after purchase.\n⚠ If the promo code becomes invalid due to your actions, a refund is not possible.")

# Handler for "Profile" button
@bot.message_handler(func=lambda message: message.text == "👤 Profile")
def show_profile(message):
    user_id = message.chat.id
    user = get_user(user_id)
    if user:
        name, balance, total_orders, ref_code, used_ref_code, invited_friends = user[1:7]
        profile_msg = (
            f"❤ Name: {name}\n"
            f"🔑 ID: {user_id}\n"
            f"💰 Balance: {balance}\n"
            f"💲 Total orders: {total_orders}\n"
            f"🆔 Referral code: `{ref_code}`\n"
            f"🤝 Invited friends: {invited_friends}"
        )
        if used_ref_code:
            profile_msg += f"\n🔗 Used referral code: `{used_ref_code}`"
    else:
        profile_msg = "❌ Profile not found!"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="📦 Order History", callback_data="order_history"))
    markup.add(types.InlineKeyboardButton(text="🔙 Back", callback_data="back_start"))

    bot.send_message(message.chat.id, profile_msg, parse_mode="Markdown", reply_markup=markup)



# Order history
@bot.callback_query_handler(func=lambda call: call.data == "order_history")
def order_history(call):
    user_id = call.message.chat.id
    logging.info(f"Order history requested by {user_id}")
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT total_orders FROM users WHERE user_id = ?", (user_id,))
    total_orders = cursor.fetchone()
    conn.close()
    
    if total_orders:
        bot.send_message(call.message.chat.id, f"📦 You have {total_orders[0]} orders.")
    else:
        bot.send_message(call.message.chat.id, "📦 You have no orders.")

# Referral system
@bot.callback_query_handler(func=lambda call: call.data == "referral_system")
def referral_system(call):
    user_id = call.message.chat.id
    referral_link = f"https://t.me/{bot.get_me().username}?start={user_id}"
    logging.info(f"Referral system requested by {user_id}")
    bot.send_message(call.message.chat.id, f"💡 Earn rewards with our referral system! Invite your friends and get rewarded for every purchase they make.\n💰 Your earnings: 1 point for each successful purchase made through your referral.\n🔗 Your unique referral link: {referral_link}")

# Find promo code
@bot.message_handler(func=lambda message: message.text == "🔍 Find promo code")
def find_promo_code(message):
    logging.info(f"Find promo code clicked by {message.chat.id}")
    # Send "Spinning the wheel..." message and remove keyboard
    markup = types.ReplyKeyboardRemove()
    sent_message = bot.send_message(message.chat.id, "🎰 Spinning the wheel...", reply_markup=markup)

    # Delay 3 seconds
    time.sleep(3)

    # Delete the message
    bot.delete_message(message.chat.id, sent_message.message_id)

    # Send main message
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="💰 Buy promo code", callback_data="buy_promo"))
    markup.add(types.InlineKeyboardButton(text="🔙 Back", callback_data="back_start"))
    bot.send_message(message.chat.id, "📃 Platform: {link} (hidden)\n📃 Promo code: {code} (hidden)", reply_markup=markup)

# Handler for buying promo code
@bot.callback_query_handler(func=lambda call: call.data == "buy_promo")
def buy_promo(call):
    logging.info(f"Promo code purchase requested by {call.message.chat.id}")
    asset = 'USDT'
    amount = 10
    send_invoice(call.message, asset, amount, 'Buying promo code')

# Function to create and send invoice
def send_invoice(message, asset, amount, description):
    invoice = create_invoice(asset, amount, description)
    if invoice:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text='💰 Pay', url=invoice['pay_url']))
        keyboard.add(types.InlineKeyboardButton(text='🔄 Check', callback_data=f'check|{invoice["invoice_id"]}|{amount}'))
        keyboard.add(types.InlineKeyboardButton(text='🧑‍🤝‍🧑 Invite 2 friends', callback_data='invite_3_friends'))
        bot.send_message(message.chat.id, f'Amount to pay: {amount} {asset}', reply_markup=keyboard)

# Список промокодов
PROMO_CODES = [
    "xO0KfdJNwH", "first3000dollars", "BITWIN_Free_1000DOGE", "BitWinPROMO_3333TRX",
    "Promo444XRP_BitWin", "yoPx9IbDmr", "edvOiPvQJN", "secretOFtron", "hackDOUBLETether",
    "TRON_EzGo2FREECODE", "FREEweu10kUSDT", "LiK4S8bxNf", "MoRethenLITE", "ZaluPA9999",
    "2xRE4FiWhn", "U7Q7OSnEMx", "hidden_3ao7ZpZtA4i", "fReE1oo0vWyQ3mm258",
    "05SOLmhstGvL4RD", "KinuL_LoHAnaTROn", "11Bitcoion4_you_BitWinCC",
    "MY11SOLANA_CCBITWIN", "PURCHASE_2MILLION", "CRAzyFrOG_123", "BNB420NigerOG",
    "FyP9f24vxe_aim999usdt", "LUCKY3MILL", "LEGIT_FREE_3_BTC", "BOMBOCLAT_millioner",
    "NAG_CHAMPA2025", "Sa7Yk9vUR2VFN", "DINO-CODE1029098", "m4V8TurboGTRS",
    "makerS13", "EASYmoney_4U", "freeRose_500doll", "Rolex4U_brr"
]

# Обработчик проверки оплаты
@bot.callback_query_handler(func=lambda call: call.data.startswith('check'))
def check_payment(call):
    _, invoice_id, amount = call.data.split('|')
    invoice_data = get_invoice(invoice_id)
    if invoice_data and invoice_data.get('status') == 'paid' and str(invoice_data.get('amount')) == amount:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET total_orders = total_orders + 1 WHERE user_id = ?", (call.message.chat.id,))
        conn.commit()
        conn.close()
        
        # Выбор случайного промокода
        promo_code = random.choice(PROMO_CODES)
        
        bot.send_message(call.message.chat.id, f'✅ Payment of {amount} confirmed.')
        bot.send_message(
            call.message.chat.id,
            f"🎁 Here's your promo code: `{promo_code}`\n"
            "🔗 Use it here: [BitWin](https://bitwin.exchange/)",
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
    else:
        bot.send_message(call.message.chat.id, "❌ Payment not confirmed. Try again later.")



@bot.callback_query_handler(func=lambda call: call.data == "invite_3_friends")
def invite_friends(call):
    user_id = call.message.chat.id
    user = get_user(user_id)

    if len(user) >= 8:
        invited_friends = user[7]  # Количество приглашенных друзей
        if invited_friends >= 2:
            promo_code = random.choice(PROMO_CODES)
            bot.send_message(
                call.message.chat.id,
                f"🎉 Congratulations! You've invited 2 friends and earned a free promo code:\n\n"
                f"🎁 Your promo code: `{promo_code}`\n"
                f"🔗 Use it here: [BitWin](https://bitwin.exchange/)",
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
        else:
            invited_friends = 0
            bot.send_message(user_id, f"❌ You need {2 - invited_friends} more friends to get a free promo code.")
    else:
        bot.send_message(user_id, "❌ Profile not found!")




# Handler for "Back" button
@bot.callback_query_handler(func=lambda call: call.data == "back_start")
def back_to_start(call):
    logging.info(f"Back button clicked by {call.message.chat.id}")
    bot.send_message(
        call.message.chat.id,
        "You are now back at the main menu.",
        reply_markup=start_menu()
    )

init_db()

# Start bot
logging.info("Bot is starting...")
bot.polling(none_stop=True) 
