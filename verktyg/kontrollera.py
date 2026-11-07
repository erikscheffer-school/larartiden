#!/usr/bin/env python3
"""Kontrollerar data/kommuner.json mot statusreglerna innan publicering.

Kör från repots rot:  python3 verktyg/kontrollera.py
Fel (måste rättas) gör att skriptet avslutas med felkod 1.
Varningar är fall som en människa bör titta på, men som kan vara riktiga.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
data = json.loads((ROOT / "data" / "kommuner.json").read_text(encoding="utf-8"))

fel, varn = [], []

# Fall där regeln ovan varnar men en människa har bedömt att statusen är rätt (2026-11-07).
UNDANTAG = {
    "Avesta": "KS-protokollet om budget 2027 innehåller inte budgeten. Själva budgetdokumentet har inte hittats.",
    "Hedemora": "Ekonomirapporten om budget 2027 som nämnden tog del av är inte granskad.",
    "Ljusdal": "Sidorna om EVP 2027 är inte lästa.",
    "Söderhamn": "Budget 2026 med plan 2027, inte budget 2027.",
    "Berg": "Protokoll om arbetsgången, inte budget 2027.",
    "Emmaboda": "KS-paragraf om tidplanen, inte budgetens innehåll.",
    "Ljungby": "Planeringsdirektiv för 2026 med plan 2027.",
    "Arvidsjaur": "Myndighetsnämndens detaljbudget, inte skolan.",
    "Eslöv": "Nämndens handlingar om budget 2027 gick inte att öppna.",
    "Simrishamn": "Bara rubriken på ärendet om budget 2027.",
    "Ängelholm": "Partinyhet, inte en kommunhandling.",
    "Årjäng": "Tidplan för budget 2027.",
    "Örnsköldsvik": "Bara rubriken på ett kommande ärende.",
    "Tjörn": "KF-protokoll utan budgetärende för 2027.",
    "Karlskoga": "Nyhetsartikel, inte en kommunhandling.",
    "Pajala": "Nämndens verksamhetsplan 2026–2027 räknas som budgethandling för 2027.",
    "Uddevalla": "Vänsterpartiets budgetförslag 2027 är en budgethandling för 2027.",
    "Mjölby": "Kommunens nyhet om KF:s beslut om driftramar 2027.",
    "Vadstena": "KS preliminära budgetramar 2027–2029.",
    "Ödeshög": "KS planeringsdirektiv för 2027.",
}
STATUS = ["Pengar beslutade", "Pengar föreslagna", "Kostnad beräknad", "Nämnt utan belopp", "Ej nämnt", "Ej bedömbart än"]


def gäller_2027(doc):
    """Ett dokument räknas som budgethandling för 2027 om titeln nämner 2027 och det inte är ett remissvar, en årsredovisning eller en plan som börjar 2026."""
    t = (doc.get("t") or "").lower()
    if "2027" not in t:
        return False
    if re.search(r"remiss|yttrande över sou|årsredovisning|nyhetsartikel|nyhet:", t):
        return False
    # "Budget 2026 med plan 2027–2028" är en budget för 2026, inte för 2027.
    if re.search(r"(budget|plan|mrp|verksamhetsplan)\s*(för\s*)?(år\s*)?2026", t) and not re.search(r"budget(ramar|ram)?\s*(för\s*)?(år\s*)?2027", t):
        return False
    return bool(re.search(r"(budget\w*|ramar|ram|direktiv|kommunplan|strategisk plan|verksamhetsplan|ekonomi|planeringsunderlag|förutsättningar|mrp|evp|prioriteringar)\s+(\w+\s+)?(för\s+|inför\s+)?(år\s+)?2027|inför 2027|2027\s*[–-]\s*20(29|30)", t))


if len(data) != 290:
    fel.append(f"Filen har {len(data)} kommuner, inte 290.")
for i, n in Counter(k["id"] for k in data).items():
    if n > 1:
        fel.append(f"id '{i}' används av {n} kommuner.")
for k in data:
    if not re.fullmatch(r"[a-z0-9-]{1,60}", k["id"]):
        fel.append(f"{k['k']}: ogiltigt id '{k['id']}'.")

for k in data:
    namn, s, docs = k["k"], k["s"], k.get("docs") or []
    if s not in range(6):
        fel.append(f"{namn}: status {s} finns inte.")
        continue
    if s <= 2 and not k.get("kort"):
        fel.append(f"{namn}: status {STATUS[s]} saknar kort beloppsrad (kort).")
    if s > 2 and k.get("kort"):
        fel.append(f"{namn}: kort ska bara finnas för status 0–2.")
    if k.get("kort") and len(k["kort"]) > 75:
        varn.append(f"{namn}: kort är {len(k['kort'])} tecken, sikta på högst cirka 60.")
    nämner = [d for d in docs if d.get("nr")]
    nämner27 = [d for d in nämner if gäller_2027(d)]
    budget27 = [d for d in docs if gäller_2027(d)]
    if s == 0:
        if not any(d.get("sk") == "beslut" for d in nämner27):
            varn.append(f"{namn}: Pengar beslutade, men inget beslutsdokument för 2027 som nämner reformen.")
        if not k.get("m"):
            fel.append(f"{namn}: Pengar beslutade utan belopp i m.")
    if s == 1 and not k.get("m"):
        fel.append(f"{namn}: Pengar föreslagna utan belopp i m.")
    if s == 2 and not k.get("mk"):
        fel.append(f"{namn}: Kostnad beräknad utan beräkning i mk.")
    if s == 3 and not nämner27:
        varn.append(f"{namn}: Nämnt utan belopp, men inget dokument för 2027 som nämner reformen.")
    if s == 4:
        if not budget27:
            varn.append(f"{namn}: Ej nämnt, men inget dokument för 2027 bland de granskade.")
        if nämner27:
            varn.append(f"{namn}: Ej nämnt, men ett dokument för 2027 är markerat som att det nämner reformen.")
    if s == 5 and budget27:
        varn.append(f"{namn}: Ej bedömbart än, men {len(budget27)} dokument för 2027 finns bland de granskade. Kontrollera om de har innehåll (ramar, belopp eller förslag).")
    for d in docs:
        c = d.get("c") or ""
        if c and not re.search(r'["“”\']', c):
            varn.append(f"{namn}: citatfältet i '{(d.get('t') or '')[:50]}' saknar citattecken. Flytta anteckningar till ko.")
        if d.get("u") and not d["u"].startswith("https://") and not d["u"].startswith("http://"):
            fel.append(f"{namn}: ogiltig länk i '{(d.get('t') or '')[:50]}'.")

print("Statusfördelning:", ", ".join(f"{STATUS[s]} {n}" for s, n in sorted(Counter(k['s'] for k in data).items())))
varn = [v for v in varn if v.split(":")[0] not in UNDANTAG or "kort" in v or "citat" in v]
for v in varn:
    print("VARNING:", v)
for f in fel:
    print("FEL:", f)
print(f"\n{len(fel)} fel, {len(varn)} varningar.")
sys.exit(1 if fel else 0)
