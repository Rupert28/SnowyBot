import os

family = 'wikipedia'

mylang = 'en'

usernames['wikipedia']['en'] = 'SnowyBot'

_pass = os.getenv('SNOWY_PASS', '')
if _pass:
    os.environ['PYWIKIBOT_PASSWORD'] = f"('SnowyBot', BotPassword('Task_1', '{_pass}'))"