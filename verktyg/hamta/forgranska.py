#!/usr/bin/env python3
"""Steg 4: skriv granskningskort för kommuner som saknar status.

Kör från repots rot:  python3 verktyg/hamta/forgranska.py
Kräver att PDF:erna finns i .cache/pdf (de sparas mellan körningarna i GitHub Actions).

För varje kommun med status 5 väljs de upp till tre troligaste budgethandlingarna för 2027
bland de hämtade, ogranskade dokumenten. Kortet (arbete/granskning/kort/<id>.md) visar för
varje dokument: förstasidan, rader om beslut och förslag, raderna för skol- och
utbildningsnämnden, alla träffar på reformorden med sidnummer eller ett konstaterande att
de saknas i hela texten, och rader om statsbidrag. Kommuner utan kandidater får ett kort
med det som är känt (antal dokument, portal, hämtfel), som underlag för manuell sökning.

Korten är arbetsmaterial. Statusen sätts av den som granskar, och citat kontrolleras mot
dokumentet.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from gemensamt import (CACHE, DOKUMENT, HAMTNING, ROOT, Hamtare, kommuner,  # noqa: E402
                       kommunhandling, las_json, uppladdad)
from hamta_dokument import STARK, SVAG, pdf_till_sidor  # noqa: E402
from prioritera import TIDIGARE, titel_budget2027  # noqa: E402

KORT = ROOT / "arbete" / "granskning" / "kort"
GRANSKADE = HAMTNING / "granskade.json"
BESLUT = re.compile(r"beslut|fastställ|antag|föreslå|förslag|godkänn|fullmäktige|kommunstyrelse|beslutsdatum|"
                    r"beslutsinstans|majoritet", re.I)
SKOLA = re.compile(r"utbildning|bildning|barn- och|barn och unga|skol|lärande|förskola|grundskola", re.I)
SIFFRA = re.compile(r"\d[\d\s ]{2,}")
STATSBIDRAG = re.compile(r"statsbidrag", re.I)
BUDGETORD = re.compile(r"budget|ramar|budgetram|mål och budget|flerårsplan|resursplan|verksamhetsplan|"
                       r"strategisk plan|kommunplan|planeringsdirektiv|driftram|nämndram|skattesats", re.I)
AR2027 = re.compile(r"2027")
LARARE = re.compile(r"lärar|undervisn", re.I)


def rader(sidor, monster, krav=None, max_antal=10, bredd=170):
    ut = []
    for nr, s in enumerate(sidor, 1):
        for r in s.splitlines():
            r2 = " ".join(r.split())
            if r2 and monster.search(r2) and (krav is None or krav.search(r2)):
                ut.append(f"s. {nr}: {r2[:bredd]}")
                if len(ut) >= max_antal:
                    return ut
    return ut


def reformtraffar(sidor, max_antal=8):
    ut = []
    for nr, s in enumerate(sidor, 1):
        for m in list(STARK.finditer(s)) + list(SVAG.finditer(s)):
            f = " ".join(s[max(0, m.start() - 220):m.end() + 220].split())
            ut.append(f"s. {nr}: …{f}…")
            if len(ut) >= max_antal:
                return ut
    return ut


def datum_i(d):
    m = re.findall(r"20\d\d-\d\d-\d\d", f"{d.get('titel') or ''} {d['url']}")
    return max(m) if m else ""


def kandidater(k, docs, granskade):
    egna = [d for d in docs if d["url"] not in granskade
            and (kommunhandling(d["url"], k) or d.get("sökning") in (4, 5, 7))
            and d.get("kommunnamn_i_text") is not False and d.get("typ") == "pdf"]
    # Äldre budgetar ("Budget 2025–2027", "Budget 2026 med plan 2027") räknas inte.
    # Dokument som laddades upp före 2026 kan inte vara budget 2027.
    egna = [d for d in egna if (uppladdad(d["url"]) or "2026") >= "2026"]
    viktade = [d for d in egna if titel_budget2027(d) or (
        d.get("budget2027") and not TIDIGARE.search(f"{d.get('titel') or ''} {d['url']}".replace("%20", " ")))]
    return sorted(viktade, key=lambda d: (not titel_budget2027(d), not d.get("budget2027"),
                                          d.get("sökning") not in (5, 6, 7), datum_i(d)), reverse=False)[:8]


HAMTARE = Hamtare()


def budgetrader(sidor):
    """Rader som nämner både budget/ramar och 2027, med sidnummer."""
    return rader(sidor, BUDGETORD, AR2027, max_antal=12)


def ar_kandidat(sidor):
    """Ser dokumentet ut att vara, eller innehålla, en budgethandling för 2027?"""
    br = budgetrader(sidor)
    tidigt = [r for r in br if int(r.split(":")[0][3:]) <= 5]
    return bool(tidigt) or len(br) >= 3


def las_sidor(d):
    pdf = CACHE / f"{d.get('sha256')}.pdf"
    if not pdf.exists():
        try:
            data, _, _ = HAMTARE.hamta(d["url"])
            if data[:5] != b"%PDF-":
                return None
            CACHE.mkdir(parents=True, exist_ok=True)
            pdf.write_bytes(data)
        except Exception:
            return None
    return pdf_till_sidor(pdf.read_bytes())


def kort_dokument(d):
    pdf = CACHE / f"{d.get('sha256')}.pdf"
    rubrik = f"### {' '.join((d.get('titel') or d['url']).split())[:160]}\n\n{d['url']}\n"
    if not pdf.exists():  # finns inte i cachen: hämta igen
        try:
            data, _, _ = HAMTARE.hamta(d["url"])
            if data[:5] != b"%PDF-":
                raise ValueError("inte en PDF")
            CACHE.mkdir(parents=True, exist_ok=True)
            pdf.write_bytes(data)
        except Exception as e:
            return rubrik + f"\nPDF:en kunde inte hämtas ({type(e).__name__}).\n"
    sidor = pdf_till_sidor(pdf.read_bytes())
    text = "\n".join(sidor)
    forsta = [" ".join(r.split()) for r in "\n".join(sidor[:2]).splitlines() if r.strip()][:30]
    reform = reformtraffar(sidor)
    delar = [rubrik, f"Sidor: {len(sidor)}. Budget 2027 enligt titeln: {'ja' if titel_budget2027(d) else 'oklart'}."
             + (" Texten är framtagen med OCR." if d.get("ocr") else ""),
             "", "**Förstasidorna**", "", "```", *[r[:170] for r in forsta], "```", "",
             "**Rader om budget och 2027**", "", *(f"- {r}" for r in budgetrader(sidor)), "",
             "**Beslut och förslag**", "", *(f"- {r}" for r in rader(sidor, BESLUT, AR2027, max_antal=6)), "",
             "**Skola och utbildning (rader med belopp)**", "",
             *(f"- {r}" for r in rader(sidor, SKOLA, SIFFRA, max_antal=10)), "",
             "**Reformorden**", ""]
    if reform:
        delar += [f"- {r}" for r in reform]
    elif text.strip():
        delar.append(f"- Inga reformord i hela texten ({len(sidor)} sidor).")
    else:
        delar.append("- Ingen text att söka i (inskannad PDF utan OCR).")
    sb = rader(sidor, STATSBIDRAG, LARARE, max_antal=4)
    if sb:
        delar += ["", "**Statsbidrag nära lärare/undervisning**", "", *(f"- {r}" for r in sb)]
    return "\n".join(delar) + "\n"


def main():
    data = kommuner()
    granskade = las_json(GRANSKADE, {})
    tillst = las_json(HAMTNING / "tillstand.json", {"dokument": {}})["dokument"]
    portaler = las_json(HAMTNING / "portaler.json", {})
    motes = las_json(HAMTNING / "motessidor.json", {})
    KORT.mkdir(parents=True, exist_ok=True)
    for f in KORT.glob("*.md"):
        f.unlink()
    med, utan = [], []
    for k in data:
        if k["s"] != 5:
            continue
        docs = las_json(DOKUMENT / f"{k['id']}.json", [])
        kand = []
        for d in kandidater(k, docs, set(granskade.get(k["id"], []))):
            s = las_sidor(d)
            if s and ar_kandidat(s):
                kand.append(d)
            if len(kand) >= 3:
                break
        huvud = [f"# {k['k']} ({k['l']})", "", f"Webbplats: {k['w']}",
                 f"Portal: {', '.join(portaler.get(k['id'], {}).get('portaler') or ['ingen känd'])}",
                 f"Hämtade dokument: {len(docs)}, hämtfel: "
                 f"{sum(1 for v in tillst.values() if v.get('kommun') == k['id'] and v.get('fel'))}",
                 f"Mötessida: {(motes.get(k['id']) or {}).get('url') or 'inte hittad'}",
                 f"KF-möten: {', '.join((motes.get(k['id']) or {}).get('kf') or []) or 'okända'}; "
                 f"KS-möten: {', '.join((motes.get(k['id']) or {}).get('ks') or []) or 'okända'}",
                 f"Nuvarande sammanfattning: {k.get('sum') or ''}", f"Luckor: {k.get('lu') or ''}", ""]
        if kand:
            med.append(k["k"])
            text = "\n".join(huvud) + "\n" + "\n".join(kort_dokument(d) for d in kand)
        else:
            utan.append(k["k"])
            senaste = sorted(docs, key=datum_i, reverse=True)[:8]
            text = "\n".join(huvud + ["Inga kandidater till budgethandling för 2027 bland de hämtade dokumenten.", "",
                                      "Senast daterade hämtade dokument:", "",
                                      *(f"- {' '.join((d.get('titel') or '').split())[:120]} – {d['url']}"
                                        for d in senaste)]) + "\n"
        (KORT / f"{k['id']}.md").write_text(text, encoding="utf-8")
    sammanfattning = (f"# Granskningskort\n\n{len(med)} kommuner med kandidater, {len(utan)} utan.\n\n"
                      f"## Med kandidater\n\n{', '.join(med)}\n\n## Utan kandidater\n\n{', '.join(utan)}\n")
    (KORT / "README.md").write_text(sammanfattning, encoding="utf-8")
    print(f"Klart: {len(med)} kort med kandidater, {len(utan)} utan.")


if __name__ == "__main__":
    main()
