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

## RDO — decisão de arquitetura diferente dos outros módulos

Os outros 8 módulos ganharam tabelas relacionais (uma linha por assunto, por nota fiscal,
por documento). O RDO **não** — e a decisão foi deliberada, não preguiça.

Antes de tocar em código, uma sessão de pesquisa (agente `Explore`) mapeou os ~9600 linhas
de `rdo.html`: 8 pontos de chamada ao Apps Script, o modelo de dados completo (`state` =
cadastro, `history` = dicionário de diários por `data#apontador`), e as 8 regras de negócio
já implementadas (baixa lógica, lixeira, um-RDO-por-apontador, sincronização sem
sobrescrever, autosave, backup, fotos, responsável obrigatório). Achado central: **nada
disso depende do Apps Script especificamente** — depende só de "consigo mandar um retrato
JSON completo e buscar o mais recente de volta". O RDO já resolve conflito e mescla
sozinho, no cliente (`mesclarDaNuvem`, `aplicarRegraRdo`, `mesclarStatusCadastro` — tudo em
`rdo.html`, testado pelas 4 suítes `test_rdo_*`).

Reescrever isso como CRUD por linha (uma tabela `colaboradores`, outra `diarios`, etc., como
os outros módulos) significaria jogar fora uma lógica testada e correta só para caber num
molde relacional que o próprio módulo não precisa. Decisão: **uma tabela `rdo_snapshot`,
uma linha só (`id=1`) por obra**, com `state jsonb`, `history jsonb`, `chaves_dia jsonb`,
`atualizado_em`, `atualizado_por` — espelha exatamente o payload que `backupNuvem()` já
montava para o Apps Script. As tabelas antigas (`colaboradores`, `equipamentos_cadastro`,
`diarios`, `diario_backups`), desenhadas antes de ler o código real, foram descartadas —
não correspondiam ao modelo de verdade (colaboradores vivem agrupados em categorias com
baixa lógica própria; o diário tem dezenas de subcampos aninhados).

Único ponto que mudou de verdade: **fotos**. Antes, cada foto ia para o Google Drive via
Apps Script e o diário guardava só `{fileId, url}`; agora, comprimidas (1280px, JPEG 0.72,
mesmo código de sempre) e guardadas como `data:` URI **dentro do próprio diário**
(`fotos: [{dataUrl}]`) — mesmo padrão que assinaturas e logo já usavam. Justificativa dupla:
não existe "Google Drive" no Supabase (a alternativa real, Supabase Storage, é escopo novo
— bucket, políticas, upload), e ficar tudo num retrato só (sem link externo para outra
tabela/serviço) é exatamente o espírito da decisão acima. Efeito colateral positivo: a
etapa `prepararFotosParaCaptura()` — que baixava cada foto de volta em base64 pra poder
desenhar no PDF, por causa de CORS do Drive — virou trivial (a foto já É base64). Efeito
colateral a monitorar: um diário com as 20 fotos no limite pode passar de alguns MB de
JSON — aceitável para Postgres, mas é tráfego de rede maior a cada autosave/sincronização
do que antes.

Retirado (não portado): `salvarDiarioGoogle`/`buildPayloadGoogle` — mandavam uma cópia
"achatada" do diário como linha de planilha legível. Como o retrato no Supabase JÁ é o
diário completo, essa segunda cópia perdeu função.

## Achado à parte, não coberto pelas 8 tarefas: o robô de IA vai ficar desatualizado

`buildly-completo.html` tem um recurso de pergunta-e-resposta ("🤖") que manda a pergunta
para o Apps Script (`path=ia&action=perguntar`), que por sua vez lê a planilha (Diário,
Pauta, Check-in, Notas Fiscais) para montar o contexto da resposta — mecanismo server-side
que não foi tocado nesta migração (é um recurso de IA, não um CRUD de módulo, e está fora
do que as 8 tarefas cobriram). Como nenhum módulo grava mais na planilha, esse contexto vai
ficar congelado no que existia antes desta migração — o robô vai responder com dados cada
vez mais velhos, sem erro nenhum aparente. Não corrigido aqui porque a lógica de resposta
mora inteira no Apps Script (bloqueado nesta sessão pelo proxy de rede, ver regra 25) e
provavelmente usa uma chave de API própria — refazer isso é decisão do usuário: manter o
Apps Script vivo só para esse recurso (lendo do Supabase por baixo, reescrevendo a leitura),
migrar para uma Edge Function do Supabase, ou aposentar o recurso.

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
