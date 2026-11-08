"""Prov: hur fungerar kommunkartan.se:s API? Läser robots.txt och JS-filerna och söker efter API-adresser."""
import json, re, sys, urllib.request
sys.path.insert(0, "verktyg/hamta")
from gemensamt import USER_AGENT
UT = "arbete/granskning/prov/ut/"
def get(u, data=None, typ=None):
    h = {"User-Agent": USER_AGENT}
    if typ: h["Content-Type"] = typ
    r = urllib.request.urlopen(urllib.request.Request(u, data=data, headers=h), timeout=30)
    return r.status, r.read().decode("utf-8", "replace")
out = []
s, t = get("https://kommunkartan.se/robots.txt"); out.append("ROBOTS:\n" + t[:2000])
s, html = get("https://kommunkartan.se/karta/salems-kommun/")
js = sorted(set(re.findall(r'src="([^"]+\.js[^"]*)"', html)))
out.append("JS: " + " ".join(js))
for j in js:
    u = j if j.startswith("http") else "https://kommunkartan.se" + j
    if "kommunkartan" not in u: continue
    try:
        s, t = get(u)
    except Exception as e:
        out.append(f"{u} FEL {e}"); continue
    for m in set(re.findall(r'["\'`](/api/[a-zA-Z0-9_\-/]+)', t)):
        out.append(f"API {m}")
    for m in re.finditer(r'map-item-cards', t):
        out.append("KONTEXT cards: " + t[max(0, m.start()-600):m.end()+600].replace("\n", " "))
    for m in re.finditer(r'search|q=|query', t):
        pass
# provanrop
for u in ["https://kommunkartan.se/api/map-item-locations/?published_from_date=2026-09-01&published_to_date=2026-11-08&municipality=lunds-kommun"]:
    s, t = get(u); d = json.loads(t); out.append(f"{u}: {len(d)} poster, exempel {t[:300]}")
    ids = [x["id"] for x in d[:5]]; item_ids = [x["item_id"] for x in d[:5]]
    for body in (json.dumps(ids), json.dumps({"ids": ids}), json.dumps(item_ids), json.dumps({"item_ids": item_ids})):
        try:
            s, t = get("https://kommunkartan.se/api/map-item-cards/", body.encode(), "application/json")
            out.append(f"CARDS {body[:60]} -> {s} {t[:400]}")
        except Exception as e:
            out.append(f"CARDS {body[:60]} -> FEL {e}")
open(UT + "kommunkartan.txt", "w").write("\n\n".join(out))
print("klart")
