# Gerador de módulo

Carimba um módulo novo (levantamento/relatório) dentro deste app: página HTML,
endpoint de backend, teste automatizado, e um checklist do que fica para
fazer à mão.

```bash
python3 scripts/gerador_modulo/novo_modulo.py <id-do-modulo> "<Título>"
# exemplo:
python3 scripts/gerador_modulo/novo_modulo.py vistoria "Vistoria de Segurança"
```

## Reaproveitando num próximo app

`novo_modulo.py` não tem nenhum conhecimento deste projeto embutido no
código — só lê os arquivos em `templates/` e substitui `{{PLACEHOLDER}}`.
Toda a parte específica do BUILDLy (paleta de cores, bloco de isolamento de
`localStorage`, formato do contrato de backend) está nos `.tpl`, não na
lógica.

Para usar num app diferente:

1. Copie esta pasta inteira (`scripts/gerador_modulo/`) para o novo repositório.
2. Edite os templates para as convenções do novo projeto:
   - `templates/modulo.html.tpl` — paleta de cores, `APPS_SCRIPT_URL`, e o
     bloco de isolamento de armazenamento (se o projeto novo tiver um
     equivalente ao `BUILDLY_ESPACO_PROPRIO`)
   - `templates/endpoint.gs.tpl` — só serve se o backend novo também for
     Google Apps Script com o mesmo padrão de `getSheet`/`upsertPorCabecalho`.
     Backend diferente = reescrever este template do zero.
   - `templates/test.py.tpl` — ajuste os seletores CSS ao HTML novo
3. Ajuste as duas constantes `MARCA_GET`/`MARCA_POST` em `novo_modulo.py`
   para os pontos de inserção reais do roteador do backend novo (ou remova
   a chamada a `inserir_rotas()` se preferir sempre colar à mão).

O que **não muda**: o fluxo do `main()` (gerar HTML → gerar/inserir
endpoint → gerar teste → imprimir checklist) e as funções auxiliares
(`slug`, `pascal`, `render`, `escrever`) — são genéricas de propósito.

## Por que existe

Cada módulo deste app repete a mesma forma: HTML isolado com seu próprio
namespace de `localStorage`, endpoint de backend com upsert por ID, teste
que confere criar/listar/remover, e uma linha no vault documentando o
contrato. Escrever isso à mão a cada módulo novo é como surgiu bug
(esquecer o espaço próprio, esquecer o upsert, esquecer o teste). O gerador
força as peças a existirem juntas, sempre.
