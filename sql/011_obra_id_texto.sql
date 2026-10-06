-- 011 — obra_id de uuid para text nas 7 tabelas de EAP / Planejamento / Suprimentos (010 fica reservada para a Fase 2 do login)
--
-- Motivo: o app grava obra_id = B3Obras.atualId(), que devolve 'obra1' / 'obra2' (texto).
-- A coluna era uuid, então TODO insert desses módulos falhava com
-- "invalid input syntax for type uuid" — por isso as 7 tabelas estavam vazias nas duas obras.
-- Corrigir no banco (e não no front) mantém o código como está e casa com o registro de obras
-- de supabase-config.js. Aplicar nas DUAS obras (regra de 06/10/2026).
-- Idempotente: só converte coluna que ainda é uuid; FKs são recriadas com IF EXISTS / checagem.

begin;

alter table public.planejamento_atividades  drop constraint if exists plan_atividade_cronograma_obra_fkey;
alter table public.planejamento_atividades  drop constraint if exists plan_atividade_eap_obra_fkey;
alter table public.planejamento_restricoes  drop constraint if exists restr_eap_obra_fkey;
alter table public.requisicoes_compra       drop constraint if exists requisicoes_compra_eap_obra_fkey;
alter table public.suprimentos_cotacoes     drop constraint if exists suprimentos_cotacoes_requisicao_fkey;
alter table public.suprimentos_pedidos      drop constraint if exists suprimentos_pedidos_requisicao_fkey;
alter table public.suprimentos_pedidos      drop constraint if exists suprimentos_pedidos_cotacao_fkey;

do $$
declare t text;
begin
  foreach t in array array['eap_itens','planejamento_cronogramas','planejamento_atividades',
                           'planejamento_restricoes','requisicoes_compra','suprimentos_cotacoes',
                           'suprimentos_pedidos'] loop
    if exists (select 1 from information_schema.columns
               where table_schema='public' and table_name=t and column_name='obra_id' and data_type='uuid') then
      execute format('alter table public.%I alter column obra_id type text using obra_id::text', t);
    end if;
  end loop;
end $$;

alter table public.planejamento_atividades add constraint plan_atividade_cronograma_obra_fkey
  foreign key (cronograma_id, obra_id) references public.planejamento_cronogramas(id, obra_id) on delete restrict;
alter table public.planejamento_atividades add constraint plan_atividade_eap_obra_fkey
  foreign key (eap_id, obra_id) references public.eap_itens(id, obra_id) on delete restrict;
alter table public.planejamento_restricoes add constraint restr_eap_obra_fkey
  foreign key (eap_id, obra_id) references public.eap_itens(id, obra_id) on delete restrict;
alter table public.requisicoes_compra add constraint requisicoes_compra_eap_obra_fkey
  foreign key (eap_id, obra_id) references public.eap_itens(id, obra_id) on delete restrict;
alter table public.suprimentos_cotacoes add constraint suprimentos_cotacoes_requisicao_fkey
  foreign key (requisicao_id, obra_id) references public.requisicoes_compra(id, obra_id) on delete restrict;
alter table public.suprimentos_pedidos add constraint suprimentos_pedidos_requisicao_fkey
  foreign key (requisicao_id, obra_id) references public.requisicoes_compra(id, obra_id) on delete restrict;
alter table public.suprimentos_pedidos add constraint suprimentos_pedidos_cotacao_fkey
  foreign key (cotacao_id, obra_id) references public.suprimentos_cotacoes(id, obra_id) on delete set null;

commit;
