---
criado: 2026-08-21
tags: [nota, localstorage, dados, frontend]
---

# Armazenamento Local (localStorage)

Todos os apps guardam estado no `localStorage` do navegador. Parte disso sobe para a planilha
(Pauta, Check-in, RDO); **parte existe só no aparelho** — e essa distinção é a origem de vários
problemas.

---

## Chaves por app

| App | Prefixo / chave | Sobe para a planilha? |
|---|---|---|
| Pauta | `pauta_*` (`pauta_assuntos`, …) | Sim |
| Check-in | `chk_*` (`chk_assuntos`, `chk_removidos`) | Sim |
| Entradas | `custo_*` (`custo_notasfiscais`, …) | **Não** (endpoint existe, front-end não chama) |
| RDO | `diario_obras_v4_state`, `diario_obras_v4_history_<obra>`, `diario_obras_aparelho_id` | Sim |
| Obra (compartilhado) | `b3_obra` | — |
| Medições | `med_contratos` | **Não** |
| Documentos | `doc_arquivos`, `doc_notas_manuais` | **Não** |
| Manutenção | `manut_mural`, `manut_ultimo_autor` | **Não** |
| Reunião | `reuniao_atas` | **Não** |

O que não sobe para a planilha é justamente o que o robô de IA recebe via `contextoLocal` na
pergunta — ver [[Notas/Contrato do Backend]].

---

## Armadilha maior: todos os apps do usuário dividem o mesmo `localStorage`

Descoberto em 26/08, e é a explicação de quase toda "mistura" já percebida.

`localStorage` é isolado por **origem** (`https://jonacir2023.github.io`), **não por pasta**.
E o usuário publica vários apps sob a mesma conta do GitHub Pages:

| Endereço | De onde vem |
|---|---|
| `/buildly2/` | o app que a equipe usa hoje |
| `/Buildly3/` | este repositório, quando for publicado |
| `/diario-obras/` | diário de obras de outro repositório |
| `/pauta/`, `/gestao-tarefas/` | idem |

Todos usam **as mesmas chaves**: `diario_obras_v4_state` e
`diario_obras_v4_history_<obra>`. Origem igual + chave igual = **um único pote compartilhado**.

Consequência prática: uma obra lançada em `/diario-obras/` aparece dentro do RDO do BUILDLy no
mesmo celular. Não é dado que atravessou repositório — os repositórios são separados e o código
não conversa. É o navegador servindo o mesmo armazenamento para os dois endereços.

O `buildly-completo.html` já tem uma tela para "apagar o RDO de uma obra errada deste
navegador" — ela existe justamente porque isso já aconteceu antes.

**Resolvido em 26/08:** o BUILDLy passou a ter espaço próprio. Um bloco no topo de cada HTML
troca `window.localStorage` por uma versão que prefixa tudo com `buildly3::`, e que enxerga só o
próprio espaço — inclusive em `length`, `key(i)` e `clear()`. Sem ponte e sem importação: o
BUILDLy não lê nem apaga nada de outro app. Ver
[[Decisões/2026-08-26 Espaço próprio de armazenamento]].

Ao inspecionar o `localStorage` pelo navegador, as chaves aparecem como
`buildly3::diario_obras_v4_history_<obra>`. Dentro do código, nada mudou.

## Armadilha: a chave do RDO carrega o nome da obra

```js
const HISTORY_KEY_BASE = 'diario_obras_v4_history';
// chave real: HISTORY_KEY_BASE + '_' + obra.nome.replace(/\s+/g,'_').toLowerCase()
```

Isolamento por obra é intencional (versão 20 do RDO), mas tem uma consequência que já confundiu:
**renomear a obra "esconde" todos os RDOs antigos**, porque o app passa a ler outra chave. Os
dados não foram perdidos — estão na chave do nome anterior, e a planilha continua intacta de
qualquer jeito (é ela a fonte de verdade). Se acontecer, restaure pelo backup na nuvem ou
volte o nome exato da obra.

Há também as chaves legadas `diario_obras_v3_state` / `_history`, lidas só para migração.

## Dentro do histórico, a chave é `data#apontador`

Desde 25/08 o `history` não é indexado pela data, e sim por `2026-08-24#renan-de-souza` — um RDO
por apontador no mesmo dia. `migrarHistoricoParaMultiRdo()` converte o formato antigo lendo o
`apontador` de dentro de cada diário, roda ao carregar **e** nos três caminhos de restauração de
backup, e é idempotente. Ver [[Decisões/2026-08-25 Um RDO por apontador no mesmo dia]].

Consequência para quem for ler o `localStorage` na mão: `Object.keys(history)` já não devolve
datas.

Chaves auxiliares por dia, incluídas no backup: `efetivoDia_`, `equipDia_`, `vlDia_`,
`ativDia_` (sufixo = data), mais `ultimoBackupNuvem` e `diario_obras_v3_autobackup`.

---

## Armadilha: cota estourada por foto em base64

Fotos guardadas como data URI dentro do `localStorage` consomem muito espaço e a cota estoura
sem aviso — o `setItem` lança exceção e, se ninguém tratar, **o registro que o usuário acabou
de preencher se perde em silêncio**.

Regra: onde o registro pode carregar imagem embutida (Entradas, RDO), envolva a gravação em
`try/catch` e avise o usuário em vez de deixar falhar quieto. Ver
[[Decisões/2026-08-21 Escaneamento de nota fiscal]].

---

## Armadilha: PWA e navegação privada no iOS

Reinstalar o ícone PWA na tela de início do iPhone pode criar um container de `localStorage`
separado e zerado — o app abre como se nunca tivesse sido usado. O Safari em modo privado
também isola e descarta o armazenamento entre sessões. É a explicação mais provável para um
"sumiço" de dados que não tem causa no código.

Por isso: **a planilha é a fonte de verdade, o local é cache.** Se o app abrir vazio, restaure
da nuvem — nunca peça para o usuário redigitar cadastro.

---

## Relacionado

- [[Notas/Regras Operacionais Críticas]]
- [[Notas/Arquitetura do App]]
- [[Notas/Contrato do Backend]]
