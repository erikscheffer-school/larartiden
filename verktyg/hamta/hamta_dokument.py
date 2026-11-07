#!/usr/bin/env python3
"""Steg 2: hämta de dokument som sökningen hittade och leta efter reformorden.

Kör från repots rot:  python3 verktyg/hamta/hamta_dokument.py [--max-dokument 150]

För varje ny träff hämtas dokumentet (PDF eller webbsida), görs om till text sida
för sida med pdftotext och genomsöks efter orden i metod/metod.md. Dokument som
redan finns i data/kommuner.json eller hämtats en tidigare vecka hämtas inte igen.

Per kommun sparas en fil i arbete/hamtning/dokument/<id>.json med titel, länk,
kontrollsumma, om dokumentet ser ut att vara en budgethandling för 2027 och korta
utdrag runt varje träff med sidnummer. Själva PDF:erna sparas i .cache/pdf.
"""
import argparse
import hashlib
import html
import os
import re
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(__file__))
from gemensamt import (BELOPP, CACHE, DOKUMENT, INTE_REFORM, REFORMKONTEXT,  # noqa: E402
                       SOKRESULTAT, STARKA, STATSBIDRAG, STATSBIDRAG_KONTEXT, SVAGA,
                       TILLSTAND, Hamtare, idag, kanda_urler, kommuner, las_json,
                       normalisera_url, skriv_json)

BUDGET27 = re.compile(
    r"(budget\w*|ramar|ram|direktiv|kommunplan|strategisk plan|verksamhetsplan|flerårsplan|"
    r"mål och budget|mrp|evp|planeringsunderlag|förutsättningar)\W+(\w+\W+){0,3}(för\W+|inför\W+)?(år\W+)?2027"
    r"|inför 2027|2027\s*[–-]\s*20(29|30)", re.I)
INTE_BUDGET27 = re.compile(r"årsredovisning|delårsrapport|remissvar|yttrande över|budget\s*(för\s*)?(år\s*)?2026\b", re.I)
def _ordregex(ord_):
    return re.compile("|".join(re.escape(o).replace(r"\ ", r"\s+")
                               for o in sorted(ord_, key=len, reverse=True)), re.I)


STARK = _ordregex(STARKA + ["reglerad undervisnings"])
SVAG = _ordregex(SVAGA)
UTDRAG = 160  # tecken före och efter träffen


def pdf_till_sidor(data):
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        f.write(data)
        f.flush()
        try:
            ut = subprocess.run(["pdftotext", "-layout", "-enc", "UTF-8", f.name, "-"],
                                capture_output=True, timeout=180)
        except subprocess.TimeoutExpired:
            return []
    text = ut.stdout.decode("utf-8", "replace")
    return text.split("\f")


def html_till_sidor(data):
    t = data.decode("utf-8", "replace")
    t = re.sub(r"(?is)<(script|style|nav|header|footer)\b.*?</\1>", " ", t)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    return [re.sub(r"\s+", " ", t)]


def kort(s):
    return re.sub(r"\s+", " ", s).strip()


