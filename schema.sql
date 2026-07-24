create extension if not exists pgcrypto;

create table sources (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  feed_url text,
  founding_date date,
  ownership text,
  correction_history text,
  created_at timestamptz not null default now()
);

create table story_clusters (
  id uuid primary key default gen_random_uuid(),
  topic text,
  created_at timestamptz not null default now()
);

create table stories (
  id uuid primary key default gen_random_uuid(),
  source_id uuid not null references sources(id),
  cluster_id uuid references story_clusters(id),
  headline text not null,
  url text not null unique,
  snippet text check (char_length(snippet) <= 200),
  published_at timestamptz not null,
  ingested_at timestamptz not null default now()
);

create table scores (
  id uuid primary key default gen_random_uuid(),
  cluster_id uuid not null references story_clusters(id),
  score int not null check (score between 0 and 100),
  reasons jsonb not null,
  computed_at timestamptz not null default now()
);
