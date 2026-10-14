-- Adicionar coluna predecessora à tabela planejamento_atividades
-- Esta coluna rastreia o código da atividade predecessora (dependência)

ALTER TABLE planejamento_atividades
ADD COLUMN predecessora TEXT DEFAULT NULL;

COMMENT ON COLUMN planejamento_atividades.predecessora IS 'Código da atividade predecessora (dependência)';

-- Criar índice para melhorar buscas por predecessora
CREATE INDEX IF NOT EXISTS idx_planejamento_atividades_predecessora
  ON planejamento_atividades(predecessora)
  WHERE predecessora IS NOT NULL;
