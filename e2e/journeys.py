"""Browser end-to-end journeys (Playwright). Requires backend on :8000 and frontend on :3000.

  python e2e/journeys.py [base_url]
"""
import asyncio
import sys
import time

from playwright.async_api import async_playwright, expect

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3000"
results = []


def ok(name):
    results.append(("PASS", name))
    print("PASS", name)


async def journey(name, fn, browser):
    ctx = await browser.new_context(viewport={"width": 1280, "height": 900})
    page = await ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    try:
        await fn(page)
        if errors:
            raise AssertionError(f"page errors: {errors}")
        ok(name)
    except Exception as e:  # noqa: BLE001
        results.append(("FAIL", name))
        print("FAIL", name, "->", repr(e)[:400])
        await page.screenshot(path=f"e2e-fail-{name.split(':')[0]}.png", full_page=True)
    finally:
        await ctx.close()


async def a_student(page):  # Journey A
    await page.goto(f"{BASE}/eligibility")
    await page.get_by_label("Education & scholarships").check()
    await page.get_by_role("button", name="Continue").click()
    await page.get_by_label("Which state or Union Territory").select_option("Uttar Pradesh")
    assert await page.get_by_label("What is your age?").count() == 0  # only relevant questions are asked
    await page.get_by_label("What best describes").select_option("student")
    await page.get_by_label("What are you studying?").select_option("undergraduate_regular")
    await page.get_by_label("Approximate annual household income").select_option(label="₹2.5 – 4.5 lakh")
    await page.locator("#q-class12_top20").get_by_text("Yes", exact=True).click()
    await page.locator("#q-other_scholarship").get_by_text("No", exact=True).click()
    await page.get_by_role("button", name="See what may apply").click()
    first = page.locator("li.card").first
    await expect(first).to_contain_text("Central Sector Scheme of Scholarships")
    await expect(first).to_contain_text("Potential match")
    await expect(page.get_by_text("not an official eligibility decision")).to_be_visible()
    await first.get_by_role("link", name="Details, documents & steps").click()
    await expect(page.get_by_role("heading", name="Official sources")).to_be_visible()
    await expect(page.get_by_text("Verified against an official source")).to_be_visible()


async def b_article(page):  # Journey B
    await page.goto(f"{BASE}/ask")
    await page.get_by_label("Ask about schemes").fill("Explain Article 21 in simple words")
    await page.get_by_role("button", name="Send").click()
    await expect(page.get_by_text("Sources (")).to_be_visible(timeout=20000)
    await expect(page.locator("details").first).to_contain_text("Article 21")


async def c_service(page):  # Journey C
    await page.goto(f"{BASE}/services?q=passport")
    await page.get_by_role("link", name="Apply for or renew a passport").click()
    link = page.get_by_role("link", name="Go to official portal")
    assert (await link.get_attribute("href")).startswith("https://www.passportindia.gov.in")


async def d_complaint(page):  # Journey D
    await page.goto(f"{BASE}/guides/complaint-consumer")
    await expect(page.get_by_role("link", name="consumerhelpline.gov.in")).to_be_visible()
    await page.goto(f"{BASE}/complaints")
    await page.get_by_role("button", name="Prepare draft").click()
    await expect(page.get_by_text("Describe what happened in at least 20 characters")).to_be_visible()  # validation
    await page.get_by_label("Addressed to").fill("Customer care, ABC Electronics")
    await page.get_by_label("Subject").fill("Refund for defective phone")
    await page.get_by_label("What happened").fill("I bought a phone on 1 October 2026 and it stopped working after five days.")
    await page.get_by_label("What you are asking for").fill("Refund or replacement")
    await page.get_by_label("Your name").fill("Asha")
    await page.get_by_label("Contact for reply").fill("asha@example.com")
    await page.get_by_role("button", name="Prepare draft").click()
    await expect(page.get_by_text("This is a draft only. It has not been sent anywhere.")).to_be_visible()


async def fg_guest_hindi(page):  # Journeys F + G
    await page.goto(f"{BASE}/schemes")
    await expect(page.get_by_role("heading", name="Government Schemes")).to_be_visible()
    await page.get_by_label("Language").select_option("hi")
    await expect(page.get_by_role("heading", name="सरकारी योजनाएँ")).to_be_visible()
    await page.goto(f"{BASE}/search?q=" + "किसान")
    await expect(page.get_by_text("प्रधानमंत्री किसान सम्मान निधि").first).to_be_visible()


async def h_unverified(page):  # Journey H
    await page.goto(f"{BASE}/schemes/pm-kisan-samman-nidhi")
    await expect(page.get_by_role("alert").filter(has_text="Not yet verified")).to_be_visible()
    await expect(page.get_by_text("benefit amount has not been verified")).to_be_visible()


async def i_admin_denied(page):  # Journey I
    await page.goto(f"{BASE}/admin")
    await expect(page.get_by_role("heading", name="Restricted area")).to_be_visible()
    r = await page.request.get(f"{BASE}/api/admin/overview")
    assert r.status == 401


async def account(page):  # save + delete personal data
    email = f"e2e{int(time.time())}@test.in"
    await page.goto(f"{BASE}/login")
    await page.get_by_role("button", name="New here? Create an account").click()
    await page.get_by_label("Email").fill(email)
    await page.get_by_label("Password").fill("e2e-long-password")
    await page.get_by_role("button", name="Create account").click()
    await expect(page.get_by_role("heading", name="My dashboard")).to_be_visible()
    await page.goto(f"{BASE}/schemes/atal-pension-yojana")
    await page.get_by_role("button", name="Save").click()
    await expect(page.get_by_text("Saved to your dashboard.")).to_be_visible()
    await page.goto(f"{BASE}/dashboard")
    await expect(page.get_by_role("link", name="Atal Pension Yojana (APY)").first).to_be_visible()
    await page.get_by_role("button", name="Delete my account").click()
    await page.get_by_role("button", name="Yes, delete everything").click()
    await page.wait_for_url(f"{BASE}/")
    r = await page.request.post(f"{BASE}/api/auth/login", data={"email": email, "password": "e2e-long-password"}, headers={"x-requested-with": "jansaathi"})
    assert r.status == 401


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for name, fn in [("A: student scholarship match", a_student), ("B: article via assistant", b_article), ("C: service to official portal", c_service),
                         ("D: complaint draft", d_complaint), ("F+G: guest + Hindi search", fg_guest_hindi), ("H: unverified warning", h_unverified),
                         ("I: admin denied", i_admin_denied), ("Account: save, delete", account)]:
            await journey(name, fn, b)
        await b.close()
    fails = [n for s, n in results if s == "FAIL"]
    print(f"\n{len(results) - len(fails)}/{len(results)} journeys passed")
    sys.exit(1 if fails else 0)

asyncio.run(main())
