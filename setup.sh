#!/bin/zsh
# One-time setup on macOS: creates a virtualenv, installs dependencies and
# Playwright's Chromium, and creates .env with a fresh encryption key.
set -e
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  echo "Creating virtualenv..."
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python -m playwright install chromium

if [ ! -f .env ]; then
  KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
  sed "s|^ENCRYPTION_KEY=.*|ENCRYPTION_KEY=$KEY|" .env.example > .env
  chmod 600 .env
  echo "Created .env with a new ENCRYPTION_KEY. Add your DISCORD_TOKEN to it, then run ./run.sh"
else
  echo ".env already exists (left unchanged). Run ./run.sh to start the bot."
fi
