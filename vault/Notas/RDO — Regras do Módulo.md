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

## Eventos do Dia (substituiu Observações do Dia, 01/10/2026)

Mesma estrutura de Atividades do Dia: catálogo em `state.eventosDia` (padrão: Chegada de material,
Chegada de equipamentos, Quebra de equipamento, Mudança de estratégia), editado em
Cadastro → 📌 Eventos; o "+" do Diário abre esse painel, onde se marca o que aconteceu e se informa
horário e detalhe; há também "+ Registrar evento avulso" para o que não está no catálogo.

- O dia guarda uma **cópia do nome** em `currentDay.eventosDia` (`{id, tipoId, tipo, detalhe, hora, custom}`).
  Remover ou renomear o tipo no cadastro **não** altera dia já registrado (regra de baixa lógica).
- O painel do Cadastro lê e grava direto em `currentDay.eventosDia` — não há rascunho separado em
  `S` como em `ativDia_<data>`.
- **Dado antigo:** o campo `observacoesDia` não tem mais tela. `eventosDoDia(day)` devolve os eventos
  do dia mais cada trecho de `observacoesDia` (separado por `*`) como evento avulso "Observação";
  PDF e WhatsApp usam essa função, então RDO antigo continua imprimindo o texto. Ao abrir um dia
  para editar (`initCurrentDay`) o texto é migrado para `eventosDia` e `observacoesDia` é zerado.
  O campo continua existindo nos dados salvos (os testes de sincronização o usam como marcador).
- **Transporte de material:** cada evento tem uma caixinha "🚛 Transporte de material" que mostra
  Placa (maiúscula), Volume (m³) e Peso (t) — no Diário, no painel do Cadastro e no avulso.
  Campos `transporte`, `placa`, `volume`, `peso` no evento (strings como digitadas, vírgula decimal
  aceita). Desmarcar esconde os campos e tira o transporte de PDF/WhatsApp, mas **não apaga** o
  digitado. `textoTransporteEvento(ev)` monta "Placa X · Volume Y m³ · Peso Z t" para os relatórios.
  As unidades m³ e t são fixas no rótulo; se a obra precisar de kg, mudar o rótulo e o texto.
- **Fornecedor e valor da carga:** campos `fornecedor` e `valorCarga` em todo evento (não dependem
  da caixinha de transporte). `valorCarga` é texto como digitado; `textoCargaEvento(ev)` acrescenta
  "R$ " se o usuário não digitou. Não há soma nem conversão numérica — se um dia for preciso totalizar
  o valor das cargas, será preciso normalizar (vírgula/ponto) antes.
- **Resumos de semana, mês e ano (PDF e WhatsApp):** `calcResumoPeriodoPDF` soma, além das atividades,
  os eventos por tipo: ocorrências, cargas (só eventos com transporte marcado), volume (m³), peso (t) e
  valor (R$, de qualquer evento com valor). Tabela "Evento / Ocorr. / Cargas / Volume / Peso / Valor" com
  linha TOTAL no PDF; bloco "Eventos acumulados" no WhatsApp. O PDF passou a ter também o RESUMO DO ANO
  (antes só semana e mês). Soma todos os RDOs do período, de todos os apontadores. Só conta
  `eventosDia` — o texto antigo de Observações do Dia não entra na soma.
- **Leitura de números:** `numeroBR()` aceita "12,5", "4.850,00", "R$ 980", "18 t". Ponto sozinho é
  milhar só no padrão 1.234 / 12.345.678; "12.5" é decimal. Se alguém digitar "1.5" para 1,5 m³ está
  certo; "1.500" vira 1500 (milhar).
- A aba Resumo (tela) ainda mostra só atividades; os eventos somados estão só nos relatórios.
- Seguem separados: Eventos de Segurança e de Meio Ambiente (têm gravidade e ação; contam como SSMA).

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

---

## Relacionado

- [[Notas/Armazenamento Local]] — chaves e a armadilha do nome da obra
- [[Notas/Regras Operacionais Críticas]]
- [[Projetos/BUILDLy Premium]]
