# Lärartiden i budgeten

En öppen sammanställning av hur Sveriges 290 kommuner hanterar statsbidraget för reglerad undervisningstid (prop. 2025/26:196) i budget 2027.

Sidan är en statisk webbplats som publiceras med GitHub Pages. Besökarnas bedömningar sparas i Supabase.

## Filer

| Fil | Innehåll |
|---|---|
| `index.html` | Sidans struktur och fasta texter (metod, kontakt) |
| `assets/config.js` | Inställningar: datum, mejladress, skolpengsgräns, Supabase |
| `assets/app.js` | Sidans logik |
| `assets/styles.css` | Utseende |
| `data/kommuner.json` | En post per kommun: status, belopp, dokument, citat, länkar |
| `texter/*.md` | Analystexterna, en fil per flik |
| `texter/index.json` | Vilka texter som visas och i vilken ordning |
| `supabase/schema.sql` | Databasskript för bedömningar |

## Fält i `data/kommuner.json`

| Fält | Betydelse |
|---|---|
| `k`, `id`, `l` | Kommunnamn, adressnamn, län |
| `s` | Status: 0 pengar beslutade, 1 pengar föreslagna, 2 kostnad beräknad, 3 nämnt utan belopp, 4 ej nämnt, 5 ej bedömbart än |
| `sum` | Sammanfattning |
| `m`, `mk` | Pengar kopplade till reformen, egen beräknad merkostnad |
| `sb`, `pl` | Kommentar om statsbidraget, om prislista/samverkan |
| `kf`, `kfu` | Fullmäktiges budgetbeslut och källa |
| `sp` | Skolpeng: `p` (procent), `not`, `u` (källa), `typ` (förslag/beslut) |
| `styre` | Styre efter valet 2026 (fritext) |
| `lu` | Luckor i granskningen |
| `docs` | Dokument: `t` titel, `d` datum, `sk` skede, `pr` producent, `nr` nämner reformen, `c` citat, `u` länk |

## Uppdatera

- **Med Claude:** be Claude uppdatera en kommun, lägga till ett dokument eller göra en ny genomgång. Claude ändrar filerna i repot och publicerar.
- **Själv:** redigera filerna direkt på github.com (pennan uppe till höger på en fil) och spara med "Commit changes". Sidan uppdateras inom någon minut.
- **Analystexter:** redigera `texter/*.md`. En ny text läggs till som en ny fil plus en rad i `texter/index.json`.

## Bedömningar

Kör `supabase/schema.sql` en gång i Supabase → SQL Editor. Besökare kan bara lägga till bedömningar. Kommentarerna läser du i Supabase → Table Editor → `bedomningar`.
