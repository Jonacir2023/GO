---
criado: 2026-10-06
atualizado: 2026-10-06
tags: [decisão, login, auth, supabase, rls]
---

# Login e perfis de acesso (2026-10-06)

**Decisão do usuário (06/10/2026):** o app passa a exigir login. Método **e-mail + senha**
(Supabase Auth). O usuário é o **administrador** e vê tudo; por ora o único outro papel é
**portaria**, que só vê **Entradas**. As permissões finas por módulo serão definidas depois de
os apps estarem prontos. **Cada pessoa acessa só as obras que o administrador liberar** (Obra 1,
Obra 2 ou as duas). O link público de envio de Pauta (`envio-pauta.html`) **passa a exigir login**.

## Como funciona

- **Duas obras = dois projetos Supabase = dois cadastros de usuários.** A pessoa tem a **mesma
  conta (e-mail e senha) nas duas**; "Criar acesso" e "Entrar" falam com as duas ao mesmo tempo.
  Quem decide onde ela entra é o `papel` em `perfis` de cada obra.
- Tabelas (por obra): `papeis` (admin `{*}`, portaria `{custos}`, pendente `{}`), `perfis`
  (`user_id`, e-mail, nome, `papel` — nasce **pendente** pelo gatilho `trg_novo_usuario`).
  Funções `papel_atual()`, `eh_admin()`, `pode_modulo(m)`. Migração: `sql/009_auth_perfis.sql`.
- Módulo `custos` é o id interno da aba **Entradas** (o nome de tela mudou, o id não).
- **Casca** (`buildly-completo.html`): tela `#login` (Entrar / Criar acesso / Esqueci a senha);
  quem entra sem papel vê "Aguardando liberação"; esconde cartões, Favoritos, Relatórios, Mais, sino
  e robô de IA conforme o papel; `switchTab` recusa módulo sem permissão; Perfil tem Trocar senha,
  Sair e (admin) **Usuários e acessos** (papel por obra por pessoa).
- **Páginas avulsas** (`custos.html`, `envio-pauta.html`…): `B3Auth.guardar()` roda sozinho em
  `supabase-config.js`; sem sessão, redireciona para `buildly-completo.html?next=<página>` e, depois
  do login, volta. Só aceita destino `^[A-Za-z0-9_.-]+\.html(\?.*)?$` (nada de URL externa).
- Offline: o perfil fica em cache (`b3_auth`); a portaria continua lançando sem rede.

## Duas fases — e por que

1. **Fase 1 (feita):** só a tela. Todas as tabelas de dados continuam com a política aberta
   ("acesso do app"). **Isto NÃO protege os dados** — quem souber a chave publicável ainda lê o banco.
   Fez-se assim para não trancar o app antes de o administrador conseguir entrar.
2. **Fase 2 (APLICADA em 06/10/2026 nas duas obras, `sql/010_auth_rls.sql`):** as políticas abertas viraram
   `to authenticated using ((select public.pode_modulo('<módulo>')))` — `custos_*`→custos, `pauta_*`→pauta,
   `checkin_*`→checkin, `rdo_*`→rdo, `obra_config` (lê qualquer papel liberado, grava `obra`) etc.
   Leituras entre módulos: rdo lê `checkin_assuntos` e `custos_*`; financeiro lê `rdo_snapshot` e grava
   `custos_notas_fiscais`/`medicao_contratos`; pauta e checkin compartilham `pauta_assuntos`/`checkin_assuntos`.
   Reversão: `sql/010_rollback_rls.sql`. **Agora o banco só responde a quem tem login e papel.**
   Testado nas duas obras com papéis simulados (anon, admin, portaria, pendente): anon lê 0 linhas; admin lê e grava
   tudo; portaria lê/escreve só `custos_*`, lê `obra_config` e não grava; pendente não lê nada.

## Armadilha: `DROP POLICY` trava neste Supabase
O comando não termina (nem com `lock_timeout`; sem bloqueio visível em `pg_locks`/`pg_stat_activity`) e estoura os 60 s do MCP.
`CREATE POLICY` e `ALTER POLICY` (inclusive `rename to`) funcionam na hora. Por isso a Fase 2 usa só ALTER + CREATE, e a
política duplicada da Obra 1 não pôde ser removida. Para testar papéis: `begin; update public.perfis set papel='x' ...;
set local role authenticated; select set_config('request.jwt.claims','{"sub":"<uid>","role":"authenticated"}',true); select ...; rollback;`
numa chamada só (um `DO` com `raise exception` também serve; `DO` com `update` travou).

## Limitações conhecidas

- **Senha em dois lugares.** Trocar a senha no app atualiza as duas obras. "Esqueci a senha" dispara
  **dois e-mails** (um por projeto): abrir o link de cada um. Se só um for usado, o login entra numa obra
  e avisa em qual a senha não confere.
- Configuração no painel do Supabase (sem ferramenta para isso), **nas duas obras**: Authentication →
  desligar "Confirm email" (ou aceitar o e-mail de confirmação) e pôr Site URL / Redirect URL em
  `https://jonacir2023.github.io/GO/`.
- Página avulsa aberta direto não checa o *módulo* do papel, só a sessão; quem protege é o RLS (Fase 2).

## Armadilhas

- `B3_CASCA` precisa estar `true` na casca, senão `guardar()` redireciona a própria casca em laço.
- O link de e-mail volta com `#access_token=…`; a casca guarda o hash e o apaga da URL **antes** de
  qualquer cliente Supabase ser criado, senão o supabase-js consome o token e troca a sessão.
- Testes: `tests/_login.py` grava uma sessão de mentira nas duas obras; as suítes usam
  `contexto(browser, ...)` em vez de `browser.new_context(...)`. O login em si é `tests/test_login.py`.
