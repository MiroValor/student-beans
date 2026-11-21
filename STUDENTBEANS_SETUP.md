# Setting up Student Beans properly

Student Beans (now operated by Pion) is harder to automate than a typical site because:

1. **Auth happens on a separate domain** — `accounts.studentbeans.com`, not `www.studentbeans.com`.
2. **You need a verified student account** before any discount codes are visible. If your account isn't verified, logging in won't show codes.
3. **Codes are per-brand, not one master list.** There's no single "all codes" page — each brand offer has its own code.
4. **Bot detection is active.** Expect Cloudflare/CAPTCHA, rate limiting, and device fingerprinting.

This guide walks you through finding the real selectors and getting the provider working.

---

## Step 1: Get a verified Student Beans account

Create an account at https://www.studentbeans.com and complete student verification (upload student ID / use your .edu email). Without verification, no codes will appear after login, and the bot will report "no codes found."

Test manually: log in on a real browser and confirm you can see codes before trying to automate.

---

## Step 2: Launch a visible browser to inspect

Run the bot with a headed browser so you can watch what happens and copy the real selectors:

```
!codes headed
```

This opens a real Chromium window instead of a headless one. Watch the login flow:

- Does it load `accounts.studentbeans.com/us/authorisation/sign-in`?
- Do the email/password fields accept input?
- Does a CAPTCHA or "verify you're human" box appear?
- After login, where do codes show up?

If a CAPTCHA appears, you'll need to solve it manually in the headed window, then the bot can continue from that session — though the current provider closes the browser after each run, so full CAPTCHA handling isn't built in yet.

---

## Step 3: Find the real login selectors

In the headed browser, open DevTools (**F12** or right-click → Inspect) and go to the **Elements** tab. Find:

1. **Email input** — look for `<input type="email">` or a field with `name="email"`, `id="email"`, or a placeholder like "Email address". Copy its CSS selector.
   - Example: `input[name="email"]`, `#email`, `.login-email-input`
2. **Password input** — same approach for the password field.
3. **Submit button** — the "Sign in" / "Log in" button. Look for `button[type="submit"]` or a button with text "Sign in".

Also check the **Network** tab while logging in — you may see a POST request to an API endpoint (e.g. `/api/v1/auth/login`). If the site uses an API instead of a form post, you could bypass the browser entirely and call that API directly (faster and less likely to be blocked).

---

## Step 4: Find the code selectors

After logging in, navigate to wherever your codes are displayed (your account dashboard, "My offers", or a brand's Student Beans page). Inspect a visible discount code and copy its selector:

- A code might look like `<span class="discount-code">SAVE15</span>` or `<div data-code="STUDENT20">...</div>`.
- Common patterns: `.discount-code`, `[data-code]`, `.offer-code`, `.voucher-code`, `.promo-code`.

Also look for **"Reveal code" / "Get code" buttons** — some codes are hidden until clicked. The provider already tries clicking buttons containing "Reveal" or "Get code".

---

## Step 5: Update `providers/studentbeans.py`

Edit the provider and replace the `TODO` placeholder selectors with the real ones you found:

```python
# Login
await page.wait_for_selector('input[name="email"]', timeout=10000)
await page.fill('input[name="email"]', email)
await page.fill('input[name="password"]', password)
await page.click('button[type="submit"]')

# Codes (after login)
codes = await page.evaluate(
    """() => {
    const els = document.querySelectorAll('YOUR_REAL_CODE_SELECTOR');
    return Array.from(els).map(e => e.innerText.trim()).filter(Boolean);
    }"""
)
```

If you found a login API endpoint in the Network tab, you can replace the whole Playwright login block with a direct `requests.post()` / `httpx` call — much more reliable than browser automation.

---

## Step 6: Test with your own account

```
!add studentbeans your@email.com yourpassword
!codes
```

If it works, you'll get a DM with your codes. If not, common issues:

| Symptom | Likely cause |
|---------|--------------|
| "Timeout" | Slow response / rate limit — wait and retry |
| "Logged in but no codes found" | Account not verified, or code selector is wrong |
| CAPTCHA/verification wall | Bot detection — use headed mode to solve manually |
| "Invalid email or password" | Wrong credentials, or the login selector is wrong |

---

## Troubleshooting tips

- **Run headless=False during development.** You can't discover selectors in a headless browser you can't see.
- **Add `await page.screenshot(path="debug.png")`** anywhere in `fetch_codes` to see what the browser is looking at.
- **Student Beans changes its site often.** Selectors that work today may break next week. Expect to re-inspect periodically.
- **Terms of Service:** Automating login may violate Student Beans' ToS. Use only on your own verified account.
