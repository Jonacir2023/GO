-- BUILDLy — Migration 010: LOGIN FASE 2 — RLS por papel (fecha o banco para quem não tem login/papel).
-- Depois da Fase 1 (sql/009), troca as políticas abertas ("acesso do app", "acesso_livre_*") por `to authenticated`
-- + public.pode_modulo('<módulo>'). Admin ('*') enxerga tudo; portaria só 'custos' (aba Entradas); pendente nada.
-- obra_config: qualquer papel liberado lê; só quem tem o módulo 'obra' grava.
-- Leituras entre módulos: rdo lê checkin_assuntos e custos_*; financeiro lê rdo_snapshot; checkin e pauta
-- compartilham pauta_assuntos/checkin_assuntos (envio-pauta.html grava nos dois).
-- ATENÇÃO: neste Supabase `DROP POLICY` TRAVA (o comando não termina, nem com lock_timeout) — por isso a migração
-- usa só ALTER POLICY (muda o papel/regra da política existente) e CREATE POLICY. Um comando por vez, em partes pequenas.
-- Nomes das políticas antigas: os da Obra 1. Na Obra 2 só rdo_locais difere (uma política 'rdo_locais_all').
-- Reversão: sql/010_rollback_rls.sql. (Obra 1: pauta_assuntos ficou com uma política duplicada, "acesso por papel (2)",
-- criada na primeira tentativa e igual à principal — inofensiva, não removível porque DROP POLICY trava.)
-- Aplicada em 06/10/2026 nas DUAS obras e testada com papéis simulados (anon, admin, portaria, pendente).

