import os
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from .base import BaseProvider


class StudentBeansProvider(BaseProvider):
    def __init__(self, headless: bool = True):
        super().__init__("studentbeans", "https://accounts.studentbeans.com/us/authorisation/sign-in")
        self.headless = headless

    def _proxy_config(self):
        """Build Playwright proxy config from Railway env vars."""
        host = os.getenv("PROXY_HOST")
        port = os.getenv("PROXY_PORT")
        user = os.getenv("PROXY_USER")
        pwd = os.getenv("PROXY_PASS")
        if not host or not port:
            return None
        proxy = {"server": f"http://{host}:{port}"}
        if user and pwd:
            proxy["username"] = user
            proxy["password"] = pwd
        return proxy

    async def fetch_codes(self, email: str, password: str) -> str:
        # NOTE: Student Beans frequently changes its DOM and runs bot detection
        # (CAPTCHA, rate limiting, device fingerprinting). The selectors below
        # are placeholders and must be reverse-engineered against the live site
        # before this works reliably.
        async with async_playwright() as p:
            proxy = self._proxy_config()
            launch_kwargs = {"headless": self.headless}
            if proxy:
                launch_kwargs["proxy"] = proxy

            browser = await p.chromium.launch(**launch_kwargs)
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            )
            page = await context.new_page()
            try:
                await page.goto(self.login_url, wait_until="networkidle", timeout=30000)

                # TODO: replace these selectors with the real Student Beans ones
                await page.fill('input[name="email"]', email, timeout=10000)
                await page.fill('input[name="password"]', password, timeout=10000)
                await page.click('button[type="submit"]', timeout=10000)
                await page.wait_for_timeout(4000)

                # Navigate to the offers/codes page and extract visible codes
                codes = await page.evaluate(
                    """() => {
                    // TODO: replace with real Student Beans code-element selectors
                    const els = document.querySelectorAll('.discount-code, [data-code]');
                    return Array.from(els).map(e => e.innerText || e.getAttribute('data-code')).filter(Boolean);
                    }"""
                )

                if not codes:
                    return "No codes found. Selectors need to be updated for the current Student Beans site."
                return "\n".join(f"- {c}" for c in codes)
            except Exception as e:
                return f"Error fetching Student Beans codes: {e}"
            finally:
                await browser.close()
