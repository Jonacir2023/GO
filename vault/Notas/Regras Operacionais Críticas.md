---
criado: 2026-08-21
tags: [nota, regras, crítico]
---

# Regras Operacionais Críticas

Cada item aqui vem de um erro que já aconteceu de verdade e custou tempo ou dado. Não são
preferências de estilo.

---

## Dados do usuário

1. **Nunca recomendar limpar dados do site / Safari como solução de cache.** Isso apaga o
   `localStorage` inteiro — cadastro e histórico. Se o app não atualizar visualmente: fechar e
   reabrir, e aguardar a propagação do GitHub Pages (1–2 min).
   - O Pages manda `cache-control: max-age=600`: o Safari pode reaproveitar um `.html` por até
     **10 min** depois do deploy, e cada app em iframe (ex.: `rdo.html`) é um arquivo à parte — dá para
     ver a tela nova no shell e o RDO velho dentro dele. Foi o que fez o usuário achar, em 02/10/2026,
     que "não mudou nada" quando o PDF completo já tinha sido trocado (o layout antigo nem existia mais
     no repositório). Antes de investigar bug de "não mudou": conferir o run `pages build and deployment`
     do commit (`gh`/API de Actions) e se o layout antigo ainda existe no código (`grep`).
   - Sintoma típico de cache velho: a aba Gerar ainda mostra botões que já foram removidos.

2. **Nunca pedir para o usuário redigitar cadastro por causa de bug.** Se dados sumirem ou
   aparecerem misturados depois de uma atualização, a correção é restaurar do backup
   (nuvem ou arquivo) automaticamente — nunca mandar apagar colaborador por colaborador.

3. **Nunca inventar dado operacional** (efetivo, quantidade, atividade) em RDO. É documento
   contratual. Faltou dado, fica em branco ou marcado como pendente — nunca estimado, nunca
   inferido.

4. **Nunca deixar o app cair silenciosamente em estado vazio / obra sem nome.** `backupNuvem()`
   usa `state.obra.nome || 'Obra'` como nome de pasta no Drive: se o nome vier vazio, cria uma
   pasta nova a cada vez, e o backup se espalha em pastas duplicadas sem ninguém perceber. Nome
   vazio é sinal de perda de estado — deve alertar, não seguir em frente.

5. **Nunca apagar registro de cadastro que um documento antigo cita.** Remoção é baixa com
   data (`inativo` + `inativoEm`), e as listas filtram pelo dia que está sendo editado. Apagar de
   verdade reescreve o RDO de ontem por causa de um cadastro de hoje. Ver
   [[Decisões/2026-08-25 Baixa lógica no cadastro do RDO]].

6. **Nunca deixar duas pessoas competirem pela mesma chave.** O histórico do RDO era indexado só
   pela data: o segundo apontador a salvar substituía o primeiro, sem aviso. Onde duas pessoas podem
   escrever o mesmo registro, a chave precisa dizer quem escreveu. Ver
   [[Decisões/2026-08-25 Um RDO por apontador no mesmo dia]].

7. **Sincronizar nunca é copiar por cima.** Cadastro só ganha item novo (nunca perde), status de
   baixa vence pelo `statusEm` mais recente, diário vence pelo `atualizadoEm` mais recente, e seleção
   do dia que já existe no aparelho não é tocada. Ver
   [[Decisões/2026-08-25 Sincronização entre aparelhos]].

8. **Nunca gravar documento contratual sem responsável** — nem no salvamento automático. RDO
   anônimo não serve como documento, e o salvamento automático era justamente o que os criava.

9. **Toda ação do usuário precisa de efeito visível.** Baixa lógica sem filtro na tela é
   indistinguível de botão quebrado: a lista de colaboradores ficou meses assim. Se o efeito é
   correto mas invisível naquele contexto (dar baixa enquanto se edita um dia passado), o app
   diz o porquê — não fica calado.

10. **Cada app tem o seu espaço de armazenamento, e nunca lê o do outro.** Publicados na mesma
    origem, apps diferentes dividem o mesmo `localStorage` se usarem as mesmas chaves. O BUILDLy
    grava sob `buildly3::` e não olha para fora. Sem ponte, sem importação — são projetos
    diferentes. Ver [[Decisões/2026-08-26 Espaço próprio de armazenamento]].

