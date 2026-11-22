import os
from pathlib import Path
from dotenv import load_dotenv

# Resolve paths relative to this folder so the bot works no matter which
# directory you launch it from.
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
STORAGE_FILE = str(BASE_DIR / "credentials.json")
