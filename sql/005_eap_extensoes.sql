-- BUILDLy GO — Migration: Extensões de EAP (responsáveis, status, datas, progresso)

alter table public.eap_itens
add column if not exists responsavel text,
add column if not exists status text not null default 'planejado',
add column if not exists data_inicio date,
add column if not exists data_fim date,
add column if not exists percentual_completo integer not null default 0,
add column if not exists descricao text;

alter table public.eap_itens
add constraint eap_status_check
  check (status in ('planejado','em_execucao','concluido','atrasado','suspenso'));

alter table public.eap_itens
add constraint eap_percentual_check
  check (percentual_completo >= 0 and percentual_completo <= 100);

create index if not exists idx_eap_responsavel on public.eap_itens(responsavel);
create index if not exists idx_eap_status on public.eap_itens(status);
create index if not exists idx_eap_data_inicio on public.eap_itens(data_inicio);
create index if not exists idx_eap_data_fim on public.eap_itens(data_fim);
