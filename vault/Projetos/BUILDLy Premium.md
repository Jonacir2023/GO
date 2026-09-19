---
criado: 2026-08-21
status: ativo
área: Gestão de Obras
tags: [projeto, buildly, cesbe]
---

# BUILDLy Premium

**Status:** 🟢 Ativo — app pronto para a próxima obra (a anterior foi encerrada e os dados
zerados de propósito).
**Responsável:** Jonacir Cazelli · **Empresa:** Cesbe S.A.

Plataforma de gestão de obra. Páginas HTML/JS estáticas, sem build, publicadas no GitHub Pages,
com Google Sheets + Apps Script como backend.

---

## Endereços

| Item | Valor |
|---|---|
| App que a equipe usa hoje, na prática | https://jonacir2023.github.io/buildly2/buildly-completo.html — **outro repositório**, código antigo. Confirmado pelo usuário em 18/09. |
| Este repositório (Buildly3) | **publicado** em https://jonacir2023.github.io/GO/buildly-completo.html — Pages ligado. Falta só a equipe passar a abrir este endereço. |
| Repositório | `Jonacir2023/GO`, branch `main` |
| Pasta local (Mac) | `~/Buildly3` |
| Planilha | "Buildly3" — `19SDuzU_CLzDRfbNZWJZQzchLDCeQYHgiSC_FxDSdhOw` |
| Backend | Apps Script como web app (`/exec`) — ver [[Notas/Contrato do Backend]] |

Módulos: Pauta, Check-in, RDO, Custos, Reunião, Resumo do Tempo, Medições, Documentos,
Manutenção. Ver [[Notas/Arquitetura do App]].

---

## Como trabalhar neste projeto

- Português, sempre.
- Explicar **o que mudou e por quê** — não só entregar o arquivo.
- Testar antes de entregar.
- **Nunca perder informação já lançada.** Ver [[Notas/Regras Operacionais Críticas]].
- O usuário não faz push. Entrega é `.zip` com scripts Python numerados (idempotentes) que
  editam os HTML por trechos exatos, mais `LEIA-ME.txt` com um comando de uma linha.
- **Ferramenta de apoio, só duas: este cofre Obsidian e o `graphify`.** Nada de conectores
  (Notion, Drive, Slack e afins), mesmo quando aparecerem disponíveis na sessão — o projeto é
  fechado em si e a memória dele mora aqui.

---

## Histórico

### 19/09/2026 (4) — Início da migração para Supabase multi-obra

Pedido do usuário: aba Obras precisa criar mais de uma obra, cada uma com "pacote de dados
totalmente independente" — e, ao perguntar se o backend continuava Sheets, a resposta foi
"muda para o Supabase". Decisão completa em
[[Decisões/2026-09-19 Migração para Supabase multi-obra]]: **um projeto Supabase por obra**
(banco separado, não coluna `obra_id`), 2 obras provisionadas até agora (de 4 pedidas — plano
grátis permite 2 projetos simultâneos), schema de 19 tabelas espelhando todos os módulos
atuais, RLS aberto (mesma postura de segurança de hoje).

Feito nesta entrada: `supabase-config.js` (registro de obras + cliente + `obra_config`
compartilhado, substitui `localStorage['b3_obra']` nos 7 arquivos que liam de lá) e a aba
Obras reescrita para ler/gravar no Supabase da obra ativa, com seletor de obra. Testado: as 7
suítes + sintaxe + isolamento continuam verdes; Playwright confirma o seletor populado com as
2 obras e o formulário respondendo aos cliques — a gravação em si não pôde ser vista
completando nesta sessão (ambiente de teste não alcança `supabase.co`, ver regra 25 em
[[Notas/Regras Operacionais Críticas]]), mas o schema da tabela `obra_config` foi conferido
direto no Postgres via `execute_sql` e bate exatamente com o que o código grava.

Pendente: migrar Pauta, Check-in, RDO, Custos, Medições, Documentos, Manutenção e Reunião
(hoje ainda no Apps Script/Sheets ou só no navegador) — [[Notas/Contrato do Backend]] e
[[Notas/Arquitetura do App]] só serão atualizadas quando isso terminar, pra não descrever um
backend que só existe pela metade.

**Atualização, mesmo dia:** Pauta migrada (nativa + `pauta.html` + `envio-pauta.html`).
Precisou de duas correções de schema no caminho: `pauta_assuntos.id`/`checkin_assuntos.id`
de `uuid` para `text` (o front-end gera `Date.now().toString()`, não um UUID de verdade), e
`pauta_membros`/`pauta_setores` ganharam índice único em `nome` para dar de upsert. Restam
Check-in, RDO, Custos, Medições, Documentos, Manutenção e Reunião.

