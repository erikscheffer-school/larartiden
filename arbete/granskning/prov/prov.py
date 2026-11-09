"""Prov 3: detaljer för fyra plattformar – Hofors fillistor (HTML), Karlstads Netpublicator-modul
(klick via JavaScript), Klippans DocumentWeb (klick på dokument), forum.norrtalje.se och ett
OpenGov-möte (Norberg)."""
import asyncio
import re

UT = "arbete/granskning/prov/ut"
UA = "larartiden-hamtning/1.0 (+https://github.com/erikscheffer-school/larartiden)"


def logga(rader, *t):
    rader.extend(str(x) for x in t)


async def ny(context):
    page = await context.new_page()
    anrop = []

    async def svar(resp):
        r = resp.request
        if r.resource_type in ("xhr", "fetch", "document") or "netpublicator" in r.url:
            kropp = ""
            try:
                if "pdf" not in resp.headers.get("content-type", ""):
                    kropp = (await resp.text())[:2000].replace("\n", " ")
            except Exception:
                pass
            anrop.append(f"  {r.method} {resp.status} {resp.headers.get('content-type', '')[:30]} {r.url[:300]}\n      {kropp}")
    page.on("response", lambda r: asyncio.ensure_future(svar(r)))
    return page, anrop


async def hofors(context, rader):
    page, _ = await ny(context)
    await page.goto("https://www.hofors.se/kommun--politik/politik/kallelser.html", wait_until="networkidle", timeout=45_000)
    html = await page.content()
    i = html.find("Kallelse Kommunfullmäktige 2026-11-10")
    logga(rader, "# Hofors HTML runt filnamnet", html[max(0, i - 2500):i + 800])


async def karlstad(context, rader):
    page, anrop = await ny(context)
    url = "https://karlstad.se/kommun-och-politik/kommunens-organisation/kommunfullmaktige"
    await page.goto(url, wait_until="networkidle", timeout=45_000)
    html = await page.content()
    for m in re.finditer(r"netpublicator", html, re.I):
        logga(rader, "HTML: " + html[max(0, m.start() - 300):m.start() + 300].replace("\n", " "))
        break
    scripts = [s for s in re.findall(r"<script[^>]*src=\"([^\"]+)\"", html) if "netpub" in s.lower()]
    logga(rader, "# Karlstad netpublicator-skript", *scripts)
    n0 = len(anrop)
    await page.evaluate("""() => { const a = [...document.querySelectorAll("a[href*='--chn-']")].find(e => e.innerText.includes('2026-10')); if (a) a.click(); }""")
    await page.wait_for_timeout(5000)
    logga(rader, "# Karlstad anrop efter klick", *anrop[n0:][:25])
    lankar = await page.eval_on_selector_all("a[href]", "els => els.map(e => e.href + ' | ' + (e.innerText||'').trim().slice(0,100))")
    logga(rader, "# Karlstad länkar med doc/chn efter klick", *[l for l in lankar if re.search(r"doc|chn|netpub|pdf", l, re.I)][:60])


async def klippan(context, rader):
    page, anrop = await ny(context)
    await page.goto("https://documentweb.klippan.se/?folderId=9e3cb028-78a2-4826-8390-c98e49219221", wait_until="networkidle", timeout=45_000)
    await page.wait_for_timeout(3000)
    txt = await page.inner_text("body")
    logga(rader, "# DocumentWeb text", " ".join(txt.split())[:2000])
    n0 = len(anrop)
    try:
        # öppna mappen för 2026 och klicka på första dokumentet
        await page.get_by_text(re.compile(r"kommunfullmäktige 2026", re.I)).first.click(timeout=8000)
        await page.wait_for_timeout(3000)
        logga(rader, "# Efter klick på 2026-mappen", " ".join((await page.inner_text("body")).split())[:2000])
        async with page.expect_popup(timeout=8000) as pop:
            await page.get_by_text(re.compile(r"Kallelse kommunfullmäktige 2026-1", re.I)).first.click(timeout=8000)
        p2 = await pop.value
        logga(rader, f"Popup: {p2.url}")
    except Exception as e:
        logga(rader, f"klick: {type(e).__name__} {str(e)[:200]}")
    await page.wait_for_timeout(3000)
    logga(rader, "# DocumentWeb anrop efter klick", *anrop[n0:][:25])
    lankar = await page.eval_on_selector_all("a[href]", "els => els.map(e => e.href + ' | ' + (e.innerText||'').trim().slice(0,100))")
    logga(rader, "# DocumentWeb länkar", *lankar[:60])


async def norrtalje(context, rader):
    page, anrop = await ny(context)
    for url in ["https://forum.norrtalje.se/committees", "https://forum.norrtalje.se/"]:
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=90_000)
            await page.wait_for_timeout(5000)
            logga(rader, f"# {url}: {await page.title()}", " ".join((await page.inner_text("body")).split())[:1500])
            lankar = await page.eval_on_selector_all("a[href]", "els => els.map(e => e.href + ' | ' + (e.innerText||'').trim().slice(0,100))")
            logga(rader, *lankar[:80])
            break
        except Exception as e:
            logga(rader, f"{url}: {type(e).__name__}")
    logga(rader, "# anrop", *anrop[:15])


async def opengov(context, rader):
    page, anrop = await ny(context)
    url = "https://opengov.360online.com/Meetings/NORBERG/Meetings/Details/278013"
    await page.goto(url, wait_until="networkidle", timeout=45_000)
    logga(rader, f"# OpenGov {url}", " ".join((await page.inner_text("body")).split())[:2000])
    lankar = await page.eval_on_selector_all("a[href]", "els => els.map(e => e.href + ' | ' + (e.innerText||'').trim().slice(0,120))")
    logga(rader, *lankar[:120])
    logga(rader, "# anrop", *anrop[:15])
    url = "https://opengov.360online.com/Meetings/NORBERG/Boards/Details/201479"
    await page.goto(url, wait_until="networkidle", timeout=45_000)
    lankar = await page.eval_on_selector_all("a[href]", "els => els.map(e => e.href + ' | ' + (e.innerText||'').trim().slice(0,120))")
    logga(rader, f"# OpenGov nämnd {url}", *lankar[:80])


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch()
        c = await b.new_context(user_agent=UA, locale="sv-SE", viewport={"width": 1400, "height": 3000})
        for namn, f in [("hofors3", hofors), ("karlstad3", karlstad), ("klippan3", klippan),
                        ("norrtalje3", norrtalje), ("opengov3", opengov)]:
            rader = []
            try:
                await f(c, rader)
            except Exception as e:
                rader.append(f"FEL {type(e).__name__}: {str(e)[:300]}")
            open(f"{UT}/{namn}.txt", "w", encoding="utf-8").write("\n".join(rader) + "\n")
            print(namn, "klar", flush=True)
        await b.close()

asyncio.run(main())
