#!/usr/bin/env python3
"""Steg 1b: leta handlingar i kommunernas mötesportaler med en riktig webbläsare.

Kör från repots rot:  python3 verktyg/hamta/portaler.py [--status 5] [--max-sidor 20]
Kräver Playwright:   pip install playwright && python -m playwright install --with-deps chromium

Många kommuner lägger kallelser, protokoll och budgethandlingar i mötesportaler
(Netpublicator, MeetingsPlus, Ciceron med flera) som sökmotorer inte indexerar och
som ofta kräver JavaScript. Skriptet utgår från kommunens webbplats, följer länkar om
politik, sammanträden och handlingar (även in i portalen) och samlar länkar till
dokument med länktext och sammanhang.

Länkarna läggs till i arbete/hamtning/sokresultat.json som träffar med sökning 3,
så att hamta_dokument.py hämtar och analyserar dem som vanligt. Vilken portal varje
kommun använder sparas i arbete/hamtning/portaler.json. Skriptet följer robots.txt,
besöker högst --max-sidor sidor per kommun och väntar mellan anropen till samma värd.
"""
import argparse
import asyncio
import heapq
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import urllib.robotparser

sys.path.insert(0, os.path.dirname(__file__))
from gemensamt import (HAMTNING, SOKRESULTAT, USER_AGENT, doman, idag,  # noqa: E402
                       kommuner, las_json, samma_doman, skriv_json)
from hamta_dokument import rang  # noqa: E402
from portalskript import Netpublicator, meetingsplus  # noqa: E402

NP_LASARE = re.compile(r"netpublicator\.com/reader/(r\d+)", re.I)

PORTALFIL = HAMTNING / "portaler.json"
MAX_LANKAR = 60  # högst så många dokumentlänkar per kommun sparas

# Kända portaler: delsträng i adressen -> namn.
PORTALTYPER = {
    "netpublicator": "Netpublicator", "meetingsplus": "MeetingsPlus", "ciceron": "Ciceron",
    "insynsverige": "Insyn Sverige", "lexkommun": "Lex", "edokmeetings": "eDok", "w3d3": "W3D3",
    "platina": "Platina", "evolution": "Evolution", "kommunkartan": "Kommunkartan",
    "public360": "Public 360", "p360": "Public 360", "politikerportal": "Politikerportal",
    "moten.": "Mötesportal", "sammantraden.": "Mötesportal", "handlingar.": "Mötesportal",
    "politik.": "Mötesportal", "dokument.": "Mötesportal",
}
NAVIGERA = re.compile(
    r"politik|protokoll|handling|kallelse|sammantr|möte|mote|fullmäktige|fullmaktige|"
    r"kommunstyrelse|nämnd|namnd|budget|ekonomi|anslagstavla|mål och|beslut|diarium|"
    r"utbildning|bildning|barn- och|meeting|agenda|reader", re.I)
UNDVIK = re.compile(
    r"mailto:|tel:|javascript:|facebook|instagram|linkedin|twitter|youtube|\.(jpe?g|png|gif|svg|zip|docx?|xlsx?|mp4)(\?|$)|"
    r"login|logga-in|cookie|/en/|english|jobb|lediga|evenemang|kalender|nyheter/\d{4}/\d{2}/\d{2}|"
    r"/elected/|/politician/|/party/|ledamoter|förtroendevalda", re.I)
DOKUMENT = re.compile(r"\.pdf(\?|$)|/download/|getdocument|getfile|documentid|/document/|/file/|fileid=|/dokument/", re.I)
BRA_DOK = re.compile(r"2027|budget|ramar|resursplan|flerårsplan|mål och|verksamhetsplan|"
                     r"fullmäktige|kommunstyrelse|utbildning|bildning|barn- och|kallelse|protokoll|handlingar", re.I)
PAUS = 2.0


def portaltyp(url):
    """Portaltyp efter adressen. Nycklar som slutar med punkt gäller bara början av värdnamnet
    (sammantraden.kommun.se), så att kommun-och-politik.html inte räknas som en portal."""
    u, host = url.lower(), urllib.parse.urlparse(url.lower()).netloc
    for nyckel, namn in PORTALTYPER.items():
        if (host.startswith(nyckel) or host.startswith("www." + nyckel)) if nyckel.endswith(".") else nyckel in u:
            return namn
    return None


