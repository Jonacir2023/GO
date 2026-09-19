---
criado: 2026-08-21
tags: [nota, backend, apps-script, api]
---

# Contrato do Backend (Google Apps Script)

Um único web app (`/exec`) atende todos os módulos. Planilha
`19SDuzU_CLzDRfbNZWJZQzchLDCeQYHgiSC_FxDSdhOw` ("Buildly3").

Código-fonte: `apps-script/BuildlyBackend.gs` na raiz do repositório (entra junto com o PR #1 —
ver [[Decisões/2026-08-21 Backend recuperado da Lixeira]]).

> **Este arquivo `.gs` não é implantado por git.** O que roda em produção é o que está colado
> dentro do projeto Apps Script no Google. O arquivo no repositório é cópia de referência e
> pode divergir do que está no ar — sempre confirme antes de assumir comportamento.

---

## Código de acesso

Toda chamada precisa levar `token=<código>` (query string ou corpo JSON). O backend compara com
a propriedade `APP_TOKEN` do script; sem bater, devolve `{ok:false, codigo:'token_invalido'}` e
não executa nada.

**A checagem é opcional de propósito:** enquanto `APP_TOKEN` não existir nas Propriedades do
script, tudo passa como antes. Isso existe para permitir implantar sem janela de app quebrado —
não é descuido. Ver [[Decisões/2026-08-21 Código de acesso ao backend]].

No front-end o token é injetado por um shim sobre `fetch()`, então não é preciso lembrar dele ao
escrever chamada nova nos arquivos que já o têm (`pauta`, `Check-in`, `rdo`,
`buildly-completo`). **`custos.html` ainda não tem o shim** — ao ligar `custos/salvar`, leve-o
junto.

---

## Roteamento

`path` e `action` podem vir na query string **ou** dentro do corpo JSON do POST — o
`buildly-completo.html` manda no corpo e o `rdo.html` manda na query. As duas formas são
aceitas de propósito; sem isso, metade das chamadas caía em "Endpoint não encontrado" e o dado
se perdia em silêncio.

### GET

| path | action | Parâmetros | Devolve |
|---|---|---|---|
| `pauta` | `listar` | — | `{ok, status:'ok', pautas:[…], dados:[…]}` (mesma lista nas duas chaves) |
| `checkin` | `historico` | — | `{ok, status:'ok', checkins:[…], dados:[…]}` |
| `diario` | `carregar` | `data=YYYY-MM-DD` | `{ok, diario}` |
| `diario` | `lista-mes` | `mes=YYYY-MM` | `{ok, mes, diarios:[…]}` |
| `diario` | `salvar` | `dados=<json>` | igual ao POST (variante por GET) |
| `pauta`/`checkin`/`diario` | `limpar-duplicatas` | — | `{ok, removidas, msg}` |
| `backup` | `buscar-ultimo` | `obra=<nome>` | `{ok, conteudo, data, arquivo}` |

Sem rota correspondente, o GET devolve `{ok:true, msg:'API Diário de Obras ativa'}` — serve
como teste rápido de "o script está no ar?".

### POST

| path | action | Observação |
|---|---|---|
| `pauta` | `criar` | Upsert por ID |
| `pauta` | `atualizar-status` | |
| `pauta` | `remover` | Apaga a linha de verdade |
| `checkin` | `salvar` | Aceita assunto avulso ou reunião com lista (grava 1 linha por assunto) |
| `checkin` | `remover` | |
| `diario` | `salvar` | Upsert por Data + Apontador |
| `custos` | `salvar` | Nota em "Notas Fiscais" + itens em "Itens NF" |
| `ia` | `perguntar` | `{ok, resposta}` |
| `foto` | *(sem action)* | `{fileId, url}` |
| `backup` | *(sem action)* | `{ok, arquivo}` |

`foto` e `backup` mandam só `path` dentro do corpo, sem `action` — não é descuido, é como o
`rdo.html` chama.

---

## Por que as respostas têm campos repetidos

Vários retornos trazem `ok` **e** `status:'ok'`, ou a mesma lista em `pautas` e `dados`. É
proposital: partes diferentes do front-end checam campos diferentes (o `rdo.html` olha `ok`, o
`buildly-completo.html` olha `status`). Ao mexer, mantenha os dois — tirar um quebra um dos
lados em silêncio. O status do registro em si vai em `statusRegistro`, justamente para não
colidir com o `status:'ok'` do envelope.

---

## Abas e colunas

Abas: `Pauta`, `CheckIn`, `Diário`, `Notas Fiscais`, `Itens NF`.

`getSheet()` acha a aba ignorando maiúscula, acento, hífen, espaço e plural — então `'Pauta'`
encontra "Pautas" e `'CheckIn'` encontra "Check-ins". Não é preciso renomear aba na planilha
para bater com o código.

