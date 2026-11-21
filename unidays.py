from playwright.async_api import async_playwright
from .base import BaseProvider


class UniDaysProvider(BaseProvider):
    def __init__(self):
        super().__init__("unidays", "https://www.myunidays.com/en-US/login")

    async def fetch_codes(self, email: str, password: str) -> str:
        # NOTE: UniDays frequently changes its DOM and runs bot detection
        # (CAPTCHA, rate limiting, device fingerprinting). The selectors below
        # are placeholders and must be reverse-engineered against the live site
        # before this works reliably. See README.md for details.
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            try:
                await page.goto(self.login_url, wait_until="networkidle", timeout=30000)

                # TODO: replace these selectors with the real UniDays ones
                await page.fill('input[name="email"]', email, timeout=10000)
                await page.fill('input[name="password"]', password, timeout=10000)
                await page.click('button[type="submit"]', timeout=10000)
                await page.wait_for_timeout(4000)

                # Navigate to the offers/codes page and extract visible codes
                codes = await page.evaluate(
                    """() => {
                    // TODO: replace with real UniDays code-element selectors
                    const els = document.querySelectorAll('.discount-code, [data-code]');
                    return Array.from(els).map(e => e.innerText || e.getAttribute('data-code')).filter(Boolean);
                    }"""
                )

                if not codes:
                    return "No codes found. Selectors need to be updated for the current UniDays site."
                return "\n".join(f"- {c}" for c in codes)
            except Exception as e:
                return f"Error fetching UniDays codes: {e}"
            finally:
                await browser.close()