11. **Projeto separado quer dizer backend separado.** Endereço próprio não isola nada: dois
    endereços apontando para o mesmo `/exec` são o mesmo sistema, e a mistura atravessa
    aparelhos. Antes de qualquer entrega, rode `python3 scripts/verificar_isolamento.py`. Ver
    [[Decisões/2026-08-26 Isolamento definitivo entre projetos]].

12. **Nunca limpar uma aba da planilha que já tem dados.** Um `clearContents()` incondicional em
    `salvarDiario()` já apagou histórico inteiro de RDO em produção. Cabeçalho só se cria quando
    a aba está genuinamente vazia (`getLastRow() === 0`).

---

## Publicação e teste

13. **Nunca afirmar que algo está publicado sem ter verificado.** Por vários dias eu disse que
    as mudanças estavam no ar; o GitHub Pages nunca tinha sido ligado neste repositório. A nota
    do cofre dizia "publicado" e eu a tratei como fato. Deste ambiente não se alcança o
    `github.io` — quando não dá para checar, a frase certa é "não consigo confirmar daqui".

14. **Integrações não funcionam em arquivo local.** Abrir o `.html` direto (`file://`) bloqueia
    POST — planilha, fotos e backup só funcionam no endereço publicado (GitHub Pages).

15. **Atualizar o Apps Script exige nova implantação.** Colar o código e salvar não põe nada no
    ar: Implantar → Gerenciar implantações → editar (lápis) → Nova versão → Implantar. Sem esse
    passo final, o `/exec` continua servindo a versão anterior.

16. **Scripts de entrega precisam ser idempotentes.** As mudanças chegam ao usuário como scripts
    Python que editam os HTML por trechos exatos. Rodar duas vezes não pode duplicar a alteração.

---

## Código

17. **O backend Apps Script não é versionado por git.** O que roda é o que está colado no projeto
    Google. Se for apagado, git não recupera — só a Lixeira do Drive (~30 dias). Ver
    [[Decisões/2026-08-21 Backend recuperado da Lixeira]].

18. **Não presumir simetria entre front-end e backend.** Existem `fetch()` sem endpoint
    correspondente (`foto&action=base64`) e endpoints que ninguém chama (`custos/salvar`).
    Reconstruir backend a partir do front-end perde tudo que nenhum `fetch()` exercita.

19. **Toda escrita no backend é upsert.** A sincronização automática de 2 em 2 minutos reenvia
    os mesmos registros; sem upsert, cada ciclo duplica linha.

20. **Elemento que precisa aparecer em toda aba tem que ser flutuante.** As 10 telas fora da
    Home têm cabeçalho próprio e não reservam espaço para o cabeçalho do shell. Ver
    [[Decisões/2026-08-21 Robô de IA visível em todas as abas]].

21. **Gravação que pode conter imagem precisa de `try/catch`.** Cota de `localStorage` estoura
    sem aviso e o registro se perde em silêncio. Ver [[Notas/Armazenamento Local]].

22. **Página estática em repositório público não guarda segredo nenhum.** Qualquer valor
    embutido no HTML é público por definição — inclusive a URL `/exec`. Todo segredo vem de
    fora: das Propriedades do script (servidor) ou digitado pelo usuário e guardado no aparelho.
    Ver [[Decisões/2026-08-21 Código de acesso ao backend]].

23. **Toda chamada nova ao backend precisa levar o código de acesso.** O shim sobre `fetch()`
    cobre isso sozinho nos arquivos onde já está (`pauta`, `Check-in`, `rdo`,
    `buildly-completo`) — mas `custos.html` ainda não o tem, porque hoje não chama o backend.
    Ao ligar `custos/salvar`, leve o shim junto.

24. **CSS de relatório impresso nunca usa nome de classe genérico sem escopar sob `.pdf-doc`.**
    A seção "PDF do RDO" (~140 linhas, copiada nos 6 arquivos da paleta Concreto Rústico)
    definia `.section-title`, `.stat-num`, `.stat-label`, `.badge` etc. sem prefixo — como o
    app usa esses mesmos nomes na tela, o CSS pensado pra papel branco (cinza-escuro sobre
    fundo claro) vazava por cima do CSS de tela (fundo escuro), deixando números como "0
    PRESENTES"/"0 TOTAL MM" praticamente invisíveis. Não apareceu em teste automatizado nem em
    Chromium — só em print visual real. Toda classe nova dentro dessa seção começa com
    `.pdf-doc `, sempre. Ver [[Projetos/BUILDLy Premium]], histórico de 19/09.

