## Prompten

Här är hela prompten för att bygga en egen version av sidan från början. Den beskriver vad sidan ska innehålla, hur kommunerna granskas, hur data lagras, hur sidan ska se ut och hur arbetet ska dokumenteras. Den bygger på [loggen över instruktionerna](#metod-logg) och på hur sidan ser ut i dag, men är skriven så att den går att använda utan att känna till det här projektet.

**Så använder du den**

1. Kopiera prompten och klistra in den i en chatt med en AI-assistent som kan söka på webben, använda en webbläsare, läsa PDF-filer och skriva till ett GitHub-repo.
2. Byt ut allt som står inom hakparentes, till exempel `[ditt namn]`.
3. Skapa ett tomt repo på GitHub och, om du vill ha besökarnas bedömningar, ett gratis projekt på Supabase innan du börjar.
4. En hel genomgång av 290 kommuner tar lång tid. Räkna med att skriva "fortsätt" många gånger, gärna under flera dagar.

Under [Utveckla prompten](#metod-utveckla) finns förslag på vad du kan ändra om du vill göra granskningen bättre eller undersöka något annat.

---PROMPT---
# Uppdrag

Du ska bygga, fylla och publicera en webbplats som heter "Lärartiden i budgeten". Den visar hur Sveriges 290 kommuner hanterar regleringen av lärares undervisningstid i sina budgetar för 2027.

Bakgrund (kontrollera mot källorna innan du skriver något på sidan):
- Regeringens proposition 2025/26:196 Tid för undervisningsuppdraget reglerar hur mycket lärare ska undervisa. Den gäller från 1 juli 2027.
- Staten kompenserar kommunerna via det generella statsbidraget med 1,3 miljarder kronor 2027 och cirka 2,6 miljarder kronor per år därefter.
- Pengarna är inte öronmärkta. Varje kommun avgör själv om de går till skolan.
- Frågan sidan ska besvara: För kommunerna synligt pengarna vidare till skolan i budget 2027?
- 2026 är valår. Många kommuner beslutar budget 2027 i november eller december. En del fattade ett första beslut i juni och fattar ett nytt efter valet.

Den som ansvarar för sidan heter [ditt namn] och nås på [din mejladress]. Skriv i jagform för hens räkning på sidan, till exempel "Här följer jag om ...".

# Grundregler

1. Hitta aldrig på citat, belopp, datum, paragrafer eller länkar. Är något okänt, lämna fältet tomt och skriv det under luckor.
2. Citat ska vara kopierade ordagrant ur originaldokumentet, med sidnummer. Återge aldrig ett citat från en sammanfattning eller ett sökresultat.
3. Varje påstående om en kommun ska gå att kontrollera via en länk till ett dokument.
4. Var ärlig om osäkerhet. Det är bättre att en kommun står som "Ej bedömbart än" än att den får en status som inte går att belägga.
5. Skriv på enkel och saklig svenska. Inga säljande eller värderande formuleringar. Inga förkortningar som läsaren inte känner till utan förklaring.
6. Logga varje instruktion du får (se Dokumentation nedan).

# Teknik

- Statisk webbplats i GitHub-repot [ditt-konto/ditt-repo], publicerad med GitHub Pages från grenen main. Lägg en tom fil `.nojekyll` i roten.
- Ingen byggprocess och inga ramverk. Ren HTML, CSS och JavaScript.
- Markdown renderas i webbläsaren med `marked@12.0.2` från cdn.jsdelivr.net. Skriv en enkel reservfunktion (rubriker, stycken, listor, fet, kursiv, länkar) om biblioteket inte laddas.
- Inga webbtypsnitt och inga andra externa anrop än Markdown-biblioteket och Supabase.
- Besökarnas bedömningar sparas i Supabase (se Databas nedan). Sidan ska fungera även om databasen inte svarar.

Filer:

| Fil | Innehåll |
|---|---|
| `index.html` | Sidans struktur och fasta texter |
| `assets/styles.css` | Utseende |
| `assets/app.js` | All logik |
| `assets/config.js` | Inställningar: datum för "läget", kontaktadress, Supabase-adress och publik nyckel |
| `data/kommuner.json` | En post per kommun |
| `texter/index.json` | Lista över analystexter, tom (`[]`) från början |
| `texter/*.md` | Analystexter, en fil per text |
| `metod/metod.md` | Hur sidan gjordes |
| `metod/logg.md` | Logg över alla instruktioner |
| `metod/prompt.md` | Den här prompten, med en kort inledning, sedan en rad med bara `---PROMPT---`, sedan prompten |
| `metod/utveckla.md` | Förslag på hur prompten kan utvecklas |
| `supabase/schema.sql` | Databasskriptet nedan |
| `README.md` | Filförteckning, fältförklaring och hur man uppdaterar |
| `arbete/INSTRUKTIONER.md` | Kort arbetsinstruktion för nästa granskningsomgång |
| `arbete/att_granska.json` | Kommuner som behöver granskas igen, med anteckningar om vad som saknas |

# Datamodell

`data/kommuner.json` är en lista med en post per kommun, alla 290. Fält:

- `k` kommunnamn, `id` adressnamn (gemener, å och ä blir a, ö blir o, mellanslag blir bindestreck), `l` län
- `s` status 0–5 (se Status)
- `sum` sammanfattning i två till fyra meningar
- `m` pengar uttryckligen kopplade till reformen: belopp, år, mottagande nämnd och om det är beslutat eller föreslaget
- `mk` kommunens egen beräknade merkostnad, med källa
- `kort` en mycket kort beloppsrad för startsidan, högst cirka 60 tecken, bara för status 0–2. Exempel: "2,1 mnkr 2027 och 4,2 mnkr per år från 2028." Om beloppet är oklart, säg det kort: "Beloppet för 2027 anges inte."
- `sb` hur kommunen beskriver statsbidraget
- `pl` om prislista eller samverkan, till exempel gymnasiets regionala prislistor
- `kf` när fullmäktige beslutar eller beslutade budget 2027, med paragraf och om det är beslutat eller planerat. `kfu` länk till källan
- `w` kommunens webbplats
- `lu` luckor i granskningen, i hela meningar: vad som inte hittats, inte kunnat öppnas eller inte kunnat kontrolleras
- `docs` lista över granskade dokument. Varje dokument: `t` titel, `d` datum (ÅÅÅÅ-MM-DD), `sk` skede ("underlag/förslag" eller "beslut"), `pr` producent ("tjänstemannaproducerat" eller "politiskt producerat"), `nr` om dokumentet nämner reformen (true eller false), `c` kort ordagrant citat med sidnummer, `u` länk

Okända fält sätts till null. Validera alltid att filen är giltig JSON och innehåller 290 poster innan du publicerar.

# Status

| Värde | Namn | Kortnamn | Betydelse |
|---|---|---|---|
| 0 | Pengar avsatta/beslutade | Pengar beslutade | Budget- eller nämndbeslut avsätter pengar uttryckligen kopplade till reformen |
| 1 | Pengar föreslagna | Pengar föreslagna | Förslag från förvaltning, majoritet eller opposition om pengar kopplade till reformen, inte bekräftat beslutat |
| 2 | Kostnad beräknad, inga pengar | Kostnad beräknad | Kommunen har räknat på merkostnad eller lärarbehov men inte avsatt pengar i det som granskats |
| 3 | Nämnt utan belopp | Nämnt utan belopp | Reformen nämns i handlingarna utan kostnad eller pengar |
| 4 | Ej nämnt i granskade dokument | Ej nämnt | Budgethandlingar för 2027 har granskats men reformen nämns inte |
| 5 | Inga budgethandlingar 2027 hittade | Ej bedömbart än | Inga budgethandlingar för 2027 kunde hittas eller öppnas. Säger inget om vad kommunen gjort |

Se upp: pengar till "utökad undervisningstid" för elever är en annan sak än reglerad undervisningstid för lärare. Läs alltid sammanhanget. Om pengarna delas med andra satsningar, skriv det.

# Granskning av en kommun

1. Gå till kommunens webbplats och dess mötesportal för kommunfullmäktige, kommunstyrelse och barn- och utbildningsnämnd eller motsvarande. Använd en riktig webbläsare för portaler som kräver JavaScript, till exempel Ciceron, Netpublicator och MeetingPlus.
2. Leta efter budgethandlingar för 2027: planeringsförutsättningar, budgetdirektiv, nämndernas budgetunderlag, budgetförslag från majoritet och opposition, kallelser och protokoll. Leta också efter kommunens remissvar på SOU 2025:26.
3. Ta reda på när kommunstyrelsen och fullmäktige behandlar budget 2027.
4. Ladda ner PDF-filerna och sök i texten efter: undervisningstid, undervisningsuppdrag, lärares arbetstid, reglerad undervisningstid, planeringstid, statsbidrag. Läs varje träff i sitt sammanhang. Är en PDF inskannad utan text, skriv det under luckor.
5. Fyll i fälten och sätt status. Skriv luckorna ärligt. Lägg till kommunens webbplats.
6. Kommuner med status 5 läggs i `arbete/att_granska.json` med anteckningar om vad som saknas och när budgeten väntas beslutas.

# Sidans delar

Sidan har flikar högst upp. Varje flik och varje kommun ska gå att länka till med en adress efter #: `#oversikt`, `#kommuner`, `#kommun-<id>`, `#metod-metod`, `#metod-logg`, `#metod-prompt`, `#metod-utveckla`, `#kontakt`.

**1. Översikt**
- Rubriken "Följer pengarna med till skolan?" och en kort inledning om reformen och statsbidraget.
- En ruta per kommun, 290 små kvadrater i ett rutnät, sorterade efter status och färgade efter status. Kommuner med status 5 är tomma rutor med kantlinje. Varje ruta visar kommunens namn och status när man håller muspekaren över den och öppnar kommunens sida vid klick.
- En teckenförklaring med antal per status.
- En kort förklaring av att många kommuner beslutar budget i november eller december och att "Ej bedömbart än" inte betyder att kommunen avstått.
- Rubriken "Kommuner som avsatt pengar eller räknat på kostnaden" med kommunerna i status 0, 1 och 2, grupperade per status. För varje kommun visas bara namn, län och fältet `kort`. Allt annat finns under fliken Kommuner.

**2. Kommuner**
- Sökfält, filter på län och kryssrutor för status.
- Sorterbar tabell: kommun, län, status, pengar kopplade till reformen, budgetbeslut 2027, antal bedömningar.
- Klick på en rad öppnar kommunens sida ovanför tabellen, med:
  - namn, län och status
  - sammanfattning
  - uppgifter: pengar kopplade till reformen, egen beräknad merkostnad, om statsbidraget, om prislista eller samverkan, fullmäktiges budgetbeslut med källa
  - rutan "Luckor i granskningen", markerad med gul bakgrund som en överstrykningspenna, med luckorna som punktlista (dela fältet `lu` vid meningsslut utan att bryta vid förkortningar som "s. 12" eller "t.ex.")
  - avsnittet "Var du kan fortsätta leta": länk till kommunens webbplats, att politiska handlingar oftast finns under rubriker som "Kommun och politik", "Politik och demokrati" eller "Möten, handlingar och protokoll", när budgeten beslutas om det är känt, att budgeten oftast först behandlas i kommunstyrelsen som föreslår beslut till fullmäktige, att det nyvalda fullmäktige under valår fastställer budgeten, ofta i november eller december, samt bra sökord
  - granskade dokument med titel, datum, skede, producent, om reformen nämns, citat och en länk "Öppna dokumentet" följt av webbplatsens namn
  - ett formulär "Stämmer det här?" där besökaren bedömer tre frågor från 1 (inte alls) till 5 (helt): Stämmer citaten och uppgifterna? Är dokumenten rimliga att granska? Är slutsatsen (status) rimlig? Plus en frivillig kommentar. Visa antal bedömningar och snitt om det finns. Lägg ett dolt honungsfält mot spam och kom ihåg i webbläsarens localStorage att besökaren redan bedömt kommunen.
  - mejladress för synpunkter

**3. Analys**
Visas bara när `texter/index.json` innehåller minst en text. Varje text är en Markdown-fil. Lämna listan tom. Ansvarig skriver egna texter.

**4. Metod och källor**
Fyra delar, valda med knappar högst upp:
- "Så gjordes sidan" (`metod/metod.md`): vem som gjort vad, vad som har undersökts, hur arbetet gick till, statusdefinitionerna, dokumenttyperna, begränsningar och centrala källor (regeringens pressmeddelande, propositionen, SKR:s cirkulär och remissvar).
- "Logg över instruktionerna" (`metod/logg.md`).
- "Prompten" (`metod/prompt.md`): inledningen som text, sedan en knapp "Kopiera prompten", antal ord och hela prompten synlig i en ruta med fast teckenbredd. Prompten ska visas i sin helhet på sidan, inte bara som länk.
- "Utveckla prompten" (`metod/utveckla.md`): förslag på vad man kan ändra.

**5. Kontakt**
Kort text om att rättelser och bättre dokument är välkomna, mejladressen och en knapp som kopierar den.

Sidfot: "Sammanställt av [ditt namn]" och länkar till rådata och GitHub-repot.

# Utseende

Sidan ska se ut som en omsorgsfull egen sammanställning, inte som en mall eller ett AI-genererat gränssnitt.

- Rubriker i en rapportlik serif ur systemets typsnitt: `Charter, "Bitstream Charter", "Sitka Text", Cambria, "Iowan Old Style", Georgia, serif`. Brödtext i systemets sans: `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif`.
- Vit bakgrund, nästan svart text (#1F2328), dämpad grå (#5E6670), tunna linjer (#E2E5E9), en djup blå för länkar och knappar (#1D4E89). Länkar är understrukna.
- Statusfärger från grönt till grått: 0 #2E7148, 1 #86AE5C, 2 #D49A2A, 3 #CDBF8E, 4 #A9B0B8, 5 vit med grå kantlinje. Visas som små fyrkanter bredvid texten.
- Flikarna högst upp är text med ett tjockt streck under den valda fliken.
- Det enda som sticker ut är rutnätet med kommunerna på startsidan och den gula markeringen (#FFF1A8 med en mörkare gul kant till vänster) för "Luckor i granskningen".
- Undvik: kort med stora siffror, etiketter i versaler ovanför rubriker, dekorativa övertoningar och skuggor överallt, typsnitt med fast teckenbredd för siffror, pilar efter länktext, krämfärgad bakgrund.
- Textrader högst cirka 70 tecken breda.
- Mörkt läge via `prefers-color-scheme`, synlig fokusmarkering för tangentbord, respekt för `prefers-reduced-motion` och en layout som fungerar ner till 360 pixlars bredd.

# Databas (Supabase)

Kör det här skriptet en gång i Supabase under SQL Editor. Lägg det också i `supabase/schema.sql`.

```sql
create table if not exists public.bedomningar (
  id         bigint generated always as identity primary key,
  kommun     text        not null check (kommun ~ '^[a-z0-9-]{1,60}$'),
  data       smallint    check (data between 1 and 5),
  dok        smallint    check (dok  between 1 and 5),
  tolk       smallint    check (tolk between 1 and 5),
  kommentar  text        check (char_length(kommentar) <= 2000),
  skapad     timestamptz not null default now(),
  constraint minst_ett_betyg check (data is not null or dok is not null or tolk is not null)
);

alter table public.bedomningar enable row level security;

drop policy if exists "alla kan lagga till" on public.bedomningar;
create policy "alla kan lagga till" on public.bedomningar
  for insert to anon, authenticated with check (true);

revoke all on public.bedomningar from anon, authenticated;
grant insert (kommun, data, dok, tolk, kommentar) on public.bedomningar to anon, authenticated;

create or replace view public.bedomningar_snitt as
  select kommun,
         count(*)::int                    as antal,
         round(avg(data)::numeric, 2)     as snitt_data,
         round(avg(dok)::numeric, 2)      as snitt_dok,
         round(avg(tolk)::numeric, 2)     as snitt_tolk
  from public.bedomningar
  group by kommun;

grant select on public.bedomningar_snitt to anon, authenticated;
```

Besökare får alltså bara lägga till bedömningar och läsa snitten, aldrig läsa enskilda rader eller kommentarer. Lägg den publika nyckeln (publishable key, börjar med `sb_publishable_`) i `assets/config.js`. Lägg aldrig den hemliga nyckeln i repot.

Webbsidan skickar en bedömning med POST till `/rest/v1/bedomningar` och läser snitten med GET från `/rest/v1/bedomningar_snitt`, med nyckeln i rubriken `apikey`.

# Arbetsgång

1. Bygg sidan med alla 290 kommuner i status 5 och tomma fält. Testa lokalt med `python3 -m http.server`, både på datorbredd och mobilbredd och i mörkt läge. Publicera.
2. Granska kommunerna i omgångar om cirka tio. Börja med de största kommunerna och kommuner som beslutade budget i juni. Validera JSON, publicera efter varje omgång och berätta kort vilka kommuner som ändrades och hur.
3. Testa på den publicerade sidan att en bedömning går att skicka. Skicka bara en testbedömning och säg till så att den kan raderas.
4. Uppdatera datumet i `assets/config.js` när du publicerar nya uppgifter.
5. När en omgång är klar, uppdatera `arbete/att_granska.json` och `arbete/INSTRUKTIONER.md` så att nästa omgång kan börja där du slutade.

# Dokumentation

Sidan ska vara helt öppen med hur den har gjorts.

- Lägg till varje instruktion du får ordagrant i `metod/logg.md`, med datum och klockslag, följt av en kort beskrivning av vad som ändrades. Utelämna hemliga nycklar och lösenord om sådana finns i instruktionen.
- Skriv i `metod/metod.md` vem som bestämt vad och vad AI-assistenten har gjort, och var tydlig med begränsningarna: att AI kan läsa fel, att vissa dokument inte gick att öppna och att bara ett urval av citaten är kontrollerade för hand.
- Skriv beskrivande meddelanden när du sparar ändringar i repot, så att historiken går att följa.
