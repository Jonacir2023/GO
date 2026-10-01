-- BUILDLy GO — RLS Policies: Locais de Trabalho
-- Políticas de segurança para permitir acesso anônimo à tabela rdo_locais
-- Aplicado em 1º de outubro de 2026 — Obra 1 (ivssgstckfcuiyetxdze)

alter table public.rdo_locais enable row level security;

-- Leitura pública: qualquer um pode ver locais
create policy "Leitura pública de locais" on public.rdo_locais
  for select using (true);

-- Inserção pública: qualquer um pode adicionar locais
create policy "Inserção pública de locais" on public.rdo_locais
  for insert with check (true);

-- Atualização pública: qualquer um pode editar locais
create policy "Atualização pública de locais" on public.rdo_locais
  for update using (true);

-- Deleção pública: qualquer um pode remover locais
create policy "Deleção pública de locais" on public.rdo_locais
  for delete using (true);
