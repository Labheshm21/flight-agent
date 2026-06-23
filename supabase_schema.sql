create table if not exists flights (
  id bigint primary key generated always as identity,
  flight_number text not null,
  origin text not null,
  destination text not null,
  status text default 'scheduled',
  created_at timestamp with time zone default now()
);

alter table flights enable row level security;

drop policy if exists "public can read flights" on flights;
create policy "public can read flights"
on flights
for select
to anon
using (true);

drop policy if exists "public can insert flights" on flights;
create policy "public can insert flights"
on flights
for insert
to anon
with check (true);