def analysera(sidor, titel):
    """Returnerar träffar med sidnummer och en bedömning av om det är en budgethandling för 2027.

    En träff räknas som reformträff om ordet är starkt (till exempel "reglerad undervisningstid")
    eller om ett svagt ord (till exempel "undervisningstid") står nära ord som "reform",
    "reglera" eller "1 juli 2027" och inte gäller garanterad undervisningstid eller förskolan.
    """
    borjan = titel + " " + " ".join(sidor[:3])[:20_000]
    budget27 = bool(BUDGET27.search(borjan)) and not INTE_BUDGET27.search(titel or "")
    traff, ord_ = [], set()
    for nr, sida in enumerate(sidor, 1):
        traffar = [(m, True) for m in STARK.finditer(sida)]
        upptagna = [(m.start(), m.end()) for m, _ in traffar]
        for m in SVAG.finditer(sida):
            if any(a <= m.start() < b for a, b in upptagna):
                continue
            kontext = sida[max(0, m.start() - 250):m.end() + 250]
            fore = sida[max(0, m.start() - 80):m.end()]
            traffar.append((m, bool(REFORMKONTEXT.search(kontext)) and not INTE_REFORM.search(fore)))
        traffar += [(m, False) for m in STATSBIDRAG.finditer(sida)
                    if STATSBIDRAG_KONTEXT.search(sida[max(0, m.start() - 200):m.end() + 200])]
        for m, reform in traffar:
            o = re.sub(r"\s+", " ", m.group(0).lower())
            if reform:
                ord_.add(o)
            fonster = sida[max(0, m.start() - UTDRAG):m.end() + UTDRAG]
            traff.append({"sida": nr, "ord": o, "reform": reform, "utdrag": kort(fonster),
                          "belopp_nara": bool(BELOPP.search(fonster))})
    # Reformträffar först, sedan träffar med belopp. Ett utdrag per sida, högst åtta.
    traff.sort(key=lambda t: (not t["reform"], not t["belopp_nara"], t["sida"]))
    unika, sidor_med = [], set()
    for t in traff:
        if t["sida"] not in sidor_med:
            unika.append(t)
            sidor_med.add(t["sida"])
    return {
        "budget2027": budget27,
        "sidor": len(sidor),
        "nämner_reformen": bool(ord_),
        "ord": sorted(ord_),
        "belopp_nära_träff": any(t["belopp_nara"] for t in unika if t["reform"]),
        "träffar": unika[:8],
        "antal_träffar": len(traff),
    }


def omanalysera():
    """Analyserar om redan hämtade PDF:er från .cache/pdf, till exempel efter att orden ändrats."""
    n = 0
    for fil in sorted(DOKUMENT.glob("*.json")):
        poster = las_json(fil, [])
        for p in poster:
            pdf = CACHE / f"{p.get('sha256')}.pdf"
            if p.get("typ") == "pdf" and pdf.exists():
                p.update(analysera(pdf_till_sidor(pdf.read_bytes()), p.get("titel") or ""))
                n += 1
            elif p.get("typ") == "html":  # webbsidor sparas inte: räkna bara om befintliga utdrag
                for t in p.get("träffar", []):
                    t["reform"] = bool(STARK.search(t["utdrag"])) or (
                        bool(SVAG.search(t["utdrag"])) and bool(REFORMKONTEXT.search(t["utdrag"]))
                        and not INTE_REFORM.search(t["utdrag"]))
                p["ord"] = sorted({t["ord"] for t in p.get("träffar", []) if t["reform"]})
                p["nämner_reformen"] = bool(p["ord"])
                p["belopp_nära_träff"] = any(t["belopp_nara"] for t in p.get("träffar", []) if t["reform"])
        skriv_json(fil, poster)
    print(f"Klart: {n} PDF:er analyserade om.")


def rang(t):
    """Lägre är bättre: budget 2027 i titel eller beskrivning först, sedan PDF:er."""
    text = f"{t.get('titel') or ''} {t.get('beskrivning') or ''} {t['url']}".lower()
    budget = bool(re.search(r"budget|ramar|mål och|resursplan|flerårsplan|verksamhetsplan|kommunplan|mrp|evp|direktiv", text))
    mote = bool(re.search(r"fullmäktige|kommunstyrelse|\bkf\b|\bks\b|utbildning|bildning|barn- och|skolnämnd", text)) \
        and bool(re.search(r"2026-(0[4-9]|1[0-2])|2026", text))
    return (not ("2027" in text and budget), not budget, not mote, not REFORM_I_TEXT.search(text),
            not t["url"].lower().split("?")[0].endswith(".pdf"))


REFORM_I_TEXT = re.compile(r"undervisningstid|undervisningsuppdrag|lärares arbetstid", re.I)
PER_KOMMUN = 6


def redan_klar(post):
    """Hämtade dokument och sidor som robots.txt stänger hämtas inte igen. Tillfälliga fel försöks igen."""
    return bool(post) and ("sha256" in post or "robots" in post.get("fel", ""))


