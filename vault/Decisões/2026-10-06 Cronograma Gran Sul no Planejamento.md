---
data: 2026-10-06
status: decidido
tags: [decisão, planejamento, supabase, gransul]
---

# Cronograma da Gran Sul carregado no Planejamento (Obra 1)

**Status:** ✅ Decidido · **PR:** ver Registro de 06/10/2026

---

## Contexto

A Obra 1 é a **Eólica GranSul** (Statkraft). O usuário pediu "o melhor app para o melhor controle da obra" e
escolheu "corrigir e carregar tudo". Havia três problemas:

- EAP, Planejamento e Suprimentos **nunca gravaram nada**: `obra_id` era uuid e o app manda `'obra1'`.
- O Planejamento só listava cronogramas. As abas Atividades e Restrições eram placeholders vazios.
- O cronograma real (Rev. 05, 2.533 linhas, PDF do MS Project) não estava no app.

## Alternativas

1. **Trocar o front para mandar um uuid por obra.** Descartada: mexe em 3 módulos e em `supabase-config.js`,
   e o resto do app (Pauta, Check-in…) já trabalha com o id texto.
2. **Importar o cronograma pela tela (upload do XML do MS Project).** Fica como evolução. Para a Gran Sul a
   carga foi feita direto no banco, para o usuário já abrir com dados.

## Decisão

- `obra_id` passa a ser **text** nas 7 tabelas, nas duas obras (`sql/011_obra_id_texto.sql`).
- **EAP = linhas-resumo do cronograma (405).** Código hierárquico `01.02.03…` (2 dígitos por nível, para a
  ordenação de texto do `eap.html` bater com a árvore). Descrição guarda o ID original: "Cronograma Rev. 05 — ID n".
- **Atividades = linhas-folha (2.128)** em `planejamento_atividades`, ligadas ao resumo-pai (`eap_id`), dentro
  do cronograma "Cronograma BOP Gran Sul — Rev. 05 (linha de base)" (tipo `baseline`). `codigo` = ID do Rev. 05,
  para cruzar com o PDF e com o MS Project.
- Prazos do PDF são **dias corridos** (conferido em todas as linhas: fim = início + prazo − 1).
- Aba **Atividades**: filtros (hoje, atrasadas, próximos 15 dias, concluídas), busca por código/nome/WTG,
  KPIs de avanço físico ponderado por duração (previsto linear × real), % real editável. Ao lançar % > 0 sem
  início real, grava o início real com hoje; em 100%, grava o fim real.
- Aba **Restrições**: cadastro e troca de status, com prazo vencido em vermelho. Carregadas 7 restrições
  vindas das inconsistências achadas nos documentos.
- **Pauta/Check-in:** 37 assuntos do Round 3 (22/09) e da análise dos documentos, com id `gs-<código>`
  (ex.: `gs-ENG-01`), gravados em `pauta_assuntos` e `checkin_assuntos` (mesmo padrão do `envio-pauta.html`).

## Consequências

- Virou regra em [[Notas/Regras Operacionais Críticas]]: `obra_id` é texto, e listas grandes leem em lotes de 1000.
- O ID 950 do Rev. 05 tem nome errado no original ("Plataforma GS2" sob PLATAFORMA GS_03). Foi mantido como
  está no documento e ficou registrado como restrição.
- A linha de base é o próprio cronograma: o "previsto" não muda quando o real é lançado.

## Pendente

- Conferir no celular, com o banco real, a aba Atividades (aqui o teste usa um Supabase simulado; o CDN é bloqueado).
- Predecessoras: o PDF não traz. Sem elas não há caminho crítico nem reprogramação automática. Pedir o .mpp.
- Importação de cronograma pela tela (XML do MS Project) para as próximas obras.
- Controle por WTG (plataforma, estacas, bloco, graute) como visão própria, cruzando atividades com o código `GS_xx`.

---

## Relacionado

- [[Projetos/BUILDLy Premium]]
- [[Decisões/2026-09-19 Migração para Supabase multi-obra]]
