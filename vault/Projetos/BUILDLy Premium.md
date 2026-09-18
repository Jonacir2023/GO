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
      para cada apontador. **Atenção ao pedir a troca:** os dois endereços moram na mesma origem
      (`jonacir2023.github.io`) e compartilham `localStorage`. A migração do histórico
      (`data` → `data#apontador`) é **porta de mão única** — depois de abrir o Buildly3 num
      aparelho, o `buildly2` não enxerga mais os RDOs daquele aparelho (procura por
      `history[data]`). Nada se perde, mas não dá pra ir e voltar.
- [ ] **Confirmar em aparelho real após a troca:** RDOs antigos aparecem no calendário
      (`migrarHistoricoParaMultiRdo()` já é automática e idempotente, mas nunca foi vista rodar
      num celular de verdade) — mesmo item da lista abaixo.

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

- [ ] **Migrar para Supabase?** `/app-supabase/` no mesmo repositório é uma geração paralela do
      mesmo sistema (só o módulo "Gestão de Equipes" completo). Vale considerar se aparecer
      necessidade real de gerenciar várias obras ao mesmo tempo — Sheets não escala bem para
      multi-tenancy. Ver `MANIFEST.md` na raiz.

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