def ska_hamtas(t):
    u = t["url"].lower()
    text = f"{t.get('titel') or ''} {t.get('beskrivning') or ''} {u}"
    # Dokumentlänkar från mötesportalerna (sökning 3) saknar ofta .pdf i adressen.
    return u.split("?")[0].endswith(".pdf") or "2027" in text or t.get("sokning") in (3, 4)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-dokument", type=int, default=int(os.environ.get("MAX_DOKUMENT") or 450))
    ap.add_argument("--max-minuter", type=float, default=70)
    ap.add_argument("--omanalysera", action="store_true",
                    help="hämta inget nytt, analysera om de PDF:er som redan finns i .cache/pdf")
    a = ap.parse_args()
    if a.omanalysera:
        return omanalysera()

    sok = las_json(SOKRESULTAT, {"kommuner": {}})
    tillst = las_json(TILLSTAND, {"kommuner": {}, "dokument": {}})
    sedda = tillst.setdefault("dokument", {})
    kanda = kanda_urler(kommuner())
    CACHE.mkdir(parents=True, exist_ok=True)
    h = Hamtare()
    start, antal, nya_totalt = time.time(), 0, 0

    # Välj högst PER_KOMMUN nya träffar per kommun och hämta dem turvis, så att taket
    # på antal dokument inte går åt på de första kommunerna.
    koer = {}
    for kid, post in sok["kommuner"].items():
        nya = [t for t in post["traffar"]
               if normalisera_url(t["url"]) not in kanda.get(kid, set())
               and not redan_klar(sedda.get(normalisera_url(t["url"]))) and ska_hamtas(t)]
        koer[kid] = sorted(nya, key=rang)[:PER_KOMMUN]
    poster = {kid: {p["url"]: p for p in las_json(DOKUMENT / f"{kid}.json", [])} for kid in koer}
    andrade = set()
    stopp = False
    for omgang in range(PER_KOMMUN):
        for kid, ko in koer.items():
            if omgang >= len(ko):
                continue
            if antal >= a.max_dokument or (time.time() - start) / 60 > a.max_minuter:
                stopp = True
                break
            t, namn = ko[omgang], sok["kommuner"][kid]["kommun"]
            nu = normalisera_url(t["url"])
            if redan_klar(sedda.get(nu)):
                continue
            if not h.tillats(t["url"]):
                sedda[nu] = {"kommun": kid, "datum": idag(), "fel": "robots.txt tillåter inte"}
                continue
            antal += 1
            try:
                data, typ, slut = h.hamta(t["url"])
            except Exception as e:
                sedda[nu] = {"kommun": kid, "datum": idag(), "fel": f"{type(e).__name__}: {str(e)[:80]}"}
                print(f"  {namn}: kunde inte hämta ({type(e).__name__})", flush=True)
                continue
            sha = hashlib.sha256(data).hexdigest()
            ar_pdf = data[:5] == b"%PDF-"
            if ar_pdf:
                (CACHE / f"{sha}.pdf").write_bytes(data)
                sidor = pdf_till_sidor(data)
            elif "html" in typ:
                sidor = html_till_sidor(data)
            else:
                sedda[nu] = {"kommun": kid, "datum": idag(), "fel": f"okänd typ {typ[:40]}"}
                continue
            res = analysera(sidor, t.get("titel") or "")
            if ar_pdf and not "".join(sidor).strip():
                res["anmärkning"] = "Ingen text i PDF:en, troligen inskannad. Behöver OCR (OCRmyPDF -l swe)."
            poster[kid][t["url"]] = {
                "url": t["url"], "titel": t.get("titel"), "typ": "pdf" if ar_pdf else "html",
                "hämtad": idag(), "sha256": sha, "sökning": t.get("sokning"), **res,
            }
            sedda[nu] = {"kommun": kid, "datum": idag(), "sha256": sha}
            andrade.add(kid)
            nya_totalt += 1
            print(f"  {namn}: {'PDF' if ar_pdf else 'webbsida'}, "
                  f"budget 2027: {'ja' if res['budget2027'] else 'nej'}, "
                  f"reformord: {', '.join(res['ord']) or 'inga'}", flush=True)
        if stopp:
            break
    for kid in andrade:
        skriv_json(DOKUMENT / f"{kid}.json",
                   sorted(poster[kid].values(), key=lambda p: p["hämtad"], reverse=True))

    skriv_json(TILLSTAND, tillst)
    print(f"Klart: {antal} hämtningar, {nya_totalt} nya dokument analyserade.")


if __name__ == "__main__":
    main()
