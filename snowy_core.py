import mwparserfromhell
import dateparser
import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "reminders.db")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rev_id INTEGER UNIQUE,
            username TEXT NOT NULL,
            reminder_text TEXT NOT NULL,
            due_date DATETIME NOT NULL,
            source_url TEXT,
            delivery_target TEXT DEFAULT 'talk',
            status TEXT DEFAULT 'pending'
        )
    ''')
    conn.commit()
    conn.close()
    print("Local database initialized with RevID and Delivery Target support.")
    
def parse_reminder_text(text):
    """
    
    """
    wikicode = mwparserfromhell.parse(text)
    
    for template in wikicode.filter_templates():
        # Handles {{remindme}}, {{Remindme}}, and your test template
        if template.name.matches("remindme") or template.name.matches("remindme_test"):
            try:
                # Param 1: Time string
                time_part = str(template.get(1).value).strip()
                # Param 2: Message string
                message_part = str(template.get(2).value).strip()
                
                # Check for optional target parameter, e.g., |target=subpage
                target = "talk"
                if template.has("target"):
                    target = str(template.get("target").value).strip().lower()
                
                due_date = dateparser.parse(
                    time_part, 
                    settings={'PREFER_DATES_FROM': 'future'}
                )
                
                return due_date, message_part, target
            except (ValueError, IndexError):
                continue
    
    return None, None, None

def add_reminder_to_db(username, due_date, message, url, target, rev_id):
    """
    Saves the reminder. Returns True if saved, False if it was a duplicate RevID.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO reminders (username, rev_id, due_date, reminder_text, source_url, delivery_target)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, rev_id, due_date.isoformat(), message, url, target))
        conn.commit()
        print(f"Reminder saved for {username} via RevID {rev_id}")
        return True
    except sqlite3.IntegrityError:
        # This catches the case where the RevID already exists
        return False
    finally:
        conn.close()
    
if __name__ == "__main__":
    init_db()
    
    # Testing the new Template logic
    fake_wikitext = 'Please do this {{remindme|2 hours|Check the Sutherland fishing report|target=subpage}} ~~~~'
    
    due, msg, target = parse_reminder_text(fake_wikitext)
    
    if due:
        # Using a dummy RevID for testing
        add_reminder_to_db("SnowyRiver28", due, msg, "https://test.wiki", target, 12345678)
    else:
        print("Failed to parse the template!")