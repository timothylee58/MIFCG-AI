-- Enable pgvector for semantic search
create extension if not exists vector;

-- User roles enum
create type user_role as enum ('admin', 'analyst', 'viewer');

-- Document source enum
create type doc_source as enum ('BNM', 'SC', 'PDPA', 'BURSA', 'OTHER');

-- ─────────────────────────────────────────────
-- Profiles (extends Supabase auth.users)
-- ─────────────────────────────────────────────
create table public.profiles (
  id           uuid primary key references auth.users(id) on delete cascade,
  email        text not null,
  full_name    text,
  role         user_role not null default 'viewer',
  organisation text,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);

-- Auto-create profile on signup
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, email, full_name)
  values (
    new.id,
    new.email,
    new.raw_user_meta_data ->> 'full_name'
  );
  return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- ─────────────────────────────────────────────
-- Compliance documents (RegComply AI)
-- ─────────────────────────────────────────────
create table public.compliance_documents (
  id          uuid primary key default gen_random_uuid(),
  title       text not null,
  source      doc_source not null,
  file_url    text,
  ingested_at timestamptz,
  chunk_count int not null default 0,
  created_at  timestamptz not null default now()
);

-- ─────────────────────────────────────────────
-- Document chunks with pgvector embeddings
-- ─────────────────────────────────────────────
create table public.document_chunks (
  id           uuid primary key default gen_random_uuid(),
  document_id  uuid not null references public.compliance_documents(id) on delete cascade,
  content      text not null,
  embedding    vector(1536),           -- OpenAI/Anthropic embedding dim
  chunk_index  int not null,
  metadata     jsonb not null default '{}',
  created_at   timestamptz not null default now()
);

create index on public.document_chunks using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);

-- Semantic search function
create or replace function public.match_document_chunks(
  query_embedding  vector(1536),
  match_threshold  float,
  match_count      int,
  filter_source    text default null
)
returns table (
  id           uuid,
  document_id  uuid,
  content      text,
  similarity   float,
  metadata     jsonb
) as $$
begin
  return query
  select
    dc.id,
    dc.document_id,
    dc.content,
    1 - (dc.embedding <=> query_embedding) as similarity,
    dc.metadata
  from public.document_chunks dc
  join public.compliance_documents d on d.id = dc.document_id
  where
    1 - (dc.embedding <=> query_embedding) > match_threshold
    and (filter_source is null or d.source::text = filter_source)
  order by dc.embedding <=> query_embedding
  limit match_count;
end;
$$ language plpgsql;

-- ─────────────────────────────────────────────
-- Audit log
-- ─────────────────────────────────────────────
create table public.audit_log (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references auth.users(id),
  action     text not null,
  resource   text not null,
  metadata   jsonb not null default '{}',
  created_at timestamptz not null default now()
);

-- ─────────────────────────────────────────────
-- Row Level Security
-- ─────────────────────────────────────────────
alter table public.profiles enable row level security;
alter table public.compliance_documents enable row level security;
alter table public.document_chunks enable row level security;
alter table public.audit_log enable row level security;

-- Profiles: users see only their own row; admins see all
create policy "users_own_profile" on public.profiles
  for all using (auth.uid() = id);

create policy "admins_all_profiles" on public.profiles
  for all using (
    exists (
      select 1 from public.profiles p
      where p.id = auth.uid() and p.role = 'admin'
    )
  );

-- Compliance docs: authenticated users can read; only admins write
create policy "auth_read_documents" on public.compliance_documents
  for select using (auth.role() = 'authenticated');

create policy "admin_write_documents" on public.compliance_documents
  for all using (
    exists (
      select 1 from public.profiles p
      where p.id = auth.uid() and p.role = 'admin'
    )
  );

-- Document chunks: same as documents
create policy "auth_read_chunks" on public.document_chunks
  for select using (auth.role() = 'authenticated');

-- Audit log: users see their own; admins see all
create policy "users_own_audit" on public.audit_log
  for select using (auth.uid() = user_id);

create policy "admins_all_audit" on public.audit_log
  for select using (
    exists (
      select 1 from public.profiles p
      where p.id = auth.uid() and p.role = 'admin'
    )
  );
