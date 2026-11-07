"""Hämtare för enskilda mötesportaler. Används av portaler.py.

Netpublicator: portalen har ett öppet JSON-gränssnitt,
  https://docs.netpublicator.com/api/public/<läsar-id>/read?hash=<sökväg>
som returnerar "items" av typen channel (mapp, nämnd eller ärende), meeting (möte,
text = datum) och document. Ett dokument hämtas från
  https://docs.netpublicator.com/api/public/<läsar-id>/document/<dok-id>?hash=<sökväg>
Sökvägen är id:n sammanfogade med bindestreck, med läsarens rot-hash först. Rot-hashen
står inte i adressen och läses av från första anropet när läsaren öppnas i webbläsaren.

MeetingsPlus: sidorna renderas på servern med adresserna
  /committees/<nämnd>/mote-ÅÅÅÅ-MM-DD/... och dokument med ?downloadMode=open.

Båda går bara in i fullmäktige, kommunstyrelsen och skol- och utbildningsnämnder, och
bara i möten från FRAN_DATUM och framåt.
"""
import asyncio
import html
import re

FRAN_DATUM = "2026-02-01"
ORGAN = re.compile(r"fullmäktige|kommunstyrelse|utbildning|bildning|barn- och|barn och|skol|lärande|budget", re.I)
GAMMAL = re.compile(r"(19|20)\d\d\s*[-–]\s*20(1\d|2[0-5])\b|\b20(1\d|2[0-5])$")
ARENDE = re.compile(r"budget|2027|ramar|ram\b|skattesats|mål och|flerårsplan|resursplan|verksamhetsplan|"
                    r"planeringsdirektiv|nulägesanalys|förutsättningar|direktiv|strategisk plan|kommunplan|"
                    r"undervisningstid|undervisningsuppdrag", re.I)
DATUM = re.compile(r"20\d\d-\d\d-\d\d")
PAUS = 0.5


def text(s):
    return " ".join(html.unescape(s or "").split())