class Robots:
    def __init__(self):
        self.cache = {}

    def tillats(self, url):
        p = urllib.parse.urlparse(url)
        bas = f"{p.scheme}://{p.netloc}"
        if bas not in self.cache:
            rp = urllib.robotparser.RobotFileParser()
            try:
                req = urllib.request.Request(bas + "/robots.txt", headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=10) as r:
                    rp.parse(r.read(200_000).decode("utf-8", "replace").splitlines())
            except Exception:
                rp = None
            self.cache[bas] = rp
        rp = self.cache[bas]
        return True if rp is None else rp.can_fetch(USER_AGENT, url)


LANKAR_JS = """els => els.map(e => {
  const box = e.closest('li, tr, article, section, .item, .meeting, div');
  return [e.href, (e.innerText || e.title || e.getAttribute('aria-label') || '').trim().slice(0, 200),
          box ? (box.innerText || '').trim().slice(0, 300) : ''];
})"""


async def genomsok(context, kommun, robots, max_sidor, senast, start=None, navigera=None, bara_egen=False):
    """Besöker kommunens webbplats och portal. Returnerar dokumentlänkar och portaltyper.

    start: lista med startadresser (standard kommunens startsida). navigera: regex som avgör
    vilka länkar som följs först. bara_egen: följ bara länkar på kommunens egen webbplats."""
    dom = doman(kommun["w"])
    navigera = navigera or NAVIGERA
    tillatna = {dom}
    kö = [(-i, i, s) for i, s in enumerate(reversed(start or [kommun["w"]]))]
    heapq.heapify(kö)
    besokta, dokument, portaler = set(), {}, set()
    adresser = set()  # adresser till portaler som har egna hämtare
    raknare = 0
    page = await context.new_page()
    try:
        while kö and len(besokta) < max_sidor:
            _, _, url = heapq.heappop(kö)
            url = url.split("#")[0]
            if url in besokta:
                continue
            besokta.add(url)
            host = urllib.parse.urlparse(url).netloc
            if not await asyncio.to_thread(robots.tillats, url):
                continue
            vanta = PAUS - (time.time() - senast.get(host, 0))
            if vanta > 0:
                await asyncio.sleep(vanta)
            senast[host] = time.time()
            try:
                svar = await page.goto(url, wait_until="domcontentloaded", timeout=25_000)
                if svar and "pdf" in (svar.headers.get("content-type") or ""):
                    dokument.setdefault(url, {"url": url, "titel": "", "beskrivning": ""})
                    continue
                await page.wait_for_timeout(1500)  # låt portaler ladda innehåll med JavaScript
                lankar = await page.eval_on_selector_all("a[href]", LANKAR_JS)
            except Exception as e:
                print(f"    {kommun['k']}: {type(e).__name__} på {url[:80]}", flush=True)
                continue
            if portaltyp(url):
                portaler.add(portaltyp(url))
            for href, text, sammanhang in lankar:
                if not href.startswith("http") or UNDVIK.search(href):
                    continue
                h = doman(href)
                typ = portaltyp(href)
                if NP_LASARE.search(href) or "meetingsplus" in h:
                    adresser.add(href)
                if typ:
                    portaler.add(typ)
                if DOKUMENT.search(href):
                    # Korta länktexter ("Kallelse") får sitt sammanhang (nämnd, datum) som titel.
                    titel = text if len(text) >= 25 else (" ".join(sammanhang.split())[:150] or text)
                    d = dokument.setdefault(href, {"url": href, "titel": titel, "beskrivning": sammanhang})
                    if len(titel) > len(d["titel"]):
                        d["titel"] = titel
                    continue
                # Följ länkar på kommunens webbplats och in i portaler som kommunen länkar till.
                extern_portal = not bara_egen and (typ or re.search(r"handlingar|protokoll|sammanträden|möten", text, re.I))
                if not (samma_doman(href, dom) or h in tillatna or extern_portal):
                    continue
                if extern_portal:
                    tillatna.add(h)
                if href.split("#")[0] in besokta:
                    continue
                poang = len(navigera.findall(f"{href} {text}")) + (3 if typ and not bara_egen else 0)
                if poang:
                    raknare += 1
                    heapq.heappush(kö, (-poang, raknare, href))
    finally:
        await page.close()
    return list(dokument.values()), sorted(portaler), len(besokta), adresser


