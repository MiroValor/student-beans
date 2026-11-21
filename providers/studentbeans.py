import os
import random
import asyncio
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

    async def _apply_stealth(self, page):
        """Hide automation fingerprints so Student Beans doesn't detect Playwright."""
        await page.evaluateOnNewDocument("""() => {
            // Hide webdriver
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined, configurable: true });

            // Mock plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
                configurable: true
            });

            // Mock languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
                configurable: true
            });

            // Mock chrome
            window.chrome = { runtime: {} };

            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications'
                    ? Promise.resolve({ state: Notification.permission })
                    : originalQuery(parameters)
            );
        }""")

    async def fetch_codes(self, email: str, password: str) -> str:
        async with async_playwright() as p:
            proxy = self._proxy_config()
            launch_kwargs = {
                "headless": self.headless,
                "args": [
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-accelerated-2d-canvas",
                    "--disable-gpu",
                    "--window-size=1280,800",
                ],
            }
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
                locale="en-US",
                timezone_id="America/New_York",
                extra_http_headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                    "DNT": "1",
                },
            )
            page = await context.new_page()
            await self._apply_stealth(page)

            # Random delay before navigating
            await asyncio.sleep(random.uniform(1, 3))

            try:
                await page.goto(self.login_url, wait_until="networkidle", timeout=60000)

                await page.wait_for_selector('#email', timeout=20000)
                await page.fill('#email', email)
                await asyncio.sleep(random.uniform(0.5, 1.5))
                await page.fill('#password', password)
                await asyncio.sleep(random.uniform(0.5, 1.5))
                await page.click('form button[type="submit"]', timeout=20000)
                await page.wait_for_timeout(8000)

                body_text = await page.inner_text("body")
                if "captcha" in body_text.lower() or "verify" in body_text.lower():
                    return (
                        "⚠️ Student Beans showed a CAPTCHA or verification step. "
                        "Even with stealth + proxy, automated login may be blocked."
                    )
                if "invalid" in body_text.lower() or "incorrect" in body_text.lower():
                    return "❌ Login failed — check your email and password."

                # Wait a bit for page to fully load after redirect
                await page.wait_for_timeout(5000)

                codes = await page.evaluate(
                    """() => {
                    const els = document.querySelectorAll(
                        '.discount-code, [data-code], .offer-code, .voucher-code'
                    );
                    return Array.from(els)
                        .map(e => (e.innerText || e.getAttribute('data-code') || '').trim())
                        .filter(Boolean);
                    }"""
                )

                if not codes:
                    reveal_buttons = await page.query_selector_all(
                        'button:has-text("Reveal"), button:has-text("Get code"), a:has-text("Reveal")'
                    )
                    for btn in reveal_buttons[:20]:
                        try:
                            await btn.click(timeout=3000)
                            await page.wait_for_timeout(1000)
                        except Exception:
                            pass
                    codes = await page.evaluate(
                        """() => {
                        const els = document.querySelectorAll(
                            '.discount-code, [data-code], .offer-code, .voucher-code'
                        );
                        return Array.from(els)
                            .map(e => (e.innerText || e.getAttribute('data-code') || '').trim())
                            .filter(Boolean);
                        }"""
                    )

                if not codes:
                    return (
                        "⚠️ Logged in but no codes found. Account may not be verified, "
                        "or selectors need updating."
                    )
                return "\n".join(f"- {c}" for c in codes)

            except PlaywrightTimeout:
                return "❌ Timeout — Student Beans took too long to respond."
            except Exception as e:
                return f"❌ Error fetching Student Beans codes: {e}"
            finally:
                await browser.close()
