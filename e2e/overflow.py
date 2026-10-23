"""Checks every main page at phone width for horizontal overflow and console errors."""
import asyncio
import sys

from playwright.async_api import async_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3000"
PAGES = ["/", "/schemes", "/schemes/central-sector-scholarship-college-university", "/eligibility", "/rights", "/rights/art-21",
         "/guides/guide-arrest", "/services", "/services/svc-rti", "/complaints", "/ask", "/dashboard", "/about", "/login", "/admin", "/offices", "/guides/guide-fir-refusal", "/complaints?draft=fir"]
JS = """() => { const W = document.documentElement.clientWidth;
  const bad = [...document.querySelectorAll('body *')].filter(e => e.getBoundingClientRect().right > W + 1)
    .slice(0, 3).map(e => e.tagName + '.' + (e.className || '').toString().slice(0, 70));
  return [document.documentElement.scrollWidth, W, bad]; }"""


async def main():
    fails = 0
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 390, "height": 800})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        for u in PAGES:
            await pg.goto(BASE + u, wait_until="networkidle")
            sw, w, bad = await pg.evaluate(JS)
            ok = sw <= w
            fails += not ok
            print(("OK  " if ok else "FAIL"), u, sw, w, "" if ok else bad)
        print("page errors:", errs or "none")
        await b.close()
    sys.exit(1 if fails or errs else 0)

asyncio.run(main())
