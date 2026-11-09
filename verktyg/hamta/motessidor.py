#!/usr/bin/env python3
"""Steg 1d: hitta kommunens sida med kallelser och protokoll, mötesdatumen för
kommunfullmäktige (KF) och kommunstyrelsen (KS), och de senaste handlingarna därifrån.

Kör från repots rot:  python3 verktyg/hamta/motessidor.py [--kommuner id,id] [--max-sok 100]
Kräver Playwright. BRAVE_API_KEY används om den finns (två sökningar per kommun som
saknar känd mötessida).

För varje kommun med status 5 (Ej bedömbart än):
  1. Startadresser: den sparade mötessidan om den finns, annars kommunens startsida,
     webbplatsens egen sökning efter "kallelse kommunfullmäktige", vanliga underdomäner
     (sammantraden., moten., politik. …) och träffar från Brave.
  2. En webbläsare följer länkar om politik, sammanträden, kallelser och protokoll,
     helst sådana som nämner KF eller KS och datum från i höstas.
  3. Varje besökt sida får poäng efter hur mycket den ser ut som en mötessida (datum
     under 2026, länkar till kallelser och protokoll, KF/KS i texten). Den bästa sparas.
  4. Mötesdatum för KF och KS plockas ur texten. Dokumentlänkar som gäller KF eller KS
     och är från september 2026 eller senare, eller nämner budget eller 2027, läggs i
     sökresultatet med sökning 7, så att hamta_dokument.py hämtar dem först.
  Hittas en Netpublicator- eller MeetingsPlus-portal används portalens egen hämtare.

Resultatet sparas i arbete/hamtning/motessidor.json. Skriptet följer robots.txt och
väntar mellan anropen till samma värd. Det sätter aldrig någon status.
"""
import argparse
import asyncio
import heapq
import os
import re
import sys
import time
import urllib.parse
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(__file__))
from gemensamt import (HAMTNING, ROOT, SOKRESULTAT, USER_AGENT, doman, idag, kommuner,  # noqa: E402
                       las_json, namn_finns, samma_doman, skriv_json, uppladdad)
from portaler import DOKUMENT as DOKLANK, LANKAR_JS, NP_LASARE, UNDVIK, Robots, portaltyp  # noqa: E402

MOTESFIL = HAMTNING / "motessidor.json"
DEBUG = bool(os.environ.get("MOTESSIDOR_DEBUG"))
DEBUGDIR = ROOT / "arbete" / "granskning" / "motessidor"
PAUS = 2.0
FRAN = "2026-09-01"  # handlingar från i höstas
UPPTACK_IGEN = 28  # dagar innan en kommun med sparad mötessida genomsöks från början igen
MAX_DOK = 40

KF = re.compile(r"kommunfullmäktige|kommunfullmaktige|\bkf\b|fullmäktige", re.I)
KS = re.compile(r"kommunstyrelse|kommunstyrelsen|\bks\b|\bksau\b", re.I)
MOTESORD = re.compile(r"kallelse|protokoll|handlingar|föredragningslista|dagordning|sammanträde|"
                      r"sammantrade|möte|mote|ärendelista|underlag", re.I)
NAVIGERA = re.compile(
    r"politik|demokrati|sammanträd|sammantrad|möten|moten|mote-|kallelse|protokoll|handlingar|"
    r"fullmäktige|fullmaktige|kommunstyrelse|nämnder|namnder|beslut|anslagstavla|meeting|agenda|"
    r"insyn|diarium", re.I)
SOKVAGAR = ["/sok.html?query=kallelse+kommunfullm%C3%A4ktige", "/sok?q=kallelse+kommunfullm%C3%A4ktige",
            "/?s=kallelse+kommunfullm%C3%A4ktige"]
UNDERDOMANER = ["sammantraden", "moten", "politik", "handlingar", "insyn", "dokument", "edok", "meetings"]
MANAD = {m: i for i, m in enumerate(
    ["januari", "februari", "mars", "april", "maj", "juni", "juli", "augusti", "september",
     "oktober", "november", "december"], 1)}
ISO = re.compile(r"(?<!\d)(20\d\d)-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])(?!\d)")
SVENSKT = re.compile(r"(?<!\d)([1-9]|[12]\d|3[01])\s+(" + "|".join(MANAD) + r")\s+(20\d\d)", re.I)
KOMPAKT = re.compile(r"(?<!\d)(2026|2027)(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])(?!\d)")


