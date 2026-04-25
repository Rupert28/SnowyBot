import os
from dotenv import load_dotenv as _load_dotenv

_load_dotenv()

if 'usernames' not in globals():
    usernames = {}
if 'authenticate' not in globals():
    authenticate = {}

family = 'wikipedia'
mylang = 'en'



usernames['wikipedia']['en'] = os.getenv('PWB_USERNAME')

authenticate['en.wikipedia.org'] = (
    os.getenv('PWB_CONSUMER_TOKEN'),
    os.getenv('PWB_CONSUMER_SECRET'),
    os.getenv('PWB_ACCESS_TOKEN'),
    os.getenv('PWB_ACCESS_SECRET')
)

user_agent_description = 'SnowyBot (en:User:SnowyBot) local-dev'