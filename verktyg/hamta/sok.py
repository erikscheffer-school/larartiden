#!/usr/bin/env python3
"""Steg 1: sök efter budgethandlingar för 2027 med Brave Search API.

Kör från repots rot:  BRAVE_API_KEY=... python3 verktyg/hamta/sok.py [--max-sok 250]

Kommunerna söks i prioritetsordning: först de som inte sökts på längst tid och
har status 5 (Ej bedömbart än), sedan 4, 3, 2, 1, 0. Varje kommun får en sökning
efter PDF:er på sin egen webbplats. Kommuner med status 3–5 får också en sökning
på reformorden på hela webben (mötesportaler ligger ofta på andra domäner).
Med 250 sökningar i veckan hinns alla kommuner med på ungefär tre veckor.

Resultatet skrivs till arbete/hamtning/sokresultat.json. Nyckeln skrivs aldrig ut.
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
from gemensamt import (SOKRESULTAT, TILLSTAND, doman, enkel, idag, kommuner,  # noqa: E402
                       las_json, skriv_json)

API = "https://api.search.brave.com/res/v1/web/search"
STATUSORDNING = {5: 0, 4: 1, 3: 2, 2: 3, 1: 4, 0: 5}


class Brave:
    def __init__(self, nyckel):
        self.nyckel = nyckel
        self.land = True
        self.antal = 0

    def sok(self, q, freshness):
        params = {"q": q, "count": 20, "freshness": freshness, "safesearch": "off"}
        if self.land:
            params.update(country="SE", search_lang="sv")
        url = API + "?" + urllib.parse.urlencode(params)
        for forsok in range(4):
            req = urllib.request.Request(url, headers={
                "Accept": "application/json",
                "X-Subscription-Token": self.nyckel,
            })
            try:
                time.sleep(1.1)  # gratisnivån tillåter ungefär ett anrop per sekund
                with urllib.request.urlopen(req, timeout=30) as r:
                    self.antal += 1
                    return json.loads(r.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                if e.code == 422 and self.land:
                    self.land = False  # parametrarna för land/språk godtogs inte, försök utan
                    return self.sok(q, freshness)
                if e.code == 429:
                    time.sleep(5 * (forsok + 1))
                    continue
                if e.code in (401, 403):
                    raise SystemExit(f"Brave Search API svarade {e.code}: kontrollera nyckeln (secret BRAVE_API_KEY).")
                print(f"  sökfel {e.code}", flush=True)
                return None
            except Exception as e:  # nätverksfel
                print(f"  sökfel: {type(e).__name__}", flush=True)
                time.sleep(3)
        return None


def traffar(svar):
    ut = []
    for r in ((svar or {}).get("web") or {}).get("results") or []:
        ut.append({
            "url": r.get("url"),
            "titel": r.get("title"),
            "beskrivning": r.get("description"),
            "alder": r.get("page_age") or r.get("age"),
        })
    return [t for t in ut if t["url"]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-sok", type=int, default=int(os.environ.get("MAX_SOK") or 250),
                    help="högsta antal anrop till Brave i den här körningen")
    ap.add_argument("--fran", default="2026-01-01", help="sök bara sidor från detta datum")
    a = ap.parse_args()

    nyckel = os.environ.get("BRAVE_API_KEY", "").strip()
    if not nyckel:
        raise SystemExit("BRAVE_API_KEY saknas. Lägg nyckeln under Settings → Secrets and variables → Actions → Repository secrets med namnet BRAVE_API_KEY.")

    data = kommuner()
    tillst = las_json(TILLSTAND, {"kommuner": {}, "dokument": {}})
    km = tillst.setdefault("kommuner", {})
    ordning = sorted(data, key=lambda k: (km.get(k["id"], {}).get("senast_sokt", ""),
                                          STATUSORDNING[k["s"]], k["k"]))
    freshness = f"{a.fran}to{idag()}"
    brave = Brave(nyckel)
    resultat = {"datum": idag(), "kommuner": {}}

    # Sökning 1: kommunens egen webbplats. Sökning 2 (status 3–5): reformorden på hela webben.
    for k in ordning:
        for omgang in (1, 2) if k["s"] >= 3 else (1,):
            if brave.antal >= a.max_sok:
                break
            dom = doman(k["w"])
            namn = k["k"]
            if omgang == 1:
                q = f"site:{dom} budget 2027 filetype:pdf"
            else:
                q = f"{namn} kommun budget 2027 undervisningstid lärare"
            svar = brave.sok(q, freshness)
            t = traffar(svar)
            if omgang == 2:  # behåll bara träffar som rör rätt kommun
                n = enkel(namn)
                t = [x for x in t if doman(x["url"]).endswith(dom)
                     or n in enkel((x["titel"] or "") + " " + (x["beskrivning"] or "") + " " + x["url"])]
            post = resultat["kommuner"].setdefault(k["id"], {"kommun": namn, "status": k["s"], "traffar": []})
            sedda = {x["url"] for x in post["traffar"]}
            post["traffar"] += [dict(x, sokning=omgang) for x in t if x["url"] not in sedda]
            km.setdefault(k["id"], {})["senast_sokt"] = idag()
            print(f"[{omgang}] {namn}: {len(t)} träffar", flush=True)

    skriv_json(SOKRESULTAT, resultat)
    skriv_json(TILLSTAND, tillst)
    print(f"Klart: {brave.antal} sökningar, {len(resultat['kommuner'])} kommuner.")


if __name__ == "__main__":
    main()
