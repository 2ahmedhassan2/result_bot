import sqlite3
import json
from datetime import datetime
from config import DATABASE_NAME

def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # جدول المستخدمين
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            seat_no TEXT,
            role TEXT DEFAULT 'user',
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # جدول الاشتراكات في الإشعارات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscribers (
            chat_id INTEGER PRIMARY KEY,
            seat_no TEXT NOT NULL,
            subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # جدول نتائج الطلاب لحفظ آخر حالة معروفة للنتيجة
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS results (
            seat_no TEXT PRIMARY KEY,
            result_data TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # جدول سجل الفحص الدوري
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            check_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT,
            details TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def add_or_update_user(user_id, username, role='user'):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (user_id, username, role, last_activity)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id) DO UPDATE SET
            username = excluded.username,
            last_activity = CURRENT_TIMESTAMP
    ''', (user_id, username, role))
    conn.commit()
    conn.close()

def get_user_role(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT role FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row['role'] if row else 'user'

def save_user_seat_no(user_id, seat_no):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET seat_no = ? WHERE user_id = ?', (seat_no, user_id))
    conn.commit()
    conn.close()

def get_user_seat_no(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT seat_no FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row['seat_no'] if row else None

def subscribe_user(chat_id, seat_no):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO subscribers (chat_id, seat_no, subscribed_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(chat_id) DO UPDATE SET seat_no = excluded.seat_no
    ''', (chat_id, seat_no))
    conn.commit()
    conn.close()

def unsubscribe_user(chat_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM subscribers WHERE chat_id = ?', (chat_id,))
    conn.commit()
    conn.close()

def is_user_subscribed(chat_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM subscribers WHERE chat_id = ?', (chat_id,))
    row = cursor.fetchone()
    conn.close()
    return row is not None

def get_all_subscribers():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT chat_id, seat_no FROM subscribers')
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_saved_result(seat_no):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT result_data FROM results WHERE seat_no = ?', (seat_no,))
    row = cursor.fetchone()
    conn.close()
    return json.loads(row['result_data']) if row else None

def save_result(seat_no, result_dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO results (seat_no, result_data, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(seat_no) DO UPDATE SET
            result_data = excluded.result_data,
            updated_at = CURRENT_TIMESTAMP
    ''', (seat_no, json.dumps(result_dict)))
    conn.commit()
    conn.close()

def log_check_operation(status, details=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO logs (status, details) VALUES (?, ?)', (status, details))
    conn.commit()
    conn.close()

def get_system_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) as total FROM users')
    total_users = cursor.fetchone()['total']
    
    cursor.execute('SELECT COUNT(*) as total FROM subscribers')
    total_subs = cursor.fetchone()['total']
    
    cursor.execute('SELECT check_time FROM logs ORDER BY id DESC LIMIT 1')
    last_check_row = cursor.fetchone()
    last_check = last_check_row['check_time'] if last_check_row else "لا يوجد"
    
    cursor.execute("SELECT updated_at FROM results ORDER BY updated_at DESC LIMIT 1")
    last_update_row = cursor.fetchone()
    last_update = last_update_row['updated_at'] if last_update_row else "لا يوجد"
    
    conn.close()
    return {
        "total_users": total_users,
        "total_subscribers": total_subs,
        "last_check": last_check,
        "last_update": last_update
    }