### 19/09/2026 (3) — Corrigida a regressão dos badges do @media print

Achado de 18/09 (badges/kanban do `@media print` com fundo escuro) corrigido. Só
`Check-in.html` tinha `@media print` de verdade — a nota de 18/09 estava errada ao citar
`pauta.html`/`custos.html`, que não têm nenhum. Três causas na mesma função
`prepararImpressao()`: cores do Modelo C nos badges/kanban em vez dos pasteis claros de
impressão; subtítulo e aviso de atrasado com cor de tela (branco/pêssego) sobre papel branco;
e `.card-title`/`.card-desc`/`.card-resp`/`.card-dates`/`.card-aging`/`.kol-title` (brancos de
propósito na tela, fundo escuro) sem override de impressão — `.card` também só tinha a borda
sobrescrita, não o fundo. Testado com Playwright (`emulate_media('print')`) chamando a função
com dados cobrindo os 4 status e um atrasado.

### 19/09/2026 (2) — Gerador de módulo (scaffold)

Pedido do usuário: um script que gere um módulo novo (levantamento/relatório) neste app,
"separado para usarmos no próximo app" — ou seja, reaproveitável fora do BUILDLy.

`scripts/gerador_modulo/novo_modulo.py` carimba as peças que todo módulo daqui precisa: HTML
isolado (espaço próprio de `localStorage`, shim do código de acesso, formulário + lista +
sincronização com o backend), endpoint de backend (upsert por ID, inserido direto em
`BuildlyBackend.gs` quando os marcadores de rota batem, com fallback de snippet manual), e
teste automatizado (criar → alternar status → remover, sem erro de JS).

Desenho: a lógica do script (`novo_modulo.py`) não conhece nada do BUILDLy além de "renderizar
um template e escrever arquivo" — toda a parte específica (paleta, contrato de backend, bloco
de isolamento) mora em `templates/*.tpl`. Reaproveitar num projeto futuro é copiar a pasta
inteira e trocar o conteúdo dos templates, sem mexer no script. Documentado em
`scripts/gerador_modulo/LEIA-ME.md`.

Bug achado e corrigido durante o teste: a função gerada `atualizarStatus<Modulo>` usava
`upsertPorCabecalho` (a mesma do `criar<Modulo>`) — como esse upsert escreve a linha inteira e
preenche com `''` qualquer coluna que não veio no payload, uma atualização de status sozinha
apagaria Título/Descrição/Responsável. Corrigido para escrever só as duas células (Status,
Atualizado Em) por nome de cabeçalho, do jeito que `atualizarStatusPauta` já existente faz.

Testado de ponta a ponta em cópia isolada do repositório (nunca na cópia real): gerados dois
módulos (`vistoria`, `relatorio-obra` — id simples e composto), os três verificadores
(sintaxe/isolamento/suítes) e o teste do próprio módulo gerado passando; rodado uma segunda vez
para confirmar que não duplica nada (idempotente).

### 19/09/2026 — Largura no iPhone (3 correções) + link público de envio de assunto

Três correções de layout mobile, cada uma achada por screenshot do usuário no iPhone real e
confirmada por medição via Playwright (390px) antes/depois:
- Pauta e Check-in aninhavam `.page` dentro de `.page` (a aba inteira e cada sub-tela dela usam
  a mesma classe) — o padding lateral de 16px contava duas vezes, deixando os campos ~32px mais
  estreitos que os da aba RDO (que roda isolada em iframe, sem esse aninhamento).
- `<input type="date">` vazio tem largura mínima maior no iOS que um já preenchido — a coluna
  `1fr` de `.frow-2`/`.frow-3` não encolhia abaixo disso, e o campo vazio (ex.: Data de Término)
  estourava a coluna. Corrigido com `min-width:0` nos itens do grid e nos campos.
- `.btn` sem `-webkit-appearance:none`/`box-sizing` explícito ficava sujeito ao controle nativo
  do botão no iOS, que pode não respeitar `width:100%` do `.btn-full` com a mesma consistência do
  Chromium — o botão ATUALIZAR do Check-in aparecia mais estreito que a fileira de campos ao
  lado, embora ambos sejam irmãos diretos do mesmo `.sec`.

