"""Sign in to iCloud once and save the session for the bot.

Run this on your Mac (it needs a screen):

    .venv/bin/python icloud_login.py

A Chrome window opens on icloud.com. Sign in (tick "Keep me signed in" and
approve the 2FA prompt), wait until you can see iCloud+, then come back here
and press Enter. The session is saved to icloud_session.json.

To use it on your server, DM the bot `!icloudlogin` with that file attached,
then delete the file from your Mac.
"""

import asyncio

from playwright.async_api import async_playwright

from icloud import ICLOUD_URL, SESSION_FILE, _write_session
from providers.base import launch_browser


async def main():
    async with async_playwright() as p:
        browser = await launch_browser(p, headless=False, name="icloud")
        context = await browser.new_context(locale="en-US")
        page = await context.new_page()
        await page.goto(ICLOUD_URL)
        print("Sign in to iCloud in the Chrome window.")
        print('Tick "Keep me signed in", approve the 2FA prompt, and wait until iCloud+ loads.')
        await asyncio.get_running_loop().run_in_executor(
            None, input, "Then press Enter here to save the session... "
        )
        _write_session(await context.storage_state())
        await browser.close()
    print(f"Saved {SESSION_FILE}")
    print("For the server: DM the bot `!icloudlogin` with this file attached, then delete it here.")


if __name__ == "__main__":
    asyncio.run(main())
