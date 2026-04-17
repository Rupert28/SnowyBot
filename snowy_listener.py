import pywikibot
import datetime
from snowy_core import parse_reminder_text, add_reminder_to_db

# Configuration
BOT_NAME = "SnowyBot" 
site = pywikibot.Site("en", "wikipedia")

def start_notification_listener():
    print(f"SnowyBot checking notifications at {datetime.datetime.now()}...")
    
    #  Login
    site.login()
    
    #  Iterate through unread "mention" notifications
    for notification in site.notifications(filter={'type': 'mention'}):
        try:
            username = notification.agent.username
            page = notification.page
            revid = notification.revid # The unique ID for this specific edit
            
            print(f"New mention from {username} on [[{page.title()}]] (Rev: {revid})")
            
            #  Get the text of the edit that triggered the notification
            content = page.getOldVersion(revid)
            
            #  Updated parser logic to handle the new Template structure
            # parse_reminder_text now returns: (due_date, message, delivery_target)
            due, msg, target = parse_reminder_text(content)
            
            if due:
                wiki_url = f"https://en.wikipedia.org/wiki/{page.title()}"
                
                #  Save to DB including the target preference and the unique RevID
                # This prevents duplicates if the script restarts before marking as read
                success = add_reminder_to_db(username, due, msg, wiki_url, target, revid)
                
                if success:
                    print(f"✅ Success: Reminder for {username} saved (Target: {target}).")
                    #  Mark as read only after successful DB save
                    notification.mark_as_read()
                else:
                    print(f"ℹ️ Reminder for RevID {revid} already exists in DB. Skipping.")
                    notification.mark_as_read()
            else:
                print(f"⚠️ Mention found, but no valid {{remindme}} template detected.")

        except Exception as e:
            print(f"Error processing notification: {e}")
            continue

if __name__ == "__main__":
    start_notification_listener()