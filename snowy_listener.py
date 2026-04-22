import pywikibot
import re
import time
import datetime
import dateparser
from snowy_core import add_reminder_if_new, init_db

site = pywikibot.Site("en", "wikipedia")

# Regex captures 3 groups: 1=Time, 2=Message, 3=Optional Target
REMINDER_REGEX = re.compile(
    r'\{\{\s*(?:User:SnowyRiver28/sandbox|Remindme)\s*\|\s*([^|]+)\s*\|\s*([^|}]+)(?:\|\s*([^}]+))?\s*\}\}', 
    re.IGNORECASE
)

def start_notification_listener():
    init_db()
    if not site.logged_in():
        print("LOG: Logging in...")
        site.login()
    
    now_str = datetime.datetime.now().strftime('%H:%M:%S')
    print(f"\n--- [SCAN START {now_str}] ---")
    
    try:
        # Fetch only unread mentions
        notifications = list(site.notifications(limit=20, filter='unread'))
        print(f"LOG: API returned {len(notifications)} unread notifications.")
    except Exception as e:
        print(f"    ❌ [API ERROR]: {e}")
        return

    if not notifications:
        print("LOG: No new activity detected.")
        print("--- [SCAN FINISHED] ---\n")
        return

    # Deduplicate pages
    pages_to_process = {} 
    for n in notifications:
        if n.type == 'mention' and n.page:
            pages_to_process[n.page.title()] = (n.page, n.revid, n.agent.username)
        # Mark read immediately to prevent loops
        n.mark_as_read()

    print(f"LOG: Processing {len(pages_to_process)} unique pages...")

    for title, (page, revid, user) in pages_to_process.items():
        try:
            print(f"  > Checking Page: [[{title}]] (Mention by {user})")
            
            # Fresh download
            text = page.get(force=True)
            print(f"    [DEBUG] Text length: {len(text)} characters.")
            
            matches = REMINDER_REGEX.findall(text)
            print(f"    [DEBUG] Found {len(matches)} potential template matches.")
            
            if not matches:
                print(f"    [INFO] No templates matched our Regex on this page.")
                continue

            new_count = 0
            for match in matches:
                time_str, msg, target_param = match
                msg_clean = msg.strip()
                target_name = target_param.strip() if target_param else "talk"
                
                print(f"    [PROCESS] Match found: '{msg_clean}' | Time: {time_str} | Target: {target_name}")
                
                due_date = dateparser.parse(time_str.strip(), settings={'PREFER_DATES_FROM': 'future'})
                
                if due_date:
                    is_new = add_reminder_if_new(user, due_date, msg_clean, revid, title, target_param)
                    if is_new:
                        print(f"    ✅ [SUCCESS] Logged to DB (Due: {due_date})")
                        new_count += 1
                    else:
                        print(f"    [SKIP] Already in DB (Fingerprint match).")
                else:
                    print(f"    [ERROR] Dateparser failed on: '{time_str}'")
            
            print(f"    [DONE] Finished [[{title}]]. New entries: {new_count}")

        except Exception as e:
            print(f"    ❌ [ERROR on {title}]: {e}")

    print(f"--- [SCAN FINISHED] ---\n")

if __name__ == "__main__":
    print("SnowyBot Listener active. Monitoring pings...")
    while True:
        try:
            start_notification_listener()
        except Exception as e:
            print(f"MAIN LOOP FATAL: {e}")
        time.sleep(30)