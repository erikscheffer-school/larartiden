## Utveckla prompten

[Prompten](#metod-prompt) återskapar sidan som den ser ut i dag. Här är det jag skulle ändra eller lägga till om jag började om, och det du kan ändra om du vill göra en bättre granskning eller undersöka något annat. Förslagen är fristående. Välj de som passar ditt syfte och skriv in dem i prompten.

### Göra granskningen säkrare

- **Låt en andra AI kontrollera citaten.** Lägg till ett steg där en separat chatt, utan tillgång till den första chattens slutsatser, öppnar varje dokument och kontrollerar att citatet finns ordagrant på angiven sida. Det är den vanligaste felkällan.
- **Spara en kopia av varje dokument.** Kommunernas länkar slutar ofta fungera när handlingar flyttas till arkiv. Be AI:n spara PDF-filerna i repot, eller lägga till en länk till en arkiverad version, till exempel på archive.org.
- **Datera varje granskning.** Lägg till ett fält som anger när kommunen senast granskades. Då ser läsaren hur färsk uppgiften är, och det blir lätt att välja vilka kommuner som ska granskas om.
- **Skilj på "hittade inget" och "kunde inte öppna".** Status 5 rymmer i dag både kommuner där inga handlingar finns och kommuner vars mötesportal inte gick att läsa. Ett eget fält för orsaken gör det lättare att veta var en människa behöver hjälpa till.
- **Begär att osäkra fall flaggas.** Be AI:n markera kommuner där statusen är en tolkning, till exempel när pengarna delas med andra satsningar eller när det är oklart om ett belopp är nytt eller totalt.

### Göra uppgifterna mer jämförbara

- **Belopp som siffror.** I dag är beloppen text. Lägg till fält med belopp i kronor per år, så att sidan kan räkna och sortera.
- **Jämför med statsbidraget.** Varje kommun får en beräknad andel av de 1,3 respektive 2,6 miljarderna. Om du lägger till den andelen (till exempel utifrån antal elever eller SKR:s beräkningar) kan sidan visa hur stor del av pengarna som förs vidare.
- **Per elev.** Lägg till antal elever i grundskola och gymnasieskola från Skolverket eller SCB så att belopp kan jämföras mellan stora och små kommuner.
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
