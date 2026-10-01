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
