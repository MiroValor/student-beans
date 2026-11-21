import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
