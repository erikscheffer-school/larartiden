## Så gjordes sidan

Sidan är gjord av mig, Erik Håkansson, med hjälp av AI-assistenten Claude från Anthropic. Jag har bestämt vad som ska undersökas, hur kommunerna ska kategoriseras och vad sidan ska innehålla. Claude har sökt upp och läst kommunernas handlingar, fyllt i uppgifterna, skrivit koden och publicerat ändringarna. Allt Claude har fått i uppdrag finns ordagrant i [loggen över instruktionerna](#metod-logg). Under [Prompten](#metod-prompt) finns hela prompten som behövs för att bygga en egen kopia av sidan, och under [Utveckla prompten](#metod-utveckla) förslag på hur den kan göras bättre.

### Vad som har undersökts

För varje kommun har vi letat efter publicerade budgethandlingar för 2027:

- planeringsförutsättningar och budgetdirektiv
- nämndernas budgetunderlag, särskilt barn- och utbildningsnämndens eller motsvarande
- budgetförslag från majoritet och opposition
- kallelser och protokoll från kommunstyrelsen och kommunfullmäktige
- kommunernas remissvar på utredningen *Tid för undervisningsuppdraget* (SOU 2025:26)

I dokumenten har vi sökt efter orden undervisningstid, undervisningsuppdrag, lärares arbetstid, reglerad undervisningstid, planeringstid och statsbidrag. Varje träff har lästs i sitt sammanhang innan kommunen fått en status.

### Hur arbetet gick till

1. Den första versionen (5 november 2026) byggdes från sökningar på webben. Claude letade upp dokument och läste dem ofta via ett verktyg som sammanfattar webbsidor. Därför kan en del citat från den omgången vara återgivna i stället för exakta.
2. Kommuner där inga budgethandlingar hittades samlades i en arbetslista (`arbete/att_granska.json`) tillsammans med anteckningar om vad som saknades.
3. Den 6 november gick Claude igenom kommuner som enligt anteckningarna troligen beslutade budget i juni. Claude använde då en webbläsare för att öppna kommunernas mötesportaler, laddade ner PDF-filerna och sökte direkt i texten. Citat från den omgången är kopierade ur dokumenten med sidnummer.
4. Efter varje omgång sparades ändringarna i `data/kommuner.json` och publicerades. Hela historiken går att följa i [GitHub-repot](https://github.com/erikscheffer-school/larartiden/commits/main).

### Status

Varje kommun har en av sex statusar. Bedömningen gäller bara de dokument som har granskats.

<div id="statusdef"></div>

### Dokumenttyp

För varje granskat dokument anges skede och vem som har tagit fram det.

- **Skede:** underlag/förslag (planeringsförutsättningar, nämndunderlag, budgetförslag) eller beslut (fullmäktige, kommunstyrelse eller nämnd).
- **Producent:** tjänstemannaproducerat (förvaltning, tjänsteutlåtande) eller politiskt producerat (budgetförslag från partier, yrkanden, politiska beslut).

### Begränsningar

- AI kan läsa fel, missa ett dokument eller dra en felaktig slutsats. Kontrollera alltid mot originalet innan du citerar vidare.
- Vissa protokoll är inskannade bilder utan text. Där har sökningen inte fungerat, och det står i så fall under "Luckor i granskningen".
- Många mötesportaler gick inte att öppna automatiskt. Därför är "Ej bedömbart än" vanligt.
- Ett budgetdatum som är markerat som planerat är inte bekräftat i ett protokoll.
- Det är valår. Flera kommuner fattade ett första beslut i juni och fattar ett nytt efter valet. Uppgifterna kan därför bli inaktuella.
- Bara ett urval av citat har kontrollerats manuellt mot originaldokumenten.

### Centrala källor

- [Regeringen: Nu regleras lärarnas undervisningsuppdrag (30 juni 2026)](https://www.regeringen.se/pressmeddelanden/2026/06/nu-regleras-lararnas-undervisningsuppdrag/)
- [Prop. 2025/26:196 Tid för undervisningsuppdraget](https://www.riksdagen.se/sv/dokument-och-lagar/dokument/proposition/tid-for-undervisningsuppdraget_hd03196/html/)
- [SKR cirkulär 25:42 om budgetpropositionen för 2026](https://extra.skr.se/download/18.1aedb661199ffe20e6b15c9/1760952016028/Cirkul%C3%A4r%2025_42.pdf)
- [SKR:s remissvar på SOU 2025:26](https://www.regeringen.se/contentassets/71983b04ad68455a913b800227c99598/sveriges-kommuner-och-regioner.pdf)
- [Storsthlm: prislista för gymnasieskolan 2027](https://www.storsthlm.se/media/yc0gsxu1/bilaga-till-rekommendation-prislista-for-gymnasieskolan-i-stockholmsregionen-2027.pdf)

### Öppna data

Alla uppgifter finns i [data/kommuner.json](data/kommuner.json). Fälten beskrivs i [README-filen](https://github.com/erikscheffer-school/larartiden#readme). Koden, arbetslistan och instruktionerna till AI:n finns i samma repo.
