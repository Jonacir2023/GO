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

---

## Relacionado

- [[Notas/Armazenamento Local]]
- [[Notas/Contrato do Backend]]
- [[Notas/RDO — Regras do Módulo]]
- [[Projetos/BUILDLy Premium]]
