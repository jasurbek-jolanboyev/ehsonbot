# ehson_all_in_one.py - Complete Telegram Ehson Bot with Integrated WebApp

import os
import json
import logging
import sqlite3
import asyncio
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid
import requests

# Flask imports
from flask import Flask, request, jsonify, make_response

# aiogram imports
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.fsm.storage.memory import MemoryStorage

# dotenv for environment variables
from dotenv import load_dotenv

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ehson.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load .env
load_dotenv()

# Environment variables with validation
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
CHANNEL_ID = os.getenv("CHANNEL_ID")
PAYMENT_FORM_URL = os.getenv("PAYMENT_FORM_URL", "/payment")
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")

# Validate required variables
required_vars = {"BOT_TOKEN": BOT_TOKEN, "ADMIN_ID": ADMIN_ID}
for var_name, var_value in required_vars.items():
    if not var_value:
        logger.error(f"{var_name} topilmadi. .env fayliga qo'shing.")
        raise SystemExit(f"{var_name} topilmadi.")

# Database path
DB_PATH = 'ehson_test.db'

# Default data
DEFAULT_CAMPAIGNS = [
    {
        'id': 'campaign_1',
        'title': "Anvar's Yurak Operatsiyasi",
        'category': "tibbiyot",
        'description': "7 yoshli Anvarning yurak operatsiyasi uchun yordam kerak. Oila imkoniyatlari cheklangan. Operatsiya Koreya Respublikasida o'tkazilishi kerak.",
        'targetAmount': 50000000,
        'currentAmount': 35000000,
        'donors': 234,
        'daysLeft': 15,
        'urgent': True,
        'cardNumber': "8600 1234 5678 9012",
        'cardOwner': "ANVAR OTASI KARIM UMAROV",
        'contactPhone': "+998-95-888-38-51",
        'contactName': "Karim Umarov (Anvar otasi)",
        'image': '🏥',
        'createdBy': 'Admin',
        'createdAt': datetime.now().isoformat()
    },
    {
        'id': 'campaign_2',
        'title': "Maryam's Onkologiya Davolash",
        'category': "tibbiyot",
        'description': "45 yoshli Maryam onaning onkologiya kasalligi uchun kimyoterapiya kursi kerak. Davolash Turkiyada o'tkaziladi.",
        'targetAmount': 80000000,
        'currentAmount': 25000000,
        'donors': 156,
        'daysLeft': 30,
        'urgent': True,
        'cardNumber': "8600 2345 6789 0123",
        'cardOwner': "MARYAM QIZI FOTIMA KARIMOVA",
        'contactPhone': "+998-95-888-38-51",
        'contactName': "Fotima Karimova (Maryam qizi)",
        'image': '🏥',
        'createdBy': 'Admin',
        'createdAt': datetime.now().isoformat()
    },
    {
        'id': 'campaign_3',
        'title': "Nogironlik Aravachasi",
        'category': "nogironlik",
        'description': "Harakat qilish imkoniyati cheklangan Dilshod uchun elektr aravachasi kerak. Nemis ishlab chiqargan yuqori sifatli aravachasi.",
        'targetAmount': 15000000,
        'currentAmount': 8500000,
        'donors': 89,
        'daysLeft': 25,
        'urgent': False,
        'cardNumber': "8600 6789 0123 4567",
        'cardOwner': "DILSHOD ONASI NARGIZA UMAROVA",
        'contactPhone': "+998-95-888-38-51",
        'contactName': "Nargiza Umarova (Dilshod onasi)",
        'image': '♿',
        'createdBy': 'Admin',
        'createdAt': datetime.now().isoformat()
    }
]

DEFAULT_ADS = [
    {
        'id': 'ad_1',
        'type': 'banner',
        'title': '🏥 Zamonaviy Tibbiy Markaz - Eng Yaxshi Xizmatlar!',
        'description': 'Eng yaxshi tibbiy xizmatlar va zamonaviy uskunalar',
        'linkUrl': 'https://t.me/serinaqu',
        'contact': '@serinaqu',
        'showDuration': 12,
        'banner': True,
        'createdAt': datetime.now().isoformat()
    },
    {
        'id': 'ad_2',
        'type': 'banner',
        'title': '⚖️ Bepul Yuridik Maslahat - 24/7 Xizmat!',
        'description': 'Har qanday huquqiy masalalar bo\'yicha bepul maslahat',
        'linkUrl': 'https://t.me/serinaqu',
        'contact': '@serinaqu',
        'showDuration': 15,
        'banner': True,
        'createdAt': datetime.now().isoformat()
    }
]

DEFAULT_TEAM = [
    {
        'id': 1,
        'name': "Jasurbek Jo'lanboyev",
        'role': "CEO & Founder",
        'description': "Platformani yaratish va boshqarishda yetakchi rol o'ynaydi.",
        'image': "/home/serinaqu/Desktop/e-ehsonweb/assets/jasurbek.png",
        'socials': {
            'telegram': "https://t.me/Vscoderr",
            'youtube': "https://www.youtube.com/@Jasurbek_Jolanboyev",
            'instagram': "https://www.instagram.com/jasurbek.official.uz",
            'linkedin': "https://www.linkedin.com/in/jasurbek-jo-lanboyev-74b758351",
            'twitter': "https://x.com/Jolanboyev",
            'tiktok': "https://tiktok.com/@jasurbek_jolanboyev"
        }
    },
    {
        'id': 2,
        'name': "Ism Familiya 2",
        'role': "CTO",
        'description': "Texnik rivojlantirish va infratuzilmani boshqaradi.",
        'image': "https://via.placeholder.com/400x200?text=Team+Member+2",
        'socials': {
            'telegram': "https://t.me/Vscoderr",
            'linkedin': "https://www.linkedin.com/in/jasurbek-jo-lanboyev-74b758351"
        }
    },
    {
        'id': 3,
        'name': "Ism Familiya 3",
        'role': "Marketing Manager",
        'description': "Marketing strategiyalari va reklama ishlarini olib boradi.",
        'image': "https://via.placeholder.com/400x200?text=Team+Member+3",
        'socials': {
            'instagram': "https://www.instagram.com/jasurbek.official.uz",
            'twitter': "https://x.com/Jolanboyev"
        }
    },
    {
        'id': 4,
        'name': "Ism Familiya 4",
        'role': "Developer",
        'description': "Frontend va backend rivojlantirishda ishtirok etadi.",
        'image': "https://via.placeholder.com/400x200?text=Team+Member+4",
        'socials': {
            'youtube': "https://www.youtube.com/@Jasurbek_Jolanboyev",
            'tiktok': "https://tiktok.com/@jasurbek_jolanboyev"
        }
    },
    {
        'id': 5,
        'name': "Ism Familiya 5",
        'role': "Designer",
        'description': "UI/UX dizayn va grafik ishlarni amalga oshiradi.",
        'image': "https://via.placeholder.com/400x200?text=Team+Member+5",
        'socials': {
            'instagram': "https://www.instagram.com/jasurbek.official.uz"
        }
    },
    {
        'id': 6,
        'name': "Ism Familiya 6",
        'role': "Content Manager",
        'description': "Kontent yaratish va boshqarish bilan shug'ullanadi.",
        'image': "https://via.placeholder.com/400x200?text=Team+Member+6",
        'socials': {
            'telegram': "https://t.me/Vscoderr"
        }
    },
    {
        'id': 7,
        'name': "Ism Familiya 7",
        'role': "Support Specialist",
        'description': "Foydalanuvchilar yordami va texnik qo'llab-quvvatlash.",
        'image': "https://via.placeholder.com/400x200?text=Team+Member+7",
        'socials': {
            'linkedin': "https://www.linkedin.com/in/jasurbek-jo-lanboyev-74b758351"
        }
    },
    {
        'id': 8,
        'name': "Ism Familiya 8",
        'role': "Analyst",
        'description': "Ma'lumotlar tahlili va statistika bilan ishlaydi.",
        'image': "https://via.placeholder.com/400x200?text=Team+Member+8",
        'socials': {
            'twitter': "https://x.com/Jolanboyev"
        }
    }
]

DEFAULT_AD_SETTINGS = {
    'overlayDuration': 8,
    'skipAfter': 3,
    'showBanner': True,
    'bannerText': '🎯 Maxsus Taklif! Eng Yaxshi Xizmatlar'
}

