## Logg över instruktionerna

Här finns de instruktioner jag har gett AI-assistenten Claude, ordagrant och i tidsordning, och en kort beskrivning av vad som hände efter varje instruktion. Syftet är att den som vill ska kunna granska hur sidan har vuxit fram. Alla ändringar finns också som versioner i [GitHub-repot](https://github.com/erikscheffer-school/larartiden/commits/main).

### 5 november 2026: första versionen

Den första versionen av sidan och den första genomgången av alla 290 kommuner gjordes i en tidigare chatt. Instruktionerna från den chatten finns inte med här.

Resultatet blev versionen [f770d18](https://github.com/erikscheffer-school/larartiden/commit/f770d18) med sidans struktur, data för alla kommuner och analystexter. Därefter lades en arbetslista och instruktioner för fortsatt granskning till ([b9682a2](https://github.com/erikscheffer-school/larartiden/commit/b9682a2)): `arbete/INSTRUKTIONER.md`, `arbete/att_granska.json` och Excel-filen `arbete/Kommuner_utan_dokument.xlsx`.

### 6 november 2026, kl. 07.43

> Här är anon key: X
> Här är Supabaseprojektets URL: X
> Här är repots namn: X

Claude hämtade repot och såg att uppgifterna redan låg i `assets/config.js`. Ingen ändring gjordes. (Nyckeln är den publika nyckel som är avsedd att synas på webbsidor.)

### 6 november 2026, kl. 07.44

> Följ arbete/INSTRUKTIONER.md i repot erikscheffer-school/larartiden. Kontrollera först att du når kommunernas webbplatser, till exempel www.kalix.se. Granska sedan kommunerna i arbete/att_granska.json. Börja med dem som beslutade budget i juni 2026. Uppdatera data/kommuner.json, samla även in skolpeng och styre, och pusha till main. Testa också att bedömningarna på erikscheffer-school.github.io/larartiden fungerar.

Claude kontrollerade att kommunernas webbplatser gick att nå och skickade en testbedömning för Karlshamn för att se att bedömningarna sparades. Därefter granskades Tranås, Mark, Munkedal, Vetlanda, Heby, Hällefors, Markaryd, Piteå, Härryda och Kristianstad. Resultatet publicerades i två omgångar.

### 6 november 2026, kl. 07.46

> Try the browser again

Webbläsaren fungerade vid andra försöket. Claude använde den för att öppna mötesportaler och läsa PDF-filer.

### 6 november 2026, kl. 08.08

> Fortsätt

Claude granskade Mellerud, Gullspång, Vara, Ljungby, Stenungsund, Hjo, Tjörn, Färgelanda, Strängnäs, Vingåker, Sala, Västervik, Vimmerby, Flen, Östersund och Leksand och publicerade efter varje omgång.

### 6 november 2026, kl. 09.50

> Publicera på github, det nya via har. Fortsätt sedan.

Allt var redan publicerat. Claude granskade sedan Kramfors, Sundsvall, Helsingborg och Bollnäs.

### 7 november 2026, kl. 07.56

> Jag vill göra några förändringar av hemsidan och förenkla den.
>
> 1. Ta bort analysen av skolpengen samt styre efter valet.
> 2. Förstärk rubriken "luckor i granskningen" per kommun om möjligt.
> 3. Lägg till en rubrik: "var du kan fortsätta leta". Där läggs en länk till respektive kommuns hemsida och en text typ: ofta kan man hitta politiska handlingar under rubriker som "kommun och politik" eller liknande. Försök att undersöka när budget ska beslutas i respektive kommun. Ofta tas ett beslut först i kommunstyrelsen och ger förslag till beslut i kommunfullmäktige.
> 4. Under metod och källor, redogör ännu tydligare för hur sidan har skapats. Skapa en logg för hur den har promptats fram så att det går att granska för den som vill. Skapa även en total prompt som skulle kunna kopieras in i en chatt, med alla instruktioner för att kunna återskapa en kopia. Full transparens.
> 5. Töm analys avsnittet. Jag lägger in mina egna texter.
> 6. Om möjligt, gör hemsidan mindre AI-lik.

Claude tog bort skolpeng och styre ur data och sida, gjorde luckorna till en markerad punktlista, lade till avsnittet "Var du kan fortsätta leta" med länk till varje kommuns webbplats, skrev den här metodtexten, loggen och prompten, tömde analysavsnittet och gjorde om sidans utseende till en enklare stil. Datum för budgetbeslut visas där det är känt från granskningen (cirka 100 kommuner). För övriga kommuner är datumet inte undersökt ännu.

### 7 november 2026, kl. 08.22

> Jag vill snygga till hemsidan lite grann. Jag gjorde den så att den inte skulle se så AI-genererad men jag vill ha den lite snyggare än den är nu. Rent formatmässigt alltså.
>
> Jag vill också ha det mer avgränsat, framför allt vad som står under respektive kommun på startsidan. Under fliken "Kommuner" ska all information dock vara kvar. Jag vill också att det ska finnas en totalprompt under fliken "metod och källor", alltså inte bara en hänvisning till Github. Skapa en ny prompt som skulle kunna användas av någon annan för att bygga samma sak som jag samt en separat kommentar om vad man skulle kunna ändra om man vill utveckla prompten.

Claude gav rubrikerna ett serift typsnitt, gjorde flikarna tydligare och putsade avstånd, tabellen och kommunsidan. Den smala stapeln på startsidan ersattes med en ruta per kommun som går att klicka på. Listan över kommuner med pengar eller beräknad kostnad grupperades per status och visar nu bara en kort beloppsrad (nytt fält `kort` i data). Hela underlaget finns kvar under Kommuner. Länkarna till dokumenten visas som "Öppna dokumentet" i stället för hela adressen. Under Metod och källor skrevs en ny, fristående prompt som visas i sin helhet, och en ny del, Utveckla prompten, med förslag på förbättringar.

### 7 november 2026, kl. 08.49

> Jag vill ändra denna texten på hemsidan:
>
> Följer pengarna med till skolan?
> Från 1 juli 2027 regleras hur mycket lärare ska undervisa. Staten kompenserar kommunerna med 1,3 miljarder kronor 2027 och 2,6 miljarder per år därefter, via det generella statsbidraget. Pengarna är inte öronmärkta. Här följer jag om kommunerna i sina budgetar för pengarna vidare till skolan.
>
> Till:
>
> Följer pengarna med till skolan?
> Från 1 juli 2027 regleras hur mycket lärare ska undervisa. Staten kompenserar kommunerna med 1,3 miljarder kronor 2027 och 2,6 miljarder per år därefter, via det generella statsbidraget. Pengarna är inte öronmärkta. Denna sida har hittat ett antal dokument till ett begränsat antal kommuner och undersökt om reformen samt tillhörande statsbidrag nämns, samt om kommunen hanterat det genom ett de facto tillskott till skolornas budget eller inte.

Claude bytte ut inledningen på startsidan mot den nya texten.

### 7 november 2026, kl. 08.50

> Byt

Svar på Claudes förslag att skriva "dokument för ett begränsat antal kommuner" i stället för "dokument till ett begränsat antal kommuner". Claude bytte ordet i inledningen.

### 7 november 2026, kl. 13.14

> Två separata granskningar genomförda av andra AI-tjänster/agenter. Genomför samtliga åtgärder. Säg till när något är oklart, fråga om behörigheter och ge mig instruktioner när det finns saker som du inte kan göra.

Med instruktionen följde två filer. Den ena, en PDF med en granskning av säkerhet, datakvalitet och metod gjord av Claude och GPT, låg till grund för ändringarna. Den andra, en Word-fil, innehöll samma text som delen Utveckla prompten på sidan och ledde inte till några ändringar.

Claude skrev ner fasta regler för när en kommun får respektive status och tillämpade dem på alla 290 kommuner. Statusen ändrades för 32 kommuner, bland annat Vaxholm (pengarna gällde budget 2026), Aneby och Solna (inget belopp kopplat till reformen), Tibro (beslutet inte verifierat) och 24 kommuner där bara remissvar, budgetar för 2026 eller nyhetsartiklar hade granskats. Varje ändring står under kommunens luckor. Habo och Håbo fick olika adressnamn. Beloppsraderna för Nykvarn, Hagfors, Kil, Österåker och Kungsör skrevs om så att de inte säger mer än källan. Egna anteckningar flyttades ur citatfälten till ett nytt fält, och på sidan syns skillnaden mellan citat och anteckning. Sammanfattningarna för Gagnef, Täby, Leksand och Munkedal rättades.

I koden lades Markdown-biblioteket och DOMPurify in i repot i stället för att hämtas från en CDN, och all Markdown saneras. Bakåtknappen, sorteringen av å, ä och ö, tangentbordsnavigeringen i tabellen och några fel där bedömningar kunde försvinna eller fel text visas rättades. Tabellen visar nu hur många dokument som granskats. Snitten för bedömningarna visas med en varning om att de inte är tillförlitliga. Ett kontrollskript, `verktyg/kontrollera.py`, prövar statusreglerna. Metodtexten, prompten och förslagen under Utveckla prompten uppdaterades med reglerna och med granskningens förslag om en billigare insamlingsmetod.

### 7 november 2026, kl. 13.39

> Fortsätt med Lärartiden i budgeten: bygg skripten för att hämta budgetdokument enligt Utveckla prompten.
>
> Ska köra med GitHub Actions veckovis.
>
> Brave Search API: [nyckeln borttagen ur loggen] (skriv inte ut detta i loggen som publiceras). Ligger som en repo secret i GitHub också.
>
> Ge mig för varje veckovisa sökning en lista på 3-10 kommuner som behöver granskas. Ge mig till att börja med 5 kommuner som behöver granskas. När körningen är klar.

Claude skrev tre skript i `verktyg/hamta/`. Det första söker med Brave Search API efter budgethandlingar för 2027 på varje kommuns webbplats, och för kommuner med status 3–5 även efter reformorden på hela webben. Det andra hämtar dokumenten, gör om PDF:erna till text och sparar korta utdrag med sidnummer runt varje träff på reformorden. Det tredje ger varje kommun poäng efter vad som hittats och väljer ut 3–10 kommuner att granska. Skripten körs varje måndag i GitHub Actions och listan sparas i `arbete/veckolista/`. Skripten sätter aldrig status. Den första körningen gjordes med fem kommuner.

### 7 november 2026, kl. 14.31

> Ja

Svar på Claudes fråga om de fem kommunerna på första veckolistan skulle granskas. Claude lät GitHub Actions hämta handlingarna och skriva ut de relevanta sidorna som text (`verktyg/hamta/utdrag.py`), läste dem och kontrollerade citaten ordagrant. Den första listan innehöll för många falska träffar, så reglerna för vad som räknas som reformträff skärptes och bara kommunernas egna handlingar ger nu poäng.

Ale fick status Nämnt utan belopp: utbildningsnämndens nulägesanalys 2026, underlag för budgetbeslutet för 2027, nämner reformen. Färgelanda fick status Ej nämnt: utbildningsnämndens underlag inför mål- och resursplanen 2027–2030 nämner inte reformen. Falköping, Bjurholm och Borås förblir Ej bedömbart än, eftersom inga budgethandlingar för 2027 med innehåll hittades. För Borås lades datumen för budgetsammanträdet till, och luckorna uppdaterades för alla fem.

### 7 november 2026, kl. 14.49

> Har du sökt så att du hittat för fler kommuner? Saknas fortfarande helt för 176

Claude svarade att den första körningen bara hade sökt 125 kommuner och hämtat dokument för 29, eftersom taket på antal hämtningar gick åt på de första kommunerna. Hämtningen ändrades till högst sex dokument per kommun i turordning, och de 53 kommuner som inte sökts söktes. Därefter fanns dokument för 151 kommuner.

### 7 november 2026, kl. 15.26

> Skript för mötesportalerna

Claude skrev en genomsökare som med en riktig webbläsare (Playwright) går från kommunens webbplats in i mötesportalerna och samlar länkar till handlingar (`verktyg/hamta/portaler.py`), egna hämtare för Netpublicator och MeetingsPlus (`verktyg/hamta/portalskript.py`) och ett verktyg som visar hur en okänd portal är uppbyggd (`verktyg/hamta/undersok_portal.py`). Hämtningen klarar nu sajter som kräver cookies. Sökresultat och PDF:er sparas i GitHub Actions cache i stället för i repot. Efter körningarna nämns reformen i handlingar från 32 av de 176 kommunerna med status Ej bedömbart än, 69 har en möjlig budgethandling för 2027 och 72 saknar ännu användbara handlingar. Inga statusar ändrades: fynden ska granskas innan de används.

### 7 november 2026, kl. 19.11

> Ja

Svar på Claudes fråga om de 32 kommuner där den automatiska hämtningen hittat reformorden skulle granskas. Claude lät GitHub Actions skriva ut de aktuella sidorna, läste dem och kontrollerade citaten ordagrant. Nio kommuner fick ny status: Hammarö Pengar beslutade (beloppet delas med aktivitetskravet), Forshaga, Bengtsfors och Växjö Pengar föreslagna (Växjös belopp delas med tidiga insatser), samt Säter, Svenljunga, Skurup, Tanum och Hallsberg Nämnt utan belopp. För 23 kommuner var träffarna inte budgethandlingar för 2027, till exempel gamla budgetar, årsredovisningar eller garanterad undervisningstid. Det står nu i deras luckor, och de förblir Ej bedömbart än.

### 8 november 2026, kl. 08.47

> Det saknas fortfarande underlag från 167 kommuner. Är det för att det inte finns något eller för att vi har för "dåliga" skript?

Claude svarade att det är båda, men att den största förklaringen var att skripten bara skickade vidare handlingar där reformen nämns: budgethandlingar för 2027 utan reformord, som ska ge status Ej nämnt, kom aldrig upp för granskning. Många kommuner beslutar dessutom budget 2027 först i november–december efter valet, och skripten missar handlingar på grund av hämtfel, Ciceron och taket på antal dokument.

### 8 november 2026, kl. 08.50

> Ja

Svar på Claudes förslag att låta veckolistan ta med budgethandlingar för 2027 utan reformord och att granska de tydligaste. Veckolistan ger nu poäng åt handlingar vars titel anger budget, ramar eller plan för 2027. Claude granskade nio kommuner. Staffanstorp, Torsby, Jokkmokk, Vännäs, Arboga och Karlskoga fick status Ej nämnt; reformorden saknas i hela respektive dokument. Arbogas status bygger på preliminära ramar. För Lidköping lades datumet för budgetbeslutet till. Handlingarna som hämtats för Orsa och Grästorp visade sig gälla Region Dalarna och Lidköping, så hämtningen kontrollerar nu att kommunnamnet står i dokumentet.

### 8 november 2026, kl. 09.00

> Jag vill ha 0 kommuner utan granskade dokument. Fortsätt bygga skript för att försöka lösa problemet.

Claude byggde en riktad sökning efter budget 2027 för kommuner med status Ej bedömbart än (`verktyg/hamta/budgetsok.py`), OCR för inskannade PDF:er, en prioritering som hämtar höstens dokument först och hoppar över dokument som laddats upp före 2026, och granskningskort per kommun (`verktyg/hamta/forgranska.py`) med de rader som nämner budget och 2027 samt besked om reformorden saknas i hela dokumentet. Claude granskade korten och kontrollerade osäkra fall mot utskrivna sidor. 25 kommuner fick status Ej nämnt och två (Vaxholm och Töreboda) Nämnt utan belopp. För ett tiotal kommuner lades kända datum för budgetbeslut och handlingar till i luckorna. Ett prov visade att Brave Search sällan indexerar kommunernas egna budgethandlingar och att kommunkartan.se:s gränssnitt kräver inloggning.

### 8 november 2026

> Det saknas fortfarande 136 kommuner. Vad krävs för att hitta dem?

Claude delade upp de 136 kommunerna efter vad som hämtats: 80 hade handlingar från oktober–november men ännu ingen budget 2027 (troligen inte publicerad än), 43 hade bara handlingar från före september (skripten nådde inte deras mötessidor), 7 saknade egna handlingar helt, 4 använder Ciceron, som stänger ute automatisk hämtning, och 2 hade bara handlingar från september.

### 9 november 2026, kl. 07.29

> Mötessidor per kommun och hämtning av KS/KF-kallelser för de 43 + 7 kommunerna, inklusive att ta fram mötesdatum. Det ger mest effekt.

Claude byggde steg 1d (`verktyg/hamta/motessidor.py`). Steget letar upp varje kommuns sida med kallelser och protokoll, sparar den och datumen för kommunfullmäktiges och kommunstyrelsens möten i `arbete/hamtning/motessidor.json` och hämtar kallelser och handlingar från september och framåt före andra dokument. Prov på 50 kommuner visade att handlingarna ofta ligger på andra plattformar. Därför fick steget hämtare för OpenGov (Public 360), DocumentWeb och Netpublicator inbäddad i Sitevision, utöver de tidigare för Netpublicator och MeetingsPlus. Steget ingår i veckokörningen, och mötessidan och mötesdatumen syns i granskningskorten. Efter körningen finns en mötessida för 131 av de 136 kommunerna och aktuella handlingar för 110. 63 kommuner har nu kandidater till budgethandling för 2027 i granskningskorten, mot 30 före körningen. Kvar utan mötessida är Ljungby, Landskrona, Storuman, Sollefteå och Örnsköldsvik. forum.norrtalje.se gick inte att nå från GitHub Actions. Brave Search svarar att sökkvoten är slut (402), så sökstegen gör inga sökningar tills kvoten fylls på. Hämtningen slår nu ihop resultaten om två körningar committar samtidigt. Inga statusar ändrades.

### Så förs loggen

Varje ny instruktion till AI:n läggs till här med datum och klockslag, ordagrant, följt av en kort beskrivning av vad som ändrades.
