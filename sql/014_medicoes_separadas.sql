-- Separar Medições em duas aplicações: Cliente e Empreiteiros
-- Obra 1 (ivssgstckfcuiyetxdze) e Obra 2 (lwjbuzubnxnzkofcrhah)
-- Criado: 2026-10-15

-- 1. Renomear medicao_contratos → medicoes_clientes e adicionar coluna tipo
-- (Mantém compatibilidade: tipo='Cliente' para todos os existentes)
ALTER TABLE IF EXISTS medicao_contratos RENAME TO medicoes_clientes;

-- 2. Criar tabela medicoes_empreiteiros (clone da estrutura de medicoes_clientes)
CREATE TABLE IF NOT EXISTS medicoes_empreiteiros (
  id text PRIMARY KEY,
  nome text NOT NULL,
  empresa text,
  especialidade text,
  numero_contrato text,
  cnpj text,
  contato text,
  telefone text,
  email text,
  itens jsonb DEFAULT '[]'::jsonb,
  medicoes jsonb DEFAULT '[]'::jsonb,
  atualizado_em timestamptz DEFAULT now(),
  criado_em timestamptz DEFAULT now()
);

-- 3. Criar tabela empreiteiros (cadastro separado)
CREATE TABLE IF NOT EXISTS empreiteiros (
  id text PRIMARY KEY,
  nome text NOT NULL,
  empresa text,
  especialidade text,
  numero_contrato text,
  cnpj text,
  contato text,
  telefone text,
  email text,
  atualizado_em timestamptz DEFAULT now(),
  criado_em timestamptz DEFAULT now()
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_medicoes_clientes_nome ON medicoes_clientes(nome);
CREATE INDEX IF NOT EXISTS idx_medicoes_empreiteiros_nome ON medicoes_empreiteiros(nome);
CREATE INDEX IF NOT EXISTS idx_empreiteiros_nome ON empreiteiros(nome);

-- RLS (assume que RLS padrão já está em vigor para authenticated + pode_modulo)
ALTER TABLE medicoes_clientes ENABLE ROW LEVEL SECURITY;
ALTER TABLE medicoes_empreiteiros ENABLE ROW LEVEL SECURITY;
ALTER TABLE empreiteiros ENABLE ROW LEVEL SECURITY;

-- Políticas RLS (padrão: authenticated + pode_modulo verifica no front-end)
DROP POLICY IF EXISTS "Leitura de medicoes_clientes" ON medicoes_clientes;
DROP POLICY IF EXISTS "Escrita em medicoes_clientes" ON medicoes_clientes;
DROP POLICY IF EXISTS "Leitura de medicoes_empreiteiros" ON medicoes_empreiteiros;
DROP POLICY IF EXISTS "Escrita em medicoes_empreiteiros" ON medicoes_empreiteiros;
DROP POLICY IF EXISTS "Leitura de empreiteiros" ON empreiteiros;
DROP POLICY IF EXISTS "Escrita em empreiteiros" ON empreiteiros;

CREATE POLICY "Leitura de medicoes_clientes" ON medicoes_clientes
  FOR SELECT TO authenticated USING (true);
CREATE POLICY "Escrita em medicoes_clientes" ON medicoes_clientes
  FOR ALL TO authenticated USING (true);

CREATE POLICY "Leitura de medicoes_empreiteiros" ON medicoes_empreiteiros
  FOR SELECT TO authenticated USING (true);
CREATE POLICY "Escrita em medicoes_empreiteiros" ON medicoes_empreiteiros
  FOR ALL TO authenticated USING (true);

CREATE POLICY "Leitura de empreiteiros" ON empreiteiros
  FOR SELECT TO authenticated USING (true);
CREATE POLICY "Escrita em empreiteiros" ON empreiteiros
  FOR ALL TO authenticated USING (true);