-- pauta_assuntos
alter policy "acesso_livre_pauta_assuntos" on public.pauta_assuntos to authenticated using ((select public.pode_modulo('pauta')) or (select public.pode_modulo('checkin'))) with check ((select public.pode_modulo('pauta')) or (select public.pode_modulo('checkin')));
alter policy "acesso_livre_pauta_assuntos" on public.pauta_assuntos rename to "acesso por papel";
-- pauta_setores
alter policy "acesso_livre_pauta_setores" on public.pauta_setores to authenticated using ((select public.pode_modulo('pauta'))) with check ((select public.pode_modulo('pauta')));
create policy "leitura por papel (outros modulos)" on public.pauta_setores for select to authenticated using ((select public.pode_modulo('checkin')));
alter policy "acesso_livre_pauta_setores" on public.pauta_setores rename to "acesso por papel";
-- pauta_membros
alter policy "acesso_livre_pauta_membros" on public.pauta_membros to authenticated using ((select public.pode_modulo('pauta'))) with check ((select public.pode_modulo('pauta')));
create policy "leitura por papel (outros modulos)" on public.pauta_membros for select to authenticated using ((select public.pode_modulo('checkin')));
alter policy "acesso_livre_pauta_membros" on public.pauta_membros rename to "acesso por papel";
-- checkin_assuntos
alter policy "acesso_livre_checkin_assuntos" on public.checkin_assuntos to authenticated using ((select public.pode_modulo('checkin')) or (select public.pode_modulo('pauta'))) with check ((select public.pode_modulo('checkin')) or (select public.pode_modulo('pauta')));
create policy "leitura por papel (outros modulos)" on public.checkin_assuntos for select to authenticated using ((select public.pode_modulo('rdo')));
alter policy "acesso_livre_checkin_assuntos" on public.checkin_assuntos rename to "acesso por papel";
-- checkin_reunioes
alter policy "acesso_livre_checkin_reunioes" on public.checkin_reunioes to authenticated using ((select public.pode_modulo('checkin'))) with check ((select public.pode_modulo('checkin')));
alter policy "acesso_livre_checkin_reunioes" on public.checkin_reunioes rename to "acesso por papel";
-- rdo_snapshot
alter policy "acesso_livre_rdo_snapshot" on public.rdo_snapshot to authenticated using ((select public.pode_modulo('rdo'))) with check ((select public.pode_modulo('rdo')));
create policy "leitura por papel (outros modulos)" on public.rdo_snapshot for select to authenticated using ((select public.pode_modulo('financeiro')));
alter policy "acesso_livre_rdo_snapshot" on public.rdo_snapshot rename to "acesso por papel";
-- rdo_locais
alter policy "Leitura pública de locais" on public.rdo_locais to authenticated using ((select public.pode_modulo('rdo')));
alter policy "Inserção pública de locais" on public.rdo_locais to authenticated with check ((select public.pode_modulo('rdo')));
alter policy "Atualização pública de locais" on public.rdo_locais to authenticated using ((select public.pode_modulo('rdo'))) with check ((select public.pode_modulo('rdo')));
alter policy "Deleção pública de locais" on public.rdo_locais to authenticated using ((select public.pode_modulo('rdo')));
alter policy "Leitura pública de locais" on public.rdo_locais rename to "select por papel";
alter policy "Inserção pública de locais" on public.rdo_locais rename to "insert por papel";
alter policy "Atualização pública de locais" on public.rdo_locais rename to "update por papel";
alter policy "Deleção pública de locais" on public.rdo_locais rename to "delete por papel";
-- custos_entradas
alter policy "custos_entradas leitura" on public.custos_entradas to authenticated using ((select public.pode_modulo('custos')));
alter policy "custos_entradas insercao" on public.custos_entradas to authenticated with check ((select public.pode_modulo('custos')));
alter policy "custos_entradas atualizacao" on public.custos_entradas to authenticated using ((select public.pode_modulo('custos'))) with check ((select public.pode_modulo('custos')));
create policy "leitura por papel (outros modulos)" on public.custos_entradas for select to authenticated using ((select public.pode_modulo('rdo')));
alter policy "custos_entradas leitura" on public.custos_entradas rename to "select por papel";
alter policy "custos_entradas insercao" on public.custos_entradas rename to "insert por papel";
alter policy "custos_entradas atualizacao" on public.custos_entradas rename to "update por papel";
-- custos_entradas_fotos
alter policy "custos_fotos leitura" on public.custos_entradas_fotos to authenticated using ((select public.pode_modulo('custos')));
alter policy "custos_fotos insercao" on public.custos_entradas_fotos to authenticated with check ((select public.pode_modulo('custos')));
create policy "leitura por papel (outros modulos)" on public.custos_entradas_fotos for select to authenticated using ((select public.pode_modulo('rdo')));
alter policy "custos_fotos leitura" on public.custos_entradas_fotos rename to "select por papel";
alter policy "custos_fotos insercao" on public.custos_entradas_fotos rename to "insert por papel";
-- custos_catalogo
alter policy "custos_catalogo leitura" on public.custos_catalogo to authenticated using ((select public.pode_modulo('custos')));
alter policy "custos_catalogo insercao" on public.custos_catalogo to authenticated with check ((select public.pode_modulo('custos')));
alter policy "custos_catalogo atualizacao" on public.custos_catalogo to authenticated using ((select public.pode_modulo('custos'))) with check ((select public.pode_modulo('custos')));
create policy "leitura por papel (outros modulos)" on public.custos_catalogo for select to authenticated using ((select public.pode_modulo('rdo')));
alter policy "custos_catalogo leitura" on public.custos_catalogo rename to "select por papel";
alter policy "custos_catalogo insercao" on public.custos_catalogo rename to "insert por papel";
alter policy "custos_catalogo atualizacao" on public.custos_catalogo rename to "update por papel";
-- custos_notas_fiscais
alter policy "acesso_livre_custos_notas_fiscais" on public.custos_notas_fiscais to authenticated using ((select public.pode_modulo('custos')) or (select public.pode_modulo('financeiro'))) with check ((select public.pode_modulo('custos')) or (select public.pode_modulo('financeiro')));
alter policy "acesso_livre_custos_notas_fiscais" on public.custos_notas_fiscais rename to "acesso por papel";
-- custos_itens_nf
alter policy "acesso_livre_custos_itens_nf" on public.custos_itens_nf to authenticated using ((select public.pode_modulo('custos')) or (select public.pode_modulo('financeiro'))) with check ((select public.pode_modulo('custos')) or (select public.pode_modulo('financeiro')));
alter policy "acesso_livre_custos_itens_nf" on public.custos_itens_nf rename to "acesso por papel";
-- medicao_contratos
alter policy "acesso_livre_medicao_contratos" on public.medicao_contratos to authenticated using ((select public.pode_modulo('medicao')) or (select public.pode_modulo('financeiro'))) with check ((select public.pode_modulo('medicao')) or (select public.pode_modulo('financeiro')));
alter policy "acesso_livre_medicao_contratos" on public.medicao_contratos rename to "acesso por papel";
-- documentos
alter policy "acesso_livre_documentos" on public.documentos to authenticated using ((select public.pode_modulo('documentos'))) with check ((select public.pode_modulo('documentos')));
alter policy "acesso_livre_documentos" on public.documentos rename to "acesso por papel";
-- documento_notas_manuais
alter policy "acesso_livre_documento_notas_manuais" on public.documento_notas_manuais to authenticated using ((select public.pode_modulo('documentos'))) with check ((select public.pode_modulo('documentos')));
alter policy "acesso_livre_documento_notas_manuais" on public.documento_notas_manuais rename to "acesso por papel";
-- eap_itens
alter policy "acesso do app" on public.eap_itens to authenticated using ((select public.pode_modulo('eap'))) with check ((select public.pode_modulo('eap')));
alter policy "acesso do app" on public.eap_itens rename to "acesso por papel";
-- planejamento_cronogramas
alter policy "acesso do app" on public.planejamento_cronogramas to authenticated using ((select public.pode_modulo('planejamento'))) with check ((select public.pode_modulo('planejamento')));
alter policy "acesso do app" on public.planejamento_cronogramas rename to "acesso por papel";
-- planejamento_atividades
alter policy "acesso do app" on public.planejamento_atividades to authenticated using ((select public.pode_modulo('planejamento'))) with check ((select public.pode_modulo('planejamento')));
alter policy "acesso do app" on public.planejamento_atividades rename to "acesso por papel";
-- planejamento_restricoes
alter policy "acesso do app" on public.planejamento_restricoes to authenticated using ((select public.pode_modulo('planejamento'))) with check ((select public.pode_modulo('planejamento')));
alter policy "acesso do app" on public.planejamento_restricoes rename to "acesso por papel";
-- manutencao_mural
alter policy "acesso_livre_manutencao_mural" on public.manutencao_mural to authenticated using ((select public.pode_modulo('manutencao'))) with check ((select public.pode_modulo('manutencao')));
alter policy "acesso_livre_manutencao_mural" on public.manutencao_mural rename to "acesso por papel";
-- reuniao_atas
alter policy "acesso_livre_reuniao_atas" on public.reuniao_atas to authenticated using ((select public.pode_modulo('reuniao'))) with check ((select public.pode_modulo('reuniao')));
alter policy "acesso_livre_reuniao_atas" on public.reuniao_atas rename to "acesso por papel";
-- requisicoes_compra
alter policy "acesso do app" on public.requisicoes_compra to authenticated using ((select public.pode_modulo('suprimentos'))) with check ((select public.pode_modulo('suprimentos')));
alter policy "acesso do app" on public.requisicoes_compra rename to "acesso por papel";
-- suprimentos_cotacoes
alter policy "acesso do app" on public.suprimentos_cotacoes to authenticated using ((select public.pode_modulo('suprimentos'))) with check ((select public.pode_modulo('suprimentos')));
alter policy "acesso do app" on public.suprimentos_cotacoes rename to "acesso por papel";
-- suprimentos_pedidos
alter policy "acesso do app" on public.suprimentos_pedidos to authenticated using ((select public.pode_modulo('suprimentos'))) with check ((select public.pode_modulo('suprimentos')));
alter policy "acesso do app" on public.suprimentos_pedidos rename to "acesso por papel";
-- obra_config
alter policy "acesso_livre_obra_config" on public.obra_config to authenticated using ((select public.pode_modulo('obra'))) with check ((select public.pode_modulo('obra')));
create policy "leitura por papel" on public.obra_config for select to authenticated using (coalesce((select public.papel_atual()),'pendente') <> 'pendente');
alter policy "acesso_livre_obra_config" on public.obra_config rename to "acesso por papel";
