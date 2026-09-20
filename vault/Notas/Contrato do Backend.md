---
criado: 2026-08-21
atualizado: 2026-09-19
tags: [nota, backend, supabase, api]
---

# Contrato do Backend

Migrado do Google Sheets/Apps Script único para **um projeto Supabase por obra** — ver
[[Decisões/2026-09-19 Migração para Supabase multi-obra]] para o porquê e o histórico. Cada
obra é um banco Postgres totalmente separado (mesmo schema, dados isolados).

O Apps Script (`apps-script/BuildlyBackend.gs`, planilha "Buildly3") continua existindo, mas
só serve o recurso de pergunta-e-resposta por IA — ver a seção própria mais abaixo.

---

## Como o front-end fala com o Supabase

`supabase-config.js` (raiz do repositório, incluído via `<script>` em todo HTML) expõe
`window.B3Obras`:

- `B3Obras.listar()` — registro fixo das obras (`id`, `nome`, `url`, `anonKey`).
- `B3Obras.atualId()` / `B3Obras.trocar(id)` — obra ativa, em
  `localStorage['buildly3::obra_atual_id']`.
- `B3Obras.cliente(idOpcional)` — devolve um cliente `supabase-js` (cacheado) para a obra
  ativa ou a informada. Todo `fetch(APPS_SCRIPT_URL, ...)` de antes virou
  `B3Obras.cliente().from('<tabela>').select()/upsert()/delete()`.
- `B3Obras.config()` / `configCarregar()` / `configSalvar(patch)` — leitura síncrona
  (cache), busca e gravação de `obra_config`. Também disponível como
  `obraCompartilhada()` global (nome mantido por compatibilidade — todo módulo já chamava
  isso desde a era `localStorage['b3_obra']`).

Não existe token de acesso por chamada como no Apps Script: a chave publicável do Supabase
já é pública por natureza (RLS decide o que pode ser lido/escrito, não o sigilo da chave) —
ver regra 22 em [[Notas/Regras Operacionais Críticas]]. RLS está **aberto** (`for all
using (true)`) em toda tabela, de propósito: mesma postura de segurança de antes (device
sem login), não é uma regressão.

---

## Padrão de sincronização, módulo por módulo

Dois padrões coexistem, cada um escolhido pelo que o módulo já fazia antes:

**Gravação imediata + reenvio do pendente** (Pauta, Check-in, Custos, Manutenção,
Documentos, Reunião, Medições): cada criar/editar/remover chama Supabase na hora
(`upsert`/`delete`); se falhar (rede fora), o item fica marcado `_sincronizado` ausente e é
reenviado na próxima busca do servidor (`carregarXDoServidor()`, chamado no início de cada
módulo). Substitui o polling de 2 em 2 minutos que existia só pela fragilidade do Apps
Script.

**Retrato único, mesclado no cliente** (RDO): uma tabela (`rdo_snapshot`), uma linha por
obra, com o `state`/`history` inteiros como jsonb. O RDO já resolvia conflito e mesclava
sozinho antes de existir Supabase (`mesclarDaNuvem`, `aplicarRegraRdo`,
`mesclarStatusCadastro`, tudo em `rdo.html`) — a migração só trocou o transporte
(`fetch` → `B3Obras.cliente().from('rdo_snapshot')`), a lógica de mescla não mudou.

## Tabelas

| Tabela | Módulo | Observação |
|---|---|---|
| `obra_config` | Aba Obras (compartilhada) | Linha única, `id=1` |
| `pauta_assuntos` | Pauta | `id` é o `Date.now().toString()` do front-end (texto, não UUID) |
| `pauta_membros`, `pauta_setores` | Pauta (Admin) | Chave natural em `nome` (índice único, upsert por nome) |
| `checkin_assuntos` | Check-in | Mesmo `id` texto de `pauta_assuntos` quando o assunto veio de lá |
| `checkin_reunioes` | Check-in | `assuntos_snapshot` jsonb — ata da reunião, insert simples (sem upsert) |
| `custos_notas_fiscais`, `custos_itens_nf` | Custos | NF não tem edição (só criar/deletar); itens entram uma vez só, junto com a NF |
| `documentos`, `documento_notas_manuais` | Documentos | |
| `manutencao_mural` | Manutenção | |
| `reuniao_atas` | Reunião | `participantes`/`pauta`/`topicos`/`plano_acao` como jsonb |
| `medicao_contratos` | Medições | `itens`/`medicoes` como jsonb **dentro** da linha do cliente/empreiteiro — o modelo real já aninha os três juntos, sempre salvos em bloco; não existem tabelas `medicao_itens`/`medicoes` separadas |
| `rdo_snapshot` | RDO | Linha única (`id=1`) por obra — ver acima |

Convenção de `id`: sempre **texto**, gerado no front-end (`Date.now().toString()` ou
`uid()`), nunca UUID gerado pelo servidor — mesma regra que já valia no Apps Script
("upsert pelo ID que o app gerou localmente"), só que agora reforçada por tipo de coluna,
não por convenção de código.

---

## Robô de IA (`ia/perguntar`) — ainda no Apps Script, agora desatualizado

Continua em `apps-script/BuildlyBackend.gs`, chamado de `buildly-completo.html`
(`fetch(APPS_SCRIPT_URL + '?path=ia&action=perguntar', ...)`). Lê a planilha (Diário, Pauta,
Check-in, Notas Fiscais) para montar o contexto da resposta, mais o que só existe no
navegador (Medições, Documentos, Mural) via `contextoLocal` (`montarContextoLocal()`).

**Como nenhum módulo grava mais na planilha, esse contexto está congelado no que existia
antes desta migração** — o robô vai responder com dados cada vez mais velhos, sem erro
nenhum aparente. Não corrigido junto com o resto porque a lógica de resposta mora inteira
no Apps Script (chave `ANTHROPIC_API_KEY` nas Propriedades do script) e é uma feature de
IA, não um CRUD de módulo — decisão de como resolver (manter o Apps Script vivo lendo do
Supabase, migrar para uma Edge Function, ou aposentar) é do usuário. Detalhes em
[[Decisões/2026-09-19 Migração para Supabase multi-obra]].

- Modelo: `claude-haiku-4-5-20251001` (constante `MODELO_IA_PERGUNTAS`).
- Contexto recortado em 3 meses para Diário e Notas Fiscais; Pauta e Check-in vão inteiras.

---

## O que sobrou do Apps Script — só referência histórica

`apps-script/BuildlyBackend.gs` continua no repositório (não é implantado por git — o que
roda é o que está colado no editor do Google, ver regra 17) e continua servindo `ia/
perguntar`. As rotas de `pauta`, `checkin`, `diario`, `custos`, `foto` e `backup` que
existiam nele não são mais chamadas por nenhum front-end — ficam mortas no script, sem
problema em continuar existindo lá (não fazem mal), mas não descreva mais o contrato delas
aqui como se estivessem em uso.

## Relacionado

- [[Projetos/BUILDLy Premium]]
- [[Decisões/2026-09-19 Migração para Supabase multi-obra]]
- [[Decisões/2026-08-21 Backend recuperado da Lixeira]]
- [[Notas/Regras Operacionais Críticas]]
