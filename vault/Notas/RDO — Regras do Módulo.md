---
criado: 2026-08-25
tags: [nota, rdo, regras]
---

# RDO — Regras do Módulo

O `rdo.html` é o maior e mais delicado app da plataforma (~7.500 linhas) e o único que produz
**documento contratual**: o que ele imprime é o que a fiscalização lê. As regras abaixo existem
por causa disso.

---

## Responsável é obrigatório

Nenhum diário é gravado sem `apontador` preenchido — nem no salvamento manual, nem no automático.

```js
function diarioPodeSerSalvo(day) { return !!String((day && day.apontador) || '').trim(); }
```

Vale para os dois caminhos de propósito: o salvamento automático sem responsável era exatamente
o que criava RDO anônimo, que ninguém sabe de quem é e não serve como documento.

A lista de responsáveis é filtrada por papel — `_ehResponsavelValido()` aceita quem tem
"apontador", "apontamento" ou "supervis" no cargo. Pedreiro não assina RDO.

## Local da obra é lista fechada

Os locais vêm do cadastro da obra (tabela `rdo_locais` no Supabase da obra, editada pelo botão
"+" do cartão Local da Obra, ou por Obras → Gerenciar Locais, que abre o mesmo modal) num
`<select>`. Texto livre gerava "Filtro 9", "filtro 9", "F9" e "Filtros ETA" para o mesmo lugar, e
relatório por local virava contagem de erros de digitação. O valor gravado no diário é o **nome**
do local (único por obra), não o id.

**Não existe lista padrão.** Até 01/10/2026 havia uma constante `LOCAIS_EXECUCAO` (Filtro 1…10, ETA,
Casa de Bombas, Canal do Reservatório — de outro projeto) usada como fallback quando o Supabase
voltava vazio ou falhava; ela aparecia no seletor de uma obra nova. Foi removida. Obra sem locais
cadastrados mostra "Nenhum local cadastrado" no seletor. O teste semeia `locaisPorObra` para simular
o cadastro.

**Valor antigo fora da lista sobrevive:** entra como opção extra já selecionada. Fechar a lista
não pode reescrever RDO que já existe.

> Armadilha: `localObra` **não** pode entrar no laço genérico de `preencherCampos()`. Atribuir
> `.value` num `<select>` antes de as `<option>` existirem não seleciona nada — e o campo abre
> vazio num RDO que estava preenchido.

## Eventos do Dia — interfaces com equipes (reformulado em 06/10/2026)

Antes (01/10) era uma lista de tipos marcados com ✓, com campos de carga e valor. Com a aba **Entradas**
cuidando de todo material que chega, virou o registro de **quem fez o quê na obra**: liberação, paralisação,
marcação, visita… Proposta e mockup aprovados em 06/10/2026 — ver
[[Decisões/2026-10-06 Proposta — Eventos do Dia do RDO]].

- **Cada evento** (`currentDay.eventosDia[]`): `id, tipoId, tipo` (nome do evento), `grupo`, `equipe`
  (Fiscalização ou Cesbe + equipe), `hora`, `detalhe` (a Descrição), `responsavel` (pessoa da equipe que
  liberou/parou/marcou), `local`, `paralisacao` (bool), `retomadaData`, `retomadaHora`, `fotos[]` (até 3,
  data URI, 1024 px q 0,65), `custom`, `removido`/`removidoEm`. O apontador e a data vêm do próprio dia.
- **Registro:** "➕ / + Registrar evento" abre a janela `#modalEvDia` (`abrirModalEventoDiaNovo(idx?)`):
  hora (já vem agora), responsável, chips de equipe (agrupados), chips de evento, local (campo com lista
  dos locais da obra, vem com o local do dia), descrição, checkbox **⛔ Paralisação**, fotos. Equipe, evento,
  hora e responsável são obrigatórios. Tocar no cartão edita (mesmo `id`); o 🗑️ é **baixa lógica**
  (`removido: true`) — `eventosAtivos(day)` filtra, PDF/WhatsApp/Resumo/.csv não mostram, os dados ficam.
