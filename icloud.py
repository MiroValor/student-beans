"""Create iCloud+ Hide My Email addresses using a saved, signed-in iCloud session.

The session (cookies) is created once by running `icloud_login.py` on a
computer with a screen, then either used there directly or sent to the bot
with `!icloudlogin` (attach the file) so a headless server can use it.

Creating an address uses the same requests the icloud.com web app makes:
  1. Open icloud.com, which calls /setup/ws/1/validate. Its response says
     whether the session is still signed in and gives the Hide My Email
     service URL for this account.
  2. POST <service>/v1/hme/generate  -> a new random address
  3. POST <service>/v1/hme/reserve   -> keep it, with a label
"""

import json
import os
from urllib.parse import urlsplit, parse_qsl, urlencode

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

from config import BASE_DIR
from providers.base import launch_browser

SESSION_FILE = BASE_DIR / "icloud_session.json"
ICLOUD_URL = "https://www.icloud.com/icloudplus/"


class ICloudError(Exception):
    """A problem worth showing to the user as-is."""


def has_session() -> bool:
    return SESSION_FILE.exists()


def save_session(data: bytes):
    """Validate and store a session file produced by icloud_login.py."""
    try:
        state = json.loads(data)
    except ValueError:
        raise ICloudError("That file isn't valid JSON. Send the `icloud_session.json` made by `icloud_login.py`.")
    cookies = state.get("cookies") if isinstance(state, dict) else None
    if not cookies or not any("icloud.com" in c.get("domain", "") for c in cookies):
        raise ICloudError("That file doesn't contain an iCloud sign-in. Run `icloud_login.py` again.")
    _write_session(state)


def _write_session(state: dict):
    tmp = SESSION_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state))
    os.chmod(tmp, 0o600)
    tmp.replace(SESSION_FILE)


_CREATE_JS = """async ({base, qs, label}) => {
  const post = async (path, body) => {
    const r = await fetch(`${base}${path}?${qs}`, {
      method: 'POST',
      credentials: 'include',
      headers: {'Content-Type': 'text/plain'},
      body: body ? JSON.stringify(body) : undefined,
    });
    let json = null;
    try { json = await r.json(); } catch (e) {}
    return {status: r.status, body: json};
  };
  const gen = await post('/v1/hme/generate');
  if (!gen.body || !gen.body.success) return {step: 'generate', ...gen};
  const hme = gen.body.result.hme;
  const res = await post('/v1/hme/reserve', {hme, label, note: ''});
  if (!res.body || !res.body.success) return {step: 'reserve', ...res};
  return {ok: true, hme};
}"""


def _error_text(result: dict) -> str:
    body = result.get("body") or {}
    err = body.get("error") or {}
    msg = (
        err.get("errorMessage")
        or body.get("errorMessage")
        or body.get("reason")
        or f"HTTP {result.get('status')}"
    )
    return f"iCloud refused to {result.get('step', 'create')} the address: {msg}"


async def create_hide_my_email(label: str) -> str:
    """Create and keep a new Hide My Email address. Returns the address."""
    if not has_session():
        raise ICloudError(
            "No iCloud sign-in saved yet. Run `python icloud_login.py` on your Mac, "
            "then DM me `!icloudlogin` with the `icloud_session.json` file attached."
        )

    async with async_playwright() as p:
        browser = await launch_browser(p, headless=True, name="icloud")
        try:
            context = await browser.new_context(storage_state=str(SESSION_FILE), locale="en-US")
            page = await context.new_page()

            try:
                async with page.expect_response(
                    lambda r: "/setup/ws/1/validate" in r.url, timeout=45000
                ) as info:
                    await page.goto(ICLOUD_URL, wait_until="domcontentloaded", timeout=45000)
                validate = await info.value
            except PlaywrightTimeout:
                raise ICloudError("icloud.com didn't load in time. Try again in a minute.")

            if validate.status != 200:
                raise ICloudError(
                    f"Your iCloud sign-in has expired (HTTP {validate.status}). "
                    "Run `python icloud_login.py` again and resend the file with `!icloudlogin`."
                )
            data = await validate.json()
            try:
                base = data["webservices"]["premiummailsettings"]["url"].rstrip("/")
                dsid = data["dsInfo"]["dsid"]
            except (KeyError, TypeError):
                raise ICloudError("This Apple account doesn't have Hide My Email (it needs iCloud+).")

            # Reuse the client parameters the web app itself sent, plus the account id.
            params = dict(parse_qsl(urlsplit(validate.url).query))
            params["dsid"] = dsid

            result = await page.evaluate(
                _CREATE_JS, {"base": base, "qs": urlencode(params), "label": label}
            )
            if not result.get("ok"):
                raise ICloudError(_error_text(result))

            # Save refreshed cookies so the sign-in lasts as long as possible.
            _write_session(await context.storage_state())
            return result["hme"]
        finally:
            await browser.close()
