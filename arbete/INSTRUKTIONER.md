# Instruktioner för en ny genomgång

Målet: fyll på `data/kommuner.json` för kommunerna i `arbete/att_granska.json` (status 5, "Ej bedömbart än").

## Per kommun
1. Gå direkt till kommunens webbplats och mötesportal (kommunfullmäktige, kommunstyrelse, utbildnings-/barn- och utbildningsnämnd). Använd Playwright/Chromium för portaler som kräver JavaScript. Ladda ner PDF:er och sök i texten (pdftotext) efter: undervisningstid, undervisningsuppdrag, lärares arbetstid, reglerad undervisningstid, planeringstid, statsbidrag.
2. Fyll i fälten enligt README.md: `s` (status 0–5), `sum`, `m`, `mk`, `kort` (kort beloppsrad för startsidan, bara status 0–2), `sb`, `pl`, `kf`, `kfu`, `lu` (luckor, i hela meningar), `docs` (med `sk` skede: "underlag/förslag" eller "beslut", `pr` producent: "tjänstemannaproducerat" eller "politiskt producerat", `pr` kan också vara "nyhetsartikel (tredje part)", `nr`, ordagrant kort `c` citat inom citattecken med sidnummer, `ko` egna anteckningar, `u` länk direkt till dokumentet).
3. Notera när kommunstyrelsen och fullmäktige behandlar budget 2027 (`kf`, `kfu`) och kontrollera att `w` pekar på kommunens webbplats.
4. Fabricera aldrig citat, belopp, datum eller länkar. Okänt = utelämna fältet.

## Status
Statusen sätts efter fasta regler, beskrivna i `metod/metod.md` och `metod/prompt.md`:

- 0 Pengar beslutade: granskat beslut, belopp för 2027 och uttrycklig koppling till reformen.
- 1 Pengar föreslagna: belopp kopplat till reformen i ett förslag, eller beslut som inte är granskat i protokoll.
- 2 Kostnad beräknad: kommunens egen beräkning av kostnad eller lärarbehov. Förväntat statsbidrag räknas inte.
- 3 Nämnt utan belopp: reformen nämns i en budgethandling för 2027.
- 4 Ej nämnt: minst en budgethandling för 2027 med ramar, belopp eller förslag är läst.
- 5 Ej bedömbart än: annars.

Budgethandling för 2027 är inte remissvar, årsredovisningar, budget 2026 med plan 2027, kallelser utan underlag, tidplaner eller nyhetsartiklar. Skilj på tillskott och total nivå, förslag och beslut.

## Efteråt
Kör `python3 verktyg/kontrollera.py` och rätta alla fel. Testa sidan lokalt (python3 -m http.server), committa och pusha till main. GitHub Pages publicerar automatiskt.

Lägg till den nya instruktionen ordagrant i `metod/logg.md`.