Depois, nova página: `envio-pauta.html` — formulário público, sem o resto do app, para um líder
preencher um assunto (mesmos campos do "Novo Assunto" da Pauta) e enviar direto para a planilha,
via link (`?lider=Nome` pré-preenche o campo; `&token=` se o backend tiver código de acesso
ativado). Grava ao mesmo tempo em `pauta/criar` e `checkin/salvar` — não depende da sincronização
local Pauta→Check-in (que só roda no mesmo navegador) nem de alguém abrir o app antes da próxima
reunião para o assunto aparecer no Check-in. Sem `localStorage` — o líder abre num aparelho que
nunca teve o app instalado.

Testado: as 7 suítes, sintaxe e isolamento; verificação visual (Playwright, 390px) da nova
página, incluindo o preenchimento do nome via `?lider=`.

Fechando o fluxo: bloco "Convidar Líder" na aba Check-in — nome opcional + botão que monta o
link de `envio-pauta.html` (com `?lider=` se preenchido) e abre `wa.me/?text=`. Sem telefone
fixo: `wa.me` sem número abre o seletor de contato do WhatsApp, então o gestor manda um líder de
cada vez escolhendo o contato na hora do envio.

### 18/09/2026 — Modelo C: tema escuro em todo o app

Redesign visual completo, pedido pelo usuário. Processo: piloto de paleta azul/cinza corporativo
claro (rejeitado), três protótipos de UI num canvas de design (Modelo A verde/lista, Modelo B
azul/painel com gaveta de índice, Modelo C recolorido a partir de uma referência visual anexada
pelo usuário — fundo azul-acinzentado `#4a5162`, acento pêssego `#dda583`, secundário
verde-petróleo `#89ab9d`). Modelo C escolhido; aplicado primeiro como piloto em
`buildly-completo.html`, depois nos 10 arquivos HTML restantes da raiz.

Vira tema **escuro** de verdade, não troca de acento: os dois sistemas de tokens do app
(`buildly-completo`/`pauta`/`Check-in`/`custos` de um lado; `rdo`/`medicoes`/`documentos`/
`manutencao`/`resumo-tempo`/`reuniao` — "Paleta Concreto Rústico" — do outro) tinham fundo claro
com cards brancos; ambos teriam texto invisível ou superfícies berrantes se só o `--accent`
trocasse.

Bugs sistêmicos achados no processo (repetidos em vários arquivos por herdarem o mesmo
boilerplate — cada um corrigido uma vez e replicado):
- Duas variáveis (`--bg-dark` usada como cor de **texto** em `.sec-title`/`.modal-title`; `--ink`
  usada como **fundo** em `.btn-secondary`/`.toast`) só funcionavam porque, no tema claro, uma
  delas por acaso tinha o valor "certo" pro papel errado. Ao virar escuras as duas, o texto some.
- `#f0ece7`/`#ffffff` usados sem passar pela variável de card ora eram fundo de superfície, ora
  cor de texto claro sobre cabeçalho escuro — o mesmo hex, dois papéis. Precisou checar
  `background:` vs `color:` em cada ocorrência, não só trocar o valor.
- `<button>` de aba em `custos.html` sem `background` explícito herdava o branco nativo do
  navegador — invisível no tema claro original, virou barra branca berrante no escuro.
  `rgba(255,255,255,0.5)`/`0.7`/`0.95` (efeito "vidro sobre concreto claro") e um
  `inset 0 1px 0 rgba(255,255,255,0.6)` (brilho "concreto polido") tinham o mesmo problema: opacidade
  pensada pra um fundo claro vira uma mancha/linha branca sobre fundo escuro.

Preservado deliberadamente **sem** conversão: toda simulação de papel impresso/PDF (`@media
print`, a seção CSS "PDF do RDO" de ~140 linhas nos 6 arquivos da paleta Concreto Rústico, e o
HTML de relatório gerado via JS) — página impressa continua clara, papel branco, textos legíveis
com tinta escura, como sempre foi.

Testado a cada arquivo: as 7 suítes de domínio, sintaxe e isolamento; verificação visual real
(Playwright, 390px e 1440px) em pelo menos uma tela por arquivo, screenshots enviados ao usuário
antes de cada rodada. Pendente, fora do escopo desta rodada: layout desktop estrutural (hoje é o
mobile esticado num container mais largo, não um painel nativo de tela cheia).

### 26/08/2026 — A lixeira do cadastro de colaboradores não removia ninguém

