import os


family = 'wikipedia'

mylang = 'en'

usernames['wikipedia']['en'] = 'SnowyBot'

password_file = None

def password_callback(shell, username):
    return os.environ.get('SNOWY_PASS')