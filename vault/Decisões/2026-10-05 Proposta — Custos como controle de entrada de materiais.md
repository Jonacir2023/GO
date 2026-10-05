---
criado: 2026-10-05
tags: [decisao, proposta, custos, portaria]
status: proposta — aguardando aprovação (nada implementado)
---

# Proposta — Custos vira controle de entrada de materiais (portaria)

**Origem (05/10/2026):** o Custos atual exige cabeçalho de NF + itens, é pesado para quem está na
portaria e só soma dinheiro. O usuário quer: formulário **curto**, 1 item ou **kit** (nota com muitos
itens), uso **em tempo real pela portaria**, e resumo **por quantidade, por categoria e subcategoria**
(areia, brita, rachão, água, argila, saibro…) para controlar a entrada diária de material.
**Nada disto foi implementado — esperando aprovação.** Mockup: 3 telas (entrada rápida, kit, resumo).

## 1. Processo da portaria

1. Caminhão/entrega chega → porteiro abre **Custos → Rápida**.
2. Toca **Categoria** (botões grandes) e **Subcategoria** (ex.: Agregados → Brita 1). A **unidade** já
   vem preenchida pela subcategoria (m³, t, un, kit…).
3. Digita **Quantidade**, **Nº da nota/ticket**, **Fornecedor** (lista dos recentes), **Placa** (opcional).
4. **Valor** é opcional na portaria; foto da nota opcional. Data/hora e "Recebido por" saem sozinhos.
5. **Salvar** → entra na lista de hoje; o resumo se atualiza na hora (offline: guarda e envia depois).
6. **Nota com muitos itens** (elétrico, hidráulico…): 1 lançamento "kit" — categoria, subcategoria,
   descrição ("Kit material elétrico – QD-02"), quantidade 1 kit, valor total da NF. Detalhar item a item
   é opcional.
7. Escritório depois **completa valores** dos lançamentos marcados "sem valor" e pode **cancelar**
   lançamento errado (baixa lógica com motivo — nunca apaga).
8. **Resumo** (Hoje / Ontem / Semana / Mês / data): quantidades por categoria → subcategoria, nº de
   cargas, NFs de origem; dinheiro fica em segundo plano. O mesmo resumo vai para o **PDF do RDO**.

## 2. Modelo de dados (uma linha por lançamento — é a sua planilha)

Nº da nota · Data de emissão · Fornecedor · Categoria · Subcategoria · Descrição · Unidade ·
Quantidade · Preço unitário · Total · Responsável — **mais** (a aprovar): Recebido em (data/hora
automática), Placa, Foto da nota, Observação, Status (ativo/cancelado + motivo).
Tabela nova `custos_entradas` + `custos_catalogo` (categoria, subcategoria, unidade padrão; editável).
As tabelas antigas (`custos_notas_fiscais`, `custos_itens_nf`) ficam intactas.

## 3. Catálogo inicial (confirmar/completar)

- **Agregados:** areia, brita 0, brita 1, brita 2, pedrisco, rachão, bica corrida
- **Terra:** argila, saibro, aterro
- **Água:** caminhão-pipa (m³), galão/garrafão (un)
- **Concreto/Cimento:** concreto usinado (m³), cimento (saco), argamassa
- **Aço:** CA-50, CA-60, tela, arame
- **Elétrico / Hidráulico:** kit, cabos, eletrodutos, tubos, conexões
- **Combustível:** diesel S10, gasolina (L) · **Outros**
- **Unidades:** m³, t, kg, L, un, kit, saco, m, viagem

## 4. Decisões a aprovar (minha recomendação em negrito)

| # | Decisão | Recomendação |
|---|---|---|
| 1 | Preço na portaria | **Opcional**; escritório completa; etiqueta "sem valor" |
| 2 | Medida dos agregados | **Por carga em m³** (cada caminhão = 1 lançamento, "cargas" contadas); t quando tiver balança |
| 3 | "Recebido por" | **Lista de porteiros escolhida 1 vez no aparelho** (sem login) |
| 4 | Nota com muitos itens | **Kit (1 lançamento)** + detalhar opcional |
| 5 | RDO | **Resumo por categoria/subcategoria** no lugar da tabela item a item; "Cargas de material" dos Eventos do dia continua separado |
| 6 | Notas antigas | **Ficam consultáveis** numa aba "Notas antigas"; não migram |
| 7 | Erro de lançamento | **Cancelar com motivo** (baixa lógica) |
| 8 | Sem sinal | **Salva no aparelho e sincroniza** (padrão do app) |
| 9 | Duplicidade | **Avisa** se repetir nº da nota + fornecedor + data |
| 10 | Exportar | **Botão .csv** com as colunas da planilha |

## 5. Plano de implementação (depois do "aprovado")

1. Banco: criar `custos_entradas` e `custos_catalogo` **nas duas obras** (Supabase) + catálogo inicial.
2. Tela Entrada rápida + kit (compacta, 1 tela no celular).
3. Resumo por categoria/subcategoria (dia/semana/mês) + lista do dia com cancelar/completar valor.
4. PDF do RDO: bloco "Entrada de materiais do dia" com as quantidades.
5. Exportar .csv; cadastro do catálogo e dos porteiros.
6. Testes (entrada, kit, resumo, cancelamento, duplicidade, offline, RDO) + cofre + registro.

## Relacionado

- [[Notas/RDO — Regras do Módulo]]
- [[Notas/Contrato do Backend]]
- [[Projetos/BUILDLy Premium]]
