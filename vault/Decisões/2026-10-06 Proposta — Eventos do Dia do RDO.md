---
criado: 2026-10-06
tags: [decisao, proposta, rdo, eventos]
status: aguardando aprovação do usuário (nada implementado)
---

# Proposta — Eventos do Dia do RDO (equipe, evento, descrição, responsável)

**Origem (06/10/2026):** com a aba **Entradas** cuidando de toda carga de material, o campo "Transporte de
material" (placa, volume, peso), o Fornecedor e o Valor da carga saem dos Eventos do Dia. O evento passa a
registrar as **interfaces com equipes**: visita/liberação/paralisação/marcação feitas pela Fiscalização
(Civil, Segurança do Trabalho, Meio Ambiente, Topografia) ou por equipes Cesbe (Energia, Civil, Topografia,
Segurança do Trabalho, Meio Ambiente, Laboratório). Mockup publicado como artefato (3 telas + planilha).

## Registro de cada evento
Hora · **Equipe causadora** (grupo + equipe) · **Evento** (Liberação de trabalho/base/terreno/acesso,
Paralisação de trabalho, Marcação de base/acesso… + sugestões: Retomada, Visita/vistoria, Ensaio/coleta,
Não conformidade) · Descrição · **Responsável** (quem da equipe liberou/parou/marcou). Entram sozinhos:
data, apontador, local da obra do dia. Vários eventos do mesmo tipo no dia, de equipes diferentes.

## Planilha
Uma linha por evento, ordem cronológica: Data · Hora · Equipe · Evento · Descrição · Responsável · Local.
No Resumo do RDO (hoje/semana/mês/data), no PDF, no WhatsApp e em .csv; resumo por equipe × tipo.

## Sem banco novo
Os eventos ficam em `currentDay.eventosDia` dentro do snapshot do RDO (`rdo_snapshot`); campos novos
`grupo`, `equipe`, `responsavel`; `tipo` continua sendo o nome do evento e `detalhe` a descrição. Sem SQL, então
a regra das duas obras não pede migração. RDO antigo continua imprimindo (Equipe em branco; placa/volume/valor
guardados, fora da tela).

## A decidir (recomendação entre parênteses)
1 Responsável = pessoa da equipe (sim) · 2 uma equipe por registro (sim) · 3 paralisação×retomada só
registrar na v1 · 4 Eventos de Segurança e Meio Ambiente continuam separados · 5 RDO antigo intacto ·
6 Local = coluna automática · 7 sem foto na v1 · 8 sem mudança de banco.


## v2 (resposta do usuário, 06/10/2026) — mockup atualizado, aguardando ok final
- **Paralisação:** checkbox no evento; marcado, abre **data e hora de retomada** (pode ficar em branco = "em aberto").
  O evento "Paralisação de trabalho" já marca o checkbox. A planilha calcula o **tempo parado**.
- **Acidentes:** "Eventos de Segurança" → **Acidentes de Segurança do Trabalho**; "Eventos de Meio Ambiente" →
  **Acidentes de Meio Ambiente** (Diário, Cadastro, PDF, WhatsApp). Dados antigos não mudam.
- **Impressão:** eventos do dia em **planilha** + **resumo** + **fotos** (leitura de "imagem": até 3 fotos por
  evento, a confirmar) no PDF, WhatsApp e Resumo; .csv com todas as colunas.
- **Local do evento** em cada evento (lista dos locais da obra, vem com o local do dia) e na planilha impressa.
- **Nada se perde:** fornecedor, valor, placa, volume e peso já lançados saem na Descrição como "Dados antigos: …";
  a sincronização não apaga campo algum.
- Assumidos (sem resposta): responsável = pessoa da equipe; uma equipe por registro; catálogo como proposto.
