import asyncio, sys
from playwright.async_api import async_playwright
PAGES = sys.argv[1:]
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        errors = []
        for spec in PAGES:
            path, w = (spec.split("@") + ["1280"])[:2]
            pg = await b.new_page(viewport={"width": int(w), "height": 900})
            pg.on("console", lambda m: errors.append(f"{m.type}: {m.text}") if m.type in ("error",) else None)
            pg.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
            await pg.goto("http://localhost:3000" + path, wait_until="networkidle")
            await pg.wait_for_timeout(500)
            name = path.strip("/").replace("/", "_").replace("?", "_").replace("=", "_") or "home"
            await pg.screenshot(path=f"shots/{name}_{w}.png", full_page=True)
            await pg.close()
        await b.close()
        print("\n".join(errors) or "no console errors")
asyncio.run(main())