- **Paralisação:** o checkbox abre Data e Hora da retomada (as duas juntas ou as duas vazias; vazias =
  "Retomada em aberto"). Escolher o evento "Paralisação de trabalho" marca o checkbox. `minutosParadoEvento`
  = retomada − (data do dia + hora do evento); retomada antes da paralisação é recusada.
- **Catálogos** (Cadastro → 📌 Eventos): `state.equipesEvento` `[{id, grupo, nome}]` (padrão: Fiscalização →
  Civil, Segurança do Trabalho, Meio Ambiente, Topografia; Cesbe → Energia, Civil, Topografia, Segurança do
  Trabalho, Meio Ambiente, Laboratório) e `state.eventosDia` `[{id, desc}]` (11 tipos). Remover do cadastro é
  **baixa lógica** (`inativo`), com "Removidos" para restaurar; entram na sincronização (`mesclarDaNuvem`).
  `migrarEventosV2` (dentro de `mergeDefaults`, flag `eventosV2`) acrescenta equipes e tipos novos UMA vez ao
  catálogo antigo sem tirar nada nem duplicar.
- **Nada se perde (pedido do usuário):** os campos antigos `fornecedor, valorCarga, transporte, placa, volume,
  peso` não têm mais tela, mas continuam nos dados e saem na Descrição como
  "Dados antigos: Fornecedor X · Valor R$ Y · Placa Z · Volume N m³ · Peso P t" (`textoLegadoEvento`, sai mesmo
  com `transporte` desmarcado). O cálculo de cargas/volume/peso/valor dos acumulados segue lendo esses campos.
- **Impressão:** PDF = planilha "Eventos do dia" (Hora · Equipe · Evento · Descrição · Responsável · Local ·
  Paralisação) com **linha de resumo** no rodapé (total, paralisações, tempo parado, por equipe) + bloco
  "Fotos dos eventos" (6 por linha, legenda hora · evento (i/n)). WhatsApp: um item por evento
  (equipe, descrição, responsável, local, ⛔ paralisação, 📷 fotos, dados antigos) + "_Resumo dos eventos_".
  Acumulados (semana/mês/ano) ganharam a linha "Paralisações · tempo parado".
  Resumo em linha (e não tabela) porque o dia cheio precisa caber em 1 folha — ver teste do PDF.
- **Aba Resumo (tela):** cartões por tipo (com paralisações e tempo parado), tabela por equipe, a **planilha
  do período** e o botão **📄 Exportar planilha de eventos (.csv)** (`baixarCsvEventos`, `;` + BOM, todas as
  colunas inclusive Dados antigos e Apontador).
- **Dado antigo:** `observacoesDia` continua virando eventos "Observação" ao abrir o dia (`initCurrentDay`
  acrescenta sem derrubar eventos removidos).
- **Acidentes:** "Eventos de Segurança" e "Eventos de Meio Ambiente" passaram a se chamar **Acidentes de
  Segurança do Trabalho** e **Acidentes de Meio Ambiente** (Diário, Cadastro "Acid. SST"/"Acid. MA", PDF,
  WhatsApp). Os dados (`eventosSeguranca`, `eventosAmbiente`) não mudaram; seguem com gravidade e ação.
- Armadilha: as janelas novas usam `z-index` 1100 e o `toast` 1200, porque a barra de abas é `z-index: 999`
  e escondia o topo de janela alta.

## PDF do RDO: um layout só, condensado (02/10/2026)

Um botão na aba Gerar ("📄 Gerar PDF do RDO") → `gerarPdfRDO()`. Até 02/10/2026 existiam um layout
grande (~8 folhas por dia cheio) e um "resumido"; o usuário pediu o mesmo layout compacto para o PDF
principal e o antigo foi **apagado** (o git guarda: commits anteriores a `06cb9a9`+1).

