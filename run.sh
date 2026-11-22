#!/bin/zsh
# Start the bot. Press Ctrl+C to stop.
set -e
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  echo "Run ./setup.sh first." >&2
  exit 1
fi
source .venv/bin/activate
exec python bot.py
