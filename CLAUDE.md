# CLAUDE.md — BUILDLy Premium (GO)

Plataforma de gestão de obra da Cesbe S.A. Páginas HTML/JS estáticas, **sem build**, publicadas
no GitHub Pages, com Google Sheets + Apps Script como backend.

**Idioma: português (PT-BR)** — notas, commits e conversa com o usuário.

---

## Leia o cofre antes de mexer no código

`vault/` é um cofre Obsidian com a memória do projeto: por que as coisas são como são, o que já
foi decidido, e quais armadilhas já custaram tempo ou dado. **Comece por `vault/Início.md`.**

Essencial antes de qualquer alteração:

| Nota | Para quê |
|---|---|
| `vault/Projetos/BUILDLy Premium.md` | Estado atual, histórico, fila de desenvolvimento |
| `vault/Notas/Regras Operacionais Críticas.md` | O que nunca fazer — cada item vem de um erro real |
| `vault/Notas/Arquitetura do App.md` | Shell + 9 apps (nativos vs. iframe) |
| `vault/Notas/Contrato do Backend.md` | Endpoints do Apps Script, entrada e saída |
| `vault/Notas/Armazenamento Local.md` | Chaves do `localStorage` e suas armadilhas |
| `vault/Registro/Índice do Registro.md` | Tudo que já mudou, dia a dia, direto do git |

## A sessão já começa pronta

`.claude/hooks/session-start.sh` roda no início de toda sessão na web: confere o navegador,
sobe o app em `$BUILDLY_URL` (porta 8795) e roda os dois verificadores. Não faz nada na máquina
do usuário.

```bash
python3 tests/executar.py          # as 7 suítes
python3 tests/executar.py rdo      # só as do RDO
python3 scripts/verificar_sintaxe.py
```

As suítes abrem o app num navegador sem tela e conferem regras que já custaram caro: um RDO por
apontador por dia, responsável obrigatório, baixa lógica, sincronização sem sobrescrever, a
lixeira do cadastro, o espaço próprio de armazenamento. **Rode antes de entregar qualquer
mudança em HTML.**

`verificar_sintaxe.py` é o mais próximo de um linter que faz sentido aqui: o projeto não tem
build, e um erro de sintaxe só apareceria quando alguém abrisse a página no celular.

## Prove o isolamento antes de entregar — obrigatório

```bash
python3 scripts/verificar_isolamento.py
```

Falha se o BUILDLy tiver qualquer vínculo com outro projeto: `/exec` que não seja o dele,
planilha que não seja a dele, endereço ou repositório de outro sistema, pasta de Drive com nome
genérico, ou app usando `localStorage` sem o espaço próprio.

Isto existe por causa de um incidente real — alteração no efetivo do RDO aparecendo no diário de
obras de outro projeto, em outro aparelho. Ver
`vault/Decisões/2026-08-26 Isolamento definitivo entre projetos.md`.

## Registre TODA alteração — obrigatório, sem exceção

Nenhuma mudança do BUILDLy pode ficar sem nota. Antes de terminar qualquer trabalho que produza
commit, rode:

```bash
python3 scripts/registro_obsidian.py
```

Ele lê o git e escreve/atualiza `vault/Registro/AAAA-MM-DD.md` — uma nota por dia, com todo
commit, todo arquivo tocado e as linhas somadas e removidas. É idempotente: rodar de novo não
duplica nada.

O script cobre o **o quê**. O **porquê** é sua parte: escreva, acima do bloco
`<!-- registro:auto -->`, o que motivou a mudança, o que foi testado e o que ficou pendente.
O script nunca toca nesse texto.

Commit o resultado junto com a alteração, no mesmo PR. Um commit sem entrada no Registro é
trabalho pela metade.

## Mantenha o cofre atualizado — sem esperar ser pedido

Toda sessão que fizer trabalho relevante aqui **atualiza as notas afetadas como parte do próprio
trabalho**, no mesmo commit ou PR. Conta como relevante: PR aberto ou mesclado, decisão tomada,
mudança no contrato do backend, armadilha nova descoberta, teste do usuário que confirma ou
desmente algo já escrito.

O guia de manutenção — o que atualizar em cada caso, como escrever, o que não guardar — está em
`vault/Notas/Como manter este cofre.md`. Siga-o.

Sem isso o cofre envelhece e passa a atrapalhar em vez de ajudar: uma nota errada é pior que
nota nenhuma.

---

## Projeto fechado em si

O BUILDLy é autocontido: código, backend, planilha e documentação vivem neste repositório e mais
nada. **Toda** documentação do projeto vai para `vault/`, aqui — nunca para outro repositório,
outro cofre ou outra base de notas, mesmo que pareça relacionado. Sem submodules, sem imports
externos, sem deploy compartilhado, sem notas cruzadas com outros projetos.

---

## Como as mudanças chegam ao usuário

O usuário **não faz push**. A entrega é um `.zip` com scripts Python numerados (`NN_*.py` na
raiz) que editam os HTML por trechos exatos, mais um `LEIA-ME.txt` com um comando de uma linha
para o Terminal. Os scripts precisam ser **idempotentes** — rodar duas vezes não pode duplicar
a alteração.

---

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
