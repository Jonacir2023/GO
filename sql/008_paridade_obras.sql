-- BUILDLy — Migration 008: PARIDADE entre Obra 1 e Obra 2 (regra do usuário, 06/10/2026:
-- toda adaptação vale para as DUAS obras). Já aplicada em 06/10/2026; fica aqui como registro.
-- Resultado conferido: as duas obras com 25 tabelas, 257 colunas, mesmo hash de estrutura.
--
-- OBRA 2 (lwjbuzubnxnzkofcrhah) estava pausada e sem as tabelas de EAP/Planejamento/Suprimentos:
--   criadas 001 + 005 (EAP), 002 (Planejamento), 004 (Suprimentos) e 007 (Entradas),
--   todas com RLS ligada e política "acesso do app" (for all using (true)) — o mesmo acesso
--   efetivo da Obra 1, só que sem o aviso de RLS desligada.
-- Colunas de aprovação que a Obra 1 tinha e a Obra 2 não (financeiro.html filtra por status):
alter table public.custos_notas_fiscais add column if not exists status text not null default 'rascunho';
alter table public.custos_notas_fiscais add column if not exists aprovado_em timestamptz;
alter table public.custos_notas_fiscais add column if not exists aprovado_por uuid;
alter table public.custos_notas_fiscais add column if not exists atualizado_em timestamptz not null default now();
-- (Obra 2) alter table public.custos_notas_fiscais add constraint custos_nf_status_check
--   check (status in ('rascunho','em_aprovacao','aprovada','rejeitada','cancelada'));
create index if not exists idx_custos_nf_status on public.custos_notas_fiscais(status) where status = 'em_aprovacao';

alter table public.medicao_contratos add column if not exists status text not null default 'rascunho';
alter table public.medicao_contratos add column if not exists aprovado_em timestamptz;
alter table public.medicao_contratos add column if not exists aprovado_por uuid;
-- (Obra 2) alter table public.medicao_contratos add constraint medicao_contratos_status_check
--   check (status in ('rascunho','em_aprovacao','aprovada','rejeitada','cancelada'));
create index if not exists idx_medicao_contratos_status on public.medicao_contratos(status) where status = 'em_aprovacao';

-- rdo_locais na Obra 2 era text sem 'ativo' (o RDO filtra .eq('ativo', true)): alinhada à Obra 1
-- (tabela vazia na hora). id uuid default gen_random_uuid(), ativo, nome único e não vazio.
-- (Obra 2) alter table public.rdo_locais alter column id drop default;
-- (Obra 2) alter table public.rdo_locais alter column id type uuid using id::uuid;
-- (Obra 2) alter table public.rdo_locais alter column id set default gen_random_uuid();
alter table public.rdo_locais add column if not exists ativo boolean not null default true;
-- (Obra 2) alter table public.rdo_locais add constraint local_nome_nao_vazio check (btrim(nome) <> '');
-- (Obra 2) alter table public.rdo_locais add constraint local_nome_uq unique (nome);
create index if not exists idx_rdo_locais_ativo on public.rdo_locais(ativo);

-- OBRA 1 (ivssgstckfcuiyetxdze) não tinha as colunas de 005 em eap_itens (o eap.html usa
-- responsavel, status, data_inicio, data_fim, percentual_completo, descricao): aplicada a 005.
-- Pendência de segurança herdada (decisão do usuário): na Obra 1 as 7 tabelas de EAP,
-- Planejamento e Suprimentos continuam SEM RLS.
