-- BUILDLy GO — Migration: EAP (Estrutura Analítica do Projeto)
-- Tabela para gestão hierárquica de estrutura de projeto

create table if not exists public.eap_itens (
  id uuid primary key default gen_random_uuid(),
  obra_id uuid not null,
  pai_id uuid,
  codigo text not null,
  nome text not null,
  tipo text not null default 'pacote',
  ordem integer not null default 0,
  ativo boolean not null default true,
  criado_em timestamptz not null default now(),
  atualizado_em timestamptz not null default now(),


  constraint eap_tipo_check
    check (tipo in ('grupo','pacote','entrega','outro')),

  constraint eap_codigo_nao_vazio
    check (btrim(codigo) <> ''),

  constraint eap_nome_nao_vazio
    check (btrim(nome) <> ''),

  constraint eap_nao_pai_de_si
    check (pai_id is null or pai_id <> id),

  constraint eap_codigo_por_obra_uq
    unique (obra_id, codigo),

  constraint eap_id_obra_uq
    unique (id, obra_id)
);

create index if not exists idx_eap_obra on public.eap_itens(obra_id);
create index if not exists idx_eap_pai on public.eap_itens(pai_id);
