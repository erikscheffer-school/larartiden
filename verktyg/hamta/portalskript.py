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

    async def genomsok(self, context, rid, rot=None):
        # Rot-hashen kan vara känd från en inbäddad läsare på kommunens webbplats (Sitevision-modul).
        rot = rot or await self.rot_hash(context, rid)
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
        traffade = False
        for it in rotniva:
            t = text(it.get("text"))
            if it.get("type") == "channel" and ORGAN.search(t) and not GAMMAL.search(t):
                traffade = True
                await kanal(f"{rot}-{it['id']}", t, 0)
        if not traffade:
            # Rotnivån har samlingsmappar ("Politiken", "Nämnder"): gå ett steg ner och leta där.
            for it in rotniva:
                t = text(it.get("text"))
                if it.get("type") == "channel" and re.search(r"politik|nämnd|organ|sammanträd|möten|handlingar", t, re.I):
                    for under in await self.las(rid, f"{rot}-{it['id']}"):
                        u = text(under.get("text"))
                        if under.get("type") == "channel" and ORGAN.search(u) and not GAMMAL.search(u):
                            await kanal(f"{rot}-{it['id']}-{under['id']}", u, 0)
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


async def opengov(context, bas, logg=print, fran="2026-08-15", max_moten=14):
    """Public 360 OpenGov (opengov.360online.com/Meetings/<KOD>): nämnder -> möten -> filer.

    Mötessidan visar kallelsen som fil. Ärenden på dagordningen som gäller budget eller 2027
    fälls ut med ett klick, och deras bilagor samlas också."""
    page = await context.new_page()
    ut, besokta = {}, 0

    async def ga(url):
        nonlocal besokta
        besokta += 1
        await asyncio.sleep(1.0)
        await page.goto(url, wait_until="domcontentloaded", timeout=40_000)
        await page.wait_for_timeout(800)
        return await page.eval_on_selector_all(
            "a[href]", "els => els.map(e => [e.href, (e.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 200)])")

    def filer(lankar, rubrik):
        for h, t in lankar:
            if "/File/Details/" in h:
                titel = f"{rubrik} – {t or h.rsplit('fileName=', 1)[-1]}"
                ut.setdefault(h, {"url": h, "titel": titel, "beskrivning": titel})

    try:
        namnder = [(h, t) for h, t in await ga(bas) if "/Boards/Details/" in h and ORGAN.search(t)]
        moten = []
        for nurl, namn in namnder[:6]:
            for h, t in await ga(nurl):
                d = DATUM.search(t)
                if "/Meetings/Details/" in h and d and d.group(0) >= fran:
                    moten.append((d.group(0), h, t))
        for datum, murl, namn in sorted(set(moten), reverse=True)[:max_moten]:
            lankar = await ga(murl)
            filer(lankar, namn)
            # Fäll ut ärenden om budget och 2027 och samla deras bilagor.
            n = await page.evaluate("""(re) => { const r = new RegExp(re, 'i'); let n = 0;
                for (const e of document.querySelectorAll('a, button, [role=button], li, .agenda-item, h3, h4')) {
                  if (n < 6 && r.test(e.innerText || '') && (e.innerText || '').length < 220) { e.click(); n++; } }
                return n; }""", ARENDE.pattern)
            if n:
                await page.wait_for_timeout(2500)
                filer(await page.eval_on_selector_all(
                    "a[href]", "els => els.map(e => [e.href, (e.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 200)])"),
                    namn)
    except Exception as e:
        logg(f"    OpenGov {bas}: {type(e).__name__}")
    finally:
        await page.close()
    logg(f"    OpenGov {bas}: {besokta} sidor, {len(ut)} filer")
    return list(ut.values())


async def documentweb(context, start, logg=print, fran="2026-08-15", max_dok=12):
    """DocumentWeb (documentweb.<kommun>.se/?folderId=...): mappar och dokument via /api/folders/<id>.

    Nedladdningsadressen (/api/download/<id>/<fil-id>) står inte i mappens JSON, så dokumentet
    klickas fram i gränssnittet och adressen läses av från anropet."""
    import urllib.parse
    p = urllib.parse.urlparse(start)
    bas = f"{p.scheme}://{p.netloc}"
    fid = urllib.parse.parse_qs(p.query).get("folderId", [""])[0]
    ut = []
    try:
        r = await context.request.get(f"{bas}/api/folders/{fid}", timeout=30_000)
        if not r.ok:
            logg(f"    DocumentWeb {start}: {r.status}")
            return []
        rot = await r.json()
    except Exception as e:
        logg(f"    DocumentWeb {start}: {type(e).__name__}")
        return []
    kandidater = []

    def ga(mapp, namn):
        for d in mapp.get("documents") or []:
            t = d.get("name") or ""
            ds = DATUM.findall(t)
            if (ds and max(ds) >= fran) or (ARENDE.search(t) and "2027" in t):
                kandidater.append((max(ds) if ds else "", mapp.get("id"), t, f"{namn} – {t}"))
        for m in mapp.get("folders") or []:
            if not GAMMAL.search(m.get("name") or "") and not re.search(r"20(1\d|2[0-5])\b", m.get("name") or ""):
                ga(m, m.get("name") or namn)

    ga(rot, rot.get("name") or "")
    kandidater = sorted(kandidater, reverse=True)[:max_dok]
    if not kandidater:
        return []
    page = await context.new_page()
    adresser = []
    page.on("request", lambda req: adresser.append(req.url) if "/api/download/" in req.url else None)
    try:
        for _, mapp, namn, titel in kandidater:
            await page.goto(f"{bas}/?folderId={mapp}", wait_until="networkidle", timeout=40_000)
            n0 = len(adresser)
            try:
                await page.get_by_text(namn, exact=False).first.click(timeout=8000)
                await page.wait_for_timeout(2500)
            except Exception:
                continue
            if len(adresser) > n0:
                ut.append({"url": adresser[n0], "titel": titel, "beskrivning": titel})
    finally:
        await page.close()
    logg(f"    DocumentWeb {start}: {len(kandidater)} aktuella dokument, {len(ut)} adresser")
    return ut