25. **Esta sessão não alcança `*.supabase.co` nem `cdn.jsdelivr.net`.** O proxy de saída do
    ambiente de teste usa lista de permissão, e nenhum dos dois está nela (`curl` para a REST
    API do Supabase devolve `403` no `CONNECT` — confirmado, não é bug do app). Isso significa
    que abrir o app num Chromium headless aqui não carrega nem o `supabase-js` do CDN, então o
    percurso completo (clique → grava no Supabase → aparece na tela) não dá pra ver rodar
    nesta sessão — só no app publicado, pelo usuário. O que dá pra verificar daqui é o dado em
    si, com `execute_sql` do MCP do Supabase (canal separado do navegador, não passa por esse
    proxy). Ver [[Decisões/2026-09-19 Migração para Supabase multi-obra]].

26. **Migrar um módulo não termina em código próprio — verifique quem mais lê a chave que
    ele escrevia.** Ao migrar a aba Obras para o Supabase, `b3_obra` parou de ser escrito —
    mas `rdo.html` também lia e escrevia essa chave por conta própria
    (`sincronizarObraCompartilhada()`, `salvarConfigObra()`, `uploadLogo()`), sem que nada
    nos arquivos migrados apontasse para lá. Só apareceu ao migrar o RDO, várias tarefas
    depois. `grep -rn` pela chave antiga em **todo o repositório**, não só nos arquivos que
    a tarefa atual toca, antes de considerar uma migração de armazenamento compartilhado
    concluída.

### O tema claro nunca entra na impressão/PDF — e `versionar_estaticos.py` depois de editar o tema

`tema.css` é ligado com `media="screen"`. Sem isso, o PDF do RDO passou de 1 para 2 folhas
(`test_rdo_pdf.py` pegou). Depois de qualquer edição em **qualquer HTML**, `tema.css` ou `supabase-config.js`, rode
`python3 scripts/versionar_estaticos.py`: ele põe `?v=hash` no tema, no config **e nos iframes da casca**
(`rdo.html?v=…`). Sem isso, o Safari mostra o app velho por até 10 minutos dentro da casca nova — visto em
05/10/2026: o usuário gerou o PDF do RDO e ainda saía a lista antiga, sem o Kanban já publicado. O
`test_padrao_visual.py` falha se o hash de um iframe estiver desatualizado.

### Assunto da Pauta no Check-in: sempre com data de lançamento, e data é LOCAL — nunca `toISOString()`

O calendário do Check-in agrupa por `dataLanc` (`a.dataLanc === iso`). A sincronização
Pauta → Check-in (`checkinSincronizarComPauta`) copiava tudo **menos** `dataLanc`: o assunto
criado hoje na Pauta aparecia no Check-in, mas nunca no dia dele no calendário (relato do
usuário em 05/10/2026). Regra: todo assunto leva `dataLanc`; se faltar, vale a data de criação
(`dataLancDoAssunto(dataLanc, criadoEm)`), em todo ponto de entrada (criar na Pauta, importar,
carregar do servidor, criar no Check-in, link público). `checkinCurarDatasDeLancamento()` corrige
e reenvia ao servidor o que já veio sem data.

Armadilha irmã: `new Date().toISOString().slice(0,10)` é a data em **UTC** — depois das 21h em
Brasília já é "amanhã", e o campo "Data de lançamento" nascia com o dia errado. Usar
`dataLocalISO()`. Teste: `tests/test_pauta_checkin_data.py` (relógio fixo às 22h10 de Brasília).

### O app se atualiza sozinho: `versao.json` + `BUILD_ID` da casca

O Pages demora a publicar (um run ficou 9+ minutos "queued" em 05/10/2026) e o Safari ainda guarda
o arquivo antigo por até 10 min. A casca agora carrega `window.BUILD_ID` (hash de páginas, tema,
config e imagens, calculado por `versionar_estaticos.py`) e, ao abrir, confere com `versao.json`
buscado sem cache; se forem diferentes, recarrega **uma vez** numa URL nova (`?b=hash`, com trava em
`sessionStorage` contra laço). Vale só para o que vier depois dessa versão: a primeira vez exige
reabrir o app. **Rode o versionador antes de todo commit que mexa em HTML/CSS/imagem** — a suíte
`padrao_visual` falha se `versao.json`, o `BUILD_ID` ou os `?v=` dos iframes estiverem velhos.
Antes de achar que um deploy "não pegou", conferir se o run do Pages terminou
(`actions/runs`: `status` deve ser `completed`).