Primeira regressão vinda da leva de 25/08, relatada pelo usuário no mesmo dia em que o código
estava no ar. Quando o Cadastro passou a dar baixa em vez de apagar, todas as listas ganharam o
filtro de vigência — menos a de colaboradores. O 🗑️ dava a baixa, salvava, avisava "Removido" e
redesenhava a linha igual.

Corrigido em duas frentes, porque eram dois caminhos para a mesma sensação: a lista passou pelo
filtro (e ganhou o bloco de removidos, com restaurar), e a baixa passou a desmarcar o item do dia
aberto — sem isso, quem estava marcado como presente hoje continuava na tela por causa da regra
do `usado`. Ver [[Decisões/2026-08-25 Baixa lógica no cadastro do RDO]].

A lição vale além do RDO e virou regra: **ação sem efeito visível é indistinguível de botão
quebrado.** Quando o efeito é correto mas invisível naquele contexto — dar baixa enquanto se
edita um dia passado —, o app tem que dizer o porquê.

### 25/08/2026 — RDO reescrito para dois apontadores (8 correções)

A maior mudança desde a criação do cofre. Oito correções pedidas para o RDO, todas em `main`
(PRs #7 e #8, mesclados) — e portanto **no ar para a equipe**. O `rdo.html` foi de ~6.900 para
~7.500 linhas.

Quatro delas são estruturais e cada uma virou decisão própria:

- **Um RDO por apontador no mesmo dia** — a chave do histórico virou `data#apontador`. Antes, o
  segundo apontador a salvar apagava o RDO do primeiro. Ver
  [[Decisões/2026-08-25 Um RDO por apontador no mesmo dia]].
- **Cadastro dá baixa, não apaga** — item removido continua existindo nos dias anteriores à
  baixa. Ver [[Decisões/2026-08-25 Baixa lógica no cadastro do RDO]].
- **Sincronização entre aparelhos a cada 3 minutos**, com política de conflito que nunca
  sobrescreve às cegas. Ver [[Decisões/2026-08-25 Sincronização entre aparelhos]].
- **Responsável obrigatório** para gravar — inclusive no salvamento automático, que era
  justamente o que criava RDO anônimo.

As outras quatro são de qualidade do documento: local da obra virou lista fechada de 13 opções,
a atividade passou a sair com os dois locais, a legenda da foto virou função única
(`Foto 3 - Concretagem`, igual na tela, no PDF, no WhatsApp e na planilha), e a numeração dupla
do PDF sumiu. Tudo reunido em [[Notas/RDO — Regras do Módulo]].

**O que isso significa para a equipe agora:** ao abrir o RDO, cada celular roda
`migrarHistoricoParaMultiRdo()` sozinho e reindexa o histórico local. É idempotente e foi
testada, mas é transformação de dado real — se algum apontador relatar "sumiu RDO", a primeira
coisa a olhar é essa chave, não a planilha (que não foi tocada).

Nenhum teste tocou o Google: tudo foi validado em navegador headless, com `page.route()`
interceptando `script.google.com`. A sincronização, em particular, **só se prova com dois
celulares reais**.

### 24/08/2026 — Os 5 PRs mesclados; o app mudou, o backend não

Todos os PRs abertos em 21/08 entraram em `main` (`6f159c6`), sem conflito. O `main` mesclado
foi validado por inteiro — não só as branches separadas: sintaxe dos 5 HTMLs, os 11 casos do
backend, os 8 do código de acesso e um teste visual confirmando que robô flutuante, foto da NF
e código de acesso convivem no mesmo `buildly-completo.html`, que era o arquivo tocado por dois
PRs diferentes.

Duas consequências que valem lembrar em qualquer merge futuro:

- **Mesclar publica o app, mas não implanta o backend.** `main` é o que o GitHub Pages serve, então
  as mudanças de HTML ficaram no ar na hora. O `.gs` não: git não implanta Apps Script, e o que
  roda continua sendo o que está colado no editor do Google.
- **A caixa do código de acesso apareceu para a equipe** antes de existir código combinado.
  Inofensiva por desenho (sem `APP_TOKEN`, cancelar ou digitar qualquer coisa segue funcionando —
  caminho testado), mas é uma mudança visível que a equipe vê sem aviso. Numa próxima, combinar o
  código antes de mesclar.

### 21/08/2026 — Retomada: backend recuperado, 3 PRs abertos

Sessão de retomada depois da limpeza da obra encerrada.

- **Backend apagado e recuperado.** O projeto Apps Script tinha sumido junto com a limpeza.
  Reconstruí uma versão parcial a partir do front-end (428 linhas); o usuário achou o original
  na Lixeira do Drive (1100+ linhas) e ele prevaleceu. Ver
  [[Decisões/2026-08-21 Backend recuperado da Lixeira]]. → **PR #1**
- **Nota fiscal: decidido usar a câmera do iPhone**, guardando a foto junto do cabeçalho e dos
  itens. OCR adiado. Ver [[Decisões/2026-08-21 Escaneamento de nota fiscal]]. → **PR #2**
- **Robô de IA passou a aparecer em todas as abas**, como botão flutuante. Ver
  [[Decisões/2026-08-21 Robô de IA visível em todas as abas]]. → **PR #3**
- **Este cofre Obsidian foi criado**, para que a próxima sessão não precise redescobrir nada
  disso. Ver [[Notas/Como manter este cofre]]. → **PR #4**
- **Backend passou a exigir código de acesso.** Avaliando o app contra a checklist de produção
  de IA ([[Notas/Maturidade de Produção]]), apareceu uma lacuna real: a URL `/exec` está no HTML
  publicado, em repositório público, e o web app aceitava qualquer um — dava para ler e alterar
  a planilha da obra e gastar a chave da Anthropic. Ver
  [[Decisões/2026-08-21 Código de acesso ao backend]]. → **PR #5**

Nada foi testado contra o Google nem em celular real — o ambiente do Claude não alcança
`script.google.com`, e os testes de interface foram em navegador headless.

---

## Fila de desenvolvimento

### 02/09 — Escopo fixado pelo usuário

Estado dos endereços, verificado no iPhone:

| Endereço | Estado |
|---|---|
| `…github.io/Buildly3/…` | **no ar** — o Pages foi ligado depois de 28/08, quando deu 404 |
| `…github.io/buildly2/…` | 404 — não existe repositório com esse nome |
| `…github.io/diario-obras/` | no ar, **de terceiro** |

**O `diario-obras` está fora do escopo, por decisão do usuário: "não mexer jamais".** Nem como
origem, nem como destino, nem como referência de código. Cheguei a lê-lo para saber o que
existia e escrevi aqui que a migração deveria partir dele — **estava errado, e a nota foi
corrigida.** O diário que vale é o deste repositório.

O que fica valendo:

| Papel | Quem |
|---|---|
| Especificação — *o que* a plataforma faz | **este repositório** e este cofre |
| Onde a plataforma nova é construída | repositório **`buildly`** |
| Banco | Supabase **P3** |
| Fora do escopo | `diario-obras`, `buildly2` |

### Publicação: Pages ligado, troca da equipe ainda pendente

Confirmado pelo usuário em 18/09: o GitHub Pages **já está ligado** neste repositório
(`jonacir2023.github.io/GO/…`). O que ainda não aconteceu é a equipe **de fato abrir** esse
endereço — no celular, hoje, quem aponta ainda usa `jonacir2023.github.io/buildly2/`. README.md
corrigido para apontar para o endereço certo (estava todo escrito como se este repositório fosse
o `buildly2`).

- [ ] **Comunicar a troca para a equipe.** Ação do usuário, não de código: passar o novo endereço
      para cada apontador. **Não é o caso de "mão única" que a nota chegou a dizer — corrigido em
      18/09, achado por review de PR.** O Buildly3 é isolado do `buildly2` em toda camada, por
      decisão de 26/08 ([[Decisões/2026-08-26 Isolamento definitivo entre projetos]]), travada por
      `scripts/verificar_isolamento.py`: código próprio, `localStorage` com prefixo `buildly3::`
      (testado em `tests/test_espaco_proprio.py`), e **`/exec` e planilha próprios — não os do
      `buildly2`**. Consequência real: **não há migração automática nenhuma** entre os dois. O
      app abre com histórico local vazio nesse aparelho. Hoje isso não é problema — a obra atual
      já está zerada de propósito (ver cabeçalho desta nota) — mas nunca prometa "nada se perde"
      à equipe: se algum dia houver RDO real só no `buildly2`, recuperar é exportação manual de
      lá, feita pelo usuário — este app não tem, e não deve ter, nenhum caminho automático até o
      backend de outro projeto.
- [ ] **Confirmar em aparelho real:** `migrarHistoricoParaMultiRdo()` — que converte o histórico
      **do próprio Buildly3** do formato antigo (por data) para o novo (`data#apontador`) — roda
      sozinha e é idempotente, mas nunca foi vista rodando num celular de verdade. Isto não tem
      relação com o `buildly2`; é só sobre o histórico que o próprio Buildly3 acumular daqui pra
      frente.

### Bloqueando tudo: implantar o Apps Script

- [ ] **Implantar `apps-script/BuildlyBackend.gs`** no editor do Google e trocar a URL `/exec`
      nos HTMLs. Passo a passo em `apps-script/README.md`. Enquanto isso não acontecer, nada do
      backend novo está no ar — nem o `custos/salvar`, nem o código de acesso, nem o robô com a
      `ANTHROPIC_API_KEY`. **É a pendência que destrava as outras.**
- [ ] **Ativar o código de acesso:** criar `APP_TOKEN` nas Propriedades do script. Até lá o app
      pede o código mas aceita qualquer coisa — o item 03 da
      [[Notas/Maturidade de Produção]] só conta como resolvido depois disso.

### Aguardando confirmação em aparelho real

Já estão no ar (mesclados em 24/08), mas nenhum foi visto num aparelho de verdade:

- [ ] **Foto da NF** — confirmar no iPhone que abre a câmera, não a galeria, e que a foto
      comprimida continua legível para reler a nota.
- [ ] **Robô flutuante** — no celular, incluindo Reunião, Resumo do Tempo, Medição, Documentos e
      Manutenção (não testadas individualmente), e em desktop ≥900px.
- [ ] **Caixa do código de acesso** — confirmar que aparece uma vez e que o app segue normal
      depois.
- [ ] **RDO com dois apontadores** — dois celulares, mesma obra, mesmo dia: os dois RDOs têm que
      coexistir e cada um enxergar o do outro depois da sincronização. **É o teste que fecha o
      item 1** — nada nele foi provado contra o Google.
- [ ] **Migração do histórico** — confirmar no celular de quem já tem RDO antigo que o calendário
      continua mostrando tudo depois da reindexação.
- [ ] **Baixa e restauração no cadastro** — dar baixa num veículo e conferir que o RDO de ontem
      continua listando ele.

### Em aberto

- [ ] **Rate limit no `ia/perguntar`.** O código de acesso protege o perímetro, mas quem o tiver
      chama à vontade — se vazar, a chave da Anthropic volta a ficar exposta. Teto diário por
      aparelho. Ver [[Notas/Maturidade de Produção]].
- [ ] **Memória multi-turno no robô.** Hoje cada pergunta é isolada; não dá para dizer "e no mês
      passado?" em seguida. Barato e o usuário sente.
- [ ] **Tools no robô.** Hoje ele responde mas não age — com tools, criaria pauta ou lançaria
      apontamento a partir da conversa.
- [ ] **Ligar Custos à planilha.** `custos/salvar` existe no backend; nenhum front-end chama.
      Hoje as notas fiscais vivem só no aparelho. **Levar o shim do código de acesso junto** —
      `custos.html` ainda não o tem.
- [ ] **OCR de nota fiscal** — depende de escolher API de visão. O robô já usa Anthropic, então
      pode ser o caminho natural.
- [ ] **Implementar `foto&action=base64`** no backend — o `rdo.html` já chama esse endpoint como
      primeira via de exibição de foto, e ele não existe. Não é urgente (há fallback), mas
      resolveria dependência de CORS do Google.

### Decisão futura, sem prazo

- [ ] **Migrar para Supabase?** Existe uma geração paralela do mesmo sistema em Supabase no
      repositório `Jonacir2023/buildly` (ex-`buidly`) — chegou a ter uma cópia em `/app-supabase/`
      neste repo, removida em 18/09 por misturar repositórios (só o módulo "Gestão de Equipes"
      completo lá). Vale considerar migrar se aparecer necessidade real de gerenciar várias obras
      ao mesmo tempo — Sheets não escala bem para multi-tenancy — mas como projeto próprio deste
      repositório, nunca como pasta importada de outro. Ver `MANIFEST.md` na raiz.

---

## Projeto fechado em si

O BUILDLy é autocontido: código, backend, planilha e documentação vivem neste repositório e mais
nada. **Toda** documentação do projeto vai para `vault/`, aqui — nunca para outro repositório,
outro cofre ou outra base de notas. Sem submodules, sem imports externos, sem deploy
compartilhado, sem notas cruzadas com outros projetos.

---

## Relacionado

- [[Início]]
- [[Notas/Arquitetura do App]]
- [[Notas/Contrato do Backend]]
- [[Notas/Armazenamento Local]]
- [[Notas/RDO — Regras do Módulo]]
- [[Notas/Regras Operacionais Críticas]]
- [[Decisões/Índice de Decisões]]
