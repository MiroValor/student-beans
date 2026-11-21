import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from .base import BaseProvider


class StudentBeansProvider(BaseProvider):
    def __init__(self, headless: bool = True):
        super().__init__("studentbeans", "https://accounts.studentbeans.com/us/authorisation/sign-in")
        self.headless = headless

    async def fetch_codes(self, email: str, password: str) -> str:
        """
        Log into Student Beans and return available discount codes.

        IMPORTANT: Student Beans (now Pion) requires a verified student account
        before any codes are visible, and each code is tied to a specific brand.
        There is no single "all codes" page. This provider logs in, then scans
        the account dashboard/offers page for visible codes.

        The CSS selectors below are placeholders. You MUST update them against
        the live site using browser DevTools (see STUDENTBEANS_SETUP.md).
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
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
                await page.goto(self.login_url, wait_until="domcontentloaded", timeout=30000)

                # ---------- LOGIN ----------
                # Selectors confirmed for accounts.studentbeans.com
                await page.wait_for_selector('#email', timeout=10000)
                await page.fill('#email', email)
                await page.fill('#password', password)
                await page.click('form button[type="submit"]')

                # Wait for navigation after login
                await page.wait_for_timeout(4000)

                # Detect login failure / CAPTCHA / verification wall
                body_text = await page.inner_text("body")
                if "captcha" in body_text.lower() or "verify" in body_text.lower():
                    return (
                        "⚠️ Student Beans showed a CAPTCHA or verification step. "
                        "Automated login is blocked here. Run with headless=False "
                        "to complete it manually in a visible browser."
                    )
                if "invalid" in body_text.lower() or "incorrect" in body_text.lower():
                    return "❌ Login failed — check your email and password."

                # ---------- FIND CODES ----------
                # Student Beans shows codes per brand, not one master list.
                # Login selectors are confirmed (#email, #password, form button[type="submit"]).
                # Code selectors still need to be discovered from your dashboard/offers page.
                # Navigate there in headed mode (!codes headed) and inspect a visible code element.
                codes = await page.evaluate(
                    """() => {
                    // TODO: replace with real Student Beans code selectors
                    const els = document.querySelectorAll(
                        '.discount-code, [data-code], .offer-code, .voucher-code'
                    );
                    return Array.from(els)
                        .map(e => (e.innerText || e.getAttribute('data-code') || '').trim())
                        .filter(Boolean);
                    }"""
                )

                # Also grab any visible "reveal code" buttons (often hidden until clicked)
                if not codes:
                    reveal_buttons = await page.query_selector_all(
                        'button:has-text("Reveal"), button:has-text("Get code"), a:has-text("Reveal")'
                    )
                    codes = []
                    for btn in reveal_buttons[:20]:  # limit so we don't hang
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
                        "⚠️ Logged in but no codes found. Your account may not be "
                        "verified yet, or the code selectors need updating. "
                        "Run with headless=False to inspect the dashboard."
                    )
                return "\n".join(f"- {c}" for c in codes)

            except PlaywrightTimeout:
                return "❌ Timeout — Student Beans took too long to respond (possibly rate-limited)."
            except Exception as e:
                return f"❌ Error fetching Student Beans codes: {e}"
            finally:
                await browser.close()
