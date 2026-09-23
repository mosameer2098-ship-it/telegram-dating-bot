import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not configured.")

if not ADMIN_ID:
    raise RuntimeError("ADMIN_ID is not configured.")

try:
    ADMIN_ID = int(ADMIN_ID)
except ValueError:
    raise RuntimeError("ADMIN_ID must be a number.")