- **Layout:** mesma folha A4 e **mesma margem de 10 mm** (o Compartilhar usa 10 mm fixos — não mexer só
  em um lado), fonte 7,5–8 pt, tabelas coladas, duas colunas (clima | jornada; efetivo | equipamentos),
  sem fundos escuros (filetes cinza), sem quebras forçadas de página. Um dia cheio (14 de efetivo, 7 fotos,
  eventos, SSMA, acumulados) **sem Kanban** cabe em **1 folha**; com Kanban de poucos assuntos, em até 2
  (o quadro é conteúdo pedido, não desperdício). O teste `test_rdo_pdf.py` trava os dois casos.
- **Ordem das seções (pedida pelo usuário):** cabeçalho, indicadores, clima | jornada, efetivo | equipamentos,
  **atividades do dia logo acima de eventos do dia**, segurança/meio ambiente, acumulados, fotos,
  **Kanban de Assuntos do Check-in**, **notas recebidas no dia (planilha + resumo, do Entradas)**, assinaturas. O teste `test_rdo_pdf.py` trava Atividades imediatamente antes de Eventos.
- **Conteúdo:** cabeçalho com RDO nº, data, cliente, contrato, local/frente (obra + local do dia);
  faixa de 7 indicadores; clima; jornada e DSS; atividades (com paralisadas e justificativa); efetivo por
  função/empresa; equipamentos e veículos (operando/parados com justificativa); eventos do dia (hora,
  detalhe, fornecedor, valor, transporte); segurança e meio ambiente (gravidade, ação); **acumulados**
  semana/mês/ano numa tabela só (atividades, eventos por tipo, cargas, m³, ton, valor); fotos; **Kanban de
  Assuntos** (04 colunas); assinaturas.
- **Fotos:** só miniaturas, sempre 8 por linha (com 6 por linha, 3 fotos ocupavam mais que 7). As
  fotos grandes saíram com o layout antigo.
- **Kanban de Assuntos (pedido do usuário em 05/10/2026):** `kanbanAssuntosPdf()` espelha o quadro da
  tela do Check-in — A FAZER, FAZENDO, CONCLUÍDO, CANCELADO; em A fazer/Fazendo o cartão completo
  (descrição, prioridade, setor, status, datas, responsável · criador, prazo restante/atrasado), em
  Concluído/Cancelado só o nome. Lê `chk_assuntos` ao gerar, então sai sempre atualizado; **não filtra por
  dia** (como a tela), logo um RDO regerado mostra o quadro de hoje. Substituiu a lista curta
  "Check-in — pendências". Se não houver assuntos, a seção some.
- Se passar de uma folha, quebra entre linhas de tabela sem partir linha (`tr` com `page-break-inside:
  avoid`; o Compartilhar também evita cortar `tr` e linhas de foto).
- Armadilha: o símbolo ⏸ não existe na fonte do PDF (sai quadradinho); no PDF use texto.
- A caixa Jornada do layout antigo tinha rótulos velhos ("Café: --:-- – 07:00"): os campos
  `cafeFim`/`almocoInicio`/`almocoFim`/`encerramento` na tela são Início de jornada / Início e Fim do
  almoço / Fim de jornada. O novo mostra "Jornada: 07:00 às 17:00 · Almoço: 12:00 – 13:00".

## Cadastro > "Salvar ... do dia": rascunhos e responsável (02/10/2026)

As telas de marcar do Cadastro (Equipe, Equip., Veículos, Ativ.) não mexem no RDO direto: gravam
**rascunhos locais** `efetivoDia_<data>`, `equipDia_<data>`, `vlDia_<data>`, `ativDia_<data>` (formato
`{id: true}`; atividades `{id: {qty, local}}`) e os botões "💾 Salvar ... do dia" **copiam o rascunho
para o RDO** (`salvarEfetivoDia`, `salvarAtividadesDodia` substituem; equip/VL só regravam o dia).
Dois defeitos reais que isto causava ao editar um dia anterior (reportado em 02/10/2026):

