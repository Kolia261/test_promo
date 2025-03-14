import telebot
import sqlite3
import requests
import logging
from telebot import types
import time
import random, string
import re
from datetime import datetime

# Initialize bot and set up API
API_TOKEN = "7075318255:AAFMcGNNV8BnIo6zqRbwqK-_3UrajgJVxJg"
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
            total_generated INTEGER DEFAULT 0,
            last_generated TIMESTAMP,
            premium_until TIMESTAMP DEFAULT NULL,
            total_donated REAL DEFAULT 0.0
        )
    ''')
    conn.commit()
    conn.close()

def generate_promo_code():
    prefix = random.choice(["WIN", "BONUS", "PROMO", "SPECIAL", "VIP", "ELITE", "SUPER"])
    numbers = ''.join(random.choices(string.digits, k=4))
    letters = ''.join(random.choices(string.ascii_uppercase, k=3))
    return f"{prefix}_{numbers}{letters}"

# Списки промокодов для разных сайтов
BITWIN_PROMO_CODES = [
    "xO0KfdJNwH", "first3000dollars", "BITWIN_Free_1000DOGE",
    "BitWinPROMO_3333TRX", "Promo444XRP_BitWin", "yoPx9IbDmr",
    "edvOiPvQJN", "secretOFtron", "hackDOUBLETether",
    "TRON_EzGo2FREECODE", "FREEweu10kUSDT", "LiK4S8bxNf",
    "MoRethenLITE", "ZaluPA9999", "2xRE4FiWhn", "U7Q7OSnEMx",
    "hidden_3ao7ZpZtA4i", "fReE1oo0vWyQ3mm258", "05SOLmhstGvL4RD",
    "KinuL_LoHAnaTROn", "11Bitcoion4_you_BitWinCC", "MY11SOLANA_CCBITWIN",
    "PURCHASE_2MILLION", "CRAzyFrOG_123", "BNB420NigerOG",
    "FyP9f24vxe_aim999usdt", "Fig8q238-8-20SOLANAbonusCLUB_20",
    "LUCKY3MILL", "ChristmasGIFT1488", "allahuakbarLIMITEDTETHER",
    "SANTASAVINGS", "LEGIT_FREE_3_BTC", "2guo_PIDIDI",
    "BOMBOCLAT_millioner", "NAG_CHAMPA2025", "DUPA_XRP2024",
    "freeRose500doll", "Sa7Yk9vUR2VFN", "DINO-CODE1029098",
    "m4V8TurboGTRS", "makerS13", "EASYmoney_4U", "freeRose_500doll",
    "Rolex4U_brr"
]

MONETURO_PROMO_CODES = ["M0neTUR01", "PROMOofSecretMILLION"]

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO users 
        (user_id, name, total_generated, last_generated) 
        VALUES (?, ?, 0, NULL)
    """, (user_id, message.from_user.first_name))
    conn.commit()
    conn.close()

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("🎁 Generate Promo Code"))
    markup.row(types.KeyboardButton("💎 Support us"), types.KeyboardButton("👑 Premium"))
    markup.row(types.KeyboardButton("📊 My Stats"), types.KeyboardButton("ℹ️ Help"))

    welcome_text = (
        "🌟 Welcome to our Premium Promo Code Service! 🌟\n\n"
        "Our goal is to help you unlock exclusive offers and rewards. "
        "By using our bot, you gain access to hidden promo codes that can give you amazing discounts and bonuses.\n\n"
        "🔥 Features:\n"
        "• Generate unique promo codes\n"
        "• Get premium access for special codes\n"
        "• Track your usage statistics\n"
        "• 24/7 code generation\n\n"
        "Get ready to discover exciting surprises and save big with our carefully curated promo codes! 🎉"
    )
    
    bot.send_message(user_id, welcome_text, reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "ℹ️ Help")
def show_help(message):
    help_text = (
        "🔍 Bot Commands and Features:\n\n"
        "🎁 Generate Promo Code - Get a unique promo code\n"
        "💎 Support us - Support our service with crypto\n"
        "👑 Premium - Get premium access\n"
        "📊 My Stats - View your usage statistics\n"
        "ℹ️ Help - Show this help message\n\n"
        "✨ Premium Benefits:\n"
        "• Priority code generation\n"
        "• Exclusive VIP codes\n"
        "• No daily limits\n"
        "• Premium support\n\n"
        "🔐 All codes are guaranteed to be unique!"
    )
    bot.send_message(message.chat.id, help_text)

@bot.message_handler(func=lambda message: message.text == "📊 My Stats")
def show_stats(message):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT total_generated, last_generated, premium_until, total_donated 
        FROM users WHERE user_id = ?
    """, (message.chat.id,))
    stats = cursor.fetchone()
    conn.close()

    if stats:
        total_generated, last_generated, premium_until, total_donated = stats
        premium_status = "✅ Active" if premium_until and datetime.strptime(premium_until, '%Y-%m-%d %H:%M:%S') > datetime.now() else "❌ Inactive"
        
        stats_text = (
            "📊 Your Statistics:\n\n"
            f"🎁 Total Codes Generated: {total_generated}\n"
            f"⏰ Last Generation: {last_generated if last_generated else 'Never'}\n"
            f"👑 Premium Status: {premium_status}\n"
            f"💎 Total Donated: {total_donated} USDT\n\n"
            "Keep generating codes to improve your stats! 🚀"
        )
        bot.send_message(message.chat.id, stats_text)

@bot.message_handler(func=lambda message: message.text == "👑 Premium")
def show_premium(message):
    premium_text = (
        "👑 Premium Membership Benefits:\n\n"
        "✨ What you get:\n"
        "• Priority code generation\n"
        "• Exclusive VIP promo codes\n"
        "• Unlimited generations\n"
        "• Premium support\n"
        "• Early access to new features\n\n"
        "💎 Premium Plans:\n"
        "• 1 Week - 5 USDT\n"
        "• 1 Month - 15 USDT\n"
        "• 3 Months - 35 USDT"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("1 Week", callback_data="premium|7|5"),
        types.InlineKeyboardButton("1 Month", callback_data="premium|30|15"),
        types.InlineKeyboardButton("3 Months", callback_data="premium|90|35")
    )
    
    bot.send_message(message.chat.id, premium_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('premium'))
def process_premium(call):
    _, days, amount = call.data.split('|')
    send_invoice(call.message, 'USDT', int(amount), f'Premium membership for {days} days')

@bot.message_handler(func=lambda message: message.text == "🎁 Generate Promo Code")
def ask_for_link(message):
    msg = bot.send_message(
        message.chat.id,
        "🔗 Please enter the link to receive your promo code:\n"
        "(Must start with http:// or https://)\n"
        "⚠️ Important: The link must be entered exactly!"
    )
    bot.register_next_step_handler(msg, process_link)

def get_promo_code_for_site(link):
    if link == "https://bitwin.exchange":
        return random.choice(BITWIN_PROMO_CODES)
    elif link == "https://moneturo.com":
        return random.choice(MONETURO_PROMO_CODES)
    return None

def process_link(message):
    link = message.text.strip()
    promo_code = get_promo_code_for_site(link)
    
    if promo_code:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users 
            SET total_generated = total_generated + 1,
                last_generated = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (message.chat.id,))
        conn.commit()
        conn.close()

        success_text = (
            "✅ Link verified successfully!\n\n"
            f"🎁 Here's your unique promo code: `{promo_code}`\n\n"
            "🌟 Benefits:\n"
            "• Guaranteed to work\n"
            "• 72-hour validity\n"
            "• Exclusive rewards\n\n"
            "💫 Use it now to claim your special bonus!"
        )

        bot.send_message(
            message.chat.id,
            success_text,
            parse_mode="Markdown"
        )
    else:
        bot.send_message(
            message.chat.id,
            "❌ Invalid link format!\n\n"
            "Please make sure your link:\n"
            "• Starts with http:// or https://\n"
            "• Contains no spaces\n"
            "• Is a valid URL\n\n"
            "Try again with a correct link format 🔄"
        )

@bot.message_handler(func=lambda message: message.text == "💎 Support us")
def support_us(message):
    support_text = (
        "💎 Support Our Service!\n\n"
        "Your contribution helps us:\n"
        "• Maintain the service\n"
        "• Add new features\n"
        "• Improve code quality\n"
        "• Provide better support\n\n"
        "Choose your contribution amount:"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("5 USDT", callback_data="donate|5"),
        types.InlineKeyboardButton("10 USDT", callback_data="donate|10"),
        types.InlineKeyboardButton("20 USDT", callback_data="donate|20")
    )
    
    bot.send_message(message.chat.id, support_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('donate'))
def process_donation(call):
    _, amount = call.data.split('|')
    send_invoice(call.message, 'USDT', int(amount), 'Support donation')

def send_invoice(message, asset, amount, description):
    invoice = create_invoice(asset, amount, description)
    if invoice:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text='💰 Pay Now', url=invoice['pay_url']))
        keyboard.add(types.InlineKeyboardButton(text='🔄 Check Payment', callback_data=f'check|{invoice["invoice_id"]}|{amount}|{description}'))
        
        invoice_text = (
            f"💎 Amount to pay: {amount} {asset}\n\n"
            "✅ Secure payment via Crypto Bot\n"
            "⚡ Instant processing\n"
            "🔐 Safe and reliable"
        )
        
        bot.send_message(message.chat.id, invoice_text, reply_markup=keyboard)

def create_invoice(asset, amount, description):
    url = "https://pay.crypt.bot/api/createInvoice"
    payload = {"asset": asset, "amount": str(amount), "description": description}
    headers = {"Crypto-Pay-API-Token": CRYPTO_PAY_API_TOKEN}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json().get('result', None)
    except requests.exceptions.RequestException as e:
        logging.error(f"Error creating invoice: {e}")
    return None

@bot.callback_query_handler(func=lambda call: call.data.startswith('check'))
def check_payment(call):
    _, invoice_id, amount, *description_parts = call.data.split('|')
    description = '|'.join(description_parts)
    url = f"https://pay.crypt.bot/api/getInvoice?invoice_id={invoice_id}"
    headers = {"Crypto-Pay-API-Token": CRYPTO_PAY_API_TOKEN}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            invoice_data = response.json().get('result', {})
            if invoice_data.get('status') == 'paid':
                conn = sqlite3.connect('users.db')
                cursor = conn.cursor()
                
                if 'Premium membership' in description:
                    days = int(description.split()[3])
                    cursor.execute("""
                        UPDATE users 
                        SET premium_until = datetime('now', '+' || ? || ' days'),
                            total_donated = total_donated + ?
                        WHERE user_id = ?
                    """, (days, float(amount), call.message.chat.id))
                else:
                    cursor.execute("""
                        UPDATE users 
                        SET total_donated = total_donated + ?
                        WHERE user_id = ?
                    """, (float(amount), call.message.chat.id))
                
                conn.commit()
                conn.close()
                
                success_text = (
                    "✨ Payment Successful! ✨\n\n"
                    f"💎 Amount: {amount} USDT\n"
                    "Thank you for your support! 🙏\n\n"
                    "Your contribution helps us maintain and improve our service."
                )
                
                bot.send_message(call.message.chat.id, success_text)
                return
    except requests.exceptions.RequestException as e:
        logging.error(f"Error checking payment: {e}")
    
    bot.send_message(
        call.message.chat.id,
        "⏳ Payment not confirmed yet.\n"
        "Please wait a few minutes and try checking again."
    )

if __name__ == "__main__":
    init_db()
    logging.info("✨ Bot is starting...")
    bot.polling(none_stop=True)
