import sqlite3
import pywikibot
import datetime
import time
from snowy_core import DB_NAME

site = pywikibot.Site("en", "wikipedia")

def get_due_reminders():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = datetime.datetime.now().isoformat()
    
    # Get all reminders where due_date is in the past and they haven't been sent
    cursor.execute('SELECT id, username, reminder_text, target_page FROM reminders WHERE due_date <= ?', (now,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_reminder(reminder_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM reminders WHERE id = ?', (reminder_id,))
    conn.commit()
    conn.close()

def send_reminders():
    due = get_due_reminders()
    if not due:
        return

    print(f"LOG: Found {len(due)} reminders to deliver!")
    
    for r_id, user, msg, target in due:
        try:
            # Determine the target page
            is_subpage = False
            if target.lower() == 'talk' or not target:
                target_title = f"User talk:{user}"
            else:
                # If they put 'reminders', it goes to User talk:Username/reminders
                target_title = f"User talk:{user}/{target}"
                is_subpage = True

            dest_page = pywikibot.Page(site, target_title)
            
            ping_text = f"{{{{u|{user}}}}}: " if is_subpage else f"{user}: "
            
            # Format the message
            reminder_wikitext = (
                f"\n== Reminder from SnowyBot ==\n"
                f"{ping_text}Here is your requested reminder: ''{msg}'' --~~~~"
            )
            
            # Append to the page
            dest_page.text += reminder_wikitext
            dest_page.save(summary=f"SnowyBot: Delivering requested reminder: {msg[:30]}...")
            
            print(f"    🚀 Delivered to {target_title}")
            
            delete_reminder(r_id)

        except Exception as e:
            print(f"    ❌ Failed to deliver reminder {r_id}: {e}")

if __name__ == "__main__":
    print("SnowyBot Sender is active. Monitoring for due dates...")
    while True:
        send_reminders()
        time.sleep(60) # Check every minute