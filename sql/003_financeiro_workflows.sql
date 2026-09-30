-- BUILDLy GO — Migration: Financeiro (Workflows de aprovação para Medições e NFs)

-- Adicionar colunas de workflow às medições (se não existirem)
alter table public.medicoes add column if not exists status text not null default 'rascunho';
alter table public.medicoes add column if not exists aprovado_em timestamptz;
alter table public.medicoes add column if not exists aprovado_por uuid;
alter table public.medicoes add column if not exists atualizado_em timestamptz not null default now();

-- Restrição de status para medições
alter table public.medicoes drop constraint if exists medicoes_status_check;
alter table public.medicoes add constraint medicoes_status_check
  check (status in ('rascunho','em_aprovacao','aprovada','rejeitada','cancelada'));

-- Adicionar colunas de workflow às notas fiscais (se não existirem)
alter table public.custos_notas_fiscais add column if not exists status text not null default 'rascunho';
alter table public.custos_notas_fiscais add column if not exists aprovado_em timestamptz;
alter table public.custos_notas_fiscais add column if not exists aprovado_por uuid;
alter table public.custos_notas_fiscais add column if not exists atualizado_em timestamptz not null default now();

-- Restrição de status para notas fiscais
alter table public.custos_notas_fiscais drop constraint if exists custos_nf_status_check;
alter table public.custos_notas_fiscais add constraint custos_nf_status_check
  check (status in ('rascunho','em_aprovacao','aprovada','rejeitada','cancelada'));

-- Índices para consultas de pendência
create index if not exists idx_medicoes_status on public.medicoes(status) where status = 'em_aprovacao';
create index if not exists idx_nf_status on public.custos_notas_fiscais(status) where status = 'em_aprovacao';
