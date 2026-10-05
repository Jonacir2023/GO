---
criado: 2026-10-05
tags: [decisao, proposta, custos, portaria]
status: aprovada e implementada em 05/10/2026 — falta aplicar sql/007 nas duas obras
---

# Proposta — Custos vira controle de entrada de materiais (portaria)

**Origem (05/10/2026):** o Custos atual exige cabeçalho de NF + itens, é pesado para quem está na
portaria e só soma dinheiro. O usuário quer: formulário **curto**, 1 item ou **kit** (nota com muitos
itens), uso **em tempo real pela portaria**, e resumo **por quantidade, por categoria e subcategoria**
(areia, brita, rachão, água, argila, saibro…) para controlar a entrada diária de material.
**Aprovada pelo usuário em 05/10/2026 ("ok coloque em prática") e implementada** — ver [[Notas/Custos — Entrada de Materiais]]. Perguntas abertas resolvidas pela recomendação: Hora na planilha = sim; RDO só quantidades; Responsável = quem recebeu; "mede por" incluído; até 4 fotos; Fornecedores e Porteiros no Cadastro. Mockup: 3 telas (entrada rápida, kit, resumo).

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

## 6. Revisão do layout (pedido do usuário, 05/10/2026) — 6 telas no mockup

O usuário pediu: **botão de foto**, **＋ para Categoria e Subcategoria** na própria tela e um **Cadastro**
para criar categorias, subcategorias e descrições de NF. Incluído no layout (ainda sem código):

1. **Entrada rápida:** chips de categoria e subcategoria com **＋ Nova** (abre painel "Nova subcategoria"
   na hora, já selecionada depois de salvar); **＋** ao lado do fornecedor; **📷 Tirar foto** e **🖼 Galeria**
   com miniaturas (nota, verso; × remove); botão **⚙️ Cadastro** no topo.
2. **Nota com vários itens:** além de categoria/subcategoria, **Descrição da nota** escolhida no
   cadastro (Kit material elétrico, Kit iluminação, Quadro de comando…) + complemento livre; várias fotos
   (páginas da nota).
3. **Câmera:** moldura de enquadramento, flash, "Página 2 de 2", galeria, "Usar 2 fotos". Fotos ficam anexadas
   ao lançamento. (Leitura automática do nº da nota por OCR fica fora desta fase — já era item em aberto.)
4. **＋ Nova subcategoria (rápida):** categoria, nome, unidade padrão e "mede por" (carga/viagem/peso/unidade).
5. **⚙️ Cadastro** (abas **Materiais · Descrições NF · Fornecedores · Porteiros**): árvore categoria →
   subcategoria com unidade padrão, ativar/desativar, editar, ＋ Subcategoria dentro de cada categoria, ＋ Nova
   categoria. 🗑 só **desativa** (histórico mantido).
6. **Resumo:** período (Hoje/Ontem/Semana/Mês/data) × visão **Por categoria ▸ subcategoria**, **Por
   descrição** ou **Lista do dia**; totais por unidade (ex.: "60 m³ · 48 t" — unidades diferentes nunca são
   somadas), nº de cargas e NFs de origem; valor em segundo plano; exportar .csv.

Pontos para o usuário confirmar nesta revisão: (a) **"Mede por"** na subcategoria (carga/viagem/peso/
unidade) é necessário? (b) fotos: **até quantas por lançamento**? (c) **Fornecedores** e **Porteiros** entram
no mesmo Cadastro (como no layout)?

## 7. Versão 3 do layout — Planilha e Resumo R$ (pedido do usuário, 05/10/2026)

O usuário mandou o modelo da planilha (11 colunas) e pediu: **preencher a planilha item a item, em ordem
cronológica, a cada entrada na obra**; **além do Resumo, apresentar a Planilha**; e um botão **Resumo R$**
para os resumos de **valores**, separando-os dos **quantitativos**. A barra do Custos passa a ter **4 botões**:

| Botão | O que mostra |
|---|---|
| **Entrada** | formulário da portaria (Salvar → a linha entra na planilha) |
| **Planilha** | uma linha por item recebido, **por hora de chegada**: **Hora · Nº nota · Emissão · Fornecedor · Categoria · Subcategoria · Descrição da nota · Un. · Qtde · Preço unit. · Total · Responsável** (= as 11 colunas dele + "Hora"); filtros dia/semana/mês/data, categoria, fornecedor, nº da nota; toque na linha: foto, completar valor, cancelar; total lançado e "sem valor"; exportar .csv e imprimir |
| **Resumo** | quantitativo: categoria ▸ subcategoria e por descrição (qtde por unidade, nº de cargas, NFs) |
| **Resumo R$** | valores: total lançado, notas, pendências "sem valor ▸ completar", R$ por categoria/subcategoria com % do total e **preço médio por unidade**, e por fornecedor |

Regras do desenho: a ordem é a de **chegada** (a nota emitida ontem e recebida hoje entra na hora em que
chegou); **"Hora"** é a única coluna além do modelo (a planilha original não tem como ordenar sem ela) —
no .csv vai como "Recebido em"; os cabeçalhos corrigem a grafia ("Quantidade", "Preço"); entrada sem
preço aparece como **"sem valor"** e fica de fora das somas até ser completada; unidades diferentes nunca
se somam. No computador do escritório a Planilha ocupa a tela toda (todas as colunas visíveis); no celular
rola na horizontal. O PDF do RDO traz a versão **quantitativa** (Resumo); valores não vão no RDO a menos que o
usuário peça.

Pontos para confirmar: (a) a coluna **Hora** pode entrar? (b) o RDO leva só quantidades (recomendado) ou também
valores? (c) "Responsável" = quem recebeu na portaria (recomendado) ou quem comprou?

## Relacionado

- [[Notas/RDO — Regras do Módulo]]
- [[Notas/Contrato do Backend]]
- [[Projetos/BUILDLy Premium]]
