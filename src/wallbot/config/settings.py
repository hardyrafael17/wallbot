import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN", "Bot Token does not exist")
PROFILE = os.getenv("PROFILE")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "-1003106570436")

TELEGRAM_API_URL = "https://api.telegram.org/bot{}/".format(TOKEN)
WALLAPOP_API_URL = "https://api.wallapop.com/api/v3/search"
WALLAPOP_ITEM_URL = "https://api.wallapop.com/api/v3/items/{item_id}"
WALLAPOP_USER_URL = "https://api.wallapop.com/api/v3/users/{user_id}"

DATABASE_PATH = "db.sqlite" if PROFILE else "/data/db.sqlite"

LOG_LEVEL = "DEBUG" if PROFILE else "INFO"
LOG_PATH = "wallbot.log" if PROFILE else "/logs/wallbot.log"
