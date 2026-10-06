---
criado: 2026-10-05
tags: [nota, custos, portaria]
---

# Entradas — controle de entrada de materiais (portaria)

**Nome da aba/módulo: "Entradas"** (renomeado de "Custos" em 05/10/2026 a pedido do usuário, em todo texto visível: cartão da home, título, Favoritos, cabeçalho). **Os identificadores internos continuam `custos`** (`switchTab('custos')`, `custos.html`, `#page-custos`, chaves `custo_*`, tabelas `custos_*`) — mudar isso quebraria dados já gravados e links.

Aprovado em 05/10/2026 (proposta: [[Decisões/2026-10-05 Proposta — Entradas como controle de entrada de materiais]]).
`custos.html` deixou de ser "cadastro de nota fiscal com itens" e virou o **controle de entrada de material
da portaria**: cada item que chega vira **uma linha** de planilha, em **ordem de chegada**.

## Telas (barra de 4 botões + ⚙️ Cadastro)

| Tela | O que faz |
|---|---|
| **Entrada** | Categoria e Subcategoria em botões (＋ Nova na hora), descrição da nota do cadastro + complemento livre, quantidade/unidade (padrão da subcategoria), nº da nota, emissão, fornecedor, preço (opcional), recebido por, **até 4 fotos** (câmera traseira ou galeria), placa/observação em "＋ mais campos". Duplicidade (mesma nota+fornecedor+emissão+subcategoria+qtde) pede confirmação. Nota com muitos itens = **kit** (1 lançamento) |
| **Planilha** | Colunas: Hora · Nº nota · Emissão · Fornecedor · Categoria · Subcategoria · Descrição da nota · Un. · Qtde · Preço unit. · Total · Responsável. Filtros dia/semana/mês/data, categoria, fornecedor, nº. Toque na linha: fotos, **completar valor**, **cancelar com motivo** (baixa lógica). **Exportar .csv** (`;`, BOM, colunas da planilha do usuário + Recebido em/Placa/Obs./Status) e imprimir |
| **Resumo** | Quantidades por categoria ▸ subcategoria (ou por descrição): soma por **unidade** (nunca mistura m³ com t), nº de cargas/viagens (campo "mede por"), NFs |
| **Resumo R$** | Total lançado, nº de notas, pendências "sem valor ▸ completar", R$ por categoria/subcategoria com % e preço médio por unidade, por fornecedor, comparação com o período anterior |
| **⚙️ Cadastro** | Materiais (categoria ▸ subcategoria com unidade padrão e "mede por"), Descrições NF, Fornecedores, Porteiros, Notas antigas (somente consulta). 🗑 só desativa |

## Regras

- **Do dia = recebido no dia** (`data_recebimento`, dia local), não a data de emissão da nota.
- **Sem valor** (`preco_unitario`/`total` nulos) fica fora das somas de R$ e aparece como "—"/"sem valor".
- Cancelar = `status='cancelado'` + motivo; nunca apaga (mesma regra do RDO).
- Foto: JPEG ≤1024 px, qualidade 0,62; fica no aparelho só até subir (depois é lida do servidor sob demanda).
- **O RDO leva a planilha do dia inteira + o resumo de quantidades** (com valores na planilha) — ver [[Notas/RDO — Regras do Módulo]].
- Seed do cadastro com **ids determinísticos** (`cat-agregados`, `sub-agregados-areia`…): dois aparelhos que
  semeiam não duplicam nada ao sincronizar.

## Dados

Local (`custo_*`): `catalogo`, `entradas`, `fotos` (pendentes), `ultimo_resp`, `notasfiscais` (modelo antigo).
Supabase (por obra): `custos_catalogo`, `custos_entradas`, `custos_entradas_fotos` — migração em
`sql/007_custos_entradas.sql` — **aplicada nas duas obras em 06/10/2026** (sem as tabelas o app funciona só no
aparelho e reenvia depois). As tabelas antigas `custos_notas_fiscais`/`custos_itens_nf` ficam intactas; o robô de IA
(`buildly-completo.html`) ainda consulta essas antigas — **pendente** apontar para `custos_entradas`.

## Relacionado

- [[Notas/Contrato do Backend]] · [[Notas/Armazenamento Local]] · [[Projetos/BUILDLy Premium]]
