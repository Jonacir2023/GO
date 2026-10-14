WITH cronograma_info AS (
  SELECT id FROM planejamento_cronogramas 
  WHERE nome = 'Cronograma F1' AND obra_id = 'obra1' LIMIT 1
)
INSERT INTO planejamento_atividades 
  (nome, codigo, cronograma_id, eap_id, obra_id, inicio_planejado, fim_planejado)
VALUES
('Executar Pavimentação', 'AT-02343', (SELECT id FROM cronograma_info), (SELECT id FROM eap_itens WHERE obra_id = 'obra1' ORDER BY RANDOM() LIMIT 1), 'obra1', '2027-04-20'::date, '2027-05-10'::date)
('PLATÔ SUBESTAÇÃO MARMELEIRO II (BAY)', 'AT-02344', (SELECT id FROM cronograma_info), (SELECT id FROM eap_itens WHERE obra_id = 'obra1' ORDER BY RANDOM() LIMIT 1), 'obra1', '2027-05-03'::date, '2027-06-09'::date)
('Executar Supressão Vegetal', 'AT-02345', (SELECT id FROM cronograma_info), (SELECT id FROM eap_itens WHERE obra_id = 'obra1' ORDER BY RANDOM() LIMIT 1), 'obra1', '2027-05-03'::date, '2027-05-13'::date)
('Remover camada vegetal (20cm), carga e transporte para Bota-fora/Bota-Espera,
('Executar Terraplenagem', 'AT-02347', (SELECT id FROM cronograma_info), (SELECT id FROM eap_itens WHERE obra_id = 'obra1' ORDER BY RANDOM() LIMIT 1), 'obra1', '2027-05-25'::date, '2027-06-09'::date)
('PLATÔ CANTEIRO DE OBRAS SUBESTAÇÃO MARMELERIRO II (BAY)', 'AT-02348', (SELECT id FROM cronograma_info), (SELECT id FROM eap_itens WHERE obra_id = 'obra1' ORDER BY RANDOM() LIMIT 1), 'obra1', '2027-05-03'::date, '2027-06-02'::date)
('Remover camada vegetal (20cm), carga e transporte para Bota-fora/Bota-Espera,
('Executar Terraplenagem', 'AT-02350', (SELECT id FROM cronograma_info), (SELECT id FROM eap_itens WHERE obra_id = 'obra1' ORDER BY RANDOM() LIMIT 1), 'obra1', '2027-05-07'::date, '2027-06-02'::date)
('PLATÔ ALMOXARIFADO E O&M', 'AT-02351', (SELECT id FROM cronograma_info), (SELECT id FROM eap_itens WHERE obra_id = 'obra1' ORDER BY RANDOM() LIMIT 1), 'obra1', '2026-12-22'::date, '2027-01-28'::date)
('Remover camada vegetal (20cm), carga e transporte para Bota-fora/Bota-Espera,
('Executar Terraplenagem', 'AT-02353', (SELECT id FROM cronograma_info), (SELECT id FROM eap_itens WHERE obra_id = 'obra1' ORDER BY RANDOM() LIMIT 1), 'obra1', '2026-12-30'::date, '2027-01-28'::date)
('PLATÔ CANTEIRO DE OBRAS 02 (PRINCIPAL)', 'AT-02354', (SELECT id FROM cronograma_info), (SELECT id FROM eap_itens WHERE obra_id = 'obra1' ORDER BY RANDOM() LIMIT 1), 'obra1', '2026-12-22'::date, '2027-03-19'::date)
('Remover camada vegetal (20cm), carga e transporte para Bota-fora/Bota-Espera,
('Executar Terraplenagem', 'AT-02356', (SELECT id FROM cronograma_info), (SELECT id FROM eap_itens WHERE obra_id = 'obra1' ORDER BY RANDOM() LIMIT 1), 'obra1', '2027-01-13'::date, '2027-03-19'::date)
('PLATÔ CANTEIRO DE OBRAS LT', 'AT-02357', (SELECT id FROM cronograma_info), (SELECT id FROM eap_itens WHERE obra_id = 'obra1' ORDER BY RANDOM() LIMIT 1), 'obra1', '2026-12-22'::date, '2027-02-01'::date)
('Remover camada vegetal (20cm), carga e transporte para Bota-fora/Bota-Espera,
('Executar Terraplenagem', 'AT-02359', (SELECT id FROM cronograma_info), (SELECT id FROM eap_itens WHERE obra_id = 'obra1' ORDER BY RANDOM() LIMIT 1), 'obra1', '2026-12-30'::date, '2027-02-01'::date)
('CERCAMENTO', 'AT-02360', (SELECT id FROM cronograma_info), (SELECT id FROM eap_itens WHERE obra_id = 'obra1' ORDER BY RANDOM() LIMIT 1), 'obra1', '2026-12-22'::date, '2027-03-11'::date)
('CERCAS E PORTÕES', 'AT-02361', (SELECT id FROM cronograma_info), (SELECT id FROM eap_itens WHERE obra_id = 'obra1' ORDER BY RANDOM() LIMIT 1), 'obra1', '2026-12-22'::date, '2027-03-11'::date)
('Instalar mata-burro de madeira ou concreto', 'AT-02362', (SELECT id FROM cronograma_info), (SELECT id FROM eap_itens WHERE obra_id = 'obra1' ORDER BY RANDOM() LIMIT 1), 'obra1', '2026-12-22'::date, '2027-01-22'::date)
('Instalar Portões de Madeira', 'AT-02363', (SELECT id FROM cronograma_info), (SELECT id FROM eap_itens WHERE obra_id = 'obra1' ORDER BY RANDOM() LIMIT 1), 'obra1', '2027-01-22'::date, '2027-02-04'::date)
('Instalar Cercas padrão rural', 'AT-02364', (SELECT id FROM cronograma_info), (SELECT id FROM eap_itens WHERE obra_id = 'obra1' ORDER BY RANDOM() LIMIT 1), 'obra1', '2027-02-04'::date, '2027-03-11'::date)
('EDIFÍCIOS DE O&M E AUXILIARES', 'AT-02365', (SELECT id FROM cronograma_info), (SELECT id FROM eap_itens WHERE obra_id = 'obra1' ORDER BY RANDOM() LIMIT 1), 'obra1', '2027-04-01'::date, '2027-09-30'::date)
('EDIFÍCIOS DE O&M', 'AT-02366', (SELECT id FROM cronograma_info), (SELECT id FROM eap_itens WHERE obra_id = 'obra1' ORDER BY RANDOM() LIMIT 1), 'obra1', '2027-04-01'::date, '2027-09-30'::date)
('Executar Guarita', 'AT-02367', (SELECT id FROM cronograma_info), (SELECT id FROM eap_itens WHERE obra_id = 'obra1' ORDER BY RANDOM() LIMIT 1), 'obra1', '2027-06-25'::date, '2027-09-30'::date)
('Executar Edifício de O&M', 'AT-02368', (SELECT id FROM cronograma_info), (SELECT id FROM eap_itens WHERE obra_id = 'obra1' ORDER BY RANDOM() LIMIT 1), 'obra1', '2027-04-01'::date, '2027-09-28'::date)
('Executar Almoxarifado', 'AT-02369', (SELECT id FROM cronograma_info), (SELECT id FROM eap_itens WHERE obra_id = 'obra1' ORDER BY RANDOM() LIMIT 1), 'obra1', '2027-04-01'::date, '2027-08-30'::date)
('Executar Depósito de Resíduos não-perigosos', 'AT-02370', (SELECT id FROM cronograma_info), (SELECT id FROM eap_itens WHERE obra_id = 'obra1' ORDER BY RANDOM() LIMIT 1), 'obra1', '2027-05-17'::date, '2027-08-18'::date)
('Executar Depósito de Resíduos Perigosos', 'AT-02371', (SELECT id FROM cronograma_info), (SELECT id FROM eap_itens WHERE obra_id = 'obra1' ORDER BY RANDOM() LIMIT 1), 'obra1', '2027-05-17'::date, '2027-08-18'::date)
('PISTAS DE DESACELERAÇÃO - BR-471', 'AT-02372', (SELECT id FROM cronograma_info), (SELECT id FROM eap_itens WHERE obra_id = 'obra1' ORDER BY RANDOM() LIMIT 1), 'obra1', '2027-09-14'::date, '2027-10-27'::date)
('ACESSOS', 'AT-02373', (SELECT id FROM cronograma_info), (SELECT id FROM eap_itens WHERE obra_id = 'obra1' ORDER BY RANDOM() LIMIT 1), 'obra1', '2027-09-14'::date, '2027-10-18'::date)
('Liberação pelos órgãos competentes para início das atividades (Resp. Cliente)', 'AT-02374', (SELECT id FROM cronograma_info), (SELECT id FROM eap_itens WHERE obra_id = 'obra1' ORDER BY RANDOM() LIMIT 1), 'obra1', '2027-09-14'::date, '2027-09-14'::date)
('Executar Supressão Vegetal', 'AT-02375', (SELECT id FROM cronograma_info), (SELECT id FROM eap_itens WHERE obra_id = 'obra1' ORDER BY RANDOM() LIMIT 1), 'obra1', '2027-09-14'::date, '2027-09-27'::date)
('Executar Terraplenagem', 'AT-02376', (SELECT id FROM cronograma_info), (SELECT id FROM eap_itens WHERE obra_id = 'obra1' ORDER BY RANDOM() LIMIT 1), 'obra1', '2027-09-17'::date, '2027-10-05'::date)
('Executar Pavimentação', 'AT-02377', (SELECT id FROM cronograma_info), (SELECT id FROM eap_itens WHERE obra_id = 'obra1' ORDER BY RANDOM() LIMIT 1), 'obra1', '2027-09-30'::date, '2027-10-18'::date)
('SINALIZAÇÃO VERTICAL', 'AT-02378', (SELECT id FROM cronograma_info), (SELECT id FROM eap_itens WHERE obra_id = 'obra1' ORDER BY RANDOM() LIMIT 1), 'obra1', '2027-10-18'::date, '2027-10-27'::date)
('Instalar Placas de Sinalização', 'AT-02379', (SELECT id FROM cronograma_info), (SELECT id FROM eap_itens WHERE obra_id = 'obra1' ORDER BY RANDOM() LIMIT 1), 'obra1', '2027-10-18'::date, '2027-10-27'::date)
('DESMOBILIZAÇÃO', 'AT-02380', (SELECT id FROM cronograma_info), (SELECT id FROM eap_itens WHERE obra_id = 'obra1' ORDER BY RANDOM() LIMIT 1), 'obra1', '2028-05-10'::date, '2028-07-31'::date)
('DESMOBILIZAÇÃO - FASE 1', 'AT-02381', (SELECT id FROM cronograma_info), (SELECT id FROM eap_itens WHERE obra_id = 'obra1' ORDER BY RANDOM() LIMIT 1), 'obra1', '2028-05-10'::date, '2028-06-30'::date)
('Desmobilização', 'AT-02382', (SELECT id FROM cronograma_info), (SELECT id FROM eap_itens WHERE obra_id = 'obra1' ORDER BY RANDOM() LIMIT 1), 'obra1', '2028-05-10'::date, '2028-06-30'::date)
ON CONFLICT DO NOTHING;