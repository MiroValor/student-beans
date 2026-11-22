#!/usr/bin/env bash
# Install everything and start the bot on a Debian/Ubuntu server.
# Safe to run on every boot: steps that are already done are quick no-ops.
#
# Needs DISCORD_TOKEN in the environment (or in .env).
set -e
cd "$(dirname "$0")"

# Use sudo only when not already root (fresh servers often run as root with no sudo).
if [ "$(id -u)" = "0" ]; then SUDO=""; else SUDO="sudo"; fi

echo "==> Installing system packages"
$SUDO apt-get update -qq
$SUDO apt-get install -y -qq python3 python3-venv python3-pip >/dev/null

echo "==> Setting up Python virtualenv"
[ -d .venv ] || python3 -m venv .venv
. .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo "==> Installing Chromium and its system libraries"
if [ -n "$SUDO" ]; then
  python -m playwright install chromium
  $SUDO "$(command -v python)" -m playwright install-deps chromium
else
  python -m playwright install --with-deps chromium
fi
$SUDO rm -rf /var/lib/apt/lists/*

# Create .env with a permanent encryption key on first run. The key must stay
# the same between restarts, or saved logins in credentials.json can't be read.
if [ ! -f .env ]; then
  KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
  printf 'ENCRYPTION_KEY=%s\nBROWSER_CHANNEL=\n' "$KEY" > .env
  chmod 600 .env
  echo "==> Created .env with a new ENCRYPTION_KEY"
fi

if [ -z "$DISCORD_TOKEN" ] && ! grep -q '^DISCORD_TOKEN=.\+' .env; then
  echo "ERROR: DISCORD_TOKEN is not set. Export it in the startup command." >&2
  exit 1
fi

echo "==> Starting bot"
exec python -u bot.py