def datum_i(text):
    """Alla datum i texten som ÅÅÅÅ-MM-DD (ISO, '24 november 2026' och 20261124)."""
    ut = {f"{a}-{b}-{c}" for a, b, c in ISO.findall(text)}
    ut |= {f"{a}-{MANAD[m.lower()]:02d}-{int(d):02d}" for d, m, a in SVENSKT.findall(text)}
    ut |= {f"{a}-{b}-{c}" for a, b, c in KOMPAKT.findall(text)}
    return ut


def sidpoang(text, lankar):
    """Hur mycket ser sidan ut som en sida med kallelser och protokoll?"""
    ar2026 = sum(1 for d in datum_i(text) if d.startswith("2026"))
    motes = sum(1 for _, t, _ in lankar if MOTESORD.search(t))
    dok = sum(1 for h, t, _ in lankar if DOKLANK.search(h) and MOTESORD.search(f"{t} {h}"))
    organ = 5 * bool(KF.search(text)) + 5 * bool(KS.search(text))
    return min(ar2026, 30) + min(motes, 20) + 2 * min(dok, 20) + organ


def organdatum(text, titel):
    """Mötesdatum per organ: rader som nämner KF/KS och ett datum, eller alla datum på en
    sida vars rubrik är KF eller KS."""
    ut = {"kf": set(), "ks": set()}
    hel = {"kf": bool(KF.search(titel)) and not KS.search(titel),
           "ks": bool(KS.search(titel)) and not KF.search(titel)}
    for rad in text.splitlines():
        ds = {d for d in datum_i(rad) if "2026-01-01" <= d <= "2027-12-31"}
        if not ds:
            continue
        for nyckel, rx in (("kf", KF), ("ks", KS)):
            if rx.search(rad) or (hel[nyckel] and MOTESORD.search(rad) or hel[nyckel] and len(rad) < 60):
                ut[nyckel] |= ds
    return ut


def lankpoang(href, text):
    t = f"{urllib.parse.unquote(href)} {text}"
    p = len(NAVIGERA.findall(t)) + 3 * bool(KF.search(t) or KS.search(t))
    ds = datum_i(t)
    if any(d >= FRAN for d in ds):
        p += 3
    elif ds and all(d < "2026" for d in ds) or re.search(r"\b(2019|2020|2021|2022|2023|2024)\b", t):
        p -= 3
    return p


def ar_aktuell(href, text):
    """Dokumentet gäller KF/KS i höstas eller budget 2027."""
    t = f"{urllib.parse.unquote(href)} {text}"
    ds = datum_i(t)
    up = uppladdad(href)
    farsk = any(d >= FRAN for d in ds) or (up or "") >= FRAN[:7]
    gammal = (ds and max(ds) < "2026-06") or (up and up < "2026-06")
    budget = re.search(r"budget|2027|ramar|mål och resurs|flerårsplan|kommunplan", t, re.I)
    return not gammal and ((farsk and (KF.search(t) or KS.search(t) or MOTESORD.search(t))) or bool(budget and farsk)
                           or bool(budget and re.search(r"2027", t)))


def dokrang(d):
    """KF och KS först, sedan budget, sedan nyast."""
    t = f"{d.get('titel') or ''} {d['url']}"
    return (not (KF.search(t) or KS.search(t)), not re.search(r"budget|2027|ramar", t, re.I),
            "".join(chr(255 - ord(c)) for c in max(datum_i(t) | {"0000"})))


def startadresser(k, sparad, brave_urler):
    dom = doman(k["w"])
    rot = k["w"].rstrip("/")
    start = []
    if sparad:
        start.append(sparad)
    start += brave_urler[:6]
    start.append(k["w"])
    if not sparad:
        start += [rot + s for s in SOKVAGAR] + [f"https://{u}.{dom}/" for u in UNDERDOMANER]
    return list(dict.fromkeys(start))


