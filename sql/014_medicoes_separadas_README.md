# Script SQL: Separação de Medições em Duas Aplicações

**Arquivo:** `sql/014_medicoes_separadas.sql`
**Data:** 2026-10-15
**Aplica:** Obra 1 (`ivssgstckfcuiyetxdze`) e Obra 2 (`lwjbuzubnxnzkofcrhah`)

## O que faz

Este script prepara as tabelas de Medições para a nova estrutura:

1. **Renomeia** `medicao_contratos` → `medicoes_clientes`
2. **Cria** tabela `medicoes_empreiteiros` (para medições de empreiteiros)
3. **Cria** tabela `empreiteiros` (cadastro de empreiteiros)
4. **Configura** RLS (Row Level Security) nas três tabelas

## Como executar

### Via Supabase Studio (Recomendado)

1. Abra o painel do projeto (Obra 1)
2. Navegue para **SQL Editor** → **New Query**
3. Cole o conteúdo de `sql/014_medicoes_separadas.sql`
4. Clique **Run**
5. Repita para Obra 2

### Migração de dados (se necessário)

Se há dados em `medicao_contratos` em Obra 1, o script preserve-os ao renomear a tabela.

Após o script rodar, verifique:

```sql
SELECT COUNT(*) FROM medicoes_clientes;
```

Deve devolver o número de contratos de clientes em Obra 1.

## Aplicação em Obra 2

Obra 2 está vazia. O script cria as três tabelas vazias, prontas para uso.

## Verificação pós-execução

Para confirmar que tudo foi criado:

```sql
\dt medicoes_*
\dt empreiteiros
```

Ambos devem listar as três tabelas com sucesso.

## Rollback

Se necessário reverter (não recomendado em produção):

```sql
ALTER TABLE medicoes_clientes RENAME TO medicao_contratos;
DROP TABLE medicoes_empreiteiros;
DROP TABLE empreiteiros;
```

---
**Vinculado:** PR #66 (Separar app Medição em duas aplicações)
