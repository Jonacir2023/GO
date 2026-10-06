# Testes do BUILDLy

Quinze suítes. Cada uma abre o app num navegador sem tela (Playwright + Chromium) e confere uma
regra que **já custou caro alguma vez** — não são testes de cobertura, são cercas em cima de
buracos conhecidos.

```bash
python3 tests/executar.py          # tudo
python3 tests/executar.py rdo      # só as que têm "rdo" no nome
```

O endereço do app vem de `$BUILDLY_URL`, que o hook de sessão define. Sem ele, cai em
`http://localhost:8795`.

| Suíte | O que protege |
|---|---|
| `test_rdo_regras_do_dia` | lista fechada de locais, responsável obrigatório, os dois locais na atividade, legenda única de foto |
| `test_rdo_baixa_logica` | item removido continua nos dias anteriores à baixa; recadastro reativa em vez de duplicar |
| `test_rdo_sincronizacao` | versão antiga da nuvem não sobrescreve trabalho local mais recente; cadastro nunca perde item |
| `test_rdo_lixeira_cadastro` | o 🗑️ do cadastro de colaboradores remove de verdade da tela |
| `test_espaco_proprio` | o BUILDLy não lê nem apaga o `localStorage` de outro app da mesma origem |
| `test_shell_e_iframes` | o app dentro do iframe herda o espaço próprio e o robô aparece |
| `test_pauta_administracao` | a tela de token do GitHub não voltou |
| `test_login` | sem sessão o app não abre; admin vê tudo, portaria só Entradas, pendente espera; páginas avulsas voltam ao login |
| `test_planejamento_atividades` | atividades lidas em lotes de 1000; situação pela data local; filtros, busca por WTG, KPIs; % real grava início/fim real; restrição grava com `obra_id` |

## Ao escrever uma suíte nova

- Abra o navegador com `contexto(browser, ...)` (de `tests/_login.py`), não `browser.new_context(...)`: ele já entra logado como administrador. Só o `test_login` abre sem sessão.
- Intercepte `script.google.com` com `page.route()`. Teste não fala com o Google.
- Confira o **comportamento**, não o nome da função. Suíte presa a nome quebra em refatoração
  e não pega bug nenhum.
- Escreva a mensagem do `check()` como a regra em português — é o que aparece quando falha.