# Database setup
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    created_at TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS payments (
                    payment_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    amount REAL,
                    status TEXT DEFAULT 'pending',
                    click_trans_id TEXT,
                    created_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS campaigns (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    category TEXT,
                    description TEXT,
                    targetAmount REAL,
                    currentAmount REAL,
                    donors INTEGER,
                    daysLeft INTEGER,
                    urgent INTEGER,
                    cardNumber TEXT,
                    cardOwner TEXT,
                    contactPhone TEXT,
                    contactName TEXT,
                    image TEXT,
                    createdBy TEXT,
                    createdAt TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS ads (
                    id TEXT PRIMARY KEY,
                    type TEXT,
                    title TEXT,
                    description TEXT,
                    linkUrl TEXT,
                    contact TEXT,
                    showDuration INTEGER,
                    banner INTEGER,
                    createdAt TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS team (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    role TEXT,
                    description TEXT,
                    image TEXT,
                    socials TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY,
                    data TEXT
                )''')
    # Insert defaults if not exist
    c.execute("SELECT COUNT(*) FROM campaigns")
    if c.fetchone()[0] == 0:
        for camp in DEFAULT_CAMPAIGNS:
            c.execute("INSERT INTO campaigns VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                      (camp['id'], camp['title'], camp['category'], camp['description'], camp['targetAmount'], camp['currentAmount'],
                       camp['donors'], camp['daysLeft'], 1 if camp['urgent'] else 0, camp['cardNumber'], camp['cardOwner'],
                       camp['contactPhone'], camp['contactName'], camp['image'], camp['createdBy'], camp['createdAt']))

    c.execute("SELECT COUNT(*) FROM ads")
    if c.fetchone()[0] == 0:
        for ad in DEFAULT_ADS:
            c.execute("INSERT INTO ads VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                      (ad['id'], ad['type'], ad['title'], ad['description'], ad['linkUrl'], ad['contact'],
                       ad['showDuration'], 1 if ad['banner'] else 0, ad['createdAt']))

    c.execute("SELECT COUNT(*) FROM team")
    if c.fetchone()[0] == 0:
        for member in DEFAULT_TEAM:
            c.execute("INSERT INTO team VALUES (?, ?, ?, ?, ?, ?)",
                      (member['id'], member['name'], member['role'], member['description'], member['image'], json.dumps(member['socials'])))

    c.execute("SELECT COUNT(*) FROM settings")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO settings VALUES (1, ?)", (json.dumps(DEFAULT_AD_SETTINGS),))

    # Test data for users and payments
    c.execute("INSERT OR IGNORE INTO users (user_id, username, first_name, created_at) VALUES (?, ?, ?, ?)",
              ("test_user_1", "testuser", "Test User", datetime.now().isoformat()))
    c.execute("INSERT OR IGNORE INTO payments (payment_id, user_id, amount, status, click_trans_id, created_at) VALUES (?, ?, ?, ?, ?, ?)",
              (str(uuid.uuid4()), "test_user_1", 10000.0, "success", "test_click_1", datetime.now().isoformat()))
    conn.commit()
    conn.close()
    logger.info("Database initialized with default and test data.")

init_db()

# Functions to get data from DB
def get_campaigns():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM campaigns")
    rows = c.fetchall()
    conn.close()
    campaigns = []
    for row in rows:
        camp = {
            'id': row[0],
            'title': row[1],
            'category': row[2],
            'description': row[3],
            'targetAmount': row[4],
            'currentAmount': row[5],
            'donors': row[6],
            'daysLeft': row[7],
            'urgent': bool(row[8]),
            'cardNumber': row[9],
            'cardOwner': row[10],
            'contactPhone': row[11],
            'contactName': row[12],
            'image': row[13],
            'createdBy': row[14],
            'createdAt': row[15]
        }
        campaigns.append(camp)
    return campaigns

def get_ads():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM ads")
    rows = c.fetchall()
    conn.close()
    ads = []
    for row in rows:
        ad = {
            'id': row[0],
            'type': row[1],
            'title': row[2],
            'description': row[3],
            'linkUrl': row[4],
            'contact': row[5],
            'showDuration': row[6],
            'banner': bool(row[7]),
            'createdAt': row[8]
        }
        ads.append(ad)
    return ads

def get_team():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM team")
    rows = c.fetchall()
    conn.close()
    team = []
    for row in rows:
        member = {
            'id': row[0],
            'name': row[1],
            'role': row[2],
            'description': row[3],
            'image': row[4],
            'socials': json.loads(row[5])
        }
        team.append(member)
    return team

def get_settings():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT data FROM settings LIMIT 1")
    row = c.fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    else:
        return DEFAULT_AD_SETTINGS

# Flask app setup
app = Flask(__name__)

# Payment HTML - Improved to match the platform style
PAYMENT_HTML = '''
<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>To'lov Qilish - E-Ehson</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-gray-100 flex items-center justify-center min-h-screen">
    <div class="bg-white p-8 rounded-lg shadow-lg max-w-md w-full">
        <h2 class="text-2xl font-bold mb-6 text-center text-gray-800">💳 To'lov Qilish</h2>
        <form id="paymentForm" action="{form_action}" method="get">
            <input type="hidden" name="merchant_id" value="YOUR_MERCHANT_ID">
            <input type="hidden" name="service_id" value="YOUR_SERVICE_ID">
            <input type="hidden" name="merchant_user_id" value="{user_id}">
            <input type="hidden" name="transaction_param" value="ehson_payment">
            <input type="hidden" name="return_url" value="{base_url}/success">
            <input type="hidden" name="card_type" value="0">
            <div class="mb-4">
                <label class="block text-sm font-medium mb-2 text-gray-700">To'lov Miqdori (so'm)</label>
                <input type="number" name="amount" value="10000" min="1000" required class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500">
            </div>
            <button type="submit" class="w-full bg-blue-600 text-white py-3 rounded-lg font-bold hover:bg-blue-700 transition-all duration-300">
                💳 To'lov Qilish
            </button>
        </form>
    </div>
    <script>
        if (window.Telegram) {
            Telegram.WebApp.expand();
        }
    </script>
</body>
</html>
'''

@app.route(PAYMENT_FORM_URL)
def payment_form():
    user_id = request.args.get('user_id', 'guest')
    campaign_id = request.args.get('campaign_id', '')
    form_action = "https://my.click.uz/services/pay" if not os.getenv("TEST_MODE") else f"{BASE_URL}/mock_click"
    html = PAYMENT_HTML.format(user_id=user_id, form_action=form_action, base_url=BASE_URL)
    return make_response(html)

@app.route("/success")
def success():
    return jsonify({"message": "To'lov muvaffaqiyatli!"})

@app.route("/mock_click", methods=["GET", "POST"])
def mock_click():
    """Simulate Click API response for testing"""
    if request.method == "GET":
        # Simulate redirect to callback
        data = {
            "merchant_id": "YOUR_MERCHANT_ID",
            "service_id": "YOUR_SERVICE_ID",
            "merchant_user_id": request.args.get("merchant_user_id"),
            "amount": request.args.get("amount", "10000"),
            "transaction_param": request.args.get("transaction_param"),
            "error": "0",
            "click_trans_id": str(uuid.uuid4()),
            "payment_id": str(uuid.uuid4())
        }
        logger.info(f"Mock Click data: {data}")
        # Send to callback
        response = requests.post(f"{BASE_URL}/click/callback", data=data)
        return jsonify({"status": "Mock payment processed", "callback_response": response.json()})
    return jsonify({"error": -1, "message": "Invalid method"})

@app.route("/click/callback", methods=["POST"])
def click_callback():
    data = request.form.to_dict()
    logger.info(f"Click callback data: {data}")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        user_id = data.get("merchant_user_id")
        amount = float(data.get("amount", 0))
        click_trans_id = data.get("click_trans_id", str(uuid.uuid4()))
        payment_id = data.get("payment_id", str(uuid.uuid4()))
        error_code = data.get("error", "-1")
        
        if not user_id:
            logger.error("No user_id in callback")
            conn.close()
            return jsonify({"error": -1, "message": "No user_id"}), 400
        
        # Save or update user
        c.execute("INSERT OR REPLACE INTO users (user_id, created_at) VALUES (?, ?)",
                  (user_id, datetime.now().isoformat()))
        
        # Update payment
        status = "success" if error_code == "0" else "failed"
        c.execute("INSERT OR REPLACE INTO payments (payment_id, user_id, amount, status, click_trans_id, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                  (payment_id, user_id, amount, status, click_trans_id, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        if error_code == "0":
            logger.info(f"✅ To‘lov qabul qilindi: ID = {payment_id}, Miqdor = {amount}, Foydalanuvchi = {user_id}")
            asyncio.run_coroutine_threadsafe(
                send_payment_confirmation(int(user_id), amount, status),
                bot_loop
            )
        else:
            logger.info(f"❌ To‘lov bekor qilindi: Error = {error_code}")
        
        return jsonify({"error": 0})
    
    except Exception as e:
        logger.error(f"Callback xatosi: {e}")
        return jsonify({"error": -1, "message": str(e)}), 500

# API routes
@app.route('/api/campaigns', methods=['GET', 'POST'])
def api_campaigns():
    if request.method == 'GET':
        return jsonify(get_campaigns())
    elif request.method == 'POST':
        data = request.json
        user_id = data.get('user_id')
        if user_id != ADMIN_ID:
            return jsonify({'error': 'Unauthorized'}), 403
        del data['user_id']
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        values = (
            data['id'], data['title'], data['category'], data['description'], data['targetAmount'], data['currentAmount'],
            data['donors'], data['daysLeft'], 1 if data['urgent'] else 0, data['cardNumber'], data['cardOwner'],
            data['contactPhone'], data['contactName'], data['image'], data['createdBy'], data['createdAt']
        )
        c.execute("INSERT OR REPLACE INTO campaigns VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", values)
        conn.commit()
        conn.close()
        return jsonify({'success': True})

@app.route('/api/campaigns/<id>', methods=['DELETE'])
def delete_campaign(id):
    data = request.json
    user_id = data.get('user_id')
    if user_id != ADMIN_ID:
        return jsonify({'error': 'Unauthorized'}), 403
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM campaigns WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/ads', methods=['GET', 'POST'])
def api_ads():
    if request.method == 'GET':
        return jsonify(get_ads())
    elif request.method == 'POST':
        data = request.json
        user_id = data.get('user_id')
        if user_id != ADMIN_ID:
            return jsonify({'error': 'Unauthorized'}), 403
        del data['user_id']
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        values = (
            data['id'], data['type'], data['title'], data['description'], data['linkUrl'], data['contact'],
            data['showDuration'], 1 if data['banner'] else 0, data['createdAt']
        )
        c.execute("INSERT OR REPLACE INTO ads VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", values)
        conn.commit()
        conn.close()
        return jsonify({'success': True})

@app.route('/api/ads/<id>', methods=['DELETE'])
def delete_ad(id):
    data = request.json
    user_id = data.get('user_id')
    if user_id != ADMIN_ID:
        return jsonify({'error': 'Unauthorized'}), 403
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM ads WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/team', methods=['GET', 'POST'])
def api_team():
    if request.method == 'GET':
        return jsonify(get_team())
    elif request.method == 'POST':
        data = request.json
        user_id = data.get('user_id')
        if user_id != ADMIN_ID:
            return jsonify({'error': 'Unauthorized'}), 403
        del data['user_id']
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        values = (
            data['id'], data['name'], data['role'], data['description'], data['image'], json.dumps(data['socials'])
        )
        c.execute("INSERT OR REPLACE INTO team VALUES (?, ?, ?, ?, ?, ?)", values)
        conn.commit()
        conn.close()
        return jsonify({'success': True})

@app.route('/api/team/<id>', methods=['DELETE'])
def delete_team(id):
    data = request.json
    user_id = data.get('user_id')
    if user_id != ADMIN_ID:
        return jsonify({'error': 'Unauthorized'}), 403
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM team WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/settings', methods=['GET', 'POST'])
def api_settings():
    if request.method == 'GET':
        return jsonify(get_settings())
    elif request.method == 'POST':
        data = request.json
        user_id = data.get('user_id')
        if user_id != ADMIN_ID:
            return jsonify({'error': 'Unauthorized'}), 403
        del data['user_id']
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE settings SET data = ? WHERE id=1", (json.dumps(data),))
        conn.commit()
        conn.close()
        return jsonify({'success': True})

@app.route('/api/clear', methods=['POST'])
def api_clear():
    data = request.json
    user_id = data.get('user_id')
    if user_id != ADMIN_ID:
        return jsonify({'error': 'Unauthorized'}), 403
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM campaigns")
    c.execute("DELETE FROM ads")
    c.execute("DELETE FROM team")
    c.execute("UPDATE settings SET data = ?", (json.dumps(DEFAULT_AD_SETTINGS),))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/export', methods=['GET'])
def api_export():
    data = {
        'campaigns': get_campaigns(),
        'ads': get_ads(),
        'team': get_team(),
        'settings': get_settings()
    }
    return jsonify(data)

# WebApp HTML - the second code with modifications
WEBAPP_HTML = '''\
<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>E-Ehson Professional - Xayriya Platformasi</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    
    <style>
        body {
            box-sizing: border-box;
        }
        
        .gradient-bg {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        .gradient-bg-2 {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        
        .card-hover {
            transition: all 0.4s ease;
        }
        
        .card-hover:hover {
            transform: translateY(-8px);
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
        }
        
        .progress-bar {
            background: linear-gradient(90deg, #4f46e5 0%, #06b6d4 100%);
        }
        
        .animate-pulse-slow {
            animation: pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
        
        .live-indicator {
            animation: pulse 2s infinite;
        }
        
        .social-icon {
            transition: all 0.3s ease;
        }
        
        .social-icon:hover {
            transform: translateY(-3px) scale(1.1);
        }
        
        .category-card {
            background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .fade-in-up {
            animation: fadeInUp 0.6s ease-out;
        }
        
        .glass-effect {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .text-shadow {
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .telegram-btn {
            background: linear-gradient(45deg, #0088cc, #00a0e6);
            transition: all 0.3s ease;
        }
        
        .telegram-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(0, 136, 204, 0.3);
        }
        
        /* Ad Overlay Styles */
        .ad-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.9);
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
            backdrop-filter: blur(10px);
        }
        
        .ad-content {
            max-width: 90%;
            max-height: 90%;
            background: white;
            border-radius: 20px;
            overflow: hidden;
            position: relative;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        }
        
        .ad-close-btn {
            position: absolute;
            top: 15px;
            right: 15px;
            background: rgba(0, 0, 0, 0.7);
            color: white;
            border: none;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            cursor: pointer;
            font-size: 18px;
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .ad-skip-btn {
            position: absolute;
            bottom: 20px;
            right: 20px;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 14px;
            z-index: 10000;
        }
        
        .ad-timer {
            position: absolute;
            top: 20px;
            left: 20px;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 14px;
            z-index: 10000;
        }
        
        /* Top Banner Ad */
        .top-banner-ad {
            background: linear-gradient(45deg, #ff6b6b, #feca57);
            color: white;
            padding: 10px 0;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .top-banner-ad::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            animation: shine 3s infinite;
        }
        
        @keyframes shine {
            0% { left: -100%; }
            100% { left: 100%; }
        }
        
        /* Mobile optimizations */
        @media (max-width: 768px) {
            .mobile-padding {
                padding: 1rem;
            }
            
            .mobile-text {
                font-size: 0.9rem;
            }
            
            .mobile-button {
                padding: 0.75rem 1.5rem;
                font-size: 0.9rem;
            }
            
            .mobile-card {
                margin-bottom: 1rem;
            }
            
            .ad-content {
                max-width: 95%;
                max-height: 85%;
            }
        }
        
        .touch-button {
            min-height: 44px;
            min-width: 44px;
        }
        
        .webview-safe {
            padding-bottom: env(safe-area-inset-bottom);
        }
        
        .hidden {
            display: none !important;
        }

        /* Admin Panel Styles */
        .admin-panel {
            background: linear-gradient(135deg, #1e3a8a 0%, #3730a3 100%);
        }
        
        .user-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        /* Privacy Modal Styles */
        .privacy-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
            backdrop-filter: blur(10px);
        }
        
        .privacy-content {
            max-width: 90%;
            max-height: 90%;
            background: white;
            border-radius: 20px;
            overflow-y: auto;
            position: relative;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            padding: 2rem;
        }
        
        .privacy-close-btn {
            position: absolute;
            top: 15px;
            right: 15px;
            background: rgba(0, 0, 0, 0.1);
            color: #333;
            border: none;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            cursor: pointer;
            font-size: 18px;
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
        }
        
        .privacy-close-btn:hover {
            background: rgba(0, 0, 0, 0.2);
        }

        /* Notification Styles */
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            border-radius: 10px;
            color: white;
            font-weight: bold;
            z-index: 10001;
            transform: translateX(400px);
            transition: transform 0.3s ease;
        }
        
        .notification.show {
            transform: translateX(0);
        }
        
        .notification.success {
            background: linear-gradient(45deg, #10b981, #059669);
        }
        
        .notification.error {
            background: linear-gradient(45deg, #ef4444, #dc2626);
        }
        
        .notification.info {
            background: linear-gradient(45deg, #3b82f6, #2563eb);
        }

        /* Team Section Styles */
        .team-card {
            background: white;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .team-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 30px rgba(0,0,0,0.15);
        }
        
        .team-image {
            height: 200px;
            object-fit: cover;
            width: 100%;
        }
        
        .team-socials {
            display: flex;
            justify-content: center;
            gap: 0.5rem;
            margin-top: 1rem;
            flex-wrap: wrap;
        }
        
        .team-social-icon {
            color: #666;
            font-size: 1.25rem;
            transition: all 0.3s ease;
            padding: 0.5rem;
            border-radius: 50%;
            background: #f3f4f6;
        }
        
        .team-social-icon:hover {
            color: #3b82f6;
            background: #e5e7eb;
            transform: scale(1.2);
        }
        
        /* Team Modal Styles */
        .team-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
            backdrop-filter: blur(10px);
        }
        
        .team-modal-content {
            max-width: 90%;
            max-height: 90%;
            background: white;
            border-radius: 20px;
            overflow-y: auto;
            position: relative;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            padding: 2rem;
            text-align: center;
        }
        
        .team-modal-image {
            width: 100%;
            max-width: 400px;
            height: auto;
            border-radius: 16px;
            margin-bottom: 1rem;
        }
        
        .team-modal-close {
            position: absolute;
            top: 15px;
            right: 15px;
            background: rgba(0, 0, 0, 0.1);
            color: #333;
            border: none;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            cursor: pointer;
            font-size: 18px;
            z-index: 10001;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
        }
        
        .team-modal-close:hover {
            background: rgba(0, 0, 0, 0.2);
        }

        /* Join Team Section */
        .join-team-btn {
            background: linear-gradient(45deg, #10b981, #059669);
            color: white;
            padding: 1rem 2rem;
            border-radius: 50px;
            font-weight: bold;
            transition: all 0.3s ease;
            border: none;
            cursor: pointer;
        }
        
        .join-team-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 10px 25px rgba(16, 185, 129, 0.3);
        }

        /* Admin List Styles */
        .admin-list-item {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.3s ease;
        }

        .admin-list-item:hover {
            background: rgba(255, 255, 255, 0.2);
        }

        .admin-action-btn {
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-size: 0.875rem;
            transition: all 0.3s ease;
        }

        .admin-edit-btn {
            background: #3b82f6;
            color: white;
        }

        .admin-edit-btn:hover {
            background: #2563eb;
        }

        .admin-delete-btn {
            background: #ef4444;
            color: white;
        }

        .admin-delete-btn:hover {
            background: #dc2626;
        }

        /* Responsive Enhancements for All Devices */
        @media (max-width: 480px) {
            .mobile-padding {
                padding: 0.75rem;
            }
            
            .mobile-text {
                font-size: 0.85rem;
            }
            
            .mobile-button {
                padding: 0.625rem 1.25rem;
                font-size: 0.85rem;
            }
            
            .admin-list-item {
                flex-direction: column;
                align-items: flex-start;
                gap: 0.5rem;
            }
        }

        @media (min-width: 769px) and (max-width: 1024px) {
            .tablet-padding {
                padding: 1.5rem;
            }
        }

        /* Monoblock/PC Optimizations */
        @media (min-width: 1200px) {
            .desktop-enhance {
                max-width: 1200px;
            }
        }

        /* Local Storage Indicator */
        .storage-indicator {
            position: fixed;
            bottom: 20px;
            left: 20px;
            background: rgba(16, 185, 129, 0.9);
            color: white;
            padding: 8px 12px;
            border-radius: 20px;
            font-size: 12px;
            z-index: 10000;
            display: none;
        }
    </style>
</head>
<body class="bg-gray-50">
    <!-- Privacy Policy Modal -->
    <div id="privacyModal" class="privacy-modal hidden">
        <div class="privacy-content">
            <button id="privacyCloseBtn" class="privacy-close-btn" onclick="closePrivacyModal()">
                <i class="fas fa-times"></i>
            </button>
            <h2 class="text-3xl font-bold mb-6 text-gray-800">🔒 Maxfiylik Siyosati</h2>
            <div class="text-gray-600 space-y-4">
                <p><strong>E-Ehson Professional</strong> platformasi foydalanuvchilarning maxfiyligini himoya qilishga bag'ishlangan.</p>
                
                <h3 class="text-xl font-bold text-gray-800 mt-6">📊 Ma'lumotlar To'plash</h3>
                <p>Biz faqat xayriya maqsadlari uchun zarur bo'lgan ma'lumotlarni to'playmiz:</p>
                <ul class="list-disc ml-6">
                    <li>Ism va familiya</li>
                    <li>Telefon raqami</li>
                    <li>Xayriya miqdori</li>
                </ul>
                
                <h3 class="text-xl font-bold text-gray-800 mt-6">🛡️ Ma'lumotlar Himoyasi</h3>
                <p>Barcha shaxsiy ma'lumotlar shifrlangan holda saqlanadi va uchinchi shaxslarga berilmaydi.</p>
                
                <h3 class="text-xl font-bold text-gray-800 mt-6">📞 Aloqa</h3>
                <p>Savollar bo'lsa, biz bilan bog'laning:</p>
                <ul class="list-disc ml-6">
                    <li>📱 Telegram: @serinaqu</li>
                    <li>📞 Telefon: +998-95-888-38-51</li>
                    <li>📧 Email: info@eehson.uz</li>
                </ul>
                
                <p class="text-sm text-gray-500 mt-6">Oxirgi yangilanish: 2025 yil</p>
            </div>
        </div>
    </div>

    <!-- Team Member Modal -->
    <div id="teamModal" class="team-modal hidden">
        <div class="team-modal-content">
            <button id="teamModalClose" class="team-modal-close" onclick="closeTeamModal()">
                <i class="fas fa-times"></i>
            </button>
            <img id="modalTeamImage" src="" alt="" class="team-modal-image">
            <h2 id="modalTeamName" class="text-3xl font-bold mb-4 text-gray-800"></h2>
            <p id="modalTeamRole" class="text-blue-600 font-semibold text-xl mb-4"></p>
            <p id="modalTeamDescription" class="text-gray-600 text-lg mb-6"></p>
            <div id="modalTeamSocials" class="team-socials justify-center"></div>
        </div>
    </div>

    <!-- Ad Overlay (Hidden by default) -->
    <div id="adOverlay" class="ad-overlay hidden">
        <div class="ad-content">
            <button id="adCloseBtn" class="ad-close-btn" onclick="closeAdOverlay()">
                <i class="fas fa-times"></i>
            </button>
            <div id="adTimer" class="ad-timer">5</div>
            <button id="adSkipBtn" class="ad-skip-btn hidden" onclick="closeAdOverlay()">
                Reklamani o'tkazib yuborish
            </button>
            <div id="adContentArea">
                <!-- Ad content will be loaded here -->
            </div>
        </div>
    </div>

    <!-- Top Banner Ad -->
    <div id="topBannerAd" class="top-banner-ad hidden">
        <div class="max-w-7xl mx-auto px-4 flex items-center justify-between mobile-padding">
            <div class="flex-1 text-center">
                <span id="bannerAdText" class="font-bold mobile-text">🎯 Maxsus Taklif! Eng Yaxshi Xizmatlar</span>
            </div>
            <button onclick="hideBannerAd()" class="text-white hover:text-gray-200 ml-4">
                <i class="fas fa-times"></i>
            </button>
        </div>
    </div>

    <!-- Local Storage Indicator (Admin uchun) -->
    <div id="storageIndicator" class="storage-indicator">
        💾 Ma'lumotlar local saqlandi. Deploy qiling!
    </div>

    <!-- Language Bar -->
    <div class="bg-gradient-to-r from-blue-500 to-purple-500 text-white py-2">
        <div class="max-w-7xl mx-auto px-4 flex justify-between items-center mobile-padding">
            <div class="flex items-center space-x-3">
                <div class="live-indicator w-3 h-3 rounded-full bg-green-400"></div>
                <span class="text-sm font-medium mobile-text">💝 E-Ehson Professional</span>
                <span class="text-xs opacity-75">Xayriya Platformasi</span>
            </div>
            <div class="flex items-center space-x-4">
                <span class="text-sm mobile-text">Foydalanuvchi: <span id="currentUserName" class="font-bold">Mehmon</span></span>
                <button onclick="showAdminPanel()" id="adminBtn" class="text-sm bg-yellow-500 px-3 py-1 rounded hover:bg-yellow-600 transition-colors hidden">
                    👑 Admin Panel
                </button>
            </div>
        </div>
    </div>

    <!-- Navigation -->
    <nav class="bg-white shadow-xl sticky top-0 z-40">
        <div class="max-w-7xl mx-auto px-4 mobile-padding">
            <div class="flex justify-between items-center h-16">
                <div class="flex items-center space-x-3">
                    <div class="text-3xl">❤️</div>
                    <div>
                        <h1 class="text-xl font-bold text-gray-800">E-Ehson Professional</h1>
                        <p class="text-xs text-gray-500">Xayriya Platformasi</p>
                    </div>
                </div>
                
                <div class="hidden md:flex space-x-8">
                    <a href="#home" onclick="scrollToSection('home')" class="nav-link text-blue-600 font-semibold cursor-pointer">Bosh sahifa</a>
                    <a href="#campaigns" onclick="scrollToSection('campaigns')" class="nav-link text-gray-600 hover:text-blue-600 cursor-pointer">E'lonlar</a>
                    <a href="#about" onclick="scrollToSection('about')" class="nav-link text-gray-600 hover:text-blue-600 cursor-pointer">Biz haqimizda</a>
                    <a href="#team" onclick="scrollToSection('team')" class="nav-link text-gray-600 hover:text-blue-600 cursor-pointer">Loyiha Jamoasi</a>
                    <a href="#contact" onclick="scrollToSection('contact')" class="nav-link text-gray-600 hover:text-blue-600 cursor-pointer">Aloqa</a>
                    <a onclick="showPrivacyModal()" class="nav-link text-gray-600 hover:text-blue-600 cursor-pointer">Maxfiylik</a>
                </div>
                
                <div class="flex items-center space-x-3">
                    <button onclick="requestCampaign()" class="telegram-btn text-white px-4 py-2 rounded-lg transition-all duration-300 transform hover:scale-105 mobile-button touch-button">
                        📢 E'lon So'rash
                    </button>
                    <button onclick="getHelp()" class="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg transition-all duration-300 transform hover:scale-105 mobile-button touch-button">
                        🆘 Yordam
                    </button>
                    <button onclick="checkAdminAccess()" class="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition-all duration-300 transform hover:scale-105 mobile-button touch-button">
                        👑 Admin
                    </button>
                    <button onclick="showAddAdModal()" id="addAdBtn" class="bg-orange-500 hover:bg-orange-600 text-white px-4 py-2 rounded-lg transition-all duration-300 transform hover:scale-105 mobile-button touch-button hidden">
                        📺 Reklama Qo'yish
                    </button>
                </div>
            </div>
        </div>
    </nav>

    <!-- Admin Panel Modal -->
    <div id="adminModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 hidden">
        <div class="admin-panel w-full max-w-6xl max-h-96 overflow-y-auto rounded-2xl p-6 text-white">
            <div class="flex justify-between items-center mb-6">
                <h2 class="text-3xl font-bold">👑 Admin Panel</h2>
                <button onclick="closeAdminPanel()" class="text-white hover:text-gray-300 text-2xl">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            
            <!-- Admin Controls -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <button onclick="showAddCampaignModal()" class="user-card rounded-xl p-4 text-center hover:bg-white hover:bg-opacity-20 transition-all">
                    <div class="text-2xl mb-2">📢</div>
                    <div class="font-bold">E'lon Qo'shish</div>
                </button>
                <button onclick="showManageCampaigns()" class="user-card rounded-xl p-4 text-center hover:bg-white hover:bg-opacity-20 transition-all">
                    <div class="text-2xl mb-2">✏️</div>
                    <div class="font-bold">E'lonlarni Boshqarish</div>
                </button>
                <button onclick="showAddAdModal()" class="user-card rounded-xl p-4 text-center hover:bg-white hover:bg-opacity-20 transition-all">
                    <div class="text-2xl mb-2">📺</div>
                    <div class="font-bold">Reklama Qo'shish</div>
                </button>
                <button onclick="showManageAds()" class="user-card rounded-xl p-4 text-center hover:bg-white hover:bg-opacity-20 transition-all">
                    <div class="text-2xl mb-2">🔧</div>
                    <div class="font-bold">Reklamalarni Boshqarish</div>
                </button>
                <button onclick="showManageTeam()" class="user-card rounded-xl p-4 text-center hover:bg-white hover:bg-opacity-20 transition-all">
                    <div class="text-2xl mb-2">👥</div>
                    <div class="font-bold">Jamoani Boshqarish</div>
                </button>
                <button onclick="showAdSettings()" class="user-card rounded-xl p-4 text-center hover:bg-white hover:bg-opacity-20 transition-all">
                    <div class="text-2xl mb-2">⚙️</div>
                    <div class="font-bold">Sozlamalar</div>
                </button>
                <button onclick="exportData()" class="user-card rounded-xl p-4 text-center hover:bg-white hover:bg-opacity-20 transition-all">
                    <div class="text-2xl mb-2">📤</div>
                    <div class="font-bold">Ma'lumotlarni Export</div>
                </button>
                <button onclick="clearLocalData()" class="user-card rounded-xl p-4 text-center hover:bg-white hover:bg-opacity-20 transition-all bg-red-500">
                    <div class="text-2xl mb-2">🗑️</div>
                    <div class="font-bold">Tozalash</div>
                </button>
            </div>
            
            <!-- Stats -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div class="user-card rounded-xl p-4 text-center">
                    <div class="text-2xl font-bold" id="adminTotalCampaigns">0</div>
                    <div class="text-sm opacity-75">Jami E'lonlar</div>
                </div>
                <div class="user-card rounded-xl p-4 text-center">
                    <div class="text-2xl font-bold" id="adminTotalAds">0</div>
                    <div class="text-sm opacity-75">Jami Reklamalar</div>
                </div>
                <div class="user-card rounded-xl p-4 text-center">
                    <div class="text-2xl font-bold" id="adminTotalDonations">0M</div>
                    <div class="text-sm opacity-75">Jami Xayriya</div>
                </div>
                <div class="user-card rounded-xl p-4 text-center">
                    <div class="text-2xl font-bold" id="adminTotalTeam">0</div>
                    <div class="text-sm opacity-75">Jamoa A'zolari</div>
                </div>
            </div>
        </div>
    </div>

    <!-- Manage Campaigns Modal -->
    <div id="manageCampaignsModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 hidden">
        <div class="bg-white rounded-2xl p-6 max-w-4xl w-full max-h-[80vh] overflow-y-auto">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-2xl font-bold">📋 E'lonlarni Boshqarish</h3>
                <button onclick="closeManageCampaigns()" class="text-gray-500 hover:text-gray-700 text-2xl">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div id="campaignsList" class="space-y-4">
                <!-- Campaigns list will be loaded here -->
            </div>
        </div>
    </div>

    <!-- Manage Ads Modal -->
    <div id="manageAdsModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 hidden">
        <div class="bg-white rounded-2xl p-6 max-w-4xl w-full max-h-[80vh] overflow-y-auto">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-2xl font-bold">📺 Reklamalarni Boshqarish</h3>
                <button onclick="closeManageAds()" class="text-gray-500 hover:text-gray-700 text-2xl">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div id="adsList" class="space-y-4">
                <!-- Ads list will be loaded here -->
            </div>
        </div>
    </div>

    <!-- Manage Team Modal -->
    <div id="manageTeamModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 hidden">
        <div class="bg-white rounded-2xl p-6 max-w-4xl w-full max-h-[80vh] overflow-y-auto">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-2xl font-bold">👥 Jamoani Boshqarish</h3>
                <button onclick="closeManageTeam()" class="text-gray-500 hover:text-gray-700 text-2xl">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div id="teamList" class="space-y-4">
                <!-- Team list will be loaded here -->
            </div>
        </div>
    </div>

    <!-- Hero Section -->
    <section id="home" class="gradient-bg text-white py-24 relative overflow-hidden">
        <div class="absolute inset-0 bg-black opacity-20"></div>
        <div class="max-w-7xl mx-auto px-4 text-center relative z-10 mobile-padding">
            <div class="fade-in-up">
                <h1 class="text-4xl md:text-6xl font-bold mb-6 text-shadow">Yaxshilik Qiling</h1>
                <p class="text-lg md:text-xl mb-8 max-w-3xl mx-auto text-shadow mobile-text">Professional xayriya platformasi orqali yaxshi ishlarni qo'llab-quvvatlang va jamiyatga hissa qo'shing</p>
                
                <!-- Platform Features -->
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
                    <div class="glass-effect rounded-xl p-6 transform hover:scale-105 transition-all duration-300 mobile-card">
                        <div class="text-3xl mb-3">💝</div>
                        <div class="text-lg font-bold mb-2">Xavfsiz Xayriya</div>
                        <div class="text-sm opacity-90 mobile-text">Ishonchli va shaffof tizim</div>
                    </div>
                    <div class="glass-effect rounded-xl p-6 transform hover:scale-105 transition-all duration-300 mobile-card">
                        <div class="text-3xl mb-3">🌍</div>
                        <div class="text-lg font-bold mb-2">Global Ta'sir</div>
                        <div class="text-sm opacity-90 mobile-text">Dunyo bo'ylab yordam</div>
                    </div>
                    <div class="glass-effect rounded-xl p-6 transform hover:scale-105 transition-all duration-300 mobile-card">
                        <div class="text-3xl mb-3">📱</div>
                        <div class="text-lg font-bold mb-2">Oson Foydalanish</div>
                        <div class="text-sm opacity-90 mobile-text">Mobil va desktop uchun</div>
                    </div>
                </div>
                
                <!-- Enhanced Stats -->
                <div class="grid grid-cols-2 md:grid-cols-4 gap-6 mb-16">
                    <div class="glass-effect rounded-xl p-6 transform hover:scale-105 transition-all duration-300 mobile-card">
                        <div class="text-3xl md:text-4xl font-bold mb-2" id="totalDonations">2.5M</div>
                        <div class="text-sm opacity-90 mobile-text">Jami Xayriya</div>
                        <div class="text-xs opacity-75 mt-1">💰 so'm</div>
                    </div>
                    <div class="glass-effect rounded-xl p-6 transform hover:scale-105 transition-all duration-300 mobile-card">
                        <div class="text-3xl md:text-4xl font-bold mb-2" id="totalUsers">1,234</div>
                        <div class="text-sm opacity-90 mobile-text">Xayriyachilar</div>
                        <div class="text-xs opacity-75 mt-1">👥 kishi</div>
                    </div>
                    <div class="glass-effect rounded-xl p-6 transform hover:scale-105 transition-all duration-300 mobile-card">
                        <div class="text-3xl md:text-4xl font-bold mb-2" id="activeCampaigns">15</div>
                        <div class="text-sm opacity-90 mobile-text">Faol E'lonlar</div>
                        <div class="text-xs opacity-75 mt-1">📢 ta</div>
                    </div>
                    <div class="glass-effect rounded-xl p-6 transform hover:scale-105 transition-all duration-300 mobile-card">
                        <div class="text-3xl md:text-4xl font-bold mb-2" id="completedCampaigns">89</div>
                        <div class="text-sm opacity-90 mobile-text">Tugallangan</div>
                        <div class="text-xs opacity-75 mt-1">✅ ta</div>
                    </div>
                </div>
                
                <div class="flex flex-col sm:flex-row gap-6 justify-center">
                    <button onclick="scrollToCampaigns()" class="bg-white text-blue-600 px-8 py-4 rounded-xl font-bold hover:bg-gray-100 transition-all duration-300 transform hover:scale-105 shadow-lg mobile-button touch-button">
                        💝 Xayriya Qilish
                    </button>
                    <button onclick="scrollToAbout()" class="border-2 border-white text-white px-8 py-4 rounded-xl font-bold hover:bg-white hover:text-blue-600 transition-all duration-300 transform hover:scale-105 mobile-button touch-button">
                        📖 Batafsil
                    </button>
                </div>
            </div>
        </div>
    </section>

    <!-- Categories Section -->
    <section class="py-16 gradient-bg-2">
        <div class="max-w-7xl mx-auto px-4 mobile-padding">
            <div class="text-center mb-12">
                <h2 class="text-3xl md:text-4xl font-bold text-white mb-4 text-shadow">Xayriya Yo'nalishlari</h2>
                <p class="text-white text-lg opacity-90 mobile-text">Har bir yo'nalishda yordam berishingiz mumkin</p>
            </div>
            
            <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4">
                <div onclick="filterCampaigns('tibbiyot')" class="category-card rounded-xl p-4 text-center cursor-pointer transform hover:scale-105 transition-all duration-300 touch-button">
                    <div class="text-3xl mb-2">🏥</div>
                    <div class="text-white text-sm font-medium mobile-text">Tibbiy Yordam</div>
                </div>
                <div onclick="filterCampaigns('nogironlik')" class="category-card rounded-xl p-4 text-center cursor-pointer transform hover:scale-105 transition-all duration-300 touch-button">
                    <div class="text-3xl mb-2">♿</div>
                    <div class="text-white text-sm font-medium mobile-text">Nogironlik</div>
                </div>
                <div onclick="filterCampaigns('talim')" class="category-card rounded-xl p-4 text-center cursor-pointer transform hover:scale-105 transition-all duration-300 touch-button">
                    <div class="text-3xl mb-2">📚</div>
                    <div class="text-white text-sm font-medium mobile-text">Ta'lim</div>
                </div>
                <div onclick="filterCampaigns('uy-joy')" class="category-card rounded-xl p-4 text-center cursor-pointer transform hover:scale-105 transition-all duration-300 touch-button">
                    <div class="text-3xl mb-2">🏠</div>
                    <div class="text-white text-sm font-medium mobile-text">Uy-Joy</div>
                </div>
                <div onclick="filterCampaigns('hayvonlar')" class="category-card rounded-xl p-4 text-center cursor-pointer transform hover:scale-105 transition-all duration-300 touch-button">
                    <div class="text-3xl mb-2">🐾</div>
                    <div class="text-white text-sm font-medium mobile-text">Hayvonlar</div>
                </div>
                <div onclick="filterCampaigns('ijtimoiy')" class="category-card rounded-xl p-4 text-center cursor-pointer transform hover:scale-105 transition-all duration-300 touch-button">
                    <div class="text-3xl mb-2">🤝</div>
                    <div class="text-white text-sm font-medium mobile-text">Ijtimoiy</div>
                </div>
                <div onclick="filterCampaigns('ayollar')" class="category-card rounded-xl p-4 text-center cursor-pointer transform hover:scale-105 transition-all duration-300 touch-button">
                    <div class="text-3xl mb-2">👩</div>
                    <div class="text-white text-sm font-medium mobile-text">Ayollar Uchun</div>
                </div>
                <div onclick="filterCampaigns('yetimlar')" class="category-card rounded-xl p-4 text-center cursor-pointer transform hover:scale-105 transition-all duration-300 touch-button">
                    <div class="text-3xl mb-2">👶</div>
                    <div class="text-white text-sm font-medium mobile-text">Yetimlar</div>
                </div>
            </div>
        </div>
    </section>

    <!-- Campaigns Section -->
    <section id="campaigns" class="py-20 bg-gray-50">
        <div class="max-w-7xl mx-auto px-4 mobile-padding">
            <div class="text-center mb-16">
                <h2 class="text-4xl md:text-5xl font-bold text-gray-800 mb-6">Faol E'lonlar</h2>
                <p class="text-gray-600 max-w-3xl mx-auto text-lg mobile-text">Har bir xayriya kimgadir umid va yordam beradi. Siz ham bu yaxshi ishning bir qismi bo'ling.</p>
            </div>
            
            <!-- Filter Buttons -->
            <div class="flex flex-wrap justify-center gap-3 mb-12">
                <button onclick="filterCampaigns('all')" class="filter-btn bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-3 rounded-full font-medium shadow-lg transform hover:scale-105 transition-all duration-300 mobile-button touch-button">
                    Barchasi
                </button>
                <button onclick="filterCampaigns('tibbiyot')" class="filter-btn bg-white text-gray-700 px-4 py-3 rounded-full font-medium hover:bg-gray-100 shadow-md transition-all duration-300 mobile-button touch-button">
                    🏥 <span class="mobile-text">Tibbiy</span>
                </button>
                <button onclick="filterCampaigns('nogironlik')" class="filter-btn bg-white text-gray-700 px-4 py-3 rounded-full font-medium hover:bg-gray-100 shadow-md transition-all duration-300 mobile-button touch-button">
                    ♿ <span class="mobile-text">Nogironlik</span>
                </button>
                <button onclick="filterCampaigns('talim')" class="filter-btn bg-white text-gray-700 px-4 py-3 rounded-full font-medium hover:bg-gray-100 shadow-md transition-all duration-300 mobile-button touch-button">
                    📚 <span class="mobile-text">Ta'lim</span>
                </button>
                <button onclick="filterCampaigns('uy-joy')" class="filter-btn bg-white text-gray-700 px-4 py-3 rounded-full font-medium hover:bg-gray-100 shadow-md transition-all duration-300 mobile-button touch-button">
                    🏠 <span class="mobile-text">Uy-Joy</span>
                </button>
                <button onclick="filterCampaigns('hayvonlar')" class="filter-btn bg-white text-gray-700 px-4 py-3 rounded-full font-medium hover:bg-gray-100 shadow-md transition-all duration-300 mobile-button touch-button">
                    🐾 <span class="mobile-text">Hayvonlar</span>
                </button>
                <button onclick="filterCampaigns('ijtimoiy')" class="filter-btn bg-white text-gray-700 px-4 py-3 rounded-full font-medium hover:bg-gray-100 shadow-md transition-all duration-300 mobile-button touch-button">
                    🤝 <span class="mobile-text">Ijtimoiy</span>
                </button>
                <button onclick="filterCampaigns('ayollar')" class="filter-btn bg-white text-gray-700 px-4 py-3 rounded-full font-medium hover:bg-gray-100 shadow-md transition-all duration-300 mobile-button touch-button">
                    👩 <span class="mobile-text">Ayollar</span>
                </button>
                <button onclick="filterCampaigns('yetimlar')" class="filter-btn bg-white text-gray-700 px-4 py-3 rounded-full font-medium hover:bg-gray-100 shadow-md transition-all duration-300 mobile-button touch-button">
                    👶 <span class="mobile-text">Yetimlar</span>
                </button>
            </div>
            
            <!-- Campaigns Grid -->
            <div id="campaignsGrid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                <!-- Campaigns will be loaded here -->
            </div>
        </div>
    </section>

    <!-- About Section -->
    <section id="about" class="py-20 bg-white">
        <div class="max-w-7xl mx-auto px-4 mobile-padding">
            <div class="text-center mb-16">
                <h2 class="text-4xl md:text-5xl font-bold text-gray-800 mb-6">Biz Haqimizda</h2>
                <p class="text-gray-600 max-w-4xl mx-auto text-lg mobile-text">E-Ehson Professional - bu zamonaviy xayriya platformasi bo'lib, odamlar o'rtasida yaxshilik va yordam ko'rsatish uchun yaratilgan.</p>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-3 gap-12 mb-16">
                <div class="text-center group mobile-card">
                    <div class="text-6xl mb-6 transform group-hover:scale-110 transition-transform duration-300">🎯</div>
                    <h3 class="text-2xl font-bold mb-4">Maqsadimiz</h3>
                    <p class="text-gray-600 text-lg mobile-text">Har bir inson o'z hissasini qo'shib, jamiyatni yaxshilashga yordam berish</p>
                </div>
                <div class="text-center group mobile-card">
                    <div class="text-6xl mb-6 transform group-hover:scale-110 transition-transform duration-300">💝</div>
                    <h3 class="text-2xl font-bold mb-4">Qadriyatlarimiz</h3>
                    <p class="text-gray-600 text-lg mobile-text">Shaffoflik, ishonch va har bir xayriyaning o'z o'rniga yetishi</p>
                </div>
                <div class="text-center group mobile-card">
                    <div class="text-6xl mb-6 transform group-hover:scale-110 transition-transform duration-300">🌍</div>
                    <h3 class="text-2xl font-bold mb-4">Ta'sir</h3>
                    <p class="text-gray-600 text-lg mobile-text">Minglab odamlarning hayotini yaxshilashga hissa qo'shamiz</p>
                </div>
            </div>

            <!-- CEO Section -->
            <div class="bg-gradient-to-r from-blue-50 to-purple-50 rounded-2xl p-8 text-center mobile-card">
                <div class="text-6xl mb-4">👨‍💼</div>
                <h3 class="text-2xl font-bold text-gray-800 mb-2">Jasurbek Jo'lanboyev G'ayrat o'g'li</h3>
                <p class="text-blue-600 font-semibold mb-4">CEO & Founder</p>
                <p class="text-gray-600 max-w-2xl mx-auto mobile-text">"Bizning maqsadimiz - har bir inson o'z imkoniyatlari doirasida yaxshilik qilishi va jamiyatga hissa qo'shishi uchun professional platforma yaratish."</p>
                <div class="mt-4 text-sm text-gray-500 mobile-text">📱 Telegram: @Vscoderr</div>
            </div>
        </div>
    </section>

    <!-- Team Section -->
    <section id="team" class="py-20 bg-gray-50">
        <div class="max-w-7xl mx-auto px-4 mobile-padding">
            <div class="text-center mb-16">
                <h2 class="text-4xl md:text-5xl font-bold text-gray-800 mb-6">Loyiha Jamoasi</h2>
                <p class="text-gray-600 max-w-4xl mx-auto text-lg mobile-text">Bizning jamoamiz 8 ta tajribali mutaxassislaridan iborat bo'lib, loyihani rivojlantirishda faol ishtirok etmoqda.</p>
                <button onclick="joinTeam()" class="join-team-btn mt-8">
                    👥 Jamoaga Qo'shilish - Ariza Yuborish
                </button>
            </div>
            
            <div id="teamGrid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                <!-- Team members will be loaded here from localStorage -->
            </div>
        </div>
    </section>

    <!-- Contact Section -->
    <section id="contact" class="py-20 bg-white">
        <div class="max-w-6xl mx-auto px-4 mobile-padding">
            <div class="text-center mb-16">
                <h2 class="text-4xl md:text-5xl font-bold text-gray-800 mb-6">Biz Bilan Bog'laning</h2>
                <p class="text-gray-600 text-lg mb-8 mobile-text">Savollaringiz bormi? Biz bilan bog'laning!</p>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-16">
                <div class="text-center group mobile-card">
                    <div class="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4 transform group-hover:scale-110 transition-all duration-300">
                        <i class="fas fa-envelope text-white text-xl"></i>
                    </div>
                    <h3 class="font-bold mb-2 mobile-text">Email</h3>
                    <p class="text-gray-600 mobile-text">info@eehson.uz</p>
                </div>
                <div class="text-center group mobile-card">
                    <div class="w-16 h-16 bg-gradient-to-r from-green-500 to-blue-500 rounded-full flex items-center justify-center mx-auto mb-4 transform group-hover:scale-110 transition-all duration-300">
                        <i class="fab fa-telegram text-white text-xl"></i>
                    </div>
                    <h3 class="font-bold mb-2 mobile-text">Telegram</h3>
                    <a href="https://t.me/serinaqu" target="_blank" class="text-blue-600 hover:text-blue-800 mobile-text">@serinaqu</a>
                </div>
                <div class="text-center group mobile-card">
                    <div class="w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center mx-auto mb-4 transform group-hover:scale-110 transition-all duration-300">
                        <i class="fas fa-phone text-white text-xl"></i>
                    </div>
                    <h3 class="font-bold mb-2 mobile-text">Telefon</h3>
                    <p class="text-gray-600 mobile-text">+998-95-888-38-51</p>
                </div>
                <div class="text-center group mobile-card">
                    <div class="w-16 h-16 bg-gradient-to-r from-red-500 to-orange-500 rounded-full flex items-center justify-center mx-auto mb-4 transform group-hover:scale-110 transition-all duration-300">
                        <i class="fas fa-map-marker-alt text-white text-xl"></i>
                    </div>
                    <h3 class="font-bold mb-2 mobile-text">Manzil</h3>
                    <p class="text-gray-600 mobile-text">Toshkent, O'zbekiston</p>
                </div>
            </div>

            <!-- Social Media -->
            <div class="text-center">
                <h3 class="text-2xl font-bold text-gray-800 mb-8 mobile-text">Ijtimoiy Tarmoqlar</h3>
                <div class="flex justify-center space-x-6 flex-wrap gap-4">
                    <a href="https://www.linkedin.com/in/jasurbek-jo-lanboyev-74b758351?utm_source=share&utm_campaign=share_via&utm_content=profile&utm_medium=android_app" target="_blank" rel="noopener noreferrer" class="social-icon w-14 h-14 bg-blue-600 rounded-full flex items-center justify-center text-white text-xl hover:bg-blue-700 touch-button">
                        <i class="fab fa-linkedin-in"></i>
                    </a>
                    <a href="https://www.instagram.com/jasurbek.official.uz" target="_blank" rel="noopener noreferrer" class="social-icon w-14 h-14 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center text-white text-xl touch-button">
                        <i class="fab fa-instagram"></i>
                    </a>
                    <a href="https://www.youtube.com/@Jasurbek_Jolanboyev" target="_blank" rel="noopener noreferrer" class="social-icon w-14 h-14 bg-red-600 rounded-full flex items-center justify-center text-white text-xl hover:bg-red-700 touch-button">
                        <i class="fab fa-youtube"></i>
                    </a>
                    <a href="https://t.me/serinaqu" target="_blank" rel="noopener noreferrer" class="social-icon w-14 h-14 bg-blue-500 rounded-full flex items-center justify-center text-white text-xl hover:bg-blue-600 touch-button">
                        <i class="fab fa-telegram"></i>
                    </a>
                    <a href="https://x.com/Jolanboyev" target="_blank" rel="noopener noreferrer" class="social-icon w-14 h-14 bg-black rounded-full flex items-center justify-center text-white text-xl hover:bg-gray-800 touch-button">
                        <i class="fab fa-x-twitter"></i>
                    </a>
                    <a href="https://tiktok.com/@jasurbek_jolanboyev" target="_blank" rel="noopener noreferrer" class="social-icon w-14 h-14 bg-black rounded-full flex items-center justify-center text-white text-xl hover:bg-gray-800 touch-button">
                        <i class="fab fa-tiktok"></i>
                    </a>
                    <a href="https://www.facebook.com/jasurbek.official.uz" target="_blank" rel="noopener noreferrer" class="social-icon w-14 h-14 bg-blue-800 rounded-full flex items-center justify-center text-white text-xl hover:bg-blue-900 touch-button">
                        <i class="fab fa-facebook-f"></i>
                    </a>
                </div>
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer class="bg-gray-900 text-white py-16 webview-safe">
        <div class="max-w-7xl mx-auto px-4 mobile-padding">
            <div class="grid grid-cols-1 md:grid-cols-4 gap-12 mb-12">
                <div class="mobile-card">
                    <div class="flex items-center space-x-3 mb-6">
                        <div class="text-3xl">❤️</div>
                        <div>
                            <h3 class="text-xl font-bold">E-Ehson Professional</h3>
                            <p class="text-sm text-gray-400">Xayriya Platformasi</p>
                        </div>
                    </div>
                    <p class="text-gray-400 mb-4 mobile-text">Professional xayriya platformasi - yaxshilik uchun birlashamiz</p>
                    <p class="text-sm text-gray-500 mobile-text">CEO: Jasurbek Jo'lanboyev G'ayrat o'g'li</p>
                    <div class="mt-4 text-xs text-gray-600 mobile-text">📱 Telegram: @serinaqu</div>
                </div>
                
                <div class="mobile-card">
                    <h4 class="font-bold mb-6 text-lg mobile-text">Tezkor Havolalar</h4>
                    <ul class="space-y-3 text-gray-400">
                        <li><a href="#home" onclick="scrollToSection('home')" class="hover:text-white transition-colors mobile-text cursor-pointer">Bosh sahifa</a></li>
                        <li><a href="#campaigns" onclick="scrollToSection('campaigns')" class="hover:text-white transition-colors mobile-text cursor-pointer">E'lonlar</a></li>
                        <li><a href="#about" onclick="scrollToSection('about')" class="hover:text-white transition-colors mobile-text cursor-pointer">Biz haqimizda</a></li>
                        <li><a href="#team" onclick="scrollToSection('team')" class="hover:text-white transition-colors mobile-text cursor-pointer">Loyiha Jamoasi</a></li>
                        <li><a href="#contact" onclick="scrollToSection('contact')" class="hover:text-white transition-colors mobile-text cursor-pointer">Aloqa</a></li>
                    </ul>
                </div>
                
                <div class="mobile-card">
                    <h4 class="font-bold mb-6 text-lg mobile-text">Kategoriyalar</h4>
                    <ul class="space-y-3 text-gray-400 text-sm mobile-text">
                        <li><span onclick="filterCampaigns('tibbiyot')" class="cursor-pointer hover:text-white transition-colors">Tibbiy Yordam</span></li>
                        <li><span onclick="filterCampaigns('talim')" class="cursor-pointer hover:text-white transition-colors">Ta'lim</span></li>
                        <li><span onclick="filterCampaigns('uy-joy')" class="cursor-pointer hover:text-white transition-colors">Uy-Joy</span></li>
                        <li><span onclick="filterCampaigns('ijtimoiy')" class="cursor-pointer hover:text-white transition-colors">Ijtimoiy Yordam</span></li>
                        <li><span onclick="filterCampaigns('hayvonlar')" class="cursor-pointer hover:text-white transition-colors">Hayvonlar</span></li>
                    </ul>
                </div>
                
                <div class="mobile-card">
                    <h4 class="font-bold mb-6 text-lg mobile-text">Aloqa</h4>
                    <ul class="space-y-3 text-gray-400 text-sm mobile-text">
                        <li>📧 info@eehson.uz</li>
                        <li>📱 +998-95-888-38-51</li>
                        <li>📍 Toshkent, O'zbekiston</li>
                        <li>💬 @serinaqu</li>
                    </ul>
                </div>
            </div>
            
            <div class="border-t border-gray-700 pt-8 text-center">
                <p class="text-gray-400 mb-4 mobile-text">&copy; 2025 E-Ehson Professional. Barcha huquqlar himoyalangan.</p>
                <p class="text-sm text-gray-500 mobile-text">Jasurbek Jo'lanboyev G'ayrat o'g'li tomonidan yaratilgan. Professional Platform.</p>
                <div class="mt-2 text-xs text-gray-600 mobile-text">💝 Xayriya Platformasi • 📱 Flutter WebView Ready • 🌍 Global Impact • 🔒 Local Storage Saqlash</div>
            </div>
        </div>
    </footer>

    <script>
        // ========================================
        // GLOBAL VARIABLES
        // ========================================
        
        let campaigns = [];
        let ads = [];
        let teamMembers = [];
        let currentFilter = 'all';
        let isAdmin = false;

        // Admin parol
        const ADMIN_PASSWORD = 'serinaqu123';

        // Ad settings
        let adSettings = {};

        // ========================================
        // NOTIFICATION SYSTEM
        // ========================================
        
        function showNotification(message, type = 'info') {
            const notification = document.createElement('div');
            notification.className = `notification ${type}`;
            notification.textContent = message;
            
            document.body.appendChild(notification);
            
            setTimeout(() => {
                notification.classList.add('show');
            }, 100);
            
            setTimeout(() => {
                notification.classList.remove('show');
                setTimeout(() => {
                    document.body.removeChild(notification);
                }, 300);
            }, 4000);
        }

        // ========================================
        // NAVIGATION FUNCTIONS
        // ========================================
        
        function scrollToSection(sectionId) {
            const element = document.getElementById(sectionId);
            if (element) {
                element.scrollIntoView({ 
                    behavior: 'smooth',
                    block: 'start'
                });
                showNotification(`📍 ${getSectionName(sectionId)} bo'limiga o'tildi`, 'info');
            }
        }
        
        function scrollToCampaigns() {
            scrollToSection('campaigns');
        }
        
        function scrollToAbout() {
            scrollToSection('about');
        }
        
        function getSectionName(sectionId) {
            const names = {
                'home': 'Bosh sahifa',
                'campaigns': 'E\'lonlar',
                'about': 'Biz haqimizda',
                'team': 'Loyiha Jamoasi',
                'contact': 'Aloqa'
            };
            return names[sectionId] || sectionId;
        }

        // ========================================
        // PRIVACY MODAL
        // ========================================
        
        function showPrivacyModal() {
            document.getElementById('privacyModal').classList.remove('hidden');
            showNotification('📋 Maxfiylik siyosati ochildi', 'info');
        }
        
        function closePrivacyModal() {
            document.getElementById('privacyModal').classList.add('hidden');
        }

        // ========================================
        // TEAM MODAL
        // ========================================
        
        function showTeamModal(memberId) {
            const member = teamMembers.find(m => m.id === memberId);
            if (!member) return;

            document.getElementById('modalTeamImage').src = member.image;
            document.getElementById('modalTeamName').textContent = member.name;
            document.getElementById('modalTeamRole').textContent = member.role;
            document.getElementById('modalTeamDescription').textContent = member.description;

            const socialsContainer = document.getElementById('modalTeamSocials');
            socialsContainer.innerHTML = '';
            for (const [platform, link] of Object.entries(member.socials)) {
                if (link) {
                    const a = document.createElement('a');
                    a.href = link;
                    a.target = '_blank';
                    a.classList.add('team-social-icon');
                    const i = document.createElement('i');
                    i.classList.add('fab');
                    i.classList.add(`fa-${platform === 'twitter' ? 'x-twitter' : platform}`);
                    a.appendChild(i);
                    socialsContainer.appendChild(a);
                }
            }

            document.getElementById('teamModal').classList.remove('hidden');
            showNotification(`👤 ${member.name} haqida batafsil ma'lumot`, 'info');
        }

        function closeTeamModal() {
            document.getElementById('teamModal').classList.add('hidden');
        }

        // ========================================
        // JOIN TEAM
        // ========================================
        
        function joinTeam() {
            const message = `👥 *JAMOAGA QO'SHILISH ARIZASI - E-EHSON PROFESSIONAL*

📝 *Sizning Ma'lumotlaringiz:*
• Ism va Familiya: [Ismingizni kiriting]
• Lavozim: [Qaysi lavozimga murojaat qilmoqdasiz? Masalan: Developer, Designer]
• Tajribangiz: [Qisqa tajribangizni yozing]
• Portfolio/Havolalar: [GitHub, LinkedIn va boshqa havolalar]

📞 *Aloqa:*
• Telefon: [+998xxxxxxxxx]
• Email: [email@example.com]
• Telegram: [@username]

💼 *Nima uchun bizning jamoamizga qo'shilmoqchisiz?*
[Bu yerga motivatsiyangizni yozing]

🔗 *Platform:* E-Ehson Professional
👨‍💼 *CEO:* Jasurbek Jo'lanboyev G'ayrat o'g'li
📱 *Admin:* @serinaqu

✅ *Ariza yuborildi! Tez orada javob beramiz.*`;

            const telegramUrl = `https://t.me/serinaqu?text=${encodeURIComponent(message)}`;
            window.open(telegramUrl, '_blank');
            
            showNotification('📝 Jamoaga qo\'shilish arizasi admin ga yuborildi!', 'success');
        }

        // ========================================
        // ADMIN LOGIN SYSTEM
        // ========================================
        
        function checkAdminAccess() {
            isAdmin = false;
            if (window.Telegram) {
                const tg = window.Telegram.WebApp;
                if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
                    if (tg.initDataUnsafe.user.id.toString() === ADMIN_ID) {
                        isAdmin = true;
                    }
                }
            }
            if (isAdmin) {
                document.getElementById('adminBtn').classList.remove('hidden');
                document.getElementById('addAdBtn').classList.remove('hidden');
                document.getElementById('currentUserName').textContent = 'Admin';
                showNotification('✅ Admin sifatida kirdingiz!', 'success');
            }
            return isAdmin;
        }

        function showAdminPanel() {
            if (!isAdmin) {
                showNotification('❌ Admin huquqi yo\'q!', 'error');
                return;
            }
            
            updateAdminStats();
            document.getElementById('adminModal').classList.remove('hidden');
        }

        function closeAdminPanel() {
            document.getElementById('adminModal').classList.add('hidden');
        }

        function updateAdminStats() {
            const totalCampaigns = campaigns.length;
            const totalAds = ads.length;
            const totalDonations = campaigns.reduce((sum, c) => sum + c.currentAmount, 0);
            const totalTeam = teamMembers.length;
            
            document.getElementById('adminTotalCampaigns').textContent = totalCampaigns;
            document.getElementById('adminTotalAds').textContent = totalAds;
            document.getElementById('adminTotalDonations').textContent = formatCurrency(totalDonations).replace(' so\'m', 'M');
            document.getElementById('adminTotalTeam').textContent = totalTeam;
        }

        // ========================================
        // MANAGE CAMPAIGNS & ADS & TEAM
        // ========================================
        
        function showManageCampaigns() {
            if (!isAdmin) {
                showNotification('❌ Faqat admin e\'lonlarni boshqara oladi!', 'error');
                return;
            }
            const list = document.getElementById('campaignsList');
            list.innerHTML = campaigns.map(campaign => createAdminCampaignItem(campaign)).join('');
            document.getElementById('manageCampaignsModal').classList.remove('hidden');
        }

        function closeManageCampaigns() {
            document.getElementById('manageCampaignsModal').classList.add('hidden');
        }

        function createAdminCampaignItem(campaign) {
            return `
                <div class="admin-list-item">
                    <div class="flex-1">
                        <h4 class="font-bold text-lg">${campaign.title}</h4>
                        <p class="text-sm text-gray-600">${getCategoryName(campaign.category)} | ${formatCurrency(campaign.currentAmount)} / ${formatCurrency(campaign.targetAmount)}</p>
                    </div>
                    <div class="flex space-x-2">
                        <button onclick="editCampaign('${campaign.id}')" class="admin-edit-btn admin-action-btn">
                            ✏️ Tahrirlash
                        </button>
                        <button onclick="deleteCampaign('${campaign.id}')" class="admin-delete-btn admin-action-btn">
                            🗑️ O'chirish
                        </button>
                    </div>
                </div>
            `;
        }

        function editCampaign(campaignId) {
            const campaign = campaigns.find(c => c.id === campaignId);
            if (!campaign) return;
            showAddCampaignModal(campaign);
        }

        async function deleteCampaign(campaignId) {
            if (confirm('Bu e\'loni o\'chirishni xohlaysizmi?')) {
                await deleteFromServer('campaigns', campaignId);
                await loadAdminData();
                showManageCampaigns();
                showNotification('🗑️ E\'lon o\'chirildi!', 'success');
            }
        }

        function showManageAds() {
            if (!isAdmin) {
                showNotification('❌ Faqat admin reklamalarni boshqara oladi!', 'error');
                return;
            }
            const list = document.getElementById('adsList');
            list.innerHTML = ads.map(ad => createAdminAdItem(ad)).join('');
            document.getElementById('manageAdsModal').classList.remove('hidden');
        }

        function closeManageAds() {
            document.getElementById('manageAdsModal').classList.add('hidden');
        }

        function createAdminAdItem(ad) {
            return `
                <div class="admin-list-item">
                    <div class="flex-1">
                        <h4 class="font-bold text-lg">${ad.title}</h4>
                        <p class="text-sm text-gray-600">${ad.type} | Davomiylik: ${ad.showDuration}s</p>
                    </div>
                    <div class="flex space-x-2">
                        <button onclick="editAd('${ad.id}')" class="admin-edit-btn admin-action-btn">
                            ✏️ Tahrirlash
                        </button>
                        <button onclick="deleteAd('${ad.id}')" class="admin-delete-btn admin-action-btn">
                            🗑️ O'chirish
                        </button>
                    </div>
                </div>
            `;
        }

        function editAd(adId) {
            const ad = ads.find(a => a.id === adId);
            if (!ad) return;
            showAddAdModal(ad);
        }

        async function deleteAd(adId) {
            if (confirm('Bu reklamani o\'chirishni xohlaysizmi?')) {
                await deleteFromServer('ads', adId);
                await loadAdminData();
                showManageAds();
                showNotification('🗑️ Reklama o\'chirildi!', 'success');
            }
        }

        function showManageTeam() {
            if (!isAdmin) {
                showNotification('❌ Faqat admin jamoani boshqara oladi!', 'error');
                return;
            }
            const list = document.getElementById('teamList');
            list.innerHTML = teamMembers.map(member => createAdminTeamItem(member)).join('');
            document.getElementById('manageTeamModal').classList.remove('hidden');
        }

        function closeManageTeam() {
            document.getElementById('manageTeamModal').classList.add('hidden');
        }

        function createAdminTeamItem(member) {
            return `
                <div class="admin-list-item">
                    <div class="flex-1">
                        <h4 class="font-bold text-lg">${member.name}</h4>
                        <p class="text-sm text-gray-600">${member.role}</p>
                    </div>
                    <div class="flex space-x-2">
                        <button onclick="editTeamMember('${member.id}')" class="admin-edit-btn admin-action-btn">
                            ✏️ Tahrirlash
                        </button>
                        <button onclick="deleteTeamMember('${member.id}')" class="admin-delete-btn admin-action-btn">
                            🗑️ O'chirish
                        </button>
                    </div>
                </div>
            `;
        }

        function editTeamMember(memberId) {
            const member = teamMembers.find(m => m.id === memberId);
            if (!member) return;
            showAddTeamModal(member);
        }

        async function deleteTeamMember(memberId) {
            if (confirm('Bu jamoa a\'zosini o\'chirishni xohlaysizmi?')) {
                await deleteFromServer('team', memberId);
                await loadAdminData();
                showManageTeam();
                showNotification('🗑️ Jamoa a\'zosi o\'chirildi!', 'success');
            }
        }

        function showAddTeamModal(existingMember = null) {
            if (!isAdmin) return;
            const isEdit = !!existingMember;
            const modal = document.createElement('div');
            modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
            modal.innerHTML = `
                <div class="bg-white rounded-2xl p-6 max-w-md w-full max-h-96 overflow-y-auto">
                    <h3 class="text-2xl font-bold mb-4">${isEdit ? '✏️ A\'zoni Tahrirlash' : '👥 Yangi A\'zo Qo\'shish'}</h3>
                    <form id="teamForm" onsubmit="saveTeamMember(event, '${existingMember ? existingMember.id : ''}')">
                        <div class="mb-4">
                            <label class="block text-sm font-medium mb-2">Ism</label>
                            <input type="text" name="name" value="${existingMember ? existingMember.name : ''}" required class="w-full px-3 py-2 border rounded-lg">
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium mb-2">Lavozim</label>
                            <input type="text" name="role" value="${existingMember ? existingMember.role : ''}" required class="w-full px-3 py-2 border rounded-lg">
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium mb-2">Tavsif</label>
                            <textarea name="description" class="w-full px-3 py-2 border rounded-lg h-20">${existingMember ? existingMember.description : ''}</textarea>
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium mb-2">Rasm URL</label>
                            <input type="url" name="image" value="${existingMember ? existingMember.image : ''}" class="w-full px-3 py-2 border rounded-lg">
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium mb-2">Telegram</label>
                            <input type="url" name="telegram" value="${existingMember ? existingMember.socials.telegram : ''}" class="w-full px-3 py-2 border rounded-lg">
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium mb-2">Instagram</label>
                            <input type="url" name="instagram" value="${existingMember ? existingMember.socials.instagram : ''}" class="w-full px-3 py-2 border rounded-lg">
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium mb-2">YouTube</label>
                            <input type="url" name="youtube" value="${existingMember ? existingMember.socials.youtube : ''}" class="w-full px-3 py-2 border rounded-lg">
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium mb-2">LinkedIn</label>
                            <input type="url" name="linkedin" value="${existingMember ? existingMember.socials.linkedin : ''}" class="w-full px-3 py-2 border rounded-lg">
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium mb-2">Twitter</label>
                            <input type="url" name="twitter" value="${existingMember ? existingMember.socials.twitter : ''}" class="w-full px-3 py-2 border rounded-lg">
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium mb-2">TikTok</label>
                            <input type="url" name="tiktok" value="${existingMember ? existingMember.socials.tiktok : ''}" class="w-full px-3 py-2 border rounded-lg">
                        </div>
                        <div class="flex gap-3">
                            <button type="submit" class="flex-1 bg-green-600 text-white py-2 rounded-lg hover:bg-green-700">
                                ${isEdit ? '💾 Saqlash' : '📤 Qo\'shish'}
                            </button>
                            <button type="button" onclick="closeModal()" class="flex-1 bg-gray-300 text-gray-700 py-2 rounded-lg hover:bg-gray-400">
                                ❌ Bekor qilish
                            </button>
                        </div>
                    </form>
                </div>
            `;
            document.body.appendChild(modal);
        }

        async function saveTeamMember(event, existingId) {
            event.preventDefault();
            const formData = new FormData(event.target);
            const isEdit = !!existingId;
            const socials = {
                telegram: formData.get('telegram'),
                instagram: formData.get('instagram'),
                youtube: formData.get('youtube'),
                linkedin: formData.get('linkedin'),
                twitter: formData.get('twitter'),
                tiktok: formData.get('tiktok')
            };
            const memberData = {
                id: existingId || Date.now(),
                name: formData.get('name'),
                role: formData.get('role'),
                description: formData.get('description'),
                image: formData.get('image'),
                socials
            };
            
            await saveToServer('team', memberData);
            await loadAdminData();
            closeModal();
            showNotification('✅ Jamoa a\'zosi saqlandi!', 'success');
        }

        function displayTeam() {
            const grid = document.getElementById('teamGrid');
            grid.innerHTML = teamMembers.map(member => createTeamCard(member)).join('');
        }

        function createTeamCard(member) {
            return `
                <div class="team-card" onclick="showTeamModal(${member.id})">
                    <img src="${member.image}" alt="${member.name}" class="team-image">
                    <div class="p-6 text-center">
                        <h3 class="text-xl font-bold mb-2">${member.name}</h3>
                        <p class="text-blue-600 font-semibold mb-4">${member.role}</p>
                        <p class="text-gray-600 mb-4">${member.description}</p>
                        <div class="team-socials">
                            ${Object.entries(member.socials).map(([platform, link]) => link ? `<a href="${link}" target="_blank" class="team-social-icon"><i class="fab fa-${platform === 'twitter' ? 'x-twitter' : platform}"></i></a>` : '').join('')}
                        </div>
                    </div>
                </div>
            `;
        }

        // ========================================
        // CAMPAIGN CREATION (with Local Save)
        // ========================================
        
        function showAddCampaignModal(existingCampaign = null) {
            if (!isAdmin) {
                showNotification('❌ Faqat admin e\'lon qo\'sha/ozgartira oladi!', 'error');
                return;
            }
            
            const isEdit = !!existingCampaign;
            const modal = document.createElement('div');
            modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
            modal.innerHTML = `
                <div class="bg-white rounded-2xl p-6 max-w-md w-full max-h-96 overflow-y-auto">
                    <h3 class="text-2xl font-bold mb-4">${isEdit ? '✏️ E\'loni Tahrirlash' : '📢 Yangi E\'lon Qo\'shish'}</h3>
                    <form id="campaignForm" onsubmit="saveCampaign(event, '${existingCampaign ? existingCampaign.id : ''}')">
                        <div class="mb-4">
                            <label class="block text-sm font-medium mb-2">E'lon nomi</label>
                            <input type="text" name="title" value="${existingCampaign ? existingCampaign.title : ''}" required class="w-full px-3 py-2 border rounded-lg">
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium mb-2">Kategoriya</label>
                            <select name="category" required class="w-full px-3 py-2 border rounded-lg">
                                <option value="">Tanlang</option>
                                <option value="tibbiyot" ${existingCampaign && existingCampaign.category === 'tibbiyot' ? 'selected' : ''}>🏥 Tibbiy Yordam</option>
                                <option value="nogironlik" ${existingCampaign && existingCampaign.category === 'nogironlik' ? 'selected' : ''}>♿ Nogironlik</option>
                                <option value="talim" ${existingCampaign && existingCampaign.category === 'talim' ? 'selected' : ''}>📚 Ta'lim</option>
                                <option value="uy-joy" ${existingCampaign && existingCampaign.category === 'uy-joy' ? 'selected' : ''}>🏠 Uy-Joy</option>
                                <option value="hayvonlar" ${existingCampaign && existingCampaign.category === 'hayvonlar' ? 'selected' : ''}>🐾 Hayvonlar</option>
                                <option value="ijtimoiy" ${existingCampaign && existingCampaign.category === 'ijtimoiy' ? 'selected' : ''}>🤝 Ijtimoiy</option>
                                <option value="ayollar" ${existingCampaign && existingCampaign.category === 'ayollar' ? 'selected' : ''}>👩 Ayollar Uchun</option>
                                <option value="yetimlar" ${existingCampaign && existingCampaign.category === 'yetimlar' ? 'selected' : ''}>👶 Yetimlar</option>
                            </select>
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium mb-2">Maqsad summasi (so'm)</label>
                            <input type="number" name="targetAmount" value="${existingCampaign ? existingCampaign.targetAmount : ''}" required class="w-full px-3 py-2 border rounded-lg">
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium mb-2">Hozirgi summa (so'm)</label>
                            <input type="number" name="currentAmount" value="${existingCampaign ? existingCampaign.currentAmount : 0}" class="w-full px-3 py-2 border rounded-lg">
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium mb-2">Tavsif</label>
                            <textarea name="description" required class="w-full px-3 py-2 border rounded-lg h-20">${existingCampaign ? existingCampaign.description : ''}</textarea>
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium mb-2">💳 Karta raqami</label>
                            <input type="text" name="cardNumber" value="${existingCampaign ? existingCampaign.cardNumber : ''}" required placeholder="8600 1234 5678 9012" class="w-full px-3 py-2 border rounded-lg">
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium mb-2">👤 Karta egasi (To'liq ism)</label>
                            <input type="text" name="cardOwner" value="${existingCampaign ? existingCampaign.cardOwner : ''}" required placeholder="ABDULLAYEV JASURBEK KARIM O'G'LI" class="w-full px-3 py-2 border rounded-lg">
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium mb-2">📞 Aloqa telefoni</label>
                            <input type="tel" name="contactPhone" value="${existingCampaign ? existingCampaign.contactPhone : ''}" required placeholder="+998901234567" class="w-full px-3 py-2 border rounded-lg">
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium mb-2">👤 Aloqa ismi</label>
                            <input type="text" name="contactName" value="${existingCampaign ? existingCampaign.contactName : ''}" required placeholder="Jasurbek Abdullayev" class="w-full px-3 py-2 border rounded-lg">
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium mb-2">⏰ Qolgan kunlar</label>
                            <input type="number" name="daysLeft" value="${existingCampaign ? existingCampaign.daysLeft : 30}" min="1" class="w-full px-3 py-2 border rounded-lg">
                        </div>
                        <div class="mb-4">
                            <label class="flex items-center">
                                <input type="checkbox" name="urgent" ${existingCampaign && existingCampaign.urgent ? 'checked' : ''} class="mr-2">
                                <span class="text-sm">Shoshilinch e'lon</span>
                            </label>
                        </div>
                        <div class="flex gap-3">
                            <button type="submit" class="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700">
                                ${isEdit ? '💾 Saqlash' : '📤 Qo\'shish'}
                            </button>
                            <button type="button" onclick="closeModal()" class="flex-1 bg-gray-300 text-gray-700 py-2 rounded-lg hover:bg-gray-400">
                                ❌ Bekor qilish
                            </button>
                        </div>
                    </form>
                </div>
            `;
            
            document.body.appendChild(modal);
        }

        async function saveCampaign(event, existingId) {
            event.preventDefault();
            
            const formData = new FormData(event.target);
            const isEdit = !!existingId;
            const campaignData = {
                id: existingId || 'campaign_' + Date.now(),
                title: formData.get('title'),
                category: formData.get('category'),
                description: formData.get('description'),
                targetAmount: parseInt(formData.get('targetAmount')),
                currentAmount: parseInt(formData.get('currentAmount')) || 0,
                donors: isEdit ? campaigns.find(c => c.id === existingId).donors : Math.floor(Math.random() * 100) + 10,
                daysLeft: parseInt(formData.get('daysLeft')) || 30,
                urgent: formData.get('urgent') === 'on',
                cardNumber: formData.get('cardNumber'),
                cardOwner: formData.get('cardOwner'),
                contactPhone: formData.get('contactPhone'),
                contactName: formData.get('contactName'),
                image: getCategoryIcon(formData.get('category')),
                createdBy: 'Admin',
                createdAt: new Date().toISOString()
            };
            
            await saveToServer('campaigns', campaignData);
            await loadAdminData();
            closeModal();
            showNotification('✅ E\'lon saqlandi!', 'success');
        }

        function showAddAdModal(existingAd = null) {
            if (!isAdmin) {
                showNotification('❌ Faqat admin reklama qo\'sha/ozgartira oladi!', 'error');
                return;
            }
            
            const isEdit = !!existingAd;
            const modal = document.createElement('div');
            modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
            modal.innerHTML = `
                <div class="bg-white rounded-2xl p-6 max-w-md w-full max-h-96 overflow-y-auto">
                    <h3 class="text-2xl font-bold mb-4">${isEdit ? '✏️ Reklamani Tahrirlash' : '📺 Reklama Qo\'shish'}</h3>
                    <form id="adForm" onsubmit="saveAd(event, '${existingAd ? existingAd.id : ''}')">
                        <div class="mb-4">
                            <label class="block text-sm font-medium mb-2">Reklama turi</label>
                            <select name="type" required class="w-full px-3 py-2 border rounded-lg">
                                <option value="">Tanlang</option>
                                <option value="banner" ${existingAd && existingAd.type === 'banner' ? 'selected' : ''}>📢 Banner Reklama</option>
                            </select>
                        </div>
                        
                        <div class="mb-4">
                            <label class="block text-sm font-medium mb-2">Sarlavha</label>
                            <input type="text" name="title" value="${existingAd ? existingAd.title : ''}" required class="w-full px-3 py-2 border rounded-lg">
                        </div>
                        
                        <div class="mb-4">
                            <label class="block text-sm font-medium mb-2">Tavsif</label>
                            <textarea name="description" class="w-full px-3 py-2 border rounded-lg h-16">${existingAd ? existingAd.description : ''}</textarea>
                        </div>
                        
                        <div class="mb-4">
                            <label class="block text-sm font-medium mb-2">🔗 Reklama havolasi (ixtiyoriy)</label>
                            <input type="url" name="linkUrl" value="${existingAd ? existingAd.linkUrl : ''}" class="w-full px-3 py-2 border rounded-lg" placeholder="https://example.com">
                            <div class="text-xs text-gray-500 mt-1">Banner bosilganda bu havolaga o'tadi</div>
                        </div>
                        
                        <div class="mb-4">
                            <label class="block text-sm font-medium mb-2">⏰ Ko'rsatish vaqti (soniya)</label>
                            <input type="number" name="showDuration" value="${existingAd ? existingAd.showDuration : 10}" min="5" max="30" class="w-full px-3 py-2 border rounded-lg">
                        </div>
                        
                        <div class="mb-4">
                            <label class="block text-sm font-medium mb-2">Aloqa ma'lumotlari</label>
                            <input type="text" name="contact" value="${existingAd ? existingAd.contact : ''}" class="w-full px-3 py-2 border rounded-lg" placeholder="Telefon yoki Telegram">
                        </div>
                        
                        <div class="mb-4">
                            <label class="flex items-center">
                                <input type="checkbox" name="banner" ${existingAd ? (existingAd.banner ? 'checked' : '') : 'checked'} class="mr-2">
                                <span class="text-sm">Yuqori banner sifatida ko'rsatish</span>
                            </label>
                        </div>
                        
                        <div class="flex gap-3">
                            <button type="submit" class="flex-1 bg-orange-600 text-white py-2 rounded-lg hover:bg-orange-700">
                                ${isEdit ? '💾 Saqlash' : '📤 Qo\'shish'}
                            </button>
                            <button type="button" onclick="closeModal()" class="flex-1 bg-gray-300 text-gray-700 py-2 rounded-lg hover:bg-gray-400">
                                ❌ Bekor qilish
                            </button>
                        </div>
                    </form>
                </div>
            `;
            
            document.body.appendChild(modal);
        }

        async function saveAd(event, existingId) {
            event.preventDefault();
            
            const formData = new FormData(event.target);
            const isEdit = !!existingId;
            const adData = {
                id: existingId || 'ad_' + Date.now(),
                type: formData.get('type'),
                title: formData.get('title'),
                description: formData.get('description'),
                linkUrl: formData.get('linkUrl'),
                contact: formData.get('contact'),
                showDuration: parseInt(formData.get('showDuration')) || 10,
                banner: formData.get('banner') === 'on',
                createdAt: new Date().toISOString()
            };
            
            await saveToServer('ads', adData);
            await loadAdminData();
            closeModal();
            showNotification('✅ Reklama saqlandi!', 'success');
        }

        function showAdSettings() {
            if (!isAdmin) return;
            
            const modal = document.createElement('div');
            modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
            modal.innerHTML = `
                <div class="bg-white rounded-2xl p-6 max-w-md w-full">
                    <h3 class="text-2xl font-bold mb-4">⚙️ Reklama Sozlamalari</h3>
                    <form id="adSettingsForm" onsubmit="updateAdSettings(event)">
                        <div class="mb-4">
                            <label class="block text-sm font-medium mb-2">Popup davomiyligi (soniya)</label>
                            <input type="number" name="overlayDuration" value="${adSettings.overlayDuration}" min="3" max="30" class="w-full px-3 py-2 border rounded-lg">
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium mb-2">O'tkazib yuborish vaqti (soniya)</label>
                            <input type="number" name="skipAfter" value="${adSettings.skipAfter}" min="1" max="10" class="w-full px-3 py-2 border rounded-lg">
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium mb-2">Banner matni</label>
                            <input type="text" name="bannerText" value="${adSettings.bannerText}" class="w-full px-3 py-2 border rounded-lg">
                        </div>
                        <div class="mb-4">
                            <label class="flex items-center">
                                <input type="checkbox" name="showBanner" ${adSettings.showBanner ? 'checked' : ''} class="mr-2">
                                <span class="text-sm">Banner reklamalarni ko'rsatish</span>
                            </label>
                        </div>
                        <div class="flex gap-3">
                            <button type="submit" class="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700">
                                💾 Saqlash
                            </button>
                            <button type="button" onclick="closeModal()" class="flex-1 bg-gray-300 text-gray-700 py-2 rounded-lg hover:bg-gray-400">
                                ❌ Bekor qilish
                            </button>
                        </div>
                    </form>
                </div>
            `;
            
            document.body.appendChild(modal);
        }

        async function updateAdSettings(event) {
            event.preventDefault();
            
            const formData = new FormData(event.target);
            const settingsData = {
                overlayDuration: parseInt(formData.get('overlayDuration')),
                skipAfter: parseInt(formData.get('skipAfter')),
                bannerText: formData.get('bannerText'),
                showBanner: formData.get('showBanner') === 'on'
            };
            
            await saveToServer('settings', settingsData);
            await loadAdminData();
            closeModal();
            showNotification('⚙️ Sozlamalar saqlandi!', 'success');
        }

        // ========================================
        // BANNER AD SYSTEM
        // ========================================
        
        function showRandomAd() {
            const bannerAds = ads.filter(ad => ad.banner);
            if (bannerAds.length === 0) return;
            
            const randomAd = bannerAds[Math.floor(Math.random() * bannerAds.length)];
            showBannerAd(randomAd);
        }

        function showAdOverlay(ad) {
            const overlay = document.getElementById('adOverlay');
            const contentArea = document.getElementById('adContentArea');
            const timer = document.getElementById('adTimer');
            const skipBtn = document.getElementById('adSkipBtn');
            
            let content = '';
            
            switch (ad.type) {
                case 'banner':
                    content = `<div class="flex items-center justify-center h-full bg-gradient-to-r from-blue-500 to-purple-500 text-white p-8">
                        <div class="text-center">
                            <h3 class="text-3xl font-bold mb-4">${ad.title}</h3>
                            <p class="text-lg mb-4">${ad.description}</p>
                            ${ad.linkUrl ? `<a href="${ad.linkUrl}" target="_blank" class="bg-white text-blue-500 px-6 py-3 rounded-lg font-bold">Batafsil</a>` : ''}
                            ${ad.contact ? `<div class="mt-4 text-lg font-bold">📞 ${ad.contact}</div>` : ''}
                        </div>
                    </div>`;
                    break;
            }
            
            contentArea.innerHTML = content;
            overlay.classList.remove('hidden');
            
            let timeLeft = adSettings.overlayDuration;
            timer.textContent = timeLeft;
            
            const countdown = setInterval(() => {
                timeLeft--;
                timer.textContent = timeLeft;
                
                if (timeLeft <= adSettings.overlayDuration - adSettings.skipAfter) {
                    skipBtn.classList.remove('hidden');
                }
                
                if (timeLeft <= 0) {
                    clearInterval(countdown);
                    closeAdOverlay();
                }
            }, 1000);
        }

        function closeAdOverlay() {
            document.getElementById('adOverlay').classList.add('hidden');
            document.getElementById('adSkipBtn').classList.add('hidden');
        }

        function showBannerAd(ad) {
            if (!adSettings.showBanner) return;
            
            const banner = document.getElementById('topBannerAd');
            const bannerText = document.getElementById('bannerAdText');
            
            if (ad.linkUrl) {
                bannerText.innerHTML = `<a href="${ad.linkUrl}" target="_blank" rel="noopener noreferrer" class="text-white hover:text-yellow-200 transition-colors">${ad.title || adSettings.bannerText}</a>`;
            } else {
                bannerText.textContent = ad.title || adSettings.bannerText;
            }
            
            banner.classList.remove('hidden');
            
            const duration = (ad.showDuration || 10) * 1000;
            setTimeout(() => {
                hideBannerAd();
            }, duration);
        }

        function hideBannerAd() {
            document.getElementById('topBannerAd').classList.add('hidden');
        }

        // ========================================
        // CAMPAIGN SYSTEM
        // ========================================

        function displayCampaigns() {
            const grid = document.getElementById('campaignsGrid');
            let filteredCampaigns = campaigns;
            
            if (currentFilter !== 'all') {
                filteredCampaigns = campaigns.filter(campaign => campaign.category === currentFilter);
            }
            
            grid.innerHTML = filteredCampaigns.map(campaign => createCampaignCard(campaign)).join('');
        }

        function createCampaignCard(campaign) {
            const progress = (campaign.currentAmount / campaign.targetAmount * 100).toFixed(1);
            const urgentBadge = campaign.urgent ? '<span class="absolute top-4 right-4 bg-red-500 text-white text-xs px-3 py-1 rounded-full font-medium">Shoshilinch</span>' : '';
            
            return `
                <div class="bg-white rounded-2xl shadow-xl overflow-hidden card-hover relative mobile-card">
                    ${urgentBadge}
                    <div class="p-6 md:p-8">
                        <div class="flex items-center mb-6">
                            <div class="text-4xl md:text-5xl mr-4">${campaign.image}</div>
                            <div>
                                <h3 class="text-xl md:text-2xl font-bold text-gray-800 mb-2">${campaign.title}</h3>
                                <div class="flex items-center space-x-2">
                                    <span class="text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full font-medium mobile-text">${getCategoryName(campaign.category)}</span>
                                </div>
                            </div>
                        </div>
                        
                        <p class="text-gray-600 mb-6 text-base md:text-lg leading-relaxed mobile-text">${campaign.description}</p>
                        
                        <div class="mb-6">
                            <div class="flex justify-between text-sm mb-3">
                                <span class="font-semibold text-gray-700 mobile-text">Yig'ildi: ${formatCurrency(campaign.currentAmount)}</span>
                                <span class="text-blue-600 font-bold text-lg">${progress}%</span>
                            </div>
                            <div class="w-full bg-gray-200 rounded-full h-4">
                                <div class="progress-bar h-4 rounded-full transition-all duration-500" style="width: ${progress}%"></div>
                            </div>
                            <div class="flex justify-between text-sm mt-3 text-gray-500">
                                <span class="mobile-text">Maqsad: ${formatCurrency(campaign.targetAmount)}</span>
                                <span class="mobile-text">${campaign.daysLeft} kun qoldi</span>
                            </div>
                        </div>
                        
                        <!-- Card Info -->
                        <div class="bg-blue-50 rounded-lg p-4 mb-4">
                            <div class="text-sm font-medium text-blue-800 mb-2">💳 To'lov Ma'lumotlari:</div>
                            <div class="text-sm text-blue-700">
                                <div>Karta: ${campaign.cardNumber}</div>
                                <div>Egasi: ${campaign.cardOwner}</div>
                            </div>
                        </div>
                        
                        <div class="flex justify-between items-center mb-4">
                            <div class="flex items-center space-x-2">
                                <span class="text-sm text-gray-500 font-medium mobile-text">${campaign.donors} xayriyachi</span>
                                <div class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                            </div>
                            <button onclick="donateToCharity('${campaign.id}')" class="telegram-btn text-white px-6 py-3 rounded-xl hover:from-green-700 hover:to-blue-700 transition-all duration-300 transform hover:scale-105 font-semibold shadow-lg mobile-button touch-button">
                                💝 Yordam Berish
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }

        function filterCampaigns(category) {
            currentFilter = category;
            displayCampaigns();
            
            document.querySelectorAll('.filter-btn').forEach(btn => {
                btn.classList.remove('bg-gradient-to-r', 'from-blue-600', 'to-purple-600', 'text-white');
                btn.classList.add('bg-white', 'text-gray-700');
            });
            
            const activeBtn = Array.from(document.querySelectorAll('.filter-btn')).find(btn => btn.onclick.toString().includes(`'${category}'`));
            if (activeBtn) {
                activeBtn.classList.remove('bg-white', 'text-gray-700');
                activeBtn.classList.add('bg-gradient-to-r', 'from-blue-600', 'to-purple-600', 'text-white');
            }
            
            scrollToSection('campaigns');
            
            const categoryName = category === 'all' ? 'Barcha e\'lonlar' : getCategoryName(category);
            showNotification(`🔍 ${categoryName} ko'rsatilmoqda`, 'info');
        }

        function getCategoryIcon(category) {
            const icons = {
                'tibbiyot': '🏥',
                'nogironlik': '♿',
                'talim': '📚',
                'uy-joy': '🏠',
                'hayvonlar': '🐾',
                'ijtimoiy': '🤝',
                'ayollar': '👩',
                'yetimlar': '👶'
            };
            return icons[category] || '💝';
        }

        function getCategoryName(category) {
            const names = {
                'tibbiyot': 'Tibbiy Yordam',
                'nogironlik': 'Nogironlik',
                'talim': 'Ta\'lim',
                'uy-joy': 'Uy-Joy',
                'hayvonlar': 'Hayvonlar',
                'ijtimoiy': 'Ijtimoiy',
                'ayollar': 'Ayollar Uchun',
                'yetimlar': 'Yetimlar'
            };
            return names[category] || category;
        }

        function formatCurrency(amount) {
            return new Intl.NumberFormat('uz-UZ').format(amount) + ' so\'m';
        }

        function updateStats() {
            const totalDonations = campaigns.reduce((sum, c) => sum + c.currentAmount, 0);
            const totalUsers = campaigns.reduce((sum, c) => sum + c.donors, 0);
            const activeCampaigns = campaigns.length;
            const completedCampaigns = campaigns.filter(c => c.currentAmount >= c.targetAmount).length;
            
            document.getElementById('totalDonations').textContent = formatCurrency(totalDonations).replace(' so\'m', 'M');
            document.getElementById('totalUsers').textContent = totalUsers.toLocaleString();
            document.getElementById('activeCampaigns').textContent = activeCampaigns;
            document.getElementById('completedCampaigns').textContent = completedCampaigns;
        }

        // ========================================
        // UTILITY FUNCTIONS
        // ========================================
        
        function closeModal() {
            const modals = document.querySelectorAll('.fixed.inset-0');
            modals.forEach(modal => {
                if (modal.id !== 'privacyModal' && modal.id !== 'adOverlay' && modal.id !== 'adminModal' && modal.id !== 'teamModal' && modal.id !== 'manageCampaignsModal' && modal.id !== 'manageAdsModal') {
                    document.body.removeChild(modal);
                }
            });
        }

        function requestCampaign() {
            const message = `🎯 *YANGI E'LON SO'ROVI - E-EHSON PROFESSIONAL*

📋 *E'lon Ma'lumotlari:*
• Nomi: [E'lon nomini kiriting]
• Kategoriya: [Kategoriyani tanlang]
• Maqsad summasi: [Summani kiriting]
• Tavsif: [Batafsil tavsif]

💳 *To'lov Ma'lumotlari:*
• Karta raqami: [8600 xxxx xxxx xxxx]
• Karta egasi: [To'liq ism]

📞 *Aloqa Ma'lumotlari:*
• Telefon: [+998xxxxxxxxx]
• Ism: [Sizning ismingiz]

📝 *Qo'shimcha Ma'lumotlar:*
• Shoshilinchmi: [Ha/Yo'q]
• Qolgan vaqt: [Kunlar soni]

🔗 *Platform:* E-Ehson Professional
👨‍💼 *CEO:* Jasurbek Jo'lanboyev G'ayrat o'g'li
📱 *Admin:* @serinaqu

💝 *E'lon qo'yish uchun yuqoridagi ma'lumotlarni to'ldiring!*`;

            const telegramUrl = `https://t.me/serinaqu?text=${encodeURIComponent(message)}`;
            window.open(telegramUrl, '_blank');
            
            showNotification('📢 E\'lon so\'rovi uchun admin bilan bog\'lanish ochildi!', 'success');
        }

        function getHelp() {
            const message = `🆘 *YORDAM SO'ROVI - E-EHSON PROFESSIONAL*

📋 *Yordam Turi:*
• Texnik yordam
• E'lon qo'yish
• To'lov masalalari
• Boshqa savollar

📝 *Sizning savolingiz:*
[Bu yerga savolingizni yozing]

🔗 *Platform:* E-Ehson Professional
👨‍💼 *CEO:* Jasurbek Jo'lanboyev G'ayrat o'g'li
📱 *Admin:* @serinaqu

💬 *Biz sizga yordam berishga tayyormiz!*`;

            const telegramUrl = `https://t.me/serinaqu?text=${encodeURIComponent(message)}`;
            window.open(telegramUrl, '_blank');
            
            showNotification('🆘 Yordam uchun admin bilan bog\'lanish ochildi!', 'success');
        }

    </script>
</body>
</html>
'''

@app.route('/webapp')
def webapp():
    html = WEBAPP_HTML.replace('{admin_id}', ADMIN_ID).replace('{base_url}', BASE_URL)
    return make_response(html)

# aiogram bot setup
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

def main_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="💝 Xayriya Qilish")
    kb.button(text="📜 To'lovlar Tarixi")
    kb.button(text="E'lonlar")
    kb.button(text="Biz haqimizda")
    kb.button(text="Loyiha Jamoasi")
    kb.button(text="Aloqa")
    kb.button(text="Maxfiylik")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)

webapp_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🌐 Veb Platformani Ochish", web_app=WebAppInfo(url=f"{BASE_URL}/webapp"))]
])

@dp.message(Command("start"))
async def start(message: types.Message):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO users (user_id, username, first_name, created_at) VALUES (?, ?, ?, ?)",
                  (str(message.from_user.id), message.from_user.username or "", message.from_user.first_name or "", datetime.now().isoformat()))
        conn.commit()
        conn.close()
        await message.answer("E-Ehson Professional ga xush kelibsiz!", reply_markup=main_keyboard())
        await message.answer("Platformani oching:", reply_markup=webapp_keyboard)
    except Exception as e:
        logger.error(f"Start command xatosi: {e}")
        await message.answer("Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")

@dp.message(F.text == "💝 Xayriya Qilish")
async def donate(message: types.Message):
    await message.answer("Xayriya qilish uchun platformani oching:", reply_markup=webapp_keyboard)

@dp.message(F.text == "📜 To'lovlar Tarixi")
async def history(message: Message):
    try:
        user_id = str(message.from_user.id)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT amount, status, created_at FROM payments WHERE user_id = ?", (user_id,))
        rows = c.fetchall()
        conn.close()
        if not rows:
            await message.answer("Hech qanday to'lov topilmadi.")
            return
        text = "To'lovlar tarixi:\n"
        for row in rows:
            text += f"Miqdor: {row[0]} so'm, Status: {row[1]}, Vaqt: {row[2]}\n"
        await message.answer(text)
    except Exception as e:
        logger.error(f"History xatosi: {e}")
        await message.answer("Tarixni ko'rishda xatolik yuz berdi.")

@dp.message(F.text.in_(["E'lonlar", "Biz haqimizda", "Loyiha Jamoasi", "Aloqa", "Maxfiylik"]))
async def web_sections(message: Message):
    await message.answer(f"{message.text} bo'limi web platformada mavjud.", reply_markup=webapp_keyboard)

@dp.message(Command("test_payment"))
async def test_payment(message: types.Message):
    try:
        user_id = str(message.from_user.id)
        test_amount = 15000.0
        payment_id = str(uuid.uuid4())
        click_trans_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO payments (payment_id, user_id, amount, status, click_trans_id, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                  (payment_id, user_id, test_amount, "success", click_trans_id, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
        await send_payment_confirmation(message.from_user.id, test_amount, "success")
        await message.answer("Test to'lovi muvaffaqiyatli qo'shildi!")
    except Exception as e:
        logger.error(f"Test payment xatosi: {e}")
        await message.answer("Test to'lovi qo'shishda xatolik yuz berdi.")

async def send_payment_confirmation(user_id: int, amount: float, status: str):
    text = f"Siz {amount} so'm to'lov qildingiz. Status: {'✅ Muvaffaqiyatli' if status == 'success' else '❌ Bekor qilingan'}"
    try:
        await bot.send_message(user_id, text)
        logger.info(f"Confirmation sent to user {user_id}")
    except Exception as e:
        logger.error(f"Xabar yuborishda xato: {e}")

# Run Flask in thread
def run_flask():
    app.run(host="0.0.0.0", port=8000, debug=False, use_reloader=False)

flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

# Run bot
bot_loop = asyncio.get_event_loop()

async def main():
    logger.info("Bot ishga tushmoqda...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Bot polling xatosi: {e}")

if __name__ == "__main__":
    asyncio.run(main())
