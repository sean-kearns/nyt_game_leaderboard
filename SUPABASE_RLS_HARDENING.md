# Supabase RLS Hardening Guide (for `rls_disabled_in_public`)

Based on your current schema screenshot, your exposed tables are Django/allauth tables such as:
- `auth_user`, `users_profile`, `users_friendship`
- `leaderboards_connectionsscore`, `leaderboards_game`
- `django_session`, `django_admin_log`, `socialaccount_*`, etc.

These should **not** be publicly writable/readable from browser clients by default.

## Why Supabase shows `rls_disabled_in_public`
Supabase warns when tables in `public` do not have Row Level Security (RLS), which means API roles could access rows too broadly if grants permit it.

---

## Plan for this Django + Supabase architecture

Because your user system is Django-auth based (`auth_user`) rather than Supabase Auth, the safest baseline is:

1. **Deny `anon` and `authenticated` access to Django tables.**
2. **Use server-only access** (service role key in backend only) for Django-managed data.
3. If you later expose specific tables to clients, add RLS + explicit policies table-by-table.

---

## 1) Immediate lockdown for current public tables

Run this in Supabase SQL Editor:

```sql
-- Revoke broad access from browser-facing roles.
revoke all on all tables in schema public from anon;
revoke all on all tables in schema public from authenticated;

-- Also lock sequences often used by Django/autoincrement ids.
revoke all on all sequences in schema public from anon;
revoke all on all sequences in schema public from authenticated;
```

This alone closes the biggest hole for tables marked `UNRESTRICTED`.

---

## 2) Enable RLS on all application tables

Even when roles are revoked, enabling RLS gives defense-in-depth:

```sql
-- Generate and run the statements this query outputs.
select 'alter table public.' || quote_ident(tablename) || ' enable row level security;'
from pg_tables
where schemaname = 'public'
order by tablename;
```

Optional (stricter):

```sql
-- Forces RLS even for table owners (unless bypassrls role).
select 'alter table public.' || quote_ident(tablename) || ' force row level security;'
from pg_tables
where schemaname = 'public'
order by tablename;
```

---

## 3) Keep Django tables server-only

For tables in your screenshot, prefer **no client policies at all**:
- `auth_*`
- `django_*`
- `socialaccount_*`
- `users_*`
- `leaderboards_*` (unless you intentionally support direct client writes)

Your Django app should read/write these via backend credentials only, not directly from the browser.

> Important: never expose the Supabase service-role key in frontend code.

---

## 4) If you intentionally expose a table to logged-in clients

Your current schema uses `player_name` (varchar) and Django `auth_user.username`, so `auth.uid() = user_id` is not compatible.

### First, remove incompatible policies (fixes your current error)

If you previously created any policies that compare `auth.uid()` (UUID) to text/varchar columns, drop them:

```sql
drop policy if exists "scores_select_own" on public.leaderboards_connectionsscore;
drop policy if exists "scores_insert_own" on public.leaderboards_connectionsscore;
drop policy if exists "scores_update_own" on public.leaderboards_connectionsscore;
drop policy if exists "scores_delete_own" on public.leaderboards_connectionsscore;
```

### Recommended for your current app: keep this table server-only

```sql
revoke all on public.leaderboards_connectionsscore from anon;
revoke all on public.leaderboards_connectionsscore from authenticated;
```

### If you *must* expose it to logged-in clients

Only do this if your Supabase JWT includes a username claim (for example `preferred_username`) that exactly matches `player_name`.

```sql
alter table public.leaderboards_connectionsscore enable row level security;

grant select, insert, update, delete
on public.leaderboards_connectionsscore
to authenticated;

create policy "scores_select_own_username"
on public.leaderboards_connectionsscore
for select
using (player_name = coalesce(auth.jwt() ->> 'preferred_username', ''));

create policy "scores_insert_own_username"
on public.leaderboards_connectionsscore
for insert
with check (player_name = coalesce(auth.jwt() ->> 'preferred_username', ''));

create policy "scores_update_own_username"
on public.leaderboards_connectionsscore
for update
using (player_name = coalesce(auth.jwt() ->> 'preferred_username', ''))
with check (player_name = coalesce(auth.jwt() ->> 'preferred_username', ''));

create policy "scores_delete_own_username"
on public.leaderboards_connectionsscore
for delete
using (player_name = coalesce(auth.jwt() ->> 'preferred_username', ''));
```

If your JWT does not include username, do **not** use this pattern. Keep server-only, or add a proper UUID owner column mapped to Supabase Auth and use `auth.uid()`.

---

## 5) Verify everything

### A) Check RLS status
```sql
select c.relname as table_name,
       c.relrowsecurity as rls_enabled,
       c.relforcerowsecurity as rls_forced
from pg_class c
join pg_namespace n on n.oid = c.relnamespace
where n.nspname = 'public'
  and c.relkind = 'r'
order by c.relname;
```

### B) Check grants on public tables
```sql
select table_schema, table_name, grantee, privilege_type
from information_schema.role_table_grants
where table_schema = 'public'
  and grantee in ('anon', 'authenticated')
order by table_name, grantee, privilege_type;
```

Expected baseline for security: no rows (or only explicitly intended rows) for `anon` and `authenticated`.

---

## 6) Why steps 5A/5B failed for you

The `uuid = character varying` error indicates at least one active RLS policy compares `auth.uid()` (UUID) to a text/varchar column. PostgreSQL evaluates policy expressions during reads, so unrelated queries can fail until the bad policy is dropped.

Use this to inspect policy definitions and find mismatched comparisons:

```sql
select schemaname, tablename, policyname, cmd, qual, with_check
from pg_policies
where schemaname = 'public'
order by tablename, policyname;
```

After dropping/fixing those policies, rerun the verification queries from section 5.

---

## 7) Practical recommendation for your current app

Given your current table set, the correct first move is:
1. Revoke all `anon`/`authenticated` table + sequence privileges in `public`.
2. Enable RLS everywhere.
3. Keep database access behind Django backend only.
4. Re-open access only per-table with explicit policies when you truly need direct client DB calls.

That will clear the dangerous exposure pattern behind `rls_disabled_in_public` and align with user-scoped security.
