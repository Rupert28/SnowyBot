import pywikibot
import re
import time
from datetime import datetime, timezone
import dateparser
from snowy_core import add_reminder_if_new, init_db

site = pywikibot.Site("en", "wikipedia")

# Regex captures 3 groups: 1=Time, 2=Message, 3=Optional Target
REMINDER_REGEX = re.compile(
    r'\{\{\s*(?:User:SnowyRiver28/sandbox|Remindme)\s*\|\s*([^|]+)\s*\|\s*([^|}]+)(?:\|\s*([^}]+))?\s*\}\}', 
    re.IGNORECASE
)

def mark_notification_read(notif_id):
    try:
        csrf_token = site.get_tokens(['csrf'])['csrf']
        
        mark_req = site.simple_request(
            action='echomarkread',
            list=notif_id,
            token=csrf_token
        )
        mark_req.submit()
        print(f"    [MARK] Notification {notif_id} marked as read.")
        return True
    except Exception as mark_error:
        print(f"    [WARN] Failed to mark {notif_id} as read: {mark_error}")
        return False

def start_notification_listener():
    init_db()
    if not site.logged_in():
        print("LOG: Logging in...")
        site.login()
    
    now_str = datetime.now(timezone.utc).strftime('%H:%M:%S')
    print(f"\n--- [SCAN START {now_str} UTC] ---")
    
    try:
        params = {
            'action': 'query',
            'meta': 'notifications',
            'notfilter': '!read',
            'notlimit': 50
        }
        req = site.simple_request(**params)
        data = req.submit()
        
        raw_notifications = data.get('query', {}).get('notifications', {}).get('list', [])
        print(f"LOG: API returned {len(raw_notifications)} unread notifications.")
        
    except Exception as e:
        print(f"    ❌ [API ERROR]: {e}")
        return

    if not raw_notifications:
        print("LOG: No new activity detected.")
        print("--- [SCAN FINISHED] ---\n")
        return

    all_notif_ids = [str(n.get('id')) for n in raw_notifications if n.get('id')]

    for n in raw_notifications:
        if n.get('type') == 'mention' and 'title' in n:
            title = n['title']['full']
            revid = n.get('revid')
            user = n.get('agent', {}).get('name')
            
            try:
                print(f"  > Checking Mention: [[{title}]] (by {user})")
                page = pywikibot.Page(site, title)
                text = page.get(force=True)
                matches = REMINDER_REGEX.findall(text)
                
                if not matches:
                    print(f"    [INFO] No templates matched Regex for this mention.")
                    continue

                new_count = 0
                for match in matches:
                    time_str, msg, target_param = match
                    
                    due_date = dateparser.parse(time_str.strip(), settings={
                        'PREFER_DATES_FROM': 'future',
                        'TIMEZONE': 'UTC',
                        'TO_TIMEZONE': 'UTC',
                        'RETURN_AS_TIMEZONE_AWARE': False
                    })
                    
                    if due_date:
                        is_new = add_reminder_if_new(user, due_date, msg.strip(), revid, title, target_param)
                        if is_new:
                            print(f"    ✅ [SUCCESS] Logged to DB (Due: {due_date})")
                            new_count += 1
                
                print(f"    [DONE] Finished processing mention by {user}. New entries: {new_count}")

            except Exception as e:
                print(f"    ❌ [ERROR on {title}]: {e}")

    if all_notif_ids:
        mark_notification_read("|".join(all_notif_ids))

    print(f"--- [SCAN FINISHED] ---\n")

if __name__ == "__main__":
    print("SnowyBot Listener active. Monitoring pings...")
    while True:
        try:
            start_notification_listener()
        except Exception as e:
            print(f"MAIN LOOP FATAL: {e}")
        
        time.sleep(60)
        now_str = datetime.now(timezone.utc).strftime('%H:%M:%S')
        print(f"[{now_str} UTC] Sleeping for 60 seconds...")