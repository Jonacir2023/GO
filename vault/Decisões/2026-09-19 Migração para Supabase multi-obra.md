---
criado: 2026-09-19
tags: [decisão, backend, supabase]
---

# 2026-09-19 — Migração para Supabase multi-obra

## Pedido

"Preciso que a aba Obras crie mais que uma obra. E para cada obra um pacote de dados
totalmente independente." Confirmado: 4 obras seriam necessárias. Perguntado se o backend
continuava Google Sheets — resposta: **"Então muda para o Supabase"**.

## Decisão

- Backend deixa de ser um único Google Sheets/Apps Script compartilhado por toda a equipe e
  passa a ser **um projeto Supabase por obra** — banco Postgres totalmente separado, não uma
  tabela com coluna `obra_id`. "Pacote de dados totalmente independente" é levado ao pé da
  letra: nada de Pauta, Check-in, RDO, Custos etc. é compartilhado entre obras.
- RLS ligado em toda tabela, com política `for all using (true)` — mantém a postura de
  segurança atual (código de acesso opcional, sem login de usuário), não inventa autenticação
  nova fora do escopo pedido.
- Duas obras já provisionadas (chegar a 4 exige novo projeto Supabase por obra — plano grátis
  permite 2 simultâneos; as 2 obras anteriores do usuário nesta conta ["P3", "gerenciamento"]
  foram **pausadas**, não apagadas, para abrir espaço):

  | Obra | Projeto Supabase | URL |
  |---|---|---|
  | Obra 1 | `ivssgstckfcuiyetxdze` | https://ivssgstckfcuiyetxdze.supabase.co |
  | Obra 2 | `lwjbuzubnxnzkofcrhah` | https://lwjbuzubnxnzkofcrhah.supabase.co |

- Front-end: `supabase-config.js` (novo, na raiz, incluído via `<script>` nos 11 HTML raiz)
  expõe `window.B3Obras` — registro fixo das obras (id/nome/url/chave publicável), obra ativa
  em `localStorage['buildly3::obra_atual_id']`, fábrica de cliente `supabase-js` por obra, e
  `obraCompartilhada()`/`configCarregar()`/`configSalvar()` para o cadastro da obra
  (`obra_config`) — substitui `localStorage['b3_obra']` nos 7 arquivos que liam de lá.
- Aba Obras (`buildly-completo.html`) ganhou um seletor "Obra ativa"; trocar de obra troca de
  banco inteiro. A seção antiga "Remover dados de outra obra" (gambiarra para várias obras
  dividindo o mesmo navegador via `diario_obras_v4_state_<slug>`) foi removida — o problema que
  ela contornava não existe mais, porque agora cada obra tem banco próprio de verdade.

## Estado em 19/09

Feito: infraestrutura (schema de 19 tabelas + RLS aplicado nos dois projetos), registro
compartilhado de obras/cliente, aba Obras reescrita ponta a ponta contra `obra_config`.

Pendente (rastreado como tarefas #3–#8 na sessão): migrar Pauta, Check-in, RDO, Custos,
Medições, Documentos, Manutenção e Reunião do Apps Script/localStorage para as tabelas já
criadas em cada projeto Supabase; depois disso, atualizar
[[Notas/Contrato do Backend]] e [[Notas/Arquitetura do App]] (hoje ainda descrevem o Sheets).
Até lá o Apps Script permanece ativo para os módulos ainda não migrados.

## Limite de teste descoberto

Este ambiente (sessão web do Claude Code) sai para a internet por um proxy com lista de
permissão — `cdn.jsdelivr.net` (CDN do `supabase-js`) e `*.supabase.co` **não estão liberados**
daqui (confirmado: `curl` para a REST API do projeto retornou `403` no `CONNECT` do proxy).
Ou seja: não dá para abrir o app num Chromium headless desta sessão e ver a chamada ao
Supabase completar — nem o script do CDN carrega. Isso é uma política do ambiente de teste,
não do GitHub Pages real (lá o navegador do usuário sai sem essa restrição). Consequência
prática: a verificação aqui usa `execute_sql` do Supabase (via MCP, canal diferente do
navegador) para inspecionar linha por linha o que cada módulo deveria gravar — mas o
percurso completo "clique no botão → grava no Supabase → aparece na tela" só pode ser
confirmado de fato pelo usuário, no app publicado. Ver regra 25 em
[[Notas/Regras Operacionais Críticas]].
