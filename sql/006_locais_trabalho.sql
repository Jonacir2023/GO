-- BUILDLy GO — Migration: Locais de Trabalho (frentes de obra)
-- Cada projeto Supabase é dedicado a uma obra, portanto não há coluna obra_id

create table if not exists public.rdo_locais (
  id uuid primary key default gen_random_uuid(),
  nome text not null,
  descricao text,
  ativo boolean not null default true,
  criado_em timestamptz not null default now(),
  atualizado_em timestamptz not null default now(),

  constraint local_nome_nao_vazio
    check (btrim(nome) <> ''),

  constraint local_nome_uq
    unique (nome)
);

create index if not exists idx_rdo_locais_ativo on public.rdo_locais(ativo);
