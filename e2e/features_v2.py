"""Browser tests for the six requested features. External services (OpenStreetMap, Gemini
transcription) are mocked with Playwright routes so the tests are deterministic.

  python e2e/features_v2.py [base_url]
"""
import asyncio
import json
import sys
import time

from playwright.async_api import async_playwright, expect

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3000"
results = []

OVERPASS_FAKE = {"elements": [
    {"type": "node", "id": 1, "lat": 12.9700, "lon": 79.1560, "tags": {"name": "Common Service Centre - Katpadi", "office": "government"}},
    {"type": "way", "id": 2, "center": {"lat": 12.9780, "lon": 79.1400}, "tags": {"name": "Katpadi Taluk Office", "office": "government", "addr:city": "Vellore"}},
    {"type": "node", "id": 3, "lat": 12.9900, "lon": 79.1200, "tags": {"name": "Gandhinagar Post Office", "amenity": "post_office"}},
    {"type": "node", "id": 4, "lat": 12.9600, "lon": 79.1600, "tags": {"name": "e-Sevai Centre Gandhi Nagar", "office": "government"}},
]}


async def run(name, fn, browser, **ctx_kw):
    ctx = await browser.new_context(viewport={"width": 1280, "height": 900}, **ctx_kw)
    page = await ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    try:
        await fn(page, ctx)
        if errors:
            raise AssertionError(f"page errors: {errors}")
        results.append(("PASS", name)); print("PASS", name)
    except Exception as e:  # noqa: BLE001
        results.append(("FAIL", name)); print("FAIL", name, "->", repr(e)[:500])
        await page.screenshot(path=f"e2e-v2-fail-{name.split(':')[0]}.png", full_page=True)
    finally:
        await ctx.close()


async def f1_eligibility_brackets_and_category(page, ctx):
    await page.goto(f"{BASE}/eligibility?categories=entrepreneurship,education")
    await page.get_by_label("Approximate annual household income").select_option(label="₹2.5 – 4.5 lakh")
    cat = page.get_by_label("Social category (optional)")
    await expect(cat).to_be_visible()
    await expect(page.get_by_text("Your answer is not stored")).to_be_visible()
    await page.get_by_label("What is your age?").fill("30")
    await page.get_by_label("Gender (optional)").select_option("male")
    await cat.select_option("sc")
    await page.get_by_label("What best describes").select_option("self_employed")
    await page.get_by_role("button", name="See what may apply").click()
    card = page.locator("li.card", has_text="Stand-Up India")
    await expect(card).to_contain_text("woman and/or from an SC/ST community")
    await expect(card.locator("text=Possible disqualifiers").locator("..")).not_to_contain_text("SC/ST community")


async def f2_voice_fallback(page, ctx):
    # Simulate a browser without built-in speech recognition (e.g. Firefox) → records audio → Gemini route.
    await ctx.add_init_script("delete window.SpeechRecognition; delete window.webkitSpeechRecognition;")
    seen = {}

    async def transcribe(route):
        seen["body"] = json.loads(route.request.post_data)
        await route.fulfill(status=200, content_type="application/json", body=json.dumps({"text": "முதியோர் ஓய்வூதியம்", "lang": "ta"}))
    await page.route("**/api/assistant/transcribe", transcribe)
    await page.goto(f"{BASE}/ask")
    await page.get_by_label("Speak & answer in").select_option("ta")
    await expect(page.get_by_text("Tamil answers are AI-generated")).to_be_visible()
    mic = page.get_by_role("button", name="Speak (தமிழ்)")
    await mic.click()
    await expect(page.get_by_role("button", name="Stop recording")).to_be_visible()
    await page.wait_for_timeout(1500)
    await page.get_by_role("button", name="Stop recording").click()
    await expect(page.get_by_label("Ask about schemes, rights, certificates or complaints…")).to_have_value("முதியோர் ஓய்வூதியம்", timeout=10000)
    assert seen["body"]["lang"] == "ta" and seen["body"]["mime_type"].startswith("audio/") and len(seen["body"]["audio_base64"]) > 500
    await page.get_by_role("button", name="Send").click()
    await expect(page.get_by_text("Sources (")).to_be_visible(timeout=20000)
    await expect(page.locator("details").first).to_contain_text("Old Age Pension")


