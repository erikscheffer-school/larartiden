"""Prov: hur visar mötessidorna sina handlingar? Klickar på datumlänkar (Netpublicator-modul i
Sitevision, dragspel) och sparar text, länkar och dataanrop före och efter klicket."""
import asyncio
import re

SIDOR = {
    "karlstad": "https://karlstad.se/kommun-och-politik/kommunens-organisation/kommunfullmaktige",
    "arjang": "https://www.arjang.se/kommunalservice/startsida/kommunochpolitik/motenhandlingarochprotokoll/kallelserochprotokoll/kommunstyrelsen.11989.html",
    "hofors": "https://www.hofors.se/kommun--politik/politik/kallelser.html",
    "norberg": "https://norberg.se/kommun--politik/insyn-och-paverkan/protokoll-och-handlingar.html",
    "kumla": "https://www.kumla.se/kommun-och-politik/demokrati-och-insyn/moten-handlingar-och-protokoll.html",
    "klippan": "https://www.klippan.se/kommun--politik/moten-handlingar--protokoll/kallelser-och-protokoll",
    "norrtalje": "https://www.norrtalje.se/info/kommun-och-politik/handlingar-och-protokoll/",
    "sollentuna": "https://www.sollentuna.se/kommun--politik/politik-och-demokrati/dagordningar-och-handlingar/",
}
UT = "arbete/granskning/prov/ut"
UA = "larartiden-hamtning/1.0 (+https://github.com/erikscheffer-school/larartiden)"


async def en(context, namn, url):
    page = await context.new_page()
    anrop = []

    async def svar(resp):
        r = resp.request
        if r.resource_type in ("xhr", "fetch", "document"):
            kropp = ""
            try:
                if any(t in resp.headers.get("content-type", "") for t in ("json", "html", "xml")):
                    kropp = (await resp.text())[:1200].replace("\n", " ")
            except Exception:
                pass
            anrop.append(f"{r.method} {resp.status} {r.resource_type} {r.url[:300]}\n    {kropp}")
    page.on("response", lambda r: asyncio.ensure_future(svar(r)))
    rader = [f"# {namn} {url}"]
    try:
        await page.goto(url, wait_until="networkidle", timeout=40_000)
        await page.wait_for_timeout(2000)
        rader += ["## Titel: " + await page.title(), "## Text (början)", (await page.inner_text("main") if await page.query_selector("main") else await page.inner_text("body"))[:4000]]
        lankar = await page.eval_on_selector_all("main a[href], #content a[href], a[href*='download'], a[href*='.pdf'], a[href*='chn']",
                                                 "els => els.map(e => e.href + ' | ' + (e.innerText||'').trim().slice(0,100))")
        rader += ["## Länkar i innehållet"] + lankar[:150]
        knappar = await page.eval_on_selector_all("main button, main [aria-expanded], main summary",
                                                  "els => els.map(e => (e.tagName + ' ' + (e.innerText||'').trim().slice(0,80)))")
        rader += ["## Knappar/dragspel"] + knappar[:60]
        anrop_fore = len(anrop)
        # Klicka på de tre första datumlänkarna/dragspelen som nämner 2026-1x eller oktober/november.
        mal = page.locator("main a, main button, main summary, main [aria-expanded]").filter(
            has_text=re.compile(r"2026-1[01]|2026-09|oktober|november|kommunfullmäktige|kommunstyrelsen", re.I))
        n = min(await mal.count(), 3)
        for i in range(n):
            try:
                el = mal.nth(i)
                rader.append(f"## Klick {i}: {(await el.inner_text())[:80]}")
                await el.click(timeout=5000)
                await page.wait_for_timeout(2500)
            except Exception as e:
                rader.append(f"   klick misslyckades: {type(e).__name__}")
        efter = await page.eval_on_selector_all("main a[href], a[href*='download'], a[href*='.pdf'], a[href*='document']",
                                                "els => els.map(e => e.href + ' | ' + (e.innerText||'').trim().slice(0,100))")
        rader += ["## Länkar efter klick (nya)"] + [l for l in efter if l not in lankar][:120]
        rader += ["## Dataanrop före klick"] + anrop[:anrop_fore][:40] + ["## Dataanrop efter klick"] + anrop[anrop_fore:][:40]
    except Exception as e:
        rader.append(f"FEL {type(e).__name__}: {e}")
    await page.close()
    open(f"{UT}/{namn}.txt", "w", encoding="utf-8").write("\n".join(rader) + "\n")
    print(namn, "klar")


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch()
        c = await b.new_context(user_agent=UA, locale="sv-SE")
        await asyncio.gather(*(en(c, n, u) for n, u in SIDOR.items()))
        await b.close()

asyncio.run(main())
