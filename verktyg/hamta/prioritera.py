#!/usr/bin/env python3
"""Steg 3: välj ut de 3–10 kommuner som mest behöver granskas den här veckan.

Kör från repots rot:  python3 verktyg/hamta/prioritera.py [--antal 5]

Poängen bygger på det som hämtades i veckan:
  +6  nytt dokument som ser ut att vara budget 2027 och nämner reformen
  +3  nytt dokument som nämner reformen men inte ser ut att vara budget 2027
  +3  belopp i närheten av en träff på reformorden
  +3  ny budgethandling för 2027 i en kommun med status 5 (kan bli status 4)
  +1  per ytterligare ny budgethandling för 2027 (högst +2)
  +2  fullmäktige beslutade budget för 2027 de senaste tre veckorna och statusen är inte 0
  +1  status 5 (Ej bedömbart än)
Bara kommunens egna handlingar (webbplatsen eller en mötesportal) ger poäng. Tidningsartiklar
och myndigheters dokument visas men räknas inte, eftersom de inte är budgethandlingar.
Utan --antal tas alla kommuner med minst 4 poäng, men aldrig färre än 3 eller fler än 10.

Listan skrivs till arbete/veckolista/<datum>.md och .json och till GitHub-sammanfattningen.
Statusen sätts aldrig av skriptet: listan är ett underlag för en människa eller AI som
granskar dokumenten enligt arbete/INSTRUKTIONER.md.
"""
import argparse
import os
import re
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(__file__))
from gemensamt import (DOKUMENT, HAMTNING, SOKRESULTAT, VECKOLISTA, kanda_urler, kommuner,  # noqa: E402
                       kommunhandling, las_json, normalisera_url, skriv_json)

GRANSKADE = HAMTNING / "granskade.json"  # dokument som redan granskats för hand, per kommun

STATUS = ["Pengar beslutade", "Pengar föreslagna", "Kostnad beräknad",
          "Nämnt utan belopp", "Ej nämnt", "Ej bedömbart än"]


def kf_datum(kf):
    m = re.search(r"20\d\d-\d\d-\d\d", kf or "")
    return date.fromisoformat(m.group(0)) if m else None


def bedom(k, nya, korning):
    poang, skal = 0, []
    nya = [d for d in nya if kommunhandling(d["url"], k)]
    reform27 = [d for d in nya if d["nämner_reformen"] and d["budget2027"]]
    reform = [d for d in nya if d["nämner_reformen"] and not d["budget2027"]]
    budget27 = [d for d in nya if d["budget2027"]]
    if reform27:
        poang += 6
        skal.append(f"{len(reform27)} ny(a) budgethandling(ar) för 2027 nämner reformen")
    elif reform:
        poang += 3
        skal.append(f"{len(reform)} nytt/nya dokument nämner reformen")
    if any(d["belopp_nära_träff"] for d in nya):
        poang += 3
        skal.append("belopp står nära reformorden")
    if budget27 and k["s"] == 5:
        poang += 3
        skal.append("ny budgethandling för 2027 i en kommun som ännu inte gått att bedöma")
    if len(budget27) > 1:
        poang += min(2, len(budget27) - 1)
    kf = kf_datum(k.get("kf"))
    if kf and korning - timedelta(days=21) <= kf <= korning and k["s"] != 0:
        poang += 2
        skal.append(f"fullmäktige planerade budgetbeslut {kf.isoformat()}")
    if k["s"] == 5 and poang:
        poang += 1
    return poang, skal


def dokumentrad(d):
    rad = f"- [{d.get('titel') or d['url']}]({d['url']}) ({d['typ'].upper()}, {d['sidor']} s.)"
    rad += f" – budget 2027: {'troligen' if d['budget2027'] else 'oklart'}"
    rad += f"; reformord: {', '.join(d['ord']) if d['ord'] else 'inga'}"
    if d.get("anmärkning"):
        rad += f". {d['anmärkning']}"
    for t in d["träffar"][:3]:
        if t.get("reform") or not d["nämner_reformen"]:
            rad += f"\n  - s. {t['sida']}: …{t['utdrag']}…"
    return rad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--antal", type=int, default=int(os.environ.get("ANTAL") or 0),
                    help="exakt antal kommuner (0 = 3–10 efter poäng)")
    a = ap.parse_args()

    sok = las_json(SOKRESULTAT, {"kommuner": {}, "datum": date.today().isoformat()})
    korning = date.fromisoformat(sok["datum"])
    data = {k["id"]: k for k in kommuner()}
    kanda = kanda_urler(list(data.values()))
    granskade = {kid: {normalisera_url(u) for u in urler} for kid, urler in las_json(GRANSKADE, {}).items()}
    kandidater = []
    for kid, k in data.items():
        alla = las_json(DOKUMENT / f"{kid}.json", [])
        nya = [d for d in alla if d["hämtad"] == sok["datum"]
               and normalisera_url(d["url"]) not in kanda.get(kid, set()) | granskade.get(kid, set())]
        poang, skal = bedom(k, nya, korning)
        if poang:
            kandidater.append({"id": kid, "kommun": k["k"], "lan": k["l"], "status": k["s"],
                               "poang": poang, "skal": skal,
                               "dokument": sorted(nya, key=lambda d: (not d["nämner_reformen"], not d["budget2027"]))})
    kandidater.sort(key=lambda x: (-x["poang"], -x["status"], x["kommun"]))
    if a.antal:
        valda = kandidater[:a.antal]
    else:
        valda = [x for x in kandidater if x["poang"] >= 4][:10]
        if len(valda) < 3:
            valda = kandidater[:3]

    sokta = len(sok["kommuner"])
    med_dok = sum(1 for kid in sok["kommuner"] if any(
        d["hämtad"] == sok["datum"] for d in las_json(DOKUMENT / f"{kid}.json", [])))
    vecka = korning.isocalendar().week
    md = [f"# Att granska vecka {vecka} ({sok['datum']})", "",
          f"Sökningen täckte {sokta} kommuner. {med_dok} av dem fick nya dokument, "
          f"{len(kandidater)} fick poäng. Här är de {len(valda)} som mest behöver granskas. "
          "Statusen sätts av den som granskar, enligt `arbete/INSTRUKTIONER.md`. "
          "Utdragen är maskinellt framtagna och ska kontrolleras mot dokumentet innan de används som citat.", ""]
    if not valda:
        md.append("Inga nya dokument med träffar den här veckan.")
    for i, x in enumerate(valda, 1):
        md += [f"## {i}. {x['kommun']} ({x['lan']})", "",
               f"Status nu: {x['status']} {STATUS[x['status']]}. Poäng {x['poang']}. "
               f"Varför: {'; '.join(x['skal'])}.", ""]
        egna = [d for d in x["dokument"] if kommunhandling(d["url"], data[x["id"]])]
        andra = [d for d in x["dokument"] if d not in egna and d["nämner_reformen"]]
        md += [dokumentrad(d) for d in egna[:6] if d["budget2027"] or d["nämner_reformen"]]
        if andra:
            md.append("\nAndra källor (räknas inte som budgethandling):\n")
            md += [dokumentrad(d) for d in andra[:3]]
        md.append("")
    text = "\n".join(md)

    VECKOLISTA.mkdir(parents=True, exist_ok=True)
    (VECKOLISTA / f"{sok['datum']}.md").write_text(text, encoding="utf-8")
    skriv_json(VECKOLISTA / f"{sok['datum']}.json", [
        {k: v for k, v in x.items() if k != "dokument"} | {"dokument": [d["url"] for d in x["dokument"]]}
        for x in valda])
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
