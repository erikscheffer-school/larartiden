"""Prov 2: följ mötessidornas länkar till externa dokumentplattformar (OpenGov, documentweb,
forum.norrtalje.se m.fl.) två steg och spara alla länkar, dataanrop och portalspår i HTML:en."""
import asyncio
import re

PROV = {
    # namn: (startadress, regex för länkar att följa i steg 1, regex i steg 2)
    "hofors": ("https://www.hofors.se/kommun--politik/politik/kallelser.html", r"\.pdf|download|kommunfullm", r"\.pdf"),
    "norberg": ("https://norberg.se/kommun--politik/insyn-och-paverkan/protokoll-och-handlingar.html",
                r"opengov|360online", r"kommunfullm|kommunstyr|meeting|2026"),
    "klippan": ("https://documentweb.klippan.se/?folderId=9e3cb028-78a2-4826-8390-c98e49219221", r"2026|kallelse|protokoll", r"\.pdf|download|file"),
    "norrtalje": ("https://www.norrtalje.se/info/kommun-och-politik/handlingar-och-protokoll/",
                  r"forum\.norrtalje\.se.*", r"2026|kallelse|protokoll|meeting"),
    "kumla": ("https://www.kumla.se/kommun-och-politik/demokrati-och-insyn/moten-handlingar-och-protokoll.html",
              r"kommunfullmaktige-och-kommunstyrelsen", r"\.pdf|download|2026|opengov|netpublicator"),
    "sollentuna": ("https://www.sollentuna.se/kommun--politik/politik-och-demokrati/dagordningar-och-handlingar/",
                   r"kommunfullm|kommunstyr|handlingar|sammantr", r"\.pdf|download|2026"),
    "karlstad": ("https://karlstad.se/kommun-och-politik/kommunens-organisation/kommunfullmaktige", r"#--chn-[^|]*\| 2026-10", r"."),
    "sundbyberg": ("https://www.sundbyberg.se/", r"opengov|360online", r"kommunfullm|kommunstyr|meeting|2026"),
}
UT = "arbete/granskning/prov/ut"
UA = "larartiden-hamtning/1.0 (+https://github.com/erikscheffer-school/larartiden)"
SPAR = re.compile(r"r\d{8}|netpublicator[^\"' ]{0,80}|opengov[^\"' ]{0,120}|360online[^\"' ]{0,120}|documentweb[^\"' ]{0,80}"
                  r"|forum\.norrtalje[^\"' ]{0,100}|data-[a-z-]*chn[^ >]{0,80}|appresource/[^\"' ]{0,120}", re.I)


async def sida(page, url, rader, anrop):
    start = len(anrop)
    rader.append(f"\n######## {url}")
    try:
        await page.goto(url, wait_until="networkidle", timeout=40_000)
    except Exception as e:
        rader.append(f"goto: {type(e).__name__}")
    await page.wait_for_timeout(2500)
    try:
        html = await page.content()
        rader.append("Titel: " + await page.title())
        rader.append("Spår i HTML: " + " ; ".join(sorted(set(m.group(0) for m in SPAR.finditer(html)))[:40]))
        text = await page.inner_text("body")
        rader.append("Text: " + " ".join(text.split())[:2500])
        lankar = await page.eval_on_selector_all("a[href]", "els => els.map(e => e.href + ' | ' + (e.innerText||e.title||'').trim().replace(/\\s+/g,' ').slice(0,100))")
    except Exception as e:
        rader.append(f"läsfel {type(e).__name__}")
        lankar = []
    rader.append("Länkar:")
    rader += [f"  {l}" for l in lankar if not re.search(r"facebook|twitter|linkedin|readspeaker|mailto", l)][:250]
    rader.append("Dataanrop:")
    rader += anrop[start:][:30]
    return lankar


async def en(context, namn, start, steg1, steg2):
    page = await context.new_page()
    anrop = []

    async def svar(resp):
        r = resp.request
        if r.resource_type in ("xhr", "fetch"):
            kropp = ""
            try:
                kropp = (await resp.text())[:1500].replace("\n", " ")
            except Exception:
                pass
            anrop.append(f"  {r.method} {resp.status} {r.url[:300]}\n      {kropp}")
    page.on("response", lambda r: asyncio.ensure_future(svar(r)))
    rader = [f"# {namn}"]
    l1 = await sida(page, start, rader, anrop)
    foljda = [l.split(" | ")[0] for l in l1 if re.search(steg1, l, re.I)][:3]
    for u in dict.fromkeys(foljda):
        if "#--chn-" in u:  # Netpublicator-modul: klicka i stället
            try:
                await page.goto(start, wait_until="networkidle", timeout=40_000)
                n0 = len(anrop)
                await page.locator(f"a[href$='{u.split('#')[1]}']").first.click(force=True, timeout=8000)
                await page.wait_for_timeout(4000)
                rader.append(f"\n## Klick på {u}\nLänkar efter klick:")
                rader += [f"  {l}" for l in await page.eval_on_selector_all(
                    "a[href]", "els => els.map(e => e.href + ' | ' + (e.innerText||'').trim().slice(0,100))") if l not in l1][:80]
                rader += ["Dataanrop efter klick:"] + anrop[n0:][:20]
            except Exception as e:
                rader.append(f"klick: {type(e).__name__} {str(e)[:200]}")
            continue
        l2 = await sida(page, u, rader, anrop)
        for u2 in list(dict.fromkeys(l.split(" | ")[0] for l in l2 if re.search(steg2, l, re.I)))[:2]:
            if not re.search(r"\.pdf|download", u2, re.I):
                await sida(page, u2, rader, anrop)
    await page.close()
    open(f"{UT}/{namn}.txt", "w", encoding="utf-8").write("\n".join(rader) + "\n")
    print(namn, "klar", flush=True)


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch()
        c = await b.new_context(user_agent=UA, locale="sv-SE")
        await asyncio.gather(*(en(c, n, *v) for n, v in PROV.items()))
        await b.close()

asyncio.run(main())
