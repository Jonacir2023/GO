---
tags: [índice, início]
---

# BUILDLy Premium — Base de Conhecimento

Cofre Obsidian do repositório `Jonacir2023/GO`. Guarda o que o código não diz sozinho:
por que as coisas são como são, o que já foi decidido, e o que ainda está em aberto.

> **Para o Claude:** leia [[Projetos/BUILDLy Premium]] antes de mexer em qualquer coisa deste
> repositório. As notas técnicas abaixo evitam refazer investigação que já foi feita.

---

## Comece por aqui

| Nota | Para quê |
|---|---|
| [[Projetos/BUILDLy Premium]] | Estado atual, histórico, fila de desenvolvimento |
| [[Notas/Arquitetura do App]] | Como o shell e os 9 apps se encaixam |
| [[Notas/Contrato do Backend]] | Todos os endpoints do Apps Script, entrada e saída |
| [[Notas/Armazenamento Local]] | Chaves do localStorage e as armadilhas de cada uma |
| [[Notas/RDO — Regras do Módulo]] | O app mais delicado — e o único que gera documento contratual |
| [[Notas/Regras Operacionais Críticas]] | O que nunca fazer (erros que já custaram caro) |

## Índices

- [[Registro/Índice do Registro]] — tudo que já mudou, dia a dia
- [[Projetos/Índice de Projetos]]
- [[Notas/Índice de Notas]]
- [[Decisões/Índice de Decisões]]
- [[Recursos/Índice de Recursos]]

---

## Como este cofre se mantém

**Nenhuma alteração do BUILDLy fica sem nota.** O que mudou e quando é gerado do próprio git por
`scripts/registro_obsidian.py`, que escreve uma nota por dia em [[Registro/Índice do Registro]] —
isso não depende de ninguém lembrar. O porquê de cada mudança é escrito à mão na mesma nota, e o
script preserva.

As notas de conhecimento (`Notas/`, `Decisões/`, `Projetos/`) são mantidas pelo Claude, por
convenção registrada no `CLAUDE.md` da raiz: toda sessão atualiza o que tocou, no mesmo
trabalho, sem esperar ser pedido. Ver [[Notas/Como manter este cofre]].

#índice
