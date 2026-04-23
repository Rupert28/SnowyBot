import os
from pywikibot.login import BotPassword

family = 'wikipedia'
mylang = 'en'
usernames['wikipedia']['en'] = 'SnowyBot'

password_file = None

def password_callback(shell, username):
    secret = os.environ.get('SNOWY_PASS')
    
    if secret:
        return BotPassword('Task_1', secret)
    return None