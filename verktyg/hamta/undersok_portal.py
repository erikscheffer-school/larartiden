#!/usr/bin/env python3
"""Undersöker hur en mötesportal är uppbyggd, som underlag för portalspecifika skript.

Kör från repots rot:  python3 verktyg/hamta/undersok_portal.py
Läser arbete/granskning/portalprov.json:  [{"kommun": "leksand", "nyckel": "netpublicator"}, ...]

För varje prov går skriptet från kommunens webbplats till första sidan vars adress
innehåller nyckeln, och sedan ett steg till (första länken som ser ut som ett möte).
För varje sida sparas länkarna och alla dataanrop (XHR/fetch) med svarens början, i
arbete/granskning/portaler/<kommun>.txt.
"""
import asyncio
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from gemensamt import ROOT, USER_AGENT, kommuner  # noqa: E402
from portaler import LANKAR_JS, NAVIGERA  # noqa: E402

PROV = ROOT / "arbete" / "granskning" / "portalprov.json"
UT = ROOT / "arbete" / "granskning" / "portaler"
MOTE = re.compile(r"möte|mote|meeting|sammantr|kallelse|protokoll|agenda|fullmäktige|kommunstyrelse|20\d\d-\d\d-\d\d", re.I)


async def dumpa(page, url, rader):
    anrop = []

    async def svar(resp):
        req = resp.request
        if req.resource_type in ("xhr", "fetch", "document"):
            typ = resp.headers.get("content-type", "")
            kropp = ""
            if "json" in typ or "xml" in typ or "text/plain" in typ:
                try:
                    kropp = (await resp.text())[:1500]
                except Exception:
                    pass
            anrop.append(f"{req.method} {resp.status} {req.resource_type} {typ[:40]} {req.url[:250]}"
                         + (f"\n      {kropp}" if kropp else "")
                         + (f"\n      POST: {(req.post_data or '')[:300]}" if req.method == "POST" else ""))

    page.on("response", svar)
    await page.goto(url, wait_until="networkidle", timeout=40_000)
    await page.wait_for_timeout(2000)
    page.remove_listener("response", svar)
    lankar = await page.eval_on_selector_all("a[href]", LANKAR_JS)
    knappar = await page.eval_on_selector_all(
        "button, [onclick], [role=button]",
        "els => els.slice(0, 40).map(e => (e.innerText || e.getAttribute('aria-label') || '').trim().slice(0, 80))")
    html = await page.content()
    rader += [f"\n######## SIDA: {url}", f"Titel: {await page.title()}", "", "## Dataanrop"] + anrop
    rader += ["", "## Länkar (href | text | sammanhang)"]
    rader += [f"{h} | {t[:80]} | {' '.join(s.split())[:120]}" for h, t, s in lankar[:150]]
    rader += ["", "## Knappar", *[k for k in knappar if k], "", "## HTML (början av body)",
              re.sub(r"\s+", " ", html[html.find("<body"):])[:4000]]
    return lankar


async def prov(context, kommun, nyckel, start=None):
    page = await context.new_page()
    rader = [f"Kommun: {kommun['k']}  nyckel: {nyckel}"]
    besokta, ko = set(), [kommun["w"]]
    mal = start
    try:
        # Leta upp portalen: bredden först bland navigeringslänkar, högst 25 sidor.
        while ko and len(besokta) < 25 and not mal:
            url = ko.pop(0)
            if url in besokta:
                continue
            besokta.add(url)
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=25_000)
                await page.wait_for_timeout(1000)
                lankar = await page.eval_on_selector_all("a[href]", LANKAR_JS)
            except Exception:
                continue
            for h, t, _ in lankar:
                if nyckel in h.lower():
                    mal = h
                    rader.append(f"Portalen hittades via {url}: {h} ({t})")
                    break
                if NAVIGERA.search(f"{h} {t}") and h.startswith("http") and h not in besokta:
                    ko.append(h)
        if not mal:
            rader.append("Portalen hittades inte.")
            return rader
        lankar = await dumpa(page, mal, rader)
        # Två steg till: första länken som ser ut som ett möte, och därifrån en gång till.
        for _ in range(2):
            nasta = next((h for h, t, s in lankar if MOTE.search(f"{h} {t} {s}") and h != page.url
                          and h.startswith("http") and not re.search(r"\.pdf|download|elected", h, re.I)), None)
            if not nasta:
                break
            lankar = await dumpa(page, nasta, rader)
    except Exception as e:
        rader.append(f"FEL: {type(e).__name__}: {e}")
    finally:
        await page.close()
    return rader


async def main():
    from playwright.async_api import async_playwright
    data = {k["id"]: k for k in kommuner()}
    prover = json.loads(PROV.read_text(encoding="utf-8"))
    UT.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(user_agent=USER_AGENT, locale="sv-SE")
        for pr in prover:
            rader = await prov(context, data[pr["kommun"]], pr.get("nyckel", ""), pr.get("start"))
            (UT / f"{pr['kommun']}-{pr.get('nyckel') or 'start'}.txt").write_text("\n".join(rader) + "\n", encoding="utf-8")
            print(f"{pr['kommun']}: {rader[1] if len(rader) > 1 else ''}"[:200], flush=True)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
