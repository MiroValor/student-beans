# UniDays / Student Beans Discord Bot

A Discord bot that stores your UniDays and Student Beans logins and retrieves
discount codes directly in Discord DMs.

## How it works

1. You `!add <service> <email> <password>` in a DM to the bot.
2. Credentials are encrypted at rest (Fernet/AES-128 + HMAC) in `credentials.json`.
3. You `!codes` to log into each saved account and pull back the active codes.
4. `!remove <service>` deletes a stored account.

All commands are restricted to DMs so your passwords are never typed in a public
server channel. The bot also attempts to delete its own command messages after
running.

## Setup

1. Create a Discord bot and get its token from the [Discord Developer Portal](https://discord.com/developers/applications).
   - Enable the **Message Content Intent** in the bot settings.
   - Invite the bot to your server with the `bot` scope.

2. Clone/download this folder, then install dependencies:

```bash
cd unidays-discord-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

3. Generate an encryption key:

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

4. Copy `.env.example` to `.env` and fill in:

```
DISCORD_TOKEN=your_discord_bot_token_here
ENCRYPTION_KEY=the_key_from_above
```

5. Run the bot:

```bash
python3 bot.py
```

## Commands (DM only)

| Command | What it does |
|---------|--------------|
| `!add unidays <email> <password>` | Save your UniDays login |
| `!add studentbeans <email> <password>` | Save your Student Beans login |
| `!codes` | Fetch codes from all saved accounts |
| `!remove <service>` | Delete a saved account |
| `!list` | List supported services |
| `!help` | Show this help |

## ⚠️ Important limitations

**The login/code-fetching code currently needs site-specific reverse engineering.**

UniDays and Student Beans are modern web apps that:
- Frequently change their HTML/DOM selectors
- Run bot detection (CAPTCHA, rate limiting, device fingerprinting)
- May require email verification or 2FA

The provider classes (`providers/unidays.py`, `providers/studentbeans.py`) use
Playwright browser automation, but the CSS selectors inside `page.fill()`,
`page.click()`, and the code-extraction `page.evaluate()` are **placeholders**.
Before the bot will actually retrieve codes, you need to:

1. Inspect the live login page of each service (browser DevTools).
2. Replace the placeholder selectors with the real ones for email, password,
   submit button, and the code elements on the offers page.
3. Handle any CAPTCHA/verification flows those sites present.

**Terms of Service:** Automating login to these services may violate their
ToS. Use this bot only on your own accounts, at your own risk, and be prepared
to update selectors when the sites change.

## Security notes

- Passwords are encrypted on disk, but they are decrypted in memory while
  fetching codes.
- Only you should run this bot; anyone with access to the bot token and the
  encryption key can retrieve stored credentials.
- Do not commit `credentials.json`, `.env`, or your bot token to version control.
