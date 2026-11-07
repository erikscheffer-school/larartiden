"""Gemensamma funktioner för hämtningsskripten i verktyg/hamta/.

Skripten körs varje vecka i GitHub Actions (.github/workflows/hamta.yml).
API-nyckeln läses ur miljövariabeln BRAVE_API_KEY och skrivs aldrig ut.
"""
import json
import re
import time
import unicodedata
import urllib.parse
import urllib.request
import urllib.robotparser
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "kommuner.json"
HAMTNING = ROOT / "arbete" / "hamtning"
TILLSTAND = HAMTNING / "tillstand.json"
SOKRESULTAT = HAMTNING / "sokresultat.json"
DOKUMENT = HAMTNING / "dokument"
VECKOLISTA = ROOT / "arbete" / "veckolista"
CACHE = ROOT / ".cache" / "pdf"  # sparas mellan körningar med actions/cache, committas inte

USER_AGENT = "larartiden-hamtning/1.0 (+https://github.com/erikscheffer-school/larartiden)"
PAUS_PER_VARD = 3.0  # sekunder mellan anrop till samma webbplats

# Ord som tyder på att dokumentet handlar om reformen (samma ord som i metod/metod.md).
# Starka ord gäller reformen nästan alltid. Svaga ord används också om annat (garanterad
# undervisningstid, förskollärares planeringstid) och räknas bara med reformsammanhang.
STARKA = ["reglerad undervisningstid", "reglering av undervisningstid", "reglera undervisningstid",
          "tid för undervisningsuppdraget", "undervisningsuppdrag", "lärares arbetstid",
          "lärarnas arbetstid", "lärares undervisningstid", "reglerad undervisnings- och planeringstid"]
SVAGA = ["undervisningstid", "planeringstid", "undervisningstimmar", "lärartäthet"]
REFORMORD = STARKA + SVAGA
REFORMKONTEXT = re.compile(r"regler|reform|nationell|lagförslag|lagändring|prop\.|proposition|1 juli 2027|sou 2025|2025/26:196", re.I)
INTE_REFORM = re.compile(r"garanterad\W+undervisningstid|erbjuden\W+undervisningstid|förskollär|barnskötar", re.I)
# Mötesportaler där kommunens handlingar ofta ligger på en annan domän.
PORTALER = ["netpublicator", "meetingsplus", "ciceron", "lexkommun", "edok", "dokument.", "handlingar.",
            "politik.", "sammantraden", "insynsverige", "kommunkartan.se/handling"]
# Statsbidrag räknas bara som träff i närheten av lärare/undervisning.
STATSBIDRAG = re.compile(r"statsbidrag", re.I)
STATSBIDRAG_KONTEXT = re.compile(r"lärar|undervisn|skol", re.I)
BELOPP = re.compile(r"\d[\d\s ]*(?:,\d+)?\s*(?:mnkr|mkr|tkr|miljoner|milj\.|mn kr|kronor|kr\b)", re.I)


def idag():
    return date.today().isoformat()


def las_json(p, standard):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return standard


def skriv_json(p, data):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def kommuner():
    return json.loads(DATA.read_text(encoding="utf-8"))


def doman(url):
    h = (urllib.parse.urlparse(url).hostname or "").lower()
    return h[4:] if h.startswith("www.") else h


def normalisera_url(url):
    u = urllib.parse.urlparse(url.strip())
    host = (u.hostname or "").lower().removeprefix("www.")
    return f"{host}{u.path.rstrip('/')}{'?' + u.query if u.query else ''}".lower()


def enkel(text):
    """Gemener utan diakritiska tecken utom åäö, för jämförelser av namn."""
    return unicodedata.normalize("NFC", text).lower()


def kommunhandling(url, kommun):
    """Ligger dokumentet på kommunens webbplats eller en mötesportal (inte en tidning eller myndighet)?"""
    d, u = doman(kommun["w"]), url.lower()
    return doman(url).endswith(d) or any(p in u for p in PORTALER)


def namn_finns(namn, text):
    """Kommunnamnet som eget ord, så att Ale inte matchar Salem."""
    return re.search(rf"(?<![a-zåäöé]){re.escape(namn.lower())}(?![a-zäöé])", text.lower()) is not None


def kanda_urler(data):
    """URL:er som redan finns i data/kommuner.json, per kommun-id."""
    ut = {}
    for k in data:
        s = ut.setdefault(k["id"], set())
        for d in k.get("docs") or []:
            if d.get("u"):
                s.add(normalisera_url(d["u"]))
        if k.get("kfu"):
            s.add(normalisera_url(k["kfu"]))
    return ut


class Hamtare:
    """Hämtar sidor artigt: följer robots.txt och pausar mellan anrop till samma värd."""

    def __init__(self):
        self.senast = {}
        self.robots = {}

    def tillats(self, url):
        p = urllib.parse.urlparse(url)
        bas = f"{p.scheme}://{p.netloc}"
        if bas not in self.robots:
            rp = urllib.robotparser.RobotFileParser()
            try:
                req = urllib.request.Request(bas + "/robots.txt", headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=15) as r:
                    rp.parse(r.read(200_000).decode("utf-8", "replace").splitlines())
            except Exception:
                rp = None  # ingen robots.txt går att läsa: tillåt
            self.robots[bas] = rp
        rp = self.robots[bas]
        return True if rp is None else rp.can_fetch(USER_AGENT, url)

    def hamta(self, url, maxbytes=30_000_000, timeout=60):
        host = urllib.parse.urlparse(url).netloc
        vanta = PAUS_PER_VARD - (time.time() - self.senast.get(host, 0))
        if vanta > 0:
            time.sleep(vanta)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                typ = r.headers.get("Content-Type", "")
                langd = int(r.headers.get("Content-Length") or 0)
                if langd > maxbytes:
                    raise ValueError(f"för stor ({langd // 1_000_000} MB)")
                data = r.read(maxbytes + 1)
                if len(data) > maxbytes:
                    raise ValueError("för stor")
                return data, typ, r.geturl()
        finally:
            self.senast[host] = time.time()
