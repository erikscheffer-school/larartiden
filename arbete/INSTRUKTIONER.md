# Instruktioner för en ny genomgång

Målet: fyll på `data/kommuner.json` för kommunerna i `arbete/att_granska.json` (status 5, "Ej bedömbart än").

## Per kommun
1. Gå direkt till kommunens webbplats och mötesportal (kommunfullmäktige, kommunstyrelse, utbildnings-/barn- och utbildningsnämnd). Använd Playwright/Chromium för portaler som kräver JavaScript. Ladda ner PDF:er och sök i texten (pdftotext) efter: undervisningstid, undervisningsuppdrag, lärares arbetstid, reglerad undervisningstid, planeringstid, statsbidrag.
2. Fyll i fälten enligt README.md: `s` (status 0–5), `sum`, `m`, `mk`, `kort` (kort beloppsrad för startsidan, bara status 0–2), `sb`, `pl`, `kf`, `kfu`, `lu` (luckor, i hela meningar), `docs` (med `sk` skede: "underlag/förslag" eller "beslut", `pr` producent: "tjänstemannaproducerat" eller "politiskt producerat", `nr`, ordagrant kort `c` citat med sidnummer, `u` länk).
3. Notera när kommunstyrelsen och fullmäktige behandlar budget 2027 (`kf`, `kfu`) och kontrollera att `w` pekar på kommunens webbplats.
4. Fabricera aldrig citat, belopp, datum eller länkar. Okänt = utelämna fältet.

## Status
0 Pengar avsatta/beslutade · 1 Pengar föreslagna · 2 Kostnad beräknad, inga pengar · 3 Nämnt utan belopp · 4 Ej nämnt i granskade dokument · 5 Inga budgethandlingar 2027 hittade

## Efteråt
Validera JSON, testa sidan lokalt (python3 -m http.server), committa och pusha till main. GitHub Pages publicerar automatiskt.

Lägg till den nya instruktionen ordagrant i `metod/logg.md`.