async def kor(valda, max_sidor, parallellt):
    from playwright.async_api import async_playwright
    robots, senast = Robots(), {}
    resultat = {}
    sem = asyncio.Semaphore(parallellt)
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(user_agent=USER_AGENT, locale="sv-SE")

        async def en(k):
            async with sem:
                try:
                    dok, port, n, adr = await asyncio.wait_for(genomsok(context, k, robots, max_sidor, senast), 300)
                except asyncio.TimeoutError:
                    dok, port, n, adr = [], [], max_sidor, set()
                    print(f"  {k['k']}: avbruten efter fem minuter", flush=True)
                # Kända läsare i kommunens befintliga data (till exempel länkar i luckorna).
                adr |= set(re.findall(r"https?://www\.netpublicator\.com/reader/r\d+", json.dumps(k)))
                lasare = sorted({m.group(1) for a in adr for m in [NP_LASARE.search(a)] if m})
                for rid in lasare[:3]:
                    try:
                        np_dok = await asyncio.wait_for(Netpublicator(context.request).genomsok(context, rid), 600)
                    except asyncio.TimeoutError:
                        np_dok = []
                    dok += [dict(d, kalla="netpublicator") for d in np_dok]
                    port = sorted(set(port) | {"Netpublicator"})
                mp = sorted({re.match(r"https?://[^/]+", a).group(0) for a in adr if "meetingsplus" in a.lower()})
                for bas in mp[:1]:
                    try:
                        mp_dok = await asyncio.wait_for(meetingsplus(context, bas), 600)
                    except asyncio.TimeoutError:
                        mp_dok = []
                    dok += [dict(d, kalla="meetingsplus") for d in mp_dok]
                resultat[k["id"]] = (dok, port, n, adr)
                bra = sum(1 for d in dok if BRA_DOK.search(f"{d['titel']} {d['beskrivning']} {d['url']}"))
                print(f"  {k['k']}: {n} sidor, {len(dok)} dokumentlänkar ({bra} relevanta), "
                      f"portal: {', '.join(port) or 'ingen känd'}", flush=True)

        await asyncio.gather(*(en(k) for k in valda))
        await browser.close()
    return resultat


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", default=os.environ.get("PORTAL_STATUS") or "5",
                    help="vilka statusar som genomsöks, kommaseparerat (standard 5)")
    ap.add_argument("--max-sidor", type=int, default=int(os.environ.get("PORTAL_MAX_SIDOR") or 20))
    ap.add_argument("--parallellt", type=int, default=6)
    ap.add_argument("--kommuner", default="", help="kommaseparerade id:n, i stället för --status")
    a = ap.parse_args()

    data = kommuner()
    if a.kommuner:
        ids = set(a.kommuner.split(","))
        valda = [k for k in data if k["id"] in ids]
    else:
        statusar = {int(s) for s in a.status.split(",")}
        valda = [k for k in data if k["s"] in statusar]
    print(f"Genomsöker {len(valda)} kommuner, högst {a.max_sidor} sidor per kommun.", flush=True)
    res = asyncio.run(kor(valda, a.max_sidor, a.parallellt))

    sok = las_json(SOKRESULTAT, {})
    if sok.get("datum") != idag():
        sok = {"datum": idag(), "kommuner": {}}
    portaler = las_json(PORTALFIL, {})
    antal = 0
    for k in valda:
        dok, port, n = res.get(k["id"], ([], [], 0))[:3]
        portaler[k["id"]] = {"kommun": k["k"], "portaler": port, "sidor": n,
                             "dokumentlänkar": len(dok), "datum": idag()}
        post = sok["kommuner"].setdefault(k["id"], {"kommun": k["k"], "status": k["s"], "traffar": []})
        sedda = {t["url"] for t in post["traffar"]}
        nya = [{**d, "beskrivning": d["beskrivning"][:200], "alder": None, "sokning": 4 if d.get("kalla") else 3}
               for d in dok if d["url"] not in sedda
               and (d.get("kalla") or BRA_DOK.search(f"{d['titel']} {d['beskrivning']} {d['url']}"))]
        nya = sorted(nya, key=lambda d: (d["sokning"] != 4, rang(d)))[:MAX_LANKAR]  # portalernas egna först
        post["traffar"] += nya
        antal += len(nya)
    skriv_json(SOKRESULTAT, sok)
    skriv_json(PORTALFIL, portaler)
    fordelning = {}
    for v in portaler.values():
        for p in v["portaler"] or ["ingen känd"]:
            fordelning[p] = fordelning.get(p, 0) + 1
    print(f"Klart: {antal} nya dokumentlänkar. Portaler: "
          + ", ".join(f"{p} {n}" for p, n in sorted(fordelning.items(), key=lambda x: -x[1])))


if __name__ == "__main__":
    main()
