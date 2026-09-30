-- BUILDLy GO — Migration: Suprimentos (Requisições de Compra)
-- Fluxo: Rascunho → Cotação → Aprovação → Pedido Emitido → Cancelada

create table if not exists public.requisicoes_compra (
  id uuid primary key default gen_random_uuid(),
  obra_id uuid not null,
  numero text not null,
  eap_id uuid,
  cbs_id uuid,
  descricao text not null,
  quantidade numeric(14,3) not null default 1,
  unidade text,
  valor_estimado numeric(14,2) not null default 0,
  responsavel text,
  necessidade_em date,
  status text not null default 'rascunho',
  criado_em timestamptz not null default now(),
  criado_por uuid,
  atualizado_em timestamptz not null default now(),
  atualizado_por uuid,

  constraint requisicoes_compra_num_obra_uq
    unique (obra_id, numero),

  constraint requisicoes_compra_id_obra_uq
    unique (id, obra_id),

  constraint requisicoes_compra_desc_check
    check (btrim(descricao) <> ''),

  constraint requisicoes_compra_qtd_check
    check (quantidade > 0),

  constraint requisicoes_compra_valor_check
    check (valor_estimado >= 0),

  constraint requisicoes_compra_status_check
    check (status in ('rascunho','em_cotacao','em_aprovacao','pedido_emitido','cancelada')),


  constraint requisicoes_compra_eap_obra_fkey
    foreign key (eap_id, obra_id)
    references public.eap_itens(id, obra_id)
    on delete restrict
);

-- Tabela de cotações (fornecedores e preços)
create table if not exists public.suprimentos_cotacoes (
  id uuid primary key default gen_random_uuid(),
  obra_id uuid not null,
  requisicao_id uuid not null,
  fornecedor_nome text not null,
  valor_cotado numeric(14,2) not null default 0,
  prazo_entrega integer,
  observacoes text,
  recebido_em timestamptz,
  criado_em timestamptz not null default now(),


  constraint suprimentos_cotacoes_requisicao_fkey
    foreign key (requisicao_id, obra_id)
    references public.requisicoes_compra(id, obra_id)
    on delete restrict,

  constraint suprimentos_cotacoes_id_obra_uq
    unique (id, obra_id)
);

-- Tabela de pedidos emitidos
create table if not exists public.suprimentos_pedidos (
  id uuid primary key default gen_random_uuid(),
  obra_id uuid not null,
  requisicao_id uuid not null,
  cotacao_id uuid,
  numero_pedido text,
  fornecedor_nome text not null,
  valor_pedido numeric(14,2) not null default 0,
  data_emissao date not null,
  data_entrega_prevista date,
  data_entrega_real date,
  status text not null default 'emitido',
  criado_em timestamptz not null default now(),
  emitido_por uuid,

  constraint suprimentos_pedidos_status_check
    check (status in ('emitido','em_transito','recebido','cancelado')),


  constraint suprimentos_pedidos_requisicao_fkey
    foreign key (requisicao_id, obra_id)
    references public.requisicoes_compra(id, obra_id)
    on delete restrict,

  constraint suprimentos_pedidos_cotacao_fkey
    foreign key (cotacao_id, obra_id)
    references public.suprimentos_cotacoes(id, obra_id)
    on delete set null,

  constraint suprimentos_pedidos_id_obra_uq
    unique (id, obra_id)
);

-- Índices
create index if not exists idx_requisicoes_obra on public.requisicoes_compra(obra_id);
create index if not exists idx_requisicoes_status on public.requisicoes_compra(status);
create index if not exists idx_requisicoes_eap on public.requisicoes_compra(eap_id);
create index if not exists idx_cotacoes_requisicao on public.suprimentos_cotacoes(requisicao_id);
create index if not exists idx_pedidos_requisicao on public.suprimentos_pedidos(requisicao_id);
create index if not exists idx_pedidos_status on public.suprimentos_pedidos(status);
