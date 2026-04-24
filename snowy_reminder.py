import sqlite3
import pywikibot
import datetime
import time
from datetime import timezone
from snowy_core import DB_NAME

site = pywikibot.Site("en", "wikipedia")

def get_due_reminders():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    now = datetime.datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
    
    cursor.execute('''
        SELECT id, username, reminder_text, target_page, origin_page 
        FROM reminders 
        WHERE due_date <= ? AND status = ?
    ''', (now, 'pending'))
    
    rows = cursor.fetchall()
    conn.close()
    return rows

def mark_as_sent(reminder_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE reminders SET status = ? WHERE id = ?', ('sent', reminder_id))
    conn.commit()
    conn.close()

def send_reminders():
    due = get_due_reminders()
    if not due:
        return

    print(f"LOG: Found {len(due)} reminders to deliver!")
    
    for r_id, user, msg, target, origin in due:
        try:
            # Determine target title
            is_subpage = False
            if not target or target.lower() == 'talk':
                target_title = f"User talk:{user}"
            else:
                target_title = f"User talk:{user}/{target}"
                is_subpage = True

            dest_page = pywikibot.Page(site, target_title)
            
            # Exclusion compliance
            if not dest_page.botMayEdit():
                print(f"    ⚠️ [BLOCKED] User {user} has opted out via nobots.")
                mark_as_sent(r_id) 
                continue
            
            # Format wikitext
            ping_text = f"[[User:{user}|{user}]]" if is_subpage else f"{user}"

            reminder_wikitext = f"""

== Reminder from SnowyBot ==

[[File:Alarm Clock Vector (cropped).svg|50px|left]]
Hi {ping_text}, here's your reminder you requested on [[{origin}]]: ''{msg}''.

''Set and don't forget with a reminder from'' ~~~~
"""
            
            # Save the edit
            dest_page.text += reminder_wikitext
            dest_page.save(summary=f"Delivering requested reminder")
            
            print(f"    🚀 Delivered to {target_title}")
            mark_as_sent(r_id)
            
            # Pacing
            time.sleep(3) 

        except pywikibot.EditConflictError:
            print(f"    ⚠️ [CONFLICT] Someone edited [[{target_title}]] at the same time. Retrying next loop.")
        except Exception as e:
            print(f"    ❌ Failed to deliver reminder {r_id}: {e}")

if __name__ == "__main__":
    print("SnowyBot Sender is active. Monitoring for due dates...")
    while True:
        try:
            send_reminders()
        except Exception as e:
            print(f"MAIN SENDER LOOP ERROR: {e}")
            
        time.sleep(180) 
        now_str = datetime.datetime.now(timezone.utc).strftime('%H:%M:%S')
        print(f"[{now_str} UTC] Sleeping for 180 seconds...")