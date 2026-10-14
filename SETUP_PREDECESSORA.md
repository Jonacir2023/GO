# Setup: Coluna Predecessora para Importação de Cronograma

## O que foi implementado

Sistema self-service de importação de cronogramas e atividades, onde qualquer usuário pode fazer upload de um arquivo Excel/CSV sem necessidade de suporte técnico.

**Arquivos da migração:**
- `migrations/add_predecessora_column.sql` — Script SQL para adicionar coluna
- `scripts/aplicar_migracao_predecessora.py` — Script Python para aplicação automática

## Como aplicar

### Opção 1: Manualmente via Supabase Dashboard (Recomendado)

1. Abra [Supabase — Obra 1](https://app.supabase.com/project/ivssgstckfcuiyetxdze)
2. Vá para **SQL Editor**
3. Cole o SQL abaixo e clique em **Execute**:

```sql
ALTER TABLE planejamento_atividades
ADD COLUMN IF NOT EXISTS predecessora TEXT DEFAULT NULL;

COMMENT ON COLUMN planejamento_atividades.predecessora IS 'Código da atividade predecessora (dependência)';

CREATE INDEX IF NOT EXISTS idx_planejamento_atividades_predecessora 
  ON planejamento_atividades(predecessora)
  WHERE predecessora IS NOT NULL;
```

4. Repita para **Obra 2** em [Supabase — Obra 2](https://app.supabase.com/project/lwjbuzubnxnzkofcrhah)

### Opção 2: Via Script Python (Se houver acesso ao Supabase)

```bash
cd /home/user/GO
python3 scripts/aplicar_migracao_predecessora.py
```

**Nota:** Este método requer credenciais do Supabase configuradas nas variáveis de ambiente `SUPABASE_KEY_1` e `SUPABASE_KEY_2`.

## O que a coluna "Predecessora" faz

- **Campo:** `predecessora TEXT DEFAULT NULL` em `planejamento_atividades`
- **Uso:** Rastreia código da atividade predecessora (dependência)
- **Exemplo:** Se AT-002 depende de AT-001, a coluna `predecessora` de AT-002 contém "AT-001"
- **Exibição:** Coluna visível na tabela de Atividades (entre "% Real" e "Início prev.")

## Como usar a importação após setup

1. Abra a aba **Atividades** em planejamento.html
2. Clique em **📥 Importar Cronograma**
3. Arraste arquivo Excel/CSV ou clique para selecionar
4. **Formato esperado:**
   ```
   Código | Nome | Predecessora | Data Início | Data Fim
   AT-001 | Atividade 1 | | 01/01/2026 | 31/01/2026
   AT-002 | Atividade 2 | AT-001 | 02/02/2026 | 28/02/2026
   ```
5. Datas em formato **DD/MM/YYYY** ou **YYYY-MM-DD**
6. Clique em **✓ Importar** após validação do preview

## Detalhes técnicos

**Arquivo:** `planejamento.html`
- Funções adicionadas:
  - `abrirImportarCronograma()` — Abre modal
  - `importarCronogramaArquivo(event)` — Parse de arquivo (XLSX via SheetJS CDN)
  - `converterData(dataStr)` — Converte múltiplos formatos de data
  - `confirmarImportarCronograma()` — Bulk insert no Supabase

**Modal:**
- ID: `modal-importar-cronograma`
- Drag-and-drop com preview em tempo real
- Validação com reportagem de erros
- Suporte a `.xlsx`, `.xls`, `.csv`

**Banco de dados:**
- Aplicar migração em **AMBAS** as obras (Obra 1 + Obra 2)
- Índice criado para otimizar buscas por predecessor

## Testes

Após aplicar a migração, execute:

```bash
# Verificar sintaxe
python3 scripts/verificar_sintaxe.py

# Rodar suítes de teste
python3 tests/executar.py

# Verificar isolamento entre obras
python3 scripts/verificar_isolamento.py
```

Todas as 15 suítes devem passar verde.
