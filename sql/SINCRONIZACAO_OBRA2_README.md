# Sincronização de Planejamento para Obra 2

## Status

Obra 1 (ivssgstckfcuiyetxdze) tem:
- 405 itens de EAP
- 1 cronograma "Cronograma BOP Gran Sul — Rev. 05"
- 2.128 atividades
- 7 restrições
- 37 assuntos de Pauta/Check-in (ids `gs-*`)

Obra 2 (lwjbuzubnxnzkofcrhah) está **vazia** e precisa ficar igual.

## Passos

### 1. Restaurar Obra 2 (se pausada)

Acesse o painel do Supabase → Obra 2 → Settings → Pause Project
- Se o projeto está pausado, clique em "Restore"
- Aguarde 2-5 minutos

### 2. Liberar acesso de jonacir70@icloud.com

**Em Obra 1 (ivssgstckfcuiyetxdze):**
```sql
UPDATE auth_usuarios 
SET papel = 'admin'
WHERE email = 'jonacir70@icloud.com';
```

**Em Obra 2 (lwjbuzubnxnzkofcrhah):**
```sql
UPDATE auth_usuarios 
SET papel = 'admin'
WHERE email = 'jonacir70@icloud.com';
```

### 3. Exportar dados de Obra 1

Acesse SQL Editor de Obra 1 e copie os resultados completos:

```sql
-- Cronograma
SELECT * FROM planejamento_cronogramas WHERE obra_id = 'obra1';

-- EAP
SELECT * FROM eap_itens WHERE obra_id = 'obra1' ORDER BY id;

-- Atividades (em lotes de 1000, se necessário)
SELECT * FROM planejamento_atividades WHERE obra_id = 'obra1' ORDER BY id;

-- Restrições
SELECT * FROM planejamento_restricoes WHERE obra_id = 'obra1' ORDER BY id;

-- Assuntos da Pauta (Gran Sul)
SELECT * FROM pauta_assuntos WHERE obra_id = 'obra1' AND id LIKE 'gs-%' ORDER BY id;
```

### 4. Importar em Obra 2

**Limpar dados antigos (se existirem):**
```sql
DELETE FROM planejamento_restricoes WHERE obra_id = 'obra2';
DELETE FROM planejamento_atividades WHERE obra_id = 'obra2';
DELETE FROM planejamento_cronogramas WHERE obra_id = 'obra2';
DELETE FROM eap_itens WHERE obra_id = 'obra2';
DELETE FROM pauta_assuntos WHERE obra_id = 'obra2' AND id LIKE 'gs-%';
DELETE FROM checkin_assuntos WHERE obra_id = 'obra2' AND id LIKE 'gs-%';
```

**Importar dados (substituir `'obra1'` → `'obra2'` nos dados copiados):**

Exemplo para cronograma:
```sql
INSERT INTO planejamento_cronogramas (id, obra_id, nome, tipo, data_status, criado_em)
VALUES 
  ('c1', 'obra2', 'Cronograma BOP Gran Sul — Rev. 05', 'baseline', '2026-10-06', '2026-10-06');
```

E assim por diante para EAP, atividades, restrições e assuntos.

### 5. Verificar paridade

Em ambas as obras:
```sql
SELECT 
  (SELECT COUNT(*) FROM eap_itens WHERE obra_id = ?obra_id?) as eap_count,
  (SELECT COUNT(*) FROM planejamento_atividades WHERE obra_id = ?obra_id?) as ativ_count,
  (SELECT COUNT(*) FROM planejamento_restricoes WHERE obra_id = ?obra_id?) as restr_count;
```

Deve retornar (405, 2128, 7).

## Notas

- As duas obras têm bancos **completamente separados** (projetos Supabase diferentes)
- Não há replicação automática — dados precisam ser copiados manualmente
- O app detecta a obra pelo `localStorage['buildly3::obra_atual_id']`
- Todos os dados têm RLS ligada (sql/010_auth_rls.sql aplicada em ambas)

## Próximas etapas

- [ ] Restaurar Obra 2
- [ ] Liberar jonacir70@icloud.com nas duas obras
- [ ] Exportar dados de Obra 1
- [ ] Importar em Obra 2
- [ ] Verificar paridade com queries acima
- [ ] Rodar testes: `python3 tests/executar.py`
- [ ] Atualizar Registro (vault/Registro/2026-10-06.md)
