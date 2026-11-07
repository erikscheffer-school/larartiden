## Utveckla prompten

[Prompten](#metod-prompt) återskapar sidan som den ser ut i dag. Här är det jag skulle ändra eller lägga till om jag började om, och det du kan ändra om du vill göra en bättre granskning eller undersöka något annat. Förslagen är fristående. Välj de som passar ditt syfte och skriv in dem i prompten.

### Göra granskningen säkrare

- **Låt en andra AI kontrollera citaten.** Lägg till ett steg där en separat chatt, utan tillgång till den första chattens slutsatser, öppnar varje dokument och kontrollerar att citatet finns ordagrant på angiven sida. Det är den vanligaste felkällan.
- **Spara en kopia av varje dokument.** Kommunernas länkar slutar ofta fungera när handlingar flyttas till arkiv. Be AI:n spara PDF-filerna i repot, eller lägga till en länk till en arkiverad version, till exempel på archive.org.
- **Datera varje granskning.** Lägg till ett fält som anger när kommunen senast granskades. Då ser läsaren hur färsk uppgiften är, och det blir lätt att välja vilka kommuner som ska granskas om.
- **Skilj på "hittade inget" och "kunde inte öppna".** Status 5 rymmer i dag både kommuner där inga handlingar finns och kommuner vars mötesportal inte gick att läsa. Ett eget fält för orsaken gör det lättare att veta var en människa behöver hjälpa till.
- **Begär att osäkra fall flaggas.** Be AI:n markera kommuner där statusen är en tolkning, till exempel när pengarna delas med andra satsningar eller när det är oklart om ett belopp är nytt eller totalt.

### Hämta dokumenten med skript i stället för att låta AI:n surfa

Den största förbättringen är att låta AI:n skriva skript en gång i stället för att själv klicka sig igenom 290 webbplatser. Varje sidvisning kostar då inget, resultatet blir detsamma varje gång och det behövs inget godkännande per webbplats. Förslaget kommer från en extern granskning av sidan den 7 november 2026.

1. **Hitta dokumenten med ett sök-API**, till exempel Serper, Brave Search API eller Exa, med sökningar som `site:kommun.se filetype:pdf "budget 2027"`. Där sökningen inte räcker kan Firecrawl eller det fria alternativet Crawl4AI kartlägga alla länkar på en kommuns webbplats.
2. **Mötesportalerna med Playwright, ett skript per portaltyp.** De flesta kommuner använder någon av en handfull portaler (MeetingsPlus, Netpublicator, Ciceron med flera). Gruppera kommunerna efter portal och låt AI:n skriva ett skript per typ. För udda portaler finns Stagehand, där AI:n bara kopplas in när ett steg krånglar.
3. **Gör om PDF:erna till text lokalt** med PyMuPDF eller pdftotext, och gör inskannade protokoll sökbara med OCRmyPDF (`-l swe`). Docling eller Marker klarar budgettabeller.
4. **Skicka bara de träffade sidorna till AI:n**, en till tre sidor per kommun, och låt den fylla ett fast formulär: belopp, år, ordagrant citat, sidnummer och om reformen nämns. Använd en billig modell för att sålla och en starkare för de svåra fallen.
5. **Kontrollera citaten automatiskt.** Ett skript söker efter varje citat i PDF-texten. Citat som inte finns där sorteras bort.
6. **Låt reglerna sätta statusen.** Statusreglerna under [Så gjordes sidan](#metod-metod) kan skrivas som kod, så att tolkningen blir likadan för alla kommuner.
7. **Mät träffsäkerheten.** Granska cirka 30 kommuner noggrant för hand, blandat mellan statusarna, och använd dem som facit. Kör gärna två olika modeller och granska bara de kommuner där de är oense.
8. **Spara varje PDF en gång**, med kommun, datum och källänk, så att nästa genomgång bara behöver ta nya dokument.

Var schysst mot kommunernas servrar: några sekunders paus mellan anropen och bara offentliga handlingar. Skripten kan köras gratis varje vecka med GitHub Actions i ett publikt repo, och changedetection.io kan larma när en kommun publicerar nya handlingar.

Ett alternativ eller komplement är att begära ut handlingarna. En standardbegäran om allmän handling till alla 290 registratorer, "budget 2027 inklusive barn- och utbildningsnämndens underlag", ger ofta ett mer komplett underlag än någon skrapare.

### Göra uppgifterna mer jämförbara

- **Belopp som siffror.** I dag är beloppen text. Lägg till fält med belopp i kronor per år, så att sidan kan räkna och sortera.
- **Jämför med statsbidraget.** Det generella statsbidraget fördelas efter antal invånare, ungefär 242 kronor per invånare vid helårseffekt enligt de uppgifter som finns i underlaget. Med befolkningen från SCB kan sidan räkna fram varje kommuns ungefärliga andel och visa den bredvid det kommunen faktiskt avsatt. Kontrollera beräkningen mot SKR:s cirkulär innan du publicerar.
- **Per elev.** Lägg till antal elever i grundskola och gymnasieskola från Skolverket eller Koladas öppna API (api.kolada.se) så att belopp kan jämföras mellan stora och små kommuner.
- **Fristående skolor.** Reformen gäller även fristående skolor, som får pengar via skolpengen. Ett fält om hur kommunen beskriver ersättningen till fristående huvudmän skulle göra bilden mer komplett.

### Följa utvecklingen över tid

- **Planera om-granskningar.** Be AI:n i början ta fram en lista med när varje kommuns fullmäktige beslutar budget, och granska om kommunerna efter beslutet. Särskilt efter december 2026, när de flesta budgetar är beslutade.
- **Spara historik på sidan.** Visa när en kommun bytt status och varför, inte bara läget i dag.
- **Följ uppföljningen 2027.** Budget är plan. Ett nästa steg vore att granska nämndernas verksamhetsplaner och delårsrapporter under 2027 för att se om pengarna faktiskt används till fler lärare.

### Använda prompten för något annat

Strukturen fungerar för de flesta frågor av typen "hur hanterar kommunerna X i sina budgetar". Det som behöver bytas ut är:

- bakgrunden och frågan sidan ska besvara
- statusskalan, så att den passar den nya frågan
- sökorden i granskningssteget
- rubriker och fasta texter på sidan

Exempel på andra frågor: hur kommunerna hanterar andra ofinansierade eller delvis finansierade reformer, satsningar på skolbibliotek, elevhälsa, eller regionernas budgetar för en viss vårdreform.

### Praktiska tips

- **Arbeta i mindre omgångar.** En chatt orkar inte med alla 290 kommuner. Låt varje chatt ta en tydligt avgränsad uppgift, till exempel "granska kommunerna i Värmlands län", och låt `arbete/INSTRUKTIONER.md` och `arbete/att_granska.json` vara minnet mellan chattarna.
- **Ge AI:n en webbläsare.** Många mötesportaler kräver JavaScript. Utan en riktig webbläsare blir de flesta kommuner "Ej bedömbart än".
- **Var tydlig med vad den inte får göra.** Formuleringarna om att aldrig hitta på citat och belopp är den viktigaste delen av prompten. Behåll dem även om du kortar resten.
- **Läs själv.** Välj ut några kommuner per omgång och kontrollera dem mot originaldokumenten. Skriv i metodtexten hur många du kontrollerat.
