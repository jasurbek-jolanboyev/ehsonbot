from flask import Flask, request, jsonify
import sqlite3
import logging
from datetime import datetime
import os

app = Flask(__name__)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DB_PATH = 'ehson.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Dict format for rows
    return conn

def init_db():
    conn = get_db_connection()
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
    conn.commit()
    conn.close()
    logger.info("Database initialized.")

init_db()

@app.route("/click/callback", methods=["POST"])
def click_callback():
    data = request.form.to_dict()
    logger.info(f"Click callback data: {data}")
    
    conn = get_db_connection()
    c = conn.cursor()
    
    user_id = data.get("merchant_trans_id")
    amount = float(data.get("amount", 0))
    click_trans_id = data.get("click_trans_id")
    error_code = data.get("error")
    
    if not user_id:
        logger.error("No user_id in callback")
        return jsonify({"error": -1}), 400
    
    # Save or update user
    c.execute("INSERT OR REPLACE INTO users (user_id, username, first_name, created_at) VALUES (?, ?, ?, ?)",
              (user_id, data.get("merchant_user_name", ""), data.get("merchant_user_first_name", ""), datetime.now().isoformat()))
    
    # Update payment status
    status = "success" if error_code == "0" else "failed"
    c.execute("INSERT OR REPLACE INTO payments (payment_id, user_id
