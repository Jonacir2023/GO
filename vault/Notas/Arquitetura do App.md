---
criado: 2026-08-21
tags: [nota, arquitetura, frontend]
---

# Arquitetura do App

Páginas HTML/JS estáticas, **sem build**, publicadas no GitHub Pages. Não há framework,
bundler nem dependência instalada — cada arquivo `.html` é autocontido (CSS e JS embutidos).

---

## Shell + apps

`buildly-completo.html` é a casca. Dentro dela, os apps aparecem de duas formas diferentes —
e essa diferença importa para qualquer mudança de layout:

### Nativos (marcação dentro do próprio shell)

| Aba | Elemento |
|---|---|
| Home | `#page-home` |
| Pauta | `#page-pauta` |
| Check-in | `#page-checkin` |
| Obra | `#page-obra` |

### Em iframe (arquivo `.html` separado)

| Aba | Elemento | Arquivo |
|---|---|---|
| Custos | `#page-custos` | `custos.html` |
| RDO | `#page-rdo` | `rdo.html` |
| Reunião | `#page-reuniao` | `reuniao.html` |
| Resumo do Tempo | `#page-resumo-tempo` | `resumo-tempo.html` |
| Medições | `#page-medicao` | `medicoes.html` |
| Documentos | `#page-documentos` | `documentos.html` |
| Manutenção | `#page-manutencao` | `manutencao.html` |

Cada app em iframe também abre sozinho (standalone) pela própria URL — por isso todos têm
cabeçalho próprio e botão de voltar (`voltarParaHome()`, que detecta se está em iframe via
`parent.switchTab`).

---

## Navegação

`switchTab(tab, el)` no shell: tira `.active` de todas as `.page` (menos as sub-páginas
`pauta-*` e `checkin-*`), põe em `#page-{tab}`, e chama o init do app quando existe
(`pautaInit()`, `checkinInit()`, `obraInit()`, ou um método dentro do iframe).

**Armadilha conhecida:** a mesma função esconde o cabeçalho da Home em toda aba que não seja
`home`:

```js
homeHeader.style.display = tab === 'home' ? 'block' : 'none';
```

Como as 10 telas restantes têm cabeçalho próprio e **nenhuma reserva espaço para o cabeçalho
da casca**, qualquer coisa que precise ficar visível em todas as abas tem que ser flutuante
(`position:fixed`), nunca colocada nesse cabeçalho. Foi exatamente o que aconteceu com o robô
de IA — ver [[Decisões/2026-08-21 Robô de IA visível em todas as abas]].

---

## Layout responsivo

- Mobile: coluna central de **480px** (`body{max-width:480px}`).
- Desktop: **900px** é o breakpoint no shell, **860px** nos apps internos.

Os dois números são diferentes de propósito, e o comentário no código explica por quê: o
iframe pode ficar alguns pixels mais estreito que a janela (barra de rolagem, bordas). Se
usasse 900 dos dois lados, numa janela de ~900px o app de fora viraria desktop e o de dentro
continuaria em formato de celular.

No desktop os iframes usam `height: calc(100vh - 76px)`; no mobile, `calc(100vh - 140px)`.

---

## Sincronização

- **Pauta → Check-in:** automática via `localStorage`, no mesmo navegador.
- **App → Supabase:** gravação imediata ao criar/editar/remover (não mais um polling de 2
  em 2 minutos — isso só existia pela fragilidade do Apps Script). O RDO é a exceção: sobe
  um retrato completo (debounced) e mescla no cliente. Ver [[Notas/Contrato do Backend]].
- Toda escrita usa `id` gerado no front-end (upsert), então reenviar não duplica linha.

---

## Como as mudanças chegam ao usuário

O usuário **não faz push**. A entrega é um `.zip` com scripts Python numerados que editam os
HTML por trechos exatos (`01_...py`, `02_...py`, …, na raiz do repositório), mais um
`LEIA-ME.txt` com um comando de uma linha para o Terminal. Os scripts precisam ser
**idempotentes** — rodar duas vezes não pode duplicar a alteração.

---

## Relacionado

- [[Projetos/BUILDLy Premium]]
- [[Notas/Armazenamento Local]]
- [[Notas/Contrato do Backend]]
