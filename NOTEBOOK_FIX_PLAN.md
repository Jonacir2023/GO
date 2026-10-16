# Notebook (AI HUB) — Plano de Melhoria e Fix

## Problema Identificado

O Notebook está retornando resultados genéricos em vez de itens específicos porque:

1. ❌ **Tabela `notebook_sources` está VAZIA** (0 registros)
2. ❌ Edge Function `notebook-perguntar` não tem contexto estruturado
3. ❌ Busca é textual simples, não semanticamente refinada

**Impacto:** Perguntas sobre "plataforma" retornam centenas de itens genéricos em vez de atividades específicas do cronograma.

---

## Solução em 3 Passos

### 1. Populate `notebook_sources` (IMEDIATO — Obra 1 e Obra 2)

**Executar em ambos os projetos Supabase:**

```
Obra 1: https://supabase.com/projects/ivssgstckfcuiyetxdze
Obra 2: https://supabase.com/projects/lwjbuzubnxnzkofcrhah
```

**Passos:**
1. Abra **SQL Editor**
2. Cole o SQL abaixo (ambas as obras):

```sql
-- Limpar e repovoar notebook_sources
DELETE FROM public.notebook_sources;

INSERT INTO public.notebook_sources (codigo, nome, ativo) VALUES
  ('planejamento', 'Planejamento (Atividades, Cronogramas)', true),
  ('rdo', 'RDO (Relatório Diário de Obras)', true),
  ('custos', 'Entradas (Custos e Financeiro)', true),
  ('medicao', 'Medições (Cliente e Empreiteiros)', true),
  ('documentos', 'Documentos da Obra', true),
  ('pauta', 'Pauta de Reuniões', true),
  ('checkin', 'Check-in (Pendências)', true),
  ('manutencao', 'Manutenção (Mural)', true),
  ('reuniao', 'Reuniões (Atas)', true);

-- Verificar
SELECT COUNT(*) as total FROM public.notebook_sources;
```

3. Clique **RUN** ou `Ctrl+Enter`
4. Resultado esperado: **9 linhas inseridas, 9 ativas**
5. Repetir na Obra 2

---

### 2. Melhorar Edge Function `notebook-perguntar`

**Problema atual:** Busca por embedding simples, sem contexto estruturado.

**Melhoria proposta:**

```sql
-- Filtrar primeiro por módulo selecionado (fonte ativa)
-- Depois por similaridade semântica
-- Depois retornar com metadados

SELECT 
  id,
  modulo,
  titulo,
  conteudo,
  metadata,
  similarity
FROM notebook_sources
WHERE modulo = ANY(fontes_ativas)  -- Só módulos selecionados
  AND conteudo <-> embedding_pergunta < 0.8  -- Similares
ORDER BY similarity DESC
LIMIT 20;
```

**Status:** Aguardando acesso a Edge Function (em `/supabase/functions/notebook-perguntar`)

---

### 3. Adicionar Estrutura de Metadados

**Antes (atual):**
```
notebook_sources: codigo, nome, ativo
```

**Depois (proposto):**
```
notebook_sources: 
  - codigo (pk)
  - nome
  - ativo
  - metadata JSONB  ← novo
    - {
        "tipo": "atividade",      -- tipo de item
        "modulo": "planejamento", -- módulo origem
        "tabela": "atividades",   -- origem dos dados
        "filtro": "status != 'cancelada'"
      }
```

---

## Checklist de Implementação

- [ ] **Hoje:** Execute SQL em Obra 1 e Obra 2
- [ ] Teste Notebook: pergunte sobre "plataforma" novamente
- [ ] Se ainda retornar genérico → revisar Edge Function
- [ ] Propor migração de schema (adicionar `metadata` JSONB)
- [ ] Implementar busca estruturada na Edge Function

---

## Teste Pós-Implementação

Após popular `notebook_sources`:

1. Abra Notebook (AI HUB) no app
2. Pergunte: **"Quais são as plataformas do cronograma?"**
3. Esperado: Retorna 9 fontes disponíveis (Planejamento, RDO, etc)
4. Pergunte: **"Quais atividades envolvem plataforma GS2?"**
5. Esperado: Retorna atividades específicas de GS2 (não 2378 genéricas)

---

## Próximos Passos

1. ✅ Diagnóstico (concluído)
2. ⏳ Populate sources (você: executar SQL)
3. ⏳ Melhorar Edge Function (Claude: implementar busca estruturada)
4. ⏳ Testar em produção

