---
criado: 2026-10-04
tags: [decisao, visual, buildly]
---

# Padrão visual claro (substitui o Modelo C escuro de 18/09)

**Pedido do usuário (04/10/2026), com 4 imagens de mockup:** "Quero este padrão para o app agora".
Respostas às perguntas: entrega **tudo de uma vez**; itens novos **funcionais e simples**;
foto do cabeçalho **ilustração própria**.

## O que o padrão é

- Tema **claro** (fundo `#f3f5f9`, cartões brancos, raio 16, sombra suave); acento tan
  `--accent #d79d6e`, navy para ação secundária.
- Casca: hero escuro com ilustração SVG de obra ao pôr do sol (`hero-obra.svg`), logo com
  guindaste, sino (ponto vermelho) e perfil; cartão branco **Obra Atual** sobre o hero.
- Home: grade de cartões (ícone em gradiente, título, descrição, chevron, barra colorida);
  3 colunas no celular (9 cartões; os 5 extras ficam em **Mais**), 5 no desktop (14).
- Barra inferior flutuante: **Início, Favoritos, Relatórios, Mais**.
- Módulo aberto: hero compacto fixo (`#hero-mod`) com voltar + cartão do título; o app em
  iframe esconde o próprio cabeçalho (`html.embutido`) e cola as abas em pílula no topo.

## Itens "funcionais e simples"

| Item | Comportamento |
|---|---|
| Estrela do cartão | favorito em `localStorage` (`favoritos`, lista de ids) |
| Favoritos | painel (bottom sheet) com os módulos favoritados |
| Relatórios | 6 atalhos: PDF/Resumo do RDO, Resumo do Tempo, Ata, Medições, Resumo do Check-in |
| Mais | os 5 módulos extras + Perguntar à IA |
| Sino | pendências do Check-in (`chk_assuntos` com status `afazer`/`fazendo`); ponto some sem pendência |
| Perfil | apontador do aparelho, obra ativa, versão |
| Cartão Obra Atual | abre a troca de obra (recarrega o app) |

## Como foi feito (e o que não quebrar)

1. **`tema.css`** compartilhado, carregado **por último** em toda página, redefine os tokens
   e restila componentes. Só vale em tela: `<link … media="screen">`. **Sem isso o PDF do RDO
   passa de 1 para 2 folhas** (o tema aumenta títulos/espaços) — pego pela suíte `test_rdo_pdf.py`.
2. As cores escuras fixas dos HTMLs foram convertidas para tokens (`var(--bg)`, `var(--ink)`…),
   sem tocar em PDF/impressão.
3. **`python3 scripts/versionar_estaticos.py`** — rodar depois de editar `tema.css` ou
   `supabase-config.js`. Põe `?v=<hash>` na URL (o Pages deixa o Safari reaproveitar por 10 min,
   e cada app em iframe é um arquivo à parte), garante o `<link>` do tema e o detector `embutido`.
4. Módulos gerados por `scripts/gerador_modulo` já saem com o detector e o `<link>` do tema.
5. Os apps genéricos (EAP, Planejamento, Financeiro, Suprimentos) perderam o
   `prefers-color-scheme: dark` próprio — o padrão é só claro.
6. Cabeçalhos antigos de Pauta/Check-in/Obra continuam no HTML (escondidos por CSS) porque o JS
   usa os IDs deles.

## Limites conhecidos

- A ilustração é própria (SVG), não a foto do mockup.
- A fonte do ambiente de teste (DejaVu) é mais larga que a do iPhone; textos que cabem no
  sandbox cabem no aparelho.
- Não validado em iPhone real ainda.

Teste: `tests/test_padrao_visual.py` (43 verificações). Relacionado:
[[Notas/Arquitetura do App]], [[Decisões/Índice de Decisões]].
