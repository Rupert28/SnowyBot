import os

family = 'wikipedia'
mylang = 'en'

usernames['wikipedia']['en'] = os.getenv('PWB_USERNAME')

authenticate['en.wikipedia.org'] = (
    os.getenv('PWB_CONSUMER_TOKEN'),
    os.getenv('PWB_CONSUMER_SECRET'),
    os.getenv('PWB_ACCESS_TOKEN'),
    os.getenv('PWB_ACCESS_SECRET')
)