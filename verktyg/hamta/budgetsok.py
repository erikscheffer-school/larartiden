#!/usr/bin/env python3
"""Steg 1c: riktad sökning efter budgethandlingar för 2027 i kommuner som saknar status.

Kör från repots rot:  BRAVE_API_KEY=... python3 verktyg/hamta/budgetsok.py [--max-sok 330]

För varje kommun med status 5 (Ej bedömbart än):
  1. Genomsöker kommunens egen webbplats med en webbläsare, med fokus på sidor om ekonomi,
     budget, styrdokument och kommunplan, och provar webbplatsens egen sökfunktion
     (Sitevision, WordPress och liknande) med frågan "budget 2027".
  2. Söker med Brave Search API på kommunens webbplats efter "budget 2027" (alla filtyper)
     och på hela webben efter kommunens budgetförslag för 2027 (partier, nyheter, portaler).

Träffar som ser ut att gälla budget, ramar eller plan för 2027 läggs i sökresultatet med
sökning 5 (webbplatsen) eller 6 (Brave), så att hamta_dokument.py hämtar dem först.
"""
import argparse
import asyncio
import os
import re
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(__file__))
from gemensamt import (ROOT, SOKRESULTAT, USER_AGENT, doman, idag, kommuner, las_json,  # noqa: E402
                       namn_finns, samma_doman, skriv_json)

BUDGETNAV = re.compile(
    r"ekonomi|budget|mål och budget|mal-och-budget|årsredovisning|arsredovisning|styrdokument|"
    r"kommunplan|flerårsplan|verksamhetsplan|strategisk plan|planer|policy|kommunens ekonomi|"
    r"sok|sök|search|2027", re.I)
BUDGET27 = re.compile(
    r"(budget|ramar|mål och|resursplan|flerårsplan|verksamhetsplan|kommunplan|strategisk plan|"
    r"planeringsdirektiv|mrp|evp|direktiv|budgetförslag|förutsättningar)\W+(\w+\W+){0,4}2027"
    r"|2027\W+(\w+\W+){0,3}(budget|ramar)|2027\s*[-–]\s*20(29|30)", re.I)
TIDIGARE = re.compile(r"(budget|plan)\W+(för\W+)?(år\W+)?202[0-6]\b", re.I)
DEBUG = bool(os.environ.get("BUDGETSOK_DEBUG"))
DEBUGDIR = ROOT / "arbete" / "granskning" / "budgetsok"
SOKVAGAR = ["/sok.html?query=budget+2027", "/sok?q=budget+2027", "/?s=budget+2027",
            "/sok/?q=budget+2027", "/search?q=budget+2027"]


def relevant(titel, url):
    t = " ".join(f"{titel} {urllib.parse.unquote(url)}".split())
    return bool(BUDGET27.search(t)) and not TIDIGARE.search(t)


async def webbplatser(valda, max_sidor, parallellt):
    from playwright.async_api import async_playwright
    from portaler import Robots, genomsok
    robots, senast, ut = Robots(), {}, {}
    sem = asyncio.Semaphore(parallellt)
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(user_agent=USER_AGENT, locale="sv-SE")

        async def en(k):
            async with sem:
                rot = k["w"].rstrip("/")
                start = [k["w"]] + [rot + s for s in SOKVAGAR]
                try:
                    dok, _, n, _ = await asyncio.wait_for(
                        genomsok(context, k, robots, max_sidor, senast, start=start,
                                 navigera=BUDGETNAV, bara_egen=True), 300)
                except asyncio.TimeoutError:
                    dok, n = [], max_sidor
                traff = [d for d in dok if relevant(f"{d['titel']} {d['beskrivning'][:200]}", d["url"])]
                ut[k["id"]] = traff
                if DEBUG:
                    rader = [f"{d['url']} | {' '.join(d['titel'].split())[:120]}" for d in dok]
                    (DEBUGDIR / f"{k['id']}-webb.txt").write_text("\n".join(rader) + "\n", encoding="utf-8")
                print(f"  {k['k']}: {n} sidor, {len(traff)} möjliga budgethandlingar för 2027", flush=True)

        await asyncio.gather(*(en(k) for k in valda))
        await browser.close()
    return ut


