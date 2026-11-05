-- Lärartiden i budgeten: databas för besökarnas bedömningar.
-- Klistra in allt i Supabase → SQL Editor och klicka Run. Går att köra flera gånger.

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

-- Besökare får bara lägga till nya bedömningar. Ingen kan läsa, ändra eller
-- radera enskilda rader via webbsidan. Du ser allt i Supabase → Table Editor.
drop policy if exists "alla kan lagga till" on public.bedomningar;
create policy "alla kan lagga till" on public.bedomningar
  for insert to anon, authenticated with check (true);

revoke all on public.bedomningar from anon, authenticated;
grant insert (kommun, data, dok, tolk, kommentar) on public.bedomningar to anon, authenticated;

-- Publik sammanställning: antal och snitt per kommun, utan kommentarer.
create or replace view public.bedomningar_snitt as
  select kommun,
         count(*)::int                    as antal,
         round(avg(data)::numeric, 2)     as snitt_data,
         round(avg(dok)::numeric, 2)      as snitt_dok,
         round(avg(tolk)::numeric, 2)     as snitt_tolk
  from public.bedomningar
  group by kommun;

grant select on public.bedomningar_snitt to anon, authenticated;