Nas abas de NF e Check-in, os campos são casados **pelo nome do cabeçalho** existente
(`appendPorCabecalho` / `upsertPorCabecalho`), então a ordem das colunas na planilha pode ser
qualquer uma. Já a aba `Diário` grava **por posição**, nas 25 colunas fixas de `COLUNAS_DIARIO`
(A Data … Y RDO Nº).

> Cuidado: o comentário acima de `COLUNAS_DIARIO` no código diz "24 colunas", mas o array tem
> 25. O comentário é que está desatualizado — confira o array, não o comentário.

---

## Upsert em toda escrita

- **Pauta / Check-in:** por ID, usando o ID que o app gerou localmente (`Date.now()`), não um
  gerado no servidor. Sem isso, apagar localmente nunca correspondia à linha real na planilha,
  que reaparecia como item "novo" na sincronização seguinte.
- **Diário:** por Data + Apontador, com data e apontador normalizados (a célula pode vir como
  tipo `Date` ou como texto).
- Motivo geral: o shell sincroniza de 2 em 2 minutos. Sem upsert, cada ciclo criaria uma linha
  nova e os assuntos se multiplicariam sem parar.

`limparDuplicatasPauta/Checkin/Diario()` existem para limpar linhas duplicadas de antes da
correção — rodar uma vez, manualmente, se aparecerem.

---

## Mapeamento de status

O app usa código minúsculo; a planilha guarda o rótulo legível.

| Código (app) | Rótulo (planilha) |
|---|---|
| `afazer` | Aberta |
| `fazendo` | Em Andamento |
| `concluido` | Concluído |
| `cancelado` | Cancelado |

`rotularStatus()` converte um no outro; `codigoStatus()` faz o caminho inverso e aceita as duas
formas, porque há linhas antigas gravadas em minúsculo.

---

## Google Drive

| Uso | Caminho |
|---|---|
| Fotos do RDO | `Diario de Obras - Fotos / [Obra] / [Data]` |
| Backups do RDO | `Diario de Obras - Backups / [Obra]` — mantém os **30 mais recentes**, o resto vai para a lixeira |

Fotos são compartilhadas como `ANYONE_WITH_LINK` / `VIEW` e devolvem `fileId` + URL de
visualização.

---

## Robô de IA (`ia/perguntar`)

- Modelo: `claude-haiku-4-5-20251001` (constante `MODELO_IA_PERGUNTAS`).
- Chave: `ANTHROPIC_API_KEY` em Configurações do projeto → **Propriedades do script**. Nunca no
  código. Sem ela, o endpoint responde com aviso amigável em vez de erro.
- Contexto recortado em **3 meses** (`MESES_CONTEXTO_IA`) para Diário e Notas Fiscais — o
  contexto inteiro viaja dentro do prompt a cada pergunta, e essas abas crescem todo dia. Pauta
  e Check-in vão inteiras (uma pendência antiga continua valendo hoje).
- `periodo_coberto` vai junto no JSON para o modelo dizer "está fora do período carregado" em
  vez de afirmar que não aconteceu.
- Medições, Documentos e Mural **não têm aba na planilha** — só existem no navegador. Por isso
  viajam junto da pergunta, no campo `contextoLocal` (montado por `montarContextoLocal()` no
  shell).

### Autorização do escopo de rede

O Apps Script só descobre que precisa de `script.external_request` quando algum código tenta
usar `UrlFetchApp`. Declarar no `appsscript.json` não basta se a autorização já tiver sido
concedida antes com um conjunto menor de escopos. Por isso existe `autorizarChamadaExterna()`:
rodar essa função uma vez no editor força o pedido de permissão.

---

## Endpoint que o front-end chama e o backend não tem

`rdo.html` tenta `GET ?path=foto&action=base64&fileId=…` como primeira via para exibir foto sem
depender de CORS do Google. **Esse endpoint não existe no backend.** Não é bug: o próprio
`rdo.html` trata como opcional e cai nas vias seguintes (busca direta e outras). Se um dia a
exibição de fotos ficar lenta ou falhar, implementar esse endpoint é a solução mais limpa.

Lição geral: **não presuma que todo `fetch()` do front-end tem endpoint do outro lado, nem que
todo endpoint é usado.** `custos/salvar` é o caso inverso — existe no backend e nenhum
front-end chama.

---

## Um front-end pode chamar dois endpoints na mesma gravação

`envio-pauta.html` (link público enviado a um líder, sem o resto do app) grava o mesmo assunto
em `pauta/criar` **e** `checkin/salvar` na mesma submissão, em paralelo. Não é redundância: o
líder pode estar num aparelho que nunca abriu o app, então a sincronização local
Pauta→Check-in (que só roda dentro do mesmo navegador, via `localStorage`) não tem como
alcançá-lo. Gravar direto nos dois evita depender de alguém abrir o app antes da próxima
reunião.

## Relacionado

- [[Projetos/BUILDLy Premium]]
- [[Decisões/2026-08-21 Backend recuperado da Lixeira]]
- [[Notas/Regras Operacionais Críticas]]