async def f2_voice_browser_api(page, ctx):
    # Simulate Chrome's speech recognition returning Hindi text.
    await ctx.add_init_script("""
      class FakeSR { constructor(){ this.lang=''; }
        start(){ window.__srLang = this.lang; setTimeout(()=>{ this.onresult && this.onresult({results:[Object.assign([{transcript:'वृद्धावस्था पेंशन'}],{isFinal:true})]}); this.onend && this.onend(); }, 300); }
        stop(){} abort(){} }
      window.webkitSpeechRecognition = FakeSR; window.SpeechRecognition = FakeSR;
    """)
    await page.goto(f"{BASE}/")
    await page.get_by_label("Voice language").select_option("hi")
    await page.get_by_role("button", name="Speak (हिन्दी)").click()
    await page.wait_for_url("**/search?q=*", timeout=10000)
    assert await page.evaluate("window.__srLang") == "hi-IN"
    await expect(page.get_by_text("Indira Gandhi National Old Age Pension", exact=False).first).to_be_visible()


async def f3_document_checklist(page, ctx):
    await page.goto(f"{BASE}/schemes/central-sector-scholarship-college-university")
    sec = page.locator("#docs").locator("..")
    await expect(page.get_by_role("heading", name="Document checklist — and where to get each one")).to_be_visible()
    await expect(sec.get_by_text("Where to get it:").first).to_be_visible()
    await expect(sec.get_by_role("link", name="Income certificate guide")).to_be_visible()
    await expect(sec.get_by_text("0 of 4 ready")).to_be_visible()
    await sec.get_by_role("button", name='Mark "Class 12 marksheet" as ready').click()
    await expect(sec.get_by_text("1 of 4 ready")).to_be_visible()
    await page.reload()
    await expect(page.locator("#docs").locator("..").get_by_text("1 of 4 ready")).to_be_visible()  # kept on device
    await sec.get_by_role("link", name="Income certificate guide").click()
    await expect(page.get_by_role("heading", name="Income certificate")).to_be_visible()


async def f4_tracker(page, ctx):
    email = f"trk{int(time.time())}@test.in"
    await page.goto(f"{BASE}/login")
    await page.get_by_role("button", name="New here? Create an account").click()
    await page.get_by_label("Email").fill(email)
    await page.get_by_label("Password").fill("tracker-long-password")
    await page.get_by_role("button", name="Create account").click()
    await expect(page.get_by_role("heading", name="My dashboard")).to_be_visible()
    await page.goto(f"{BASE}/schemes/atal-pension-yojana")
    await page.get_by_role("button", name="Save").click()
    await expect(page.get_by_text("Saved to your dashboard.")).to_be_visible()
    await page.goto(f"{BASE}/dashboard")
    card = page.locator("li.card", has_text="Atal Pension Yojana")
    await card.get_by_label("My status").select_option("applied")
    await expect(card.get_by_text("Status updated.")).to_be_visible()
    await card.get_by_label("Applied on").fill("2026-10-01")
    await card.get_by_label("Application / acknowledgement number").click()
    await expect(card.get_by_text("Application date saved.")).to_be_visible()
    await card.get_by_label("Application / acknowledgement number").fill("APY-778899")
    await card.get_by_label("Reminder date").click()
    await expect(card.get_by_text("Reference saved.")).to_be_visible()
    soon = time.strftime("%Y-%m-%d", time.localtime(time.time() + 3 * 86400))
    await card.get_by_label("Reminder date").fill(soon)
    await card.get_by_role("button", name="Add reminder").click()
    await expect(card.get_by_text("Reminder added.")).to_be_visible()
    await expect(page.get_by_role("heading", name="Coming up")).to_be_visible()
    async with page.expect_download() as dl:
        await card.get_by_role("button", name="Add to calendar").click()
    path = await (await dl.value).path()
    ics = open(path).read()
    assert "BEGIN:VEVENT" in ics and soon.replace("-", "") in ics and "not an official deadline" in ics
    await page.reload()
    card = page.locator("li.card", has_text="Atal Pension Yojana")
    await expect(card.get_by_label("Applied on")).to_have_value("2026-10-01")
    await expect(card.get_by_label("Application / acknowledgement number")).to_have_value("APY-778899")
    await page.get_by_role("button", name="Delete my account").click()
    await page.get_by_role("button", name="Yes, delete everything").click()
    await page.wait_for_url(f"{BASE}/")


