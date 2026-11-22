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

2. Run the one-time setup (macOS, uses the built-in `python3`):

```bash
cd ~/Documents/student-beans
./setup.sh
```

   This creates `.venv`, installs dependencies and Playwright's Chromium, and
   creates `.env` with a freshly generated `ENCRYPTION_KEY`.

3. Open `.env` and paste in your `DISCORD_TOKEN`.

4. Start the bot (Ctrl+C to stop):

```bash
./run.sh
```

The bot only runs while your Mac is awake and the terminal is open.

### Browser options (`.env`)

| Variable | Default | Effect |
|----------|---------|--------|
| `BROWSER_CHANNEL` | `chrome` | Uses your installed Google Chrome (less likely to trip bot detection). Falls back to bundled Chromium if Chrome isn't installed. Set empty to always use Chromium. |
| `HEADLESS` | `true` | Set `false` to always show the browser window. `!codes headed` does this for a single run. |
| `PROXY_HOST` / `PROXY_PORT` / `PROXY_USER` / `PROXY_PASS` | unset | Optional HTTP proxy. |

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
