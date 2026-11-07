## Gör en egen kopia

Prompten nedan innehåller allt som behövs för att en AI-assistent med webbsökning, webbläsare och tillgång till GitHub ska kunna bygga en egen version av sidan från början. Den sammanfattar instruktionerna i [loggen](#metod-logg) och de regler som sidan följer i dag. Kopiera den, klistra in den i en chatt och byt ut det som står inom hakparentes.

En hel genomgång av 290 kommuner tar lång tid. Räkna med att behöva skriva "fortsätt" flera gånger.

---PROMPT---
Du ska bygga och fylla en webbplats som heter "Lärartiden i budgeten". Den visar hur Sveriges 290 kommuner hanterar regleringen av lärares undervisningstid (prop. 2025/26:196 Tid för undervisningsuppdraget, gäller från 1 juli 2027) i sina budgetar för 2027. Staten kompenserar kommunerna via det generella statsbidraget, 1,3 miljarder kronor 2027 och därefter cirka 2,6 miljarder per år. Pengarna är inte öronmärkta. Frågan är om kommunerna synligt för pengarna vidare till skolan.

Arbeta på svenska. Skriv enkelt och sakligt, utan säljande formuleringar.

## Teknik
- Statisk webbplats i ett GitHub-repo [ditt-konto/ditt-repo] som publiceras med GitHub Pages från grenen main (lägg en tom fil .nojekyll i roten).
- Filer: index.html, assets/styles.css, assets/app.js, assets/config.js (datum för "läget", kontaktadress, Supabase-adress och publik nyckel), data/kommuner.json, texter/index.json (lista över analystexter, tom från början), texter/*.md, metod/metod.md, metod/logg.md, metod/prompt.md, supabase/schema.sql, README.md, arbete/INSTRUKTIONER.md, arbete/att_granska.json.
- Ingen byggprocess. Markdown renderas i webbläsaren med marked@12.0.2 från cdn.jsdelivr.net, med en enkel reserv om biblioteket inte laddas.
- Bedömningar från besökare sparas i Supabase. Skapa tabellen bedomningar (id, kommun text, data int 1–5, dok int 1–5, tolk int 1–5, kommentar text max 2000 tecken, skapad timestamptz, minst ett betyg krävs) med radsäkerhet påslagen. Besökare (rollen anon) får bara lägga till rader, aldrig läsa dem. Skapa en vy bedomningar_snitt (kommun, antal, snitt_data, snitt_dok, snitt_tolk) som anon får läsa. Använd en publishable-nyckel i config.js. Lägg ett dolt honungsfält i formuläret mot spam och kom ihåg i localStorage att besökaren redan bedömt en kommun.

## Sidans delar (flikar)
1. Översikt: en kort inledning om reformen och statsbidraget, en stapel som visar fördelningen mellan statusarna, en tabell med antal per status och en lista över kommuner med status 0–2.
2. Kommuner: sökfält, filter på län, kryssrutor för status, sorterbar tabell (kommun, län, status, pengar kopplade till reformen, budgetbeslut 2027, antal bedömningar). Klick på en rad öppnar kommunens sida med: status, sammanfattning, uppgifter (pengar, egen beräknad merkostnad, om statsbidraget, om prislista eller samverkan, fullmäktiges budgetbeslut med källa), en tydligt markerad ruta "Luckor i granskningen" som punktlista, avsnittet "Var du kan fortsätta leta" (länk till kommunens webbplats, tips om att politiska handlingar oftast finns under "Kommun och politik" eller liknande, när budgeten beslutas om det är känt, att budgeten oftast först behandlas i kommunstyrelsen som föreslår beslut till fullmäktige, att det nyvalda fullmäktige under valår fastställer budgeten, ofta i november eller december, samt bra sökord), granskade dokument och ett formulär där besökaren bedömer uppgifterna 1–5 i tre frågor (stämmer citaten och uppgifterna, är dokumenten rimliga, är slutsatsen rimlig) med frivillig kommentar. Varje kommun ska gå att länka till med #kommun-<id>.
3. Analys: visas bara när texter/index.json innehåller texter. Varje text är en Markdown-fil.
4. Metod och källor: tre delar som läses från metod/metod.md (hur sidan gjordes, statusdefinitioner, dokumenttyper, begränsningar, källor), metod/logg.md (alla instruktioner till AI:n ordagrant med datum och vad som hände) och metod/prompt.md (den här prompten, med en knapp som kopierar den).
5. Kontakt: mejladress med kopieringsknapp.

## Utseende
Enkelt och textnära, som en egen sammanställning och inte som en mall. Systemtypsnitt, vit bakgrund, understrukna länkar, flikarna som vanliga textlänkar. Inga kort med stora siffror, inga etiketter i versaler ovanför rubriker, ingen monospace för siffror och inga dekorativa övertoningar. Statusfärger visas som små fyrkanter bredvid texten. Det enda som sticker ut är en gul markering (som en överstrykningspenna) för "Luckor i granskningen". Mörkt läge, synlig tangentbordsfokus och fungerande layout ner till mobilbredd.

## Datamodell (data/kommuner.json, en post per kommun)
- k: kommunnamn, id: adressnamn utan å, ä, ö och mellanslag, l: län
- s: status 0–5 (se nedan)
- sum: sammanfattning i två till fyra meningar
- m: pengar uttryckligen kopplade till reformen (belopp, år, nämnd)
- mk: kommunens egen beräknade merkostnad
- sb: kommentar om hur statsbidraget hanteras
- pl: kommentar om prislista eller samverkan (till exempel gymnasiets regionala prislistor)
- kf: när fullmäktige beslutar eller beslutade budget 2027, med paragraf och om det är beslutat eller planerat. kfu: länk till källan
- w: kommunens webbplats
- lu: luckor i granskningen, i hela meningar: vad som inte hittats eller inte kunnat kontrolleras
- docs: lista med granskade dokument. t titel, d datum, sk skede ("underlag/förslag" eller "beslut"), pr producent ("tjänstemannaproducerat" eller "politiskt producerat"), nr om dokumentet nämner reformen (true/false), c kort ordagrant citat med sidnummer, u länk
Utelämna fält som är okända.

## Status
0 Pengar avsatta/beslutade: budget- eller nämndbeslut avsätter pengar uttryckligen kopplade till reformen.
1 Pengar föreslagna: förslag från förvaltning, majoritet eller opposition om pengar kopplade till reformen, inte bekräftat beslutat.
2 Kostnad beräknad, inga pengar: kommunen har räknat på merkostnad eller lärarbehov men inte avsatt pengar.
3 Nämnt utan belopp: reformen nämns i handlingarna utan kostnad eller pengar.
4 Ej nämnt i granskade dokument: budgethandlingar för 2027 har granskats men reformen nämns inte.
5 Inga budgethandlingar 2027 hittade: säger inget om vad kommunen har gjort.
Pengar till "utökad undervisningstid" för elever är inte samma sak som reglerad undervisningstid för lärare. Läs sammanhanget.

## Granskning per kommun
1. Gå till kommunens webbplats och mötesportal (kommunfullmäktige, kommunstyrelse och barn- och utbildningsnämnd eller motsvarande). Använd en riktig webbläsare för portaler som kräver JavaScript (till exempel Ciceron, Netpublicator, MeetingPlus).
2. Leta efter budgethandlingar för 2027: planeringsförutsättningar, budgetdirektiv, nämndunderlag, budgetförslag från majoritet och opposition, kallelser och protokoll. Notera när budgeten ska beslutas. Det är valår 2026, så många kommuner beslutar i november eller december och vissa fattar ett preliminärt beslut i juni.
3. Ladda ner PDF-filerna och sök i texten efter: undervisningstid, undervisningsuppdrag, lärares arbetstid, reglerad undervisningstid, planeringstid, statsbidrag. Läs varje träff i sitt sammanhang.
4. Fyll i fälten och sätt status. Skriv luckorna ärligt. Lägg till kommunens webbplats.
5. Hitta aldrig på citat, belopp, datum eller länkar. Är något okänt, utelämna det och skriv det under luckor. Citat ska vara kopierade ur dokumentet, inte återgivna från en sammanfattning.
6. Kommuner med status 5 läggs i arbete/att_granska.json med anteckningar om vad som saknas, så att de kan granskas igen.

## Arbetsgång
- Börja med att bygga sidan med tom data för alla 290 kommuner (status 5), testa den lokalt och publicera.
- Granska sedan kommunerna i omgångar om cirka tio. Validera JSON, publicera efter varje omgång och berätta kort vad som ändrades.
- Logga varje ny instruktion du får ordagrant i metod/logg.md med datum, klockslag och vad som ändrades.
- Testa att bedömningarna fungerar på den publicerade sidan. Skicka bara en testbedömning och säg till så att den kan raderas.
- Kontaktadress: [din mejladress]. Avsändare i sidfoten: [ditt namn].
