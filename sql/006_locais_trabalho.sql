-- BUILDLy GO — Migration: Locais de Trabalho (frentes de obra)
-- Tabela para gerenciar os locais específicos de cada obra

create table if not exists public.rdo_locais (
  id uuid primary key default gen_random_uuid(),
  obra_id uuid not null,
  nome text not null,
  descricao text,
  ativo boolean not null default true,
  criado_em timestamptz not null default now(),
  atualizado_em timestamptz not null default now(),

  constraint local_nome_nao_vazio
    check (btrim(nome) <> ''),

  constraint local_obra_nome_uq
    unique (obra_id, nome)
);

create index if not exists idx_rdo_locais_obra on public.rdo_locais(obra_id);
create index if not exists idx_rdo_locais_ativo on public.rdo_locais(ativo);
