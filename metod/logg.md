## Logg över instruktionerna

Här finns de instruktioner jag har gett AI-assistenten Claude, ordagrant och i tidsordning, och en kort beskrivning av vad som hände efter varje instruktion. Syftet är att den som vill ska kunna granska hur sidan har vuxit fram. Alla ändringar finns också som versioner i [GitHub-repot](https://github.com/erikscheffer-school/larartiden/commits/main).

### 5 november 2026: första versionen

Den första versionen av sidan och den första genomgången av alla 290 kommuner gjordes i en tidigare chatt. Instruktionerna från den chatten finns inte med här ännu. *Erik fyller i dem.*

Resultatet blev versionen [f770d18](https://github.com/erikscheffer-school/larartiden/commit/f770d18) med sidans struktur, data för alla kommuner och analystexter. Därefter lades en arbetslista och instruktioner för fortsatt granskning till ([b9682a2](https://github.com/erikscheffer-school/larartiden/commit/b9682a2)): `arbete/INSTRUKTIONER.md`, `arbete/att_granska.json` och Excel-filen `arbete/Kommuner_utan_dokument.xlsx`.

### 6 november 2026, kl. 07.43

> Här är anon key: sb_publishable_wjad3LeuLWyZJ4fejKLbkw_kbgIRLDZ
> Här är Supabaseprojektets URL:
> https://rrfiyxqmjwvmsraotigy.supabase.co
> Här är repots namn: erikscheffer-school/larartiden

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

### Så förs loggen

Varje ny instruktion till AI:n läggs till här med datum och klockslag, ordagrant, följt av en kort beskrivning av vad som ändrades.