1. **Dia sem apontador: voltava ao Diário "sem nada salvo e nada selecionado".** `salvarDiarioDia()` recusa
   em silêncio dia sem responsável; o fluxo seguia dizendo "✓ salvas" e depois `initCurrentDay(data)`
   recarregava do histórico — um dia vazio por cima do que acabara de ser marcado. Agora
   `voltarAoDiarioAposSalvar(data, gravou)` só recarrega se gravou; senão mantém as seleções **em memória**,
   mostra "⚠️ Marcado, mas ainda NÃO gravado" e leva ao seletor de Apontador; `selecionarApontadorDireto`
   grava o dia com tudo. A regra "só grava com responsável" continua valendo.
2. **Dia já gravado, sem rascunho neste aparelho (outro aparelho, backup, rascunho limpo): o Salvar APAGAVA
   o que o dia tinha** (o Cadastro abria tudo desmarcado e o Salvar substituía o dia pelo rascunho vazio).
   Agora `semearRascunhosDoDia(dia)`, chamado em `initCurrentDay`, cria os 4 rascunhos a partir do dia
   gravado **só quando não existem** (nunca pisa em marcação mais nova).
- Armadilha para futuros botões "Salvar" do Cadastro: sempre calcular `diarioPodeSerSalvo(currentDay)`
  antes e usar `voltarAoDiarioAposSalvar`/`toastSalvoDoCadastro`; nunca chamar `initCurrentDay` logo depois
  de um `salvarDiarioDia()` sem checar se gravou.
- Suíte: `tests/test_rdo_salvar_cadastro.py`.

## Duas chaves são strings parecidas: data e `data#apontador`

Ver [[Decisões/2026-08-25 Um RDO por apontador no mesmo dia]]. `history` é indexado pela chave
composta; calendário e navegação trabalham com datas. Confundir as duas não dá erro — dá
`undefined` silencioso.

## Cadastro não apaga, dá baixa

Ver [[Decisões/2026-08-25 Baixa lógica no cadastro do RDO]]. Toda lista de cadastro filtra por
`itemVigenteNoDia(item, dia, usado)` — o que existe hoje não é o que existia no dia do RDO que
está aberto.

> Armadilha, e ela já aconteceu: **remoção que não é visível parece botão quebrado.** A lista de
> colaboradores foi a única que não recebeu o filtro de vigência — o 🗑️ dava a baixa e a linha
> continuava na tela. Duas condições precisam valer juntas em toda lista do Cadastro:
>
> 1. a lista passa por `vigentesNoDia` / `categoriasVigentes`;
> 2. a baixa **desmarca o item do dia aberto** (`desmarcarDoDia`), senão a regra "usado no dia
>    aparece sempre" o mantém na tela.
>
> E quando o dia aberto é passado, o item fica mesmo — aí o certo é o app dizer isso
> (`toastBaixa`), não deixar parecer falha.

Segurança e Meio Ambiente são a exceção proposital: o evento do dia copia a descrição do tipo
(`ev.tipo`), então apagar o cadastro não mexe em RDO nenhum, e ali a exclusão é de verdade.

## Sincronização a cada 3 minutos

Ver [[Decisões/2026-08-25 Sincronização entre aparelhos]].

## Texto e legenda são gerados, não digitados

- A atividade sai com **os dois locais**: o local do dia e o local próprio da atividade
  (`Concretagem – ETA – Filtro 9 (5 m³)`). Locais iguais aparecem uma vez; local ausente não
  escreve travessão; sem quantidade não abre parênteses.
- A legenda da foto é uma função só, `legendaFoto(foto, indice)` → `Foto 3 - Concretagem`, usada
  na tela, no PDF, no WhatsApp e na planilha. Antes cada saída numerava do seu jeito e o PDF
  chegava a numerar duas vezes (`3. Foto 3 - …`). O campo de legenda livre foi removido; a
  legenda antiga de fotos já tiradas continua sendo respeitada quando não há atividade.


