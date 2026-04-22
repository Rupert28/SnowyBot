import sqlite3
import os

DB_NAME = "reminders.db"

def inspect_database():
    if os.path.exists(DB_NAME):
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # Added rev_id to the query
            cursor.execute("SELECT id, username, due_date, reminder_text FROM reminders")
            rows = cursor.fetchall()
            
            # Adjusted header to include RevID
            print(f"{'ID':<3} | {'User':<15} | {'Due Date':<20} | {'Message':<30}")
            print("-" * 70)
            
            for row in rows:
                print(f"{row['id']:<3} | {row['username']:<15} | {row['due_date']:<20} | {row['reminder_text']:<30}")
                print()
                
        except sqlite3.OperationalError as e:
            print(f"Error reading table: {e}")
        
        conn.close()
    else:
        print("Database file 'reminders.db' not found!")

if __name__ == "__main__":
    inspect_database()