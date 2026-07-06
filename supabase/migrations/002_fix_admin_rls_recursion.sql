-- Fix self-recursive RLS admin policies introduced in 001_initial_schema.sql.
--
-- Policies such as "admins_all_profiles" queried `public.profiles` from
-- inside a RLS policy defined *on* `public.profiles`. Postgres re-applies
-- RLS to that inner subquery, which is a classic self-recursion risk for
-- RLS policies (unpredictable behaviour / infinite evaluation loops).
--
-- The fix: a SECURITY DEFINER helper function. SECURITY DEFINER runs with
-- the privileges of the function owner and therefore bypasses RLS for its
-- internal query, breaking the recursive cycle.

create or replace function public.is_admin(uid uuid)
returns boolean
language sql
security definer
set search_path = public
stable
as $$
  select exists (
    select 1 from public.profiles
    where id = uid and role = 'admin'
  );
$$;

comment on function public.is_admin(uuid) is
  'Returns true if the given user id has role = admin. SECURITY DEFINER '
  'so it bypasses RLS on public.profiles and does not recurse when used '
  'inside a policy defined on public.profiles itself.';

-- ─────────────────────────────────────────────
-- profiles: recreate admins_all_profiles using is_admin()
-- ─────────────────────────────────────────────
drop policy if exists "admins_all_profiles" on public.profiles;

create policy "admins_all_profiles" on public.profiles
  for all using (public.is_admin(auth.uid()));

-- ─────────────────────────────────────────────
-- compliance_documents: recreate admin_write_documents using is_admin()
-- ─────────────────────────────────────────────
drop policy if exists "admin_write_documents" on public.compliance_documents;

create policy "admin_write_documents" on public.compliance_documents
  for all using (public.is_admin(auth.uid()));

-- ─────────────────────────────────────────────
-- audit_log: recreate admins_all_audit using is_admin()
-- ─────────────────────────────────────────────
drop policy if exists "admins_all_audit" on public.audit_log;

create policy "admins_all_audit" on public.audit_log
  for select using (public.is_admin(auth.uid()));

-- ─────────────────────────────────────────────
-- Documentation: writes to document_chunks and audit_log are backend-only
-- ─────────────────────────────────────────────
comment on table public.document_chunks is
  'Ingested compliance document chunks with pgvector embeddings. '
  'Intentionally has no INSERT/UPDATE/DELETE RLS policy: writes only '
  'happen via the backend service using the Supabase service-role key '
  '(which bypasses RLS), as part of the RegComply ingestion pipeline. '
  'Client-facing roles only ever read via match_document_chunks()/SELECT.';

comment on table public.audit_log is
  'Append-only audit trail. Intentionally has no INSERT/UPDATE/DELETE RLS '
  'policy for regular users: entries are written only by the backend '
  'service using the Supabase service-role key (which bypasses RLS), '
  'so audit logging cannot be tampered with or forged by end users. '
  'Users may only SELECT their own rows; admins may SELECT all rows '
  '(see users_own_audit / admins_all_audit).';
