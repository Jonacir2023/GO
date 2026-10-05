-- BUILDLy — Migration 007: Custos como controle de ENTRADA DE MATERIAIS (portaria)
-- Proposta aprovada em 05/10/2026 (vault/Decisões/2026-10-05 Proposta — Custos...).
-- Aplicar em CADA projeto Supabase de obra (Obra 1: ivssgstckfcuiyetxdze · Obra 2: lwjbuzubnxnzkofcrhah).
-- Idempotente: pode rodar mais de uma vez. As tabelas antigas (custos_notas_fiscais,
-- custos_itens_nf) NÃO são tocadas.

-- Cadastro: categorias, subcategorias, descrições de NF, fornecedores e porteiros (uma tabela só)
create table if not exists public.custos_catalogo (
  id text primary key,
  tipo text not null,                 -- categoria | subcategoria | descricao | fornecedor | porteiro
  nome text not null,
  pai_id text,                        -- subcategoria -> categoria; descricao -> subcategoria
  unidade text,                       -- unidade padrão (subcategoria/descrição)
  mede_por text,                      -- carga | viagem | peso | unidade (subcategoria)
  ativo boolean not null default true,
  ordem integer not null default 0,
  criado_em timestamptz not null default now(),
  atualizado_em timestamptz not null default now(),
  constraint custos_catalogo_tipo_check
    check (tipo in ('categoria','subcategoria','descricao','fornecedor','porteiro')),
  constraint custos_catalogo_nome_nao_vazio check (btrim(nome) <> '')
);
create index if not exists idx_custos_catalogo_tipo on public.custos_catalogo(tipo);

-- Uma linha por item que entra na obra (é a planilha)
create table if not exists public.custos_entradas (
  id text primary key,
  recebido_em timestamptz not null default now(),   -- hora de chegada (ordena a planilha)
  data_recebimento date not null,                   -- dia local do recebimento (resumos e RDO)
  numero_nf text not null,
  data_emissao date,
  fornecedor text not null,
  categoria text not null,
  subcategoria text not null,
  descricao text,
  unidade text,
  quantidade numeric not null default 0,
  preco_unitario numeric,                           -- null = "sem valor" (escritório completa)
  total numeric,
  responsavel text,
  placa text,
  observacoes text,
  mede_por text,
  n_fotos integer not null default 0,
  status text not null default 'ativo',             -- ativo | cancelado (baixa lógica, nunca apaga)
  cancelado_motivo text,
  criado_em timestamptz not null default now(),
  atualizado_em timestamptz not null default now(),
  constraint custos_entradas_status_check check (status in ('ativo','cancelado'))
);
create index if not exists idx_custos_entradas_data on public.custos_entradas(data_recebimento);
create index if not exists idx_custos_entradas_status on public.custos_entradas(status);

-- Fotos da nota (separadas para não pesar a consulta da planilha); até 4 por lançamento
create table if not exists public.custos_entradas_fotos (
  id text primary key,
  entrada_id text not null,
  ordem integer not null default 0,
  foto text not null,                               -- data URL (JPEG comprimido)
  criado_em timestamptz not null default now()
);
create index if not exists idx_custos_fotos_entrada on public.custos_entradas_fotos(entrada_id);

-- RLS no mesmo padrão das demais tabelas do app (acesso anônimo; sem delete nas entradas)
alter table public.custos_catalogo enable row level security;
alter table public.custos_entradas enable row level security;
alter table public.custos_entradas_fotos enable row level security;

drop policy if exists "custos_catalogo leitura" on public.custos_catalogo;
drop policy if exists "custos_catalogo insercao" on public.custos_catalogo;
drop policy if exists "custos_catalogo atualizacao" on public.custos_catalogo;
create policy "custos_catalogo leitura" on public.custos_catalogo for select using (true);
create policy "custos_catalogo insercao" on public.custos_catalogo for insert with check (true);
create policy "custos_catalogo atualizacao" on public.custos_catalogo for update using (true);

drop policy if exists "custos_entradas leitura" on public.custos_entradas;
drop policy if exists "custos_entradas insercao" on public.custos_entradas;
drop policy if exists "custos_entradas atualizacao" on public.custos_entradas;
create policy "custos_entradas leitura" on public.custos_entradas for select using (true);
create policy "custos_entradas insercao" on public.custos_entradas for insert with check (true);
create policy "custos_entradas atualizacao" on public.custos_entradas for update using (true);

drop policy if exists "custos_fotos leitura" on public.custos_entradas_fotos;
drop policy if exists "custos_fotos insercao" on public.custos_entradas_fotos;
create policy "custos_fotos leitura" on public.custos_entradas_fotos for select using (true);
create policy "custos_fotos insercao" on public.custos_entradas_fotos for insert with check (true);