async def f5_quick_cards_and_templates(page, ctx):
    await page.goto(f"{BASE}/rights")
    card = page.locator("article", has_text="Police refuse to register your FIR")
    await expect(card).to_contain_text("Superintendent of Police")
    await card.get_by_role("link", name="Letter to the SP").click()
    await expect(page.get_by_role("tab", name="FIR refused — letter to SP")).to_have_attribute("aria-selected", "true")
    await page.get_by_role("button", name="Prepare letter to SP").click()
    await expect(page.get_by_text("This is required.").first).to_be_visible()
    for label, val in [("District", "Vellore"), ("Police station that refused", "Katpadi"), ("Date of the incident", "1 October 2026"),
                       ("Place of the incident", "Katpadi bus stand"), ("What happened (facts only)", "Two men on a motorbike snatched my phone near the bus stand."),
                       ("How the police refused", "The duty officer refused to write my complaint."), ("Your name", "Asha"), ("Phone or email", "asha@example.com"),
                       ("Your address", "12 Main Road, Vellore")]:
        await page.get_by_label(label, exact=True).fill(val)
    await page.get_by_role("button", name="Prepare letter to SP").click()
    await expect(page.locator("pre")).to_contain_text("Section 173(4)")
    await page.goto(f"{BASE}/")
    consumer = page.locator("article", has_text="Defective product or bad service")
    await consumer.get_by_role("link", name="Letter to the company").click()
    await expect(page.get_by_role("tab", name="Consumer complaint to a company")).to_have_attribute("aria-selected", "true")
    await page.goto(f"{BASE}/guides/guide-fir-refusal")
    await expect(page.get_by_text("BNSS Section 173(4)", exact=False).first).to_be_visible()


async def f6_offices(page, ctx):
    await ctx.grant_permissions(["geolocation"], origin=BASE)
    await ctx.set_geolocation({"latitude": 12.9692, "longitude": 79.1559})
    calls = []

    async def fake_overpass(route):
        calls.append(route.request.post_data or "")
        await route.fulfill(status=200, content_type="application/json", body=json.dumps(OVERPASS_FAKE))
    await page.route("https://overpass-api.de/**", fake_overpass)
    await page.route("https://nominatim.openstreetmap.org/**", lambda r: r.fulfill(status=200, content_type="application/json",
                     body=json.dumps([{"lat": "12.9692", "lon": "79.1559", "display_name": "Katpadi, Vellore, Tamil Nadu, India"}])))
    await page.goto(f"{BASE}/offices")
    await page.get_by_role("button", name="Use my location").click()
    await expect(page.get_by_role("heading", name="4 places near your location")).to_be_visible(timeout=15000)
    first = page.locator("ul li.card").first
    await expect(first).to_contain_text("Common Service Centre - Katpadi")
    await expect(first).to_contain_text("Citizen service centre")
    await expect(page.locator("ul li.card", has_text="Katpadi Taluk Office")).to_contain_text("Taluk / Tehsil office")
    await page.get_by_role("button", name="CSC / e-Sevai · 2").click()
    await expect(page.locator("ul li.card")).to_have_count(2)
    href = await page.locator("ul li.card").first.get_by_role("link", name="Directions").get_attribute("href")
    assert "destination=12.97,79.156" in href
    assert "around:10000,12.9692,79.1559" in calls[0].replace("%2C", ",").replace("%3A", ":") or "around" in calls[0]
    # place search path
    await page.get_by_label("Town, area or PIN code").fill("632014")
    await page.get_by_role("button", name="Search").click()
    await expect(page.get_by_role("heading", name="places near Katpadi", exact=False)).to_be_visible(timeout=15000)


async def f6_offices_denied(page, ctx):
    await page.goto(f"{BASE}/offices")
    await page.get_by_role("button", name="Use my location").click()
    await expect(page.get_by_text("Type your town, area or PIN code instead", exact=False)).to_be_visible(timeout=15000)


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream"])
        await run("1: eligibility brackets + optional category", f1_eligibility_brackets_and_category, b)
        await run("2a: voice via Gemini fallback (Tamil)", f2_voice_fallback, b, permissions=["microphone"])
        await run("2b: voice via browser speech API (Hindi)", f2_voice_browser_api, b)
        await run("3: document checklist + where to get", f3_document_checklist, b)
        await run("4: application tracker + calendar", f4_tracker, b)
        await run("5: quick cards + FIR/consumer templates", f5_quick_cards_and_templates, b)
        await run("6a: office locator (location)", f6_offices, b)
        await run("6b: office locator (permission denied)", f6_offices_denied, b)
        await b.close()
    fails = [n for s, n in results if s == "FAIL"]
    print(f"\n{len(results) - len(fails)}/{len(results)} feature tests passed")
    sys.exit(1 if fails else 0)

asyncio.run(main())
