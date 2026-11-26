import os
import sys
from abc import ABC, abstractmethod


def _env_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None or val.strip() == "":
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


def proxy_config():
    """Optional proxy from PROXY_HOST / PROXY_PORT / PROXY_USER / PROXY_PASS."""
    host = os.getenv("PROXY_HOST")
    port = os.getenv("PROXY_PORT")
    if not host or not port:
        return None
    proxy = {"server": f"http://{host}:{port}"}
    user = os.getenv("PROXY_USER")
    pwd = os.getenv("PROXY_PASS")
    if user and pwd:
        proxy["username"] = user
        proxy["password"] = pwd
    return proxy


async def launch_browser(playwright, headless: bool = True, name: str = "browser"):
    """Launch Chrome (or the bundled Chromium as a fallback).

    By default this uses the installed Google Chrome (BROWSER_CHANNEL=chrome),
    which looks far more like a real user to bot detection than Playwright's
    bundled Chromium. If Chrome isn't installed, it falls back to the bundled
    Chromium. Set BROWSER_CHANNEL= (empty) to always use the bundled Chromium.
    """
    if not headless and sys.platform.startswith("linux") and not os.getenv("DISPLAY"):
        # A server has no screen to show a window on.
        print(f"[{name}] No display available; running headless.")
        headless = True
    kwargs = {"headless": headless}
    proxy = proxy_config()
    if proxy:
        kwargs["proxy"] = proxy

    channel = os.getenv("BROWSER_CHANNEL", "chrome").strip()
    if channel:
        try:
            return await playwright.chromium.launch(channel=channel, **kwargs)
        except Exception as e:
            print(f"[{name}] Could not launch '{channel}' ({e}); using bundled Chromium.")
    return await playwright.chromium.launch(**kwargs)


class BaseProvider(ABC):
    def __init__(self, name: str, login_url: str):
        self.name = name
        self.login_url = login_url
        # HEADLESS=false in .env shows the browser window by default.
        self.headless = _env_bool("HEADLESS", True)

    async def launch_browser(self, playwright):
        return await launch_browser(playwright, headless=self.headless, name=self.name)

    @abstractmethod
    async def fetch_codes(self, email: str, password: str) -> str:
        """Return a human-readable string of available discount codes."""
        pass
