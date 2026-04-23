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
            'notlimit': 20
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

    pages_to_process = {} 
    for n in raw_notifications:
        if n.get('type') == 'mention' and 'title' in n:
            title = n['title']['full']
            revid = n.get('revid')
            agent = n.get('agent', {}).get('name')
            notif_id = n.get('id')
            
            page_obj = pywikibot.Page(site, title)
            pages_to_process[title] = (page_obj, revid, agent, notif_id)

    print(f"LOG: Processing {len(pages_to_process)} unique pages...")

    for title, (page, revid, user, notif_id) in pages_to_process.items():
        try:
            print(f"  > Checking Page: [[{title}]] (Mention by {user})")
            
            text = page.get(force=True)
            matches = REMINDER_REGEX.findall(text)
            
            if not matches:
                print(f"    [INFO] No templates matched Regex on this page.")
                mark_notification_read(notif_id)
                continue

            new_count = 0
            for match in matches:
                time_str, msg, target_param = match
                
                # dateparser forced to UTC
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
            
            mark_notification_read(notif_id)
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
        
        time.sleep(60)
        now_str = datetime.now(timezone.utc).strftime('%H:%M:%S')
        print(f"[{now_str} UTC] Sleeping for 60 seconds...")