class Netpublicator:
    API = "https://docs.netpublicator.com/api/public"

    def __init__(self, request, logg=print, max_anrop=200):
        self.request = request  # Playwright APIRequestContext
        self.logg = logg
        self.max_anrop = max_anrop
        self.anrop = 0

    async def las(self, rid, sokvag, rot=False):
        if self.anrop >= self.max_anrop:
            return []
        self.anrop += 1
        await asyncio.sleep(PAUS)
        try:
            # Rotnivån läses med isr=true, precis som läsaren själv gör.
            isr = "true" if rot else "false"
            r = await self.request.get(f"{self.API}/{rid}/read?hash={sokvag}&isr={isr}", timeout=30_000,
                                       headers={"Referer": f"https://www.netpublicator.com/reader/{rid}",
                                                "Origin": "https://www.netpublicator.com",
                                                "Accept": "application/json"})
            if not r.ok:
                if rot:
                    self.logg(f"    Netpublicator {rid}: rotnivån svarade {r.status}")
                return []
            return (await r.json()).get("items") or []
        except Exception:
            return []

    @staticmethod
    async def rot_hash(context, rid):
        """Öppnar läsaren och läser av rot-hashen från första anropet till gränssnittet."""
        page = await context.new_page()
        hittad = asyncio.get_event_loop().create_future()

        def vid_anrop(req):
            m = re.search(rf"/api/public/{rid}/read\?hash=([0-9a-f]+)", req.url)
            if m and not hittad.done():
                hittad.set_result(m.group(1))

        page.on("request", vid_anrop)
        try:
            await page.goto(f"https://www.netpublicator.com/reader/{rid}", wait_until="domcontentloaded", timeout=30_000)
            return await asyncio.wait_for(hittad, 20)
        except Exception:
            return None
        finally:
            await page.close()

    def dok(self, rid, sokvag, item, titel):
        return {"url": f"{self.API}/{rid}/document/{item['id']}?hash={sokvag}",
                "titel": titel, "beskrivning": titel}

    async def genomsok(self, context, rid):
        rot = await self.rot_hash(context, rid)
        if not rot:
            self.logg(f"    Netpublicator {rid}: rot-hashen hittades inte")
            return []
        ut = []

        async def kanal(sokvag, namn, djup):
            for it in await self.las(rid, sokvag):
                t, typ, s = text(it.get("text")), it.get("type"), f"{sokvag}-{it['id']}"
                if typ == "meeting":
                    d = DATUM.search(t)
                    if d and d.group(0) >= FRAN_DATUM:
                        await mote(s, f"{namn} {t}")
                elif typ == "document" and ARENDE.search(t):
                    ut.append(self.dok(rid, sokvag, it, f"{namn} – {t}"))
                elif typ == "channel" and djup < 2 and ORGAN.search(f"{namn} {t}") and not GAMMAL.search(t):
                    await kanal(s, f"{namn} {t}".strip(), djup + 1)

        async def mote(sokvag, namn):
            for it in await self.las(rid, sokvag):
                t, typ, s = text(it.get("text")), it.get("type"), f"{sokvag}-{it['id']}"
                if typ == "document":  # kallelse, protokoll och liknande på mötesnivå
                    ut.append(self.dok(rid, sokvag, it, f"{namn} – {t}"))
                elif typ == "channel" and ARENDE.search(t):  # ett ärende om budget eller 2027
                    for d in await self.las(rid, s):
                        if d.get("type") == "document":
                            ut.append(self.dok(rid, s, d, f"{namn} – {t} – {text(d.get('text'))}"))

        rotniva = await self.las(rid, rot, rot=True)
        self.logg(f"    Netpublicator {rid}: rotnivån har {len(rotniva)} mappar: "
                  + "; ".join(text(i.get("text")) for i in rotniva[:8]))
        for it in rotniva:
            t = text(it.get("text"))
            if it.get("type") == "channel" and ORGAN.search(t) and not GAMMAL.search(t):
                await kanal(f"{rot}-{it['id']}", t, 0)
        self.logg(f"    Netpublicator {rid}: {self.anrop} anrop, {len(ut)} dokument")
        return ut


async def meetingsplus(context, bas, logg=print, max_sidor=40):
    """Går igenom /committees på en MeetingsPlus-portal och samlar dokumentlänkar."""
    page = await context.new_page()
    ut, besokta = {}, 0

    async def lankar(url):
        nonlocal besokta
        besokta += 1
        await asyncio.sleep(1.0)
        await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        return await page.eval_on_selector_all(
            "a[href]", "els => els.map(e => [e.href, (e.innerText || '').trim().slice(0, 200)])")

    try:
        namnder = [(h, t) for h, t in await lankar(f"{bas}/committees")
                   if re.search(r"/committees/[^/#?]+$", h) and ORGAN.search(t)]
        for nurl, namn in namnder:
            if besokta >= max_sidor:
                break
            moten = sorted({h for h, _ in await lankar(nurl)
                            if re.search(r"/mote-(20\d\d-\d\d-\d\d)", h)
                            and re.search(r"/mote-(20\d\d-\d\d-\d\d)", h).group(1) >= FRAN_DATUM
                            and "downloadMode" not in h}, reverse=True)
            for murl in moten[:8]:
                if besokta >= max_sidor:
                    break
                datum = re.search(r"mote-(20\d\d-\d\d-\d\d)", murl).group(1)
                for h, t in await lankar(murl):
                    if "downloadmode" in h.lower() or h.lower().split("?")[0].endswith(".pdf"):
                        titel = f"{namn} {datum} – {t or h.rsplit('/', 1)[-1]}"
                        ut.setdefault(h, {"url": h, "titel": titel, "beskrivning": titel})
    except Exception as e:
        logg(f"    MeetingsPlus {bas}: {type(e).__name__}")
    finally:
        await page.close()
    logg(f"    MeetingsPlus {bas}: {besokta} sidor, {len(ut)} dokument")
    return list(ut.values())
