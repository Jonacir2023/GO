-- Adicionar coluna 'prazo' à tabela planejamento_atividades
-- Obra 1 (ivssgstckfcuiyetxdze)

ALTER TABLE planejamento_atividades
ADD COLUMN IF NOT EXISTS prazo TEXT DEFAULT NULL;

CREATE INDEX IF NOT EXISTS idx_planejamento_atividades_prazo
ON planejamento_atividades(prazo);