async def genomsok(context, k, robots, senast, start, max_sidor):
    dom = doman(k["w"])
    tillatna = {dom}
    for s in start:
        if portaltyp(s):
            tillatna.add(doman(s))
    ko = [(-1000 + i, i, s) for i, s in enumerate(start)]  # startadresserna först, i ordning
    heapq.heapify(ko)
    besokta, sidor, dokument, adresser = set(), [], {}, set()
    ky = {"kf": set(), "ks": set()}
    raknare = len(start)
    page = await context.new_page()
    anrop = []  # nätverksanrop: inbäddade portaler (Netpublicator-widgetar) syns bara här
    page.on("request", lambda req: anrop.append(req.url) if len(anrop) < 3000 else None)
    try:
        while ko and len(besokta) < max_sidor:
            _, _, url = heapq.heappop(ko)
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
                svar = await page.goto(url, wait_until="domcontentloaded", timeout=20_000)
                if svar is None or svar.status >= 400:
                    continue
                if "pdf" in (svar.headers.get("content-type") or ""):
                    dokument.setdefault(url, {"url": url, "titel": "", "beskrivning": ""})
                    continue
                await page.wait_for_timeout(1500)
                titel = await page.title()
                text = (await page.inner_text("body"))[:150_000]
                lankar = await page.eval_on_selector_all("a[href]", LANKAR_JS)
                # Inbäddade portaler (iframe) följs som länkar.
                lankar += [[s, "inbäddad portal kallelser protokoll", ""] for s in await page.eval_on_selector_all(
                    "iframe[src]", "els => els.map(e => e.src)") if s.startswith("http")]
            except Exception:
                continue
            slut = page.url.split("#")[0]
            if slut != url and portaltyp(slut):
                tillatna.add(doman(slut))
            p = sidpoang(text, lankar)
            sidor.append({"url": slut, "titel": " ".join(titel.split())[:150], "poang": p,
                          "lankar": [(h, " ".join(t.split())[:100]) for h, t, _ in lankar
                                     if h.startswith("http") and not UNDVIK.search(h)][:300]})
            od = organdatum(text, titel)
            ky["kf"] |= od["kf"]
            ky["ks"] |= od["ks"]
            for href, ltext, sammanhang in lankar:
                if not href.startswith("http") or UNDVIK.search(href):
                    continue
                h = doman(href)
                if NP_LASARE.search(href) or "meetingsplus" in h:
                    adresser.add(href)
                egen = samma_doman(href, dom) or h in tillatna or (portaltyp(href) and (
                    namn_finns(k["k"], f"{href} {ltext}") or dom.split(".")[0] in h))
                if DOKLANK.search(href):
                    if not (egen or portaltyp(href)):
                        continue
                    kort = len(ltext) < 25
                    titel_d = " ".join(f"{titel} – {ltext}".split())[:160] if kort else ltext
                    if kort and len(sammanhang) > len(ltext):
                        titel_d = " ".join(f"{titel} – {sammanhang}".split())[:200]
                    if ar_aktuell(href, f"{titel_d} {sammanhang}"):
                        d = dokument.setdefault(href, {"url": href, "titel": titel_d,
                                                       "beskrivning": " ".join(sammanhang.split())[:200]})
                        if len(titel_d) > len(d["titel"]):
                            d["titel"] = titel_d
                    continue
                if not egen:
                    continue
                if portaltyp(href):
                    tillatna.add(h)
                if href.split("#")[0] in besokta:
                    continue
                lp = lankpoang(href, ltext)
                if lp > 0:
                    raknare += 1
                    heapq.heappush(ko, (-lp, raknare, href))
    finally:
        await page.close()
    for a in anrop:
        m = re.search(r"netpublicator\.com/(?:api/public|reader)/(r\d+)", a)
        if m:
            adresser.add(f"https://www.netpublicator.com/reader/{m.group(1)}")
        elif "meetingsplus" in a:
            adresser.add(a)
    return sidor, dokument, ky, adresser, len(besokta)


def brave_urler(k, b):
    from sok import traffar
    dom, namn = doman(k["w"]), k["k"]
    ut = []
    for q in (f"{namn} kommunfullmäktige kallelse handlingar 2026", f"{namn} kommunstyrelsen sammanträde protokoll 2026"):
        t = traffar(b.sok(q, f"2026-01-01to{idag()}"))
        for x in t:
            u = x["url"]
            if not (samma_doman(u, dom) or (portaltyp(u) and namn_finns(namn, f"{u} {x['titel'] or ''}"))):
                continue
            if DOKLANK.search(u):
                # En PDF i en mappstruktur: prova mappen eller sidan den ligger på.
                u = u.rsplit("/", 1)[0] + "/" if not re.search(r"/download/|/document/", u) else None
            if u:
                ut.append(u)
    return list(dict.fromkeys(ut))


