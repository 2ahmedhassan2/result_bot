import sqlite3
from datetime import datetime
import json
from config import DATABASE_NAME

def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            role TEXT DEFAULT 'user',
            seat_no TEXT,
            created_at TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscribers (
            chat_id INTEGER PRIMARY KEY,
            seat_no TEXT,
            subscribed_at TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS results (
            seat_no TEXT PRIMARY KEY,
            result_json TEXT,
            updated_at TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operation TEXT,
            status TEXT,
            details TEXT,
            timestamp TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def add_or_update_user(user_id, username, role='user'):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if cursor.fetchone():
        cursor.execute("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))
    else:
        cursor.execute("INSERT INTO users (user_id, username, role, created_at) VALUES (?, ?, ?, ?)",
                       (user_id, username, role, now))
    conn.commit()
    conn.close()

def get_user_role(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row['role'] if row else 'user'

def save_user_seat_no(user_id, seat_no):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET seat_no = ? WHERE user_id = ?", (seat_no, user_id))
    conn.commit()
    conn.close()

def get_user_seat_no(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT seat_no FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row['seat_no'] if row else None

def is_user_subscribed(chat_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM subscribers WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    conn.close()
    return row is not None

def subscribe_user(chat_id, seat_no):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT OR REPLACE INTO subscribers (chat_id, seat_no, subscribed_at) VALUES (?, ?, ?)",
                   (chat_id, seat_no, now))
    conn.commit()
    conn.close()

def unsubscribe_user(chat_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM subscribers WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()

def get_all_subscribers():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id, seat_no FROM subscribers")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def save_result(seat_no, result_dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT OR REPLACE INTO results (seat_no, result_json, updated_at) VALUES (?, ?, ?)",
                   (seat_no, json.dumps(result_dict), now))
    conn.commit()
    conn.close()

def get_saved_result(seat_no):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT result_json FROM results WHERE seat_no = ?", (seat_no,))
    row = cursor.fetchone()
    conn.close()
    return json.loads(row['result_json']) if row else None

def log_check_operation(status, details):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO system_logs (operation, status, details, timestamp) VALUES (?, ?, ?, ?)",
                   ("background_check", status, details, now))
    conn.commit()
    conn.close()

def get_system_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as count FROM users")
    total_users = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM subscribers")
    total_subscribers = cursor.fetchone()['count']
    
    cursor.execute("SELECT timestamp FROM system_logs WHERE operation='background_check' ORDER BY id DESC LIMIT 1")
    last_check_row = cursor.fetchone()
    last_check = last_check_row['timestamp'] if last_check_row else "لا يوجد"
    
    conn.close()
    return {
        "total_users": total_users,
        "total_subscribers": total_subscribers,
        "last_check": last_check
    }
