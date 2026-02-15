import os

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

ADMIN_ID = int(os.getenv("ADMIN_ID"))
LOG_GROUP_ID = int(os.getenv("LOG_GROUP_ID"))  # private storage group id

AUTO_DELETE = int(os.getenv("AUTO_DELETE", "600"))
