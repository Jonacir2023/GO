# MANIFEST — Buildly3 (Repositório Único Consolidado)

Este repositório consolida o histórico de desenvolvimento da plataforma Buildly que rodava em
`buildly2`. A partir de agora, **Buildly3 (este repositório, `Jonacir2023/GO`) é a única fonte**
para esta plataforma — Google Sheets + Apps Script, planilha e `/exec` próprios, exclusivos.

## 📦 Conteúdo

### `/` (raiz) — App em produção

- `buildly-completo.html` — App integrado (Pauta + Check-in + RDO + Custos)
- `pauta.html`, `Check-in.html`, `custos.html`, `rdo.html` — Módulos standalone
- Backend: Google Sheets via Google Apps Script

## 🚫 Independência de qualquer outro repositório

Este repositório é fechado em si: código, backend, planilha e documentação vivem só aqui. Sem
submodules, imports, links de deploy compartilhados ou dependências cruzadas com nenhum outro
repositório — incluindo `Jonacir2023/buildly2`, `Jonacir2023/buildly` (ex-`buidly`, geração
paralela em Supabase — já existiu uma cópia dela em `/app-supabase/` neste repo, removida em
18/09 por violar esta regra) e `Jonacir2023/JC` (vault de gestão de tarefas, sistema separado).

Uma eventual migração para Supabase, se um dia for decidida, começa deste repositório e do seu
próprio schema — nunca importando a pasta ou o banco de outro projeto para dentro deste.