### Assinaturas do RDO (pedido do usuário, 05/10/2026)

Documento de **levantamento interno da empresa**: o PDF fecha com duas assinaturas — **Apontador**
(esquerda) e **Gerência** (direita, padrão Jonacir Cazelli, `GERENTE_OBRA`). Saiu a "Fiscalização /
Cliente". **Tocar no campo** (na tela do PDF) abre a escolha: assinaturas guardadas neste aparelho
(`diario_assinaturasSalvas`: `{apontador: [], gerente: []}`; o padrão do Jonacir é fixo e não some),
**desenhar nova** (quadro de assinatura com nome e "guardar na lista"), **deixar em branco** (assinar à
mão no papel) ou, na Gerência, **voltar ao padrão**; cada item da lista pode ser apagado. A escolha vale
**só para o dia** (`currentDay.assinaturas[slot]` = imagem, `''` = em branco de propósito, ausente = padrão;
`assinaturaNomes[slot]` = nome impresso). Nada é assinado automaticamente pelo apontador: ele escolhe a
cada dia. A dica "toque para assinar" é só de tela (`@media print` e `data-html2canvas-ignore`).
A imagem padrão é `assinatura-gerente.png` (PNG transparente tratado da foto enviada pelo usuário).
Limites: a lista de assinaturas é **por aparelho** (não sincroniza); o repositório é público, então a
imagem da assinatura é acessível a qualquer um — decisão do usuário ao fornecê-la. Testes em
`test_rdo_pdf.py`.

### Notas recebidas no dia no PDF (pedido do usuário, 05/10/2026)

Logo **abaixo do Kanban** e acima das assinaturas, `custosDoDiaPdf()` imprime **a planilha inteira das notas
recebidas no dia** e o **resumo**, vindos do módulo Entradas (`custos_entradas`):

1. **Planilha** item a item, em **ordem de chegada**, com as colunas do Entradas: Hora · Nº nota · Emissão ·
   Fornecedor · Categoria · Subcateg. · Descrição da nota · Un. · Qtde · Preço unit. · Total · Respons.; item
   sem preço aparece como "—" (em vermelho); linha **TOTAL LANÇADO** e, no título, quantos itens estão sem valor.
2. **Resumo de quantidade por categoria e subcategoria**: Categoria | Subcategoria | Quantidade | Cargas | NF,
   alfabético, somando por **unidade** (24 m³, 1 kit; nunca mistura unidades) e contando cargas/viagens pelo
   "mede por" da subcategoria.

"Do dia" = **recebido na obra** no dia do RDO (`data_recebimento`). Cancelados não entram. Fonte: Supabase +
`custo_entradas` local (local vale no mesmo id), como no Kanban; se o aparelho não tem as entradas, o PDF se
refaz quando o servidor responde. Dia sem entradas: a seção **não aparece**. Fonte pequena (6,3 pt) para caber:
um dia com muitas entradas pode levar o RDO a 2 folhas. (Substitui a versão "só quantidades", que durou horas.)
**WhatsApp (texto) leva o mesmo conteúdo**: bloco "📦 Notas Recebidas no Dia" depois dos Eventos do Dia e antes dos resumos acumulados — cada item numerado (hora, NF, emissão, fornecedor, categoria ▸ subcategoria — descrição, `qtde × preço = total`, responsável), "Total lançado" e o resumo de quantidade por categoria/subcategoria (`agruparEntradas()`, o mesmo agrupamento do PDF). `gerarRelatorio()` busca as entradas no servidor e atualiza a caixa do texto quando chegam; o texto copiado/enviado usa o que já estava carregado (entradas lançadas neste aparelho sempre entram). Dia sem entradas: sem bloco.
Detalhes do módulo: [[Notas/Entradas — Controle de Materiais]].

---

## Relacionado

- [[Notas/Armazenamento Local]] — chaves e a armadilha do nome da obra
- [[Notas/Regras Operacionais Críticas]]
- [[Projetos/BUILDLy Premium]]