def brave(valda, max_sok):
    from sok import Brave, traffar
    nyckel = os.environ.get("BRAVE_API_KEY", "").strip()
    if not nyckel:
        print("BRAVE_API_KEY saknas: hoppar över Brave-sökningen.")
        return {}
    b, ut = Brave(nyckel), {}
    fresh = f"2026-03-01to{idag()}"
    for k in valda:
        dom, namn = doman(k["w"]), k["k"]
        for q in (f'site:{dom} "budget 2027"',
                  f'"{namn}" kommun "budget 2027" förslag'):
            if b.antal >= max_sok:
                return ut
            t = traffar(b.sok(q, fresh))
            if DEBUG:
                with open(DEBUGDIR / f"{k['id']}-brave.txt", "a", encoding="utf-8") as f:
                    f.write(f"## {q}\n" + "".join(f"{x['url']} | {x['titel']} | {(x['beskrivning'] or '')[:150]}\n" for x in t))
            t = [x for x in t if samma_doman(x["url"], dom) or namn_finns(
                namn, f"{x['titel'] or ''} {x['beskrivning'] or ''} {x['url']}")]
            t = [x for x in t if relevant(f"{x['titel'] or ''} {x['beskrivning'] or ''}", x["url"])]
            ut.setdefault(k["id"], []).extend(t)
        print(f"  {namn}: {len(ut.get(k['id'], []))} träffar från Brave", flush=True)
    print(f"Brave: {b.antal} sökningar.")
    return ut


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-sok", type=int, default=int(os.environ.get("BUDGET_MAX_SOK") or 330))
    ap.add_argument("--max-sidor", type=int, default=15)
    ap.add_argument("--parallellt", type=int, default=6)
    ap.add_argument("--utan-webblasare", action="store_true")
    ap.add_argument("--kommuner", default=os.environ.get("BUDGETSOK_KOMMUNER") or "",
                    help="kommaseparerade id:n i stället för alla med status 5")
    a = ap.parse_args()

    valda = [k for k in kommuner() if (k["id"] in a.kommuner.split(",") if a.kommuner else k["s"] == 5)]
    if DEBUG:
        DEBUGDIR.mkdir(parents=True, exist_ok=True)
    print(f"Riktad budgetsökning för {len(valda)} kommuner med status 5.", flush=True)
    webb = {} if a.utan_webblasare else asyncio.run(webbplatser(valda, a.max_sidor, a.parallellt))
    br = brave(valda, a.max_sok) if a.max_sok else {}

    sok = las_json(SOKRESULTAT, {})
    if sok.get("datum") != idag():
        sok = {"datum": idag(), "kommuner": {}}
    antal = 0
    for k in valda:
        post = sok["kommuner"].setdefault(k["id"], {"kommun": k["k"], "status": k["s"], "traffar": []})
        sedda = {t["url"] for t in post["traffar"]}
        for nr, lista in ((5, webb.get(k["id"], [])), (6, br.get(k["id"], []))):
            for d in lista:
                if d["url"] in sedda:
                    # redan funnen: lyft den så att den hämtas först
                    for t in post["traffar"]:
                        if t["url"] == d["url"] and t.get("sokning") != 4:
                            t["sokning"] = nr
                    continue
                sedda.add(d["url"])
                post["traffar"].append({"url": d["url"], "titel": d.get("titel"),
                                        "beskrivning": (d.get("beskrivning") or "")[:200],
                                        "alder": d.get("alder"), "sokning": nr})
                antal += 1
    skriv_json(SOKRESULTAT, sok)
    utan = [k["k"] for k in valda if not webb.get(k["id"]) and not br.get(k["id"])]
    print(f"Klart: {antal} nya länkar. Utan träff: {len(utan)} kommuner.")


if __name__ == "__main__":
    main()
