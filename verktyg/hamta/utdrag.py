#!/usr/bin/env python3
"""Hämtar dokument och skriver ut de sidor som behövs för en manuell granskning.

Kör från repots rot:  python3 verktyg/hamta/utdrag.py
Läser arbete/granskning/begaran.json:
  [{"kommun": "ale", "url": "...", "sidor": [12, 13]}, ...]
För varje dokument skrivs arbete/granskning/text/<kommun>-<nr>.txt med
  - en innehållsförteckning: första raden på varje sida
  - hela texten på angivna sidor och på sidor med reformord eller budget 2027
Texten används för att kontrollera citat ordagrant. Den kan tas bort efter granskningen.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from gemensamt import ROOT, Hamtare  # noqa: E402
from hamta_dokument import STARK, SVAG, html_till_sidor, pdf_till_sidor  # noqa: E402

BEGARAN = ROOT / "arbete" / "granskning" / "begaran.json"
UT = ROOT / "arbete" / "granskning" / "text"
BUDGET = re.compile(r"(budget|ram|tillskott|resursfördelning|kommunbidrag)\w*", re.I)
MAX_SIDOR = 60


def main():
    begaran = json.loads(BEGARAN.read_text(encoding="utf-8"))
    UT.mkdir(parents=True, exist_ok=True)
    h, nr = Hamtare(), {}
    for b in begaran:
        k = b["kommun"]
        nr[k] = nr.get(k, 0) + 1
        fil = UT / f"{k}-{nr[k]}.txt"
        try:
            data, typ, _ = h.hamta(b["url"])
        except Exception as e:
            fil.write_text(f"URL: {b['url']}\nKUNDE INTE HÄMTAS: {type(e).__name__}: {e}\n", encoding="utf-8")
            print(f"{k}: kunde inte hämta ({type(e).__name__})", flush=True)
            continue
        sidor = pdf_till_sidor(data) if data[:5] == b"%PDF-" else html_till_sidor(data)
        valda = set(b.get("sidor") or [])
        for i, s in enumerate(sidor, 1):
            if b.get("endast"):  # bara de angivna sidorna
                break
            if STARK.search(s) or SVAG.search(s) or ("2027" in s and BUDGET.search(s)):
                valda.add(i)
        valda = sorted(valda)[:MAX_SIDOR] if not b.get("sidor") else sorted(valda)
        ut = [f"URL: {b['url']}", f"Titel: {b.get('titel') or ''}", f"Sidor: {len(sidor)}", "",
              "== INNEHÅLL (första raden per sida) =="]
        for i, s in enumerate(sidor if len(sidor) <= 80 or not b.get("endast") else [], 1):
            rad = next((r.strip() for r in s.splitlines() if r.strip()), "")
            ut.append(f"{i}: {rad[:110]}")
        for i in valda:
            if 1 <= i <= len(sidor):
                ut += ["", f"===== SIDA {i} =====", sidor[i - 1].rstrip()]
        fil.write_text("\n".join(ut) + "\n", encoding="utf-8")
        print(f"{k}: {len(sidor)} sidor, {len(valda)} utskrivna", flush=True)


if __name__ == "__main__":
    main()
