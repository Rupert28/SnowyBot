import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "reminders.db")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fingerprint TEXT UNIQUE, 
            username TEXT,
            reminder_text TEXT,
            due_date DATETIME,
            target_page TEXT,
            revid INTEGER,
            origin_page TEXT,
            status TEXT DEFAULT 'pending'
        )
    ''')
    conn.commit()
    conn.close()
    print("LOG: Database initialized.")

def add_reminder_if_new(username, due_date, message, revid, page_title, target_param=None):
    
    target = target_param.strip().lower() if target_param else 'talk'
    
    
    fingerprint = f"{username}|{message}|{page_title}|{revid}".lower().strip()
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        
        cursor.execute('''
            INSERT INTO reminders (fingerprint, username, due_date, reminder_text, target_page, revid, origin_page)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (fingerprint, username, due_date.isoformat(), message, target, revid, page_title))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False 
    finally:
        conn.close()