### Kanban do PDF do RDO vem do servidor, não só do localStorage

`rdo.html` lia só `chk_assuntos` (preenchido quando a aba Check-in é aberta). Em aparelho novo ou
janela privada que abre o RDO sem passar pelo Check-in, o Kanban saía vazio e a seção sumia
(print do usuário, 05/10/2026). Agora `lerAssuntosCheckin()` junta o Supabase (`checkin_assuntos`,
buscado ao gerar o PDF; o Kanban se refaz quando os dados chegam) com o `chk_assuntos` local (vale no
mesmo id; traz o ainda não sincronizado) e respeita `chk_removidos`.

### Mudança de banco = nas DUAS obras, sempre (regra do usuário, 06/10/2026)

Obra 1 (`ivssgstckfcuiyetxdze`) e Obra 2 (`lwjbuzubnxnzkofcrhah`) rodam o mesmo código. Tabela, coluna ou
política criada só numa quebra o módulo quando alguém troca de obra. Aplicar nas duas, conferir nas duas e
anotar no Registro. A Obra 2 costuma estar **pausada** — restaurar antes. Comando do Supabase que estoura o
tempo: dividir em partes e conferir o estado antes de repetir. Conferir a paridade com um hash da estrutura
(`md5(string_agg(tabela.coluna:tipo:nulo …))` em `information_schema.columns`, igual nas duas). Divergências
encontradas e corrigidas em 06/10/2026: ver `sql/008_paridade_obras.sql`. RLS: as 25 tabelas das duas obras estão com RLS ligada (as 7 de EAP/Planejamento/Suprimentos da Obra 1 foram ligadas em 06/10/2026, com política aberta "acesso do app" — mesmo acesso efetivo de antes; o app não usa login). **Política aberta = quem tem a chave pública lê e escreve**; fechar de verdade exigiria autenticação no app (decisão futura).

### `obra_id` é TEXTO (`'obra1'`/`'obra2'`), nunca uuid — e leitura grande vem em lotes de 1000 (06/10/2026)

O app grava `obra_id = B3Obras.atualId()`, que é `'obra1'`/`'obra2'`. As 7 tabelas de EAP/Planejamento/
Suprimentos nasceram com `obra_id uuid`: **todo insert desses módulos falhava** ("invalid input syntax for
type uuid") e ninguém viu porque o erro só aparecia num `alert`/console — as tabelas estavam vazias nas duas
obras. Corrigido no banco (`sql/011_obra_id_texto.sql`, nas duas obras). Tabela nova com `obra_id`: **text**.
Segunda armadilha do mesmo módulo: o Supabase devolve **no máximo 1000 linhas por consulta** sem avisar.
O cronograma da Gran Sul tem 2.128 atividades — `planejamento.html` lê com `.range()` em lotes
(`buscarTudo`). Qualquer lista que possa passar de 1000 linhas precisa disso.

### Login: o que existe e o que ainda NÃO protege (06/10/2026)

O app tem login (e-mail + senha, Supabase Auth, mesma conta nas duas obras) e papéis (`admin` vê tudo, `portaria`
só Entradas). **Enquanto `sql/010_auth_rls.sql` (Fase 2) não for aplicada nas duas obras, o login só controla a
tela — as tabelas continuam com política aberta.** Nunca dizer ao usuário que os dados estão protegidos antes da
Fase 2. Na casca, `window.B3_CASCA = true` é obrigatório (senão `B3Auth.guardar()` redireciona a própria casca
em laço); toda página nova que inclua `supabase-config.js` ganha a guarda sozinha; suíte nova usa
`contexto(browser, ...)` de `tests/_login.py`, não `browser.new_context(...)`.
Ver [[Decisões/2026-10-06 Login e perfis de acesso]].

---

## Relacionado

- [[Notas/Armazenamento Local]]
- [[Notas/Contrato do Backend]]
- [[Notas/RDO — Regras do Módulo]]
- [[Projetos/BUILDLy Premium]]
