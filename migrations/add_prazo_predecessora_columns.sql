-- Adicionar colunas 'prazo' e 'predecessora' à tabela planejamento_atividades
-- Aplicar em ambas as obras (Obra 1 + Obra 2)

ALTER TABLE planejamento_atividades
ADD COLUMN IF NOT EXISTS prazo TEXT DEFAULT NULL,
ADD COLUMN IF NOT EXISTS predecessora TEXT DEFAULT NULL;

CREATE INDEX IF NOT EXISTS idx_planejamento_atividades_prazo
ON planejamento_atividades(prazo);

CREATE INDEX IF NOT EXISTS idx_planejamento_atividades_predecessora
ON planejamento_atividades(predecessora);
