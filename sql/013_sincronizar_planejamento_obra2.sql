-- Sincronizar cronograma, EAP, atividades e restrições para Obra 2
-- Aplicar em Obra 2 (lwjbuzubnxnzkofcrhah) APENAS
-- Dados vêm da Obra 1 (ivssgstckfcuiyetxdze)
-- Data: 06/10/2026

-- ⚠️  INSTRUÇÕES MANUAIS:
-- 1. Certificar que Obra 2 está RESTAURADA e ativa (não pausada)
-- 2. Exportar de Obra 1 (ivssgstckfcuiyetxdze):
--    - SELECT * FROM eap_itens WHERE obra_id = 'obra1';
--    - SELECT * FROM planejamento_cronogramas WHERE obra_id = 'obra1';
--    - SELECT * FROM planejamento_atividades WHERE obra_id = 'obra1';
--    - SELECT * FROM planejamento_restricoes WHERE obra_id = 'obra1';
--    - SELECT * FROM pauta_assuntos WHERE obra_id = 'obra1' AND id LIKE 'gs-%';
-- 3. Trocar obra_id de 'obra1' para 'obra2' nos dados exportados
-- 4. Importar em Obra 2

-- Template SQL para importar em Obra 2:
-- (substituir os valores abaixo pelos dados reais)

-- Limpar tabelas da Obra 2 (opcional, se já tiver dados antigos)
DELETE FROM planejamento_restricoes WHERE obra_id = 'obra2';
DELETE FROM planejamento_atividades WHERE obra_id = 'obra2';
DELETE FROM planejamento_cronogramas WHERE obra_id = 'obra2';
DELETE FROM eap_itens WHERE obra_id = 'obra2';
DELETE FROM pauta_assuntos WHERE obra_id = 'obra2' AND id LIKE 'gs-%';

-- Confirmar que as tabelas estão vazias para obra2
SELECT COUNT(*) FROM eap_itens WHERE obra_id = 'obra2';
SELECT COUNT(*) FROM planejamento_cronogramas WHERE obra_id = 'obra2';
SELECT COUNT(*) FROM planejamento_atividades WHERE obra_id = 'obra2';
SELECT COUNT(*) FROM planejamento_restricoes WHERE obra_id = 'obra2';
SELECT COUNT(*) FROM pauta_assuntos WHERE obra_id = 'obra2' AND id LIKE 'gs-%';