async def kor(valda, sparat, max_sok, parallellt, max_sidor_upptack, max_sidor_kand):
    from playwright.async_api import async_playwright
    from portalskript import Netpublicator, meetingsplus
    b = None
    nyckel = os.environ.get("BRAVE_API_KEY", "").strip()
    if nyckel and max_sok:
        from sok import Brave
        b = Brave(nyckel)
    robots, senast, res = Robots(), {}, {}
    sem = asyncio.Semaphore(parallellt)
    gräns = (date.today() - timedelta(days=UPPTACK_IGEN)).isoformat()
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(user_agent=USER_AGENT, locale="sv-SE")

        async def en(k):
            gammal = sparat.get(k["id"]) or {}
            sparad = gammal.get("url") if (gammal.get("poang") or 0) >= 15 else None
            upptack = not sparad or (gammal.get("upptackt") or "") < gräns
            async with sem:
                bu = []
                if upptack and b and b.antal < max_sok - 1:
                    bu = await asyncio.to_thread(brave_urler, k, b)
                start = startadresser(k, sparad, bu) if upptack else [sparad]
                ms = max_sidor_upptack if upptack else max_sidor_kand
                try:
                    sidor, dok, ky, adr, n = await asyncio.wait_for(
                        genomsok(context, k, robots, senast, start, ms), 420)
                except asyncio.TimeoutError:
                    sidor, dok, ky, adr, n = [], {}, {"kf": set(), "ks": set()}, set(), ms
                # Fas 2: gå djupare från de två bästa sidorna (möten, nämnder, år 2026).
                basta = [s["url"] for s in sorted(sidor, key=lambda s: -s["poang"])[:2] if s["poang"] >= 15]
                if basta:
                    try:
                        s2, d2, k2, a2, n2 = await asyncio.wait_for(
                            genomsok(context, k, robots, senast, basta, max_sidor_kand + 10), 300)
                        sidor += [s for s in s2 if s["url"] not in {x["url"] for x in sidor}]
                        dok.update(d2)
                        ky["kf"] |= k2["kf"]
                        ky["ks"] |= k2["ks"]
                        adr |= a2
                        n += n2
                    except asyncio.TimeoutError:
                        pass
                dok = sorted(dok.values(), key=dokrang)
                adr |= set(gammal.get("portaladresser") or [])
                for rid in sorted({m.group(1) for a in adr for m in [NP_LASARE.search(a)] if m})[:2]:
                    try:
                        dok += sorted(await asyncio.wait_for(Netpublicator(context.request).genomsok(context, rid), 600), key=dokrang)
                    except Exception:
                        pass
                for bas in sorted({re.match(r"https?://[^/]+", a).group(0) for a in adr if "meetingsplus" in a.lower()})[:1]:
                    try:
                        dok += await asyncio.wait_for(meetingsplus(context, bas), 600)
                    except Exception:
                        pass
                res[k["id"]] = {"sidor": sidor, "dok": dok, "ky": ky, "n": n, "upptack": upptack, "brave": bu,
                               "portaler": sorted(adr)[:10]}
                bast = max(sidor, key=lambda s: s["poang"], default=None)
                print(f"  {k['k']}: {n} sidor, bästa {bast['poang'] if bast else 0} p "
                      f"({(bast or {}).get('url', '–')[:90]}), {len(dok)} aktuella handlingar, "
                      f"KF {len(ky['kf'])} datum, KS {len(ky['ks'])} datum", flush=True)

        await asyncio.gather(*(en(k) for k in valda))
        await browser.close()
    if b:
        print(f"Brave: {b.antal} sökningar.")
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kommuner", default=os.environ.get("MOTESSIDOR_KOMMUNER") or "",
                    help="kommaseparerade id:n i stället för alla med status 5")
    ap.add_argument("--max-sok", type=int, default=int(os.environ.get("MOTES_MAX_SOK") or 120))
    ap.add_argument("--max-sidor", type=int, default=40, help="sidor per kommun när mötessidan söks")
    ap.add_argument("--max-sidor-kand", type=int, default=15, help="sidor per kommun med känd mötessida")
    ap.add_argument("--parallellt", type=int, default=8)
    a = ap.parse_args()

    data = kommuner()
    valda = [k for k in data if (k["id"] in a.kommuner.split(",") if a.kommuner else k["s"] == 5)]
    sparat = las_json(MOTESFIL, {})
    print(f"Mötessidor för {len(valda)} kommuner.", flush=True)
    res = asyncio.run(kor(valda, sparat, a.max_sok, a.parallellt, a.max_sidor, a.max_sidor_kand))

    sok = las_json(SOKRESULTAT, {})
    if sok.get("datum") != idag():
        sok = {"datum": idag(), "kommuner": {}}
    if DEBUG:
        DEBUGDIR.mkdir(parents=True, exist_ok=True)
    nya_totalt, utan = 0, []
    for k in valda:
        r = res.get(k["id"])
        if not r:
            continue
        gammal = sparat.get(k["id"]) or {}
        bast = max(r["sidor"], key=lambda s: s["poang"], default=None)
        if bast and bast["poang"] >= (gammal.get("poang") or 0) * 0.7:
            url, poang = bast["url"], bast["poang"]
        else:
            url, poang = gammal.get("url"), gammal.get("poang") or 0
        kf = sorted(set(gammal.get("kf") or []) | r["ky"]["kf"])
        ks = sorted(set(gammal.get("ks") or []) | r["ky"]["ks"])
        idag_s = idag()
        post = {"kommun": k["k"], "url": url, "titel": (bast or {}).get("titel") if url == (bast or {}).get("url") else gammal.get("titel"),
                "poang": poang, "upptackt": idag_s if r["upptack"] else gammal.get("upptackt"),
                "senast": idag_s, "kf": kf[-12:], "ks": ks[-12:],
                "nasta_kf": next((d for d in kf if d >= idag_s), None),
                "senaste_kf": next((d for d in reversed(kf) if d < idag_s), None),
                "nasta_ks": next((d for d in ks if d >= idag_s), None),
                "aktuella_handlingar": len(r["dok"]),
                "portaladresser": sorted(set(gammal.get("portaladresser") or []) | set(r["portaler"]))[:10]}
        sparat[k["id"]] = post
        if poang < 15:
            utan.append(k["k"])
        sp = sok["kommuner"].setdefault(k["id"], {"kommun": k["k"], "status": k["s"], "traffar": []})
        sedda = {t["url"]: t for t in sp["traffar"]}
        for d in r["dok"][:MAX_DOK * 2]:
            if d["url"] in sedda:
                if sedda[d["url"]].get("sokning") not in (4, 5, 6):
                    sedda[d["url"]]["sokning"] = 7
                continue
            sp["traffar"].append({"url": d["url"], "titel": d.get("titel"), "beskrivning": (d.get("beskrivning") or "")[:200],
                                  "alder": None, "sokning": 7})
            sedda[d["url"]] = sp["traffar"][-1]
            nya_totalt += 1
        if DEBUG:
            rader = [f"Startadresser från Brave: {', '.join(r['brave']) or 'inga'}",
                     f"Portaladresser: {', '.join(r['portaler']) or 'inga'}", "", "Sidor (poäng):"]
            rader += [f"{s['poang']:3d}  {s['url']}  {s['titel']}" for s in sorted(r["sidor"], key=lambda s: -s["poang"])]
            for s in sorted(r["sidor"], key=lambda s: -s["poang"])[:3]:
                rader += ["", f"Länkar på {s['url']}:"] + [f"  {h} | {t}" for h, t in s["lankar"]]
            rader += ["", f"KF: {', '.join(kf)}", f"KS: {', '.join(ks)}", "", "Aktuella handlingar:"]
            rader += [f"- {d.get('titel')} | {d['url']}" for d in r["dok"]]
            (DEBUGDIR / f"{k['id']}.txt").write_text("\n".join(rader) + "\n", encoding="utf-8")
    skriv_json(SOKRESULTAT, sok)
    skriv_json(MOTESFIL, dict(sorted(sparat.items())))
    print(f"Klart: {nya_totalt} nya länkar till handlingar. "
          f"Ingen tydlig mötessida för {len(utan)} kommuner: {', '.join(utan)}")


if __name__ == "__main__":
    main()
