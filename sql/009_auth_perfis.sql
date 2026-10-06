-- BUILDLy — Migration 009: LOGIN (Supabase Auth) — perfis e papéis. FASE 1 (não restritiva).
-- Decisão do usuário (06/10/2026): e-mail + senha; ele é o administrador; por ora administrador vê tudo e
-- portaria só vê Entradas (módulo de id interno 'custos'); cada pessoa acessa só as obras que o admin liberar;
-- o link público de envio da Pauta passa a exigir login.
-- Aplicar nas DUAS obras. Esta fase só CRIA tabelas/funções/gatilho; as políticas abertas das tabelas de
-- dados continuam valendo até a FASE 2 (sql/010_auth_rls.sql), que fecha o banco só para quem tem login.

create table if not exists public.papeis (
  papel text primary key,
  rotulo text not null,
  modulos text[] not null default '{}'      -- ids internos dos módulos; '*' = todos
);
insert into public.papeis (papel, rotulo, modulos) values
  ('admin',    'Administrador', '{*}'),
  ('portaria', 'Portaria',      '{custos}'),
  ('pendente', 'Sem acesso',    '{}')
on conflict (papel) do nothing;

create table if not exists public.perfis (
  user_id uuid primary key references auth.users(id) on delete cascade,
  email text,
  nome text,
  papel text not null default 'pendente' references public.papeis(papel),
  criado_em timestamptz not null default now(),
  atualizado_em timestamptz not null default now()
);
create index if not exists idx_perfis_papel on public.perfis(papel);

-- Funções usadas pelas políticas (security definer: leem perfis sem depender das políticas dele)
create or replace function public.papel_atual() returns text
  language sql stable security definer set search_path = public as
$$ select papel from public.perfis where user_id = auth.uid() $$;

create or replace function public.eh_admin() returns boolean
  language sql stable security definer set search_path = public as
$$ select coalesce((select papel = 'admin' from public.perfis where user_id = auth.uid()), false) $$;

create or replace function public.pode_modulo(m text) returns boolean
  language sql stable security definer set search_path = public as
$$ select exists (
     select 1 from public.perfis p join public.papeis r on r.papel = p.papel
      where p.user_id = auth.uid() and ('*' = any(r.modulos) or m = any(r.modulos))) $$;

-- Todo cadastro novo nasce "pendente" (sem acesso) até o administrador liberar
create or replace function public.novo_usuario() returns trigger
  language plpgsql security definer set search_path = public as
$$ begin
  insert into public.perfis (user_id, email, nome, papel)
  values (new.id, new.email, coalesce(new.raw_user_meta_data->>'nome', ''), 'pendente')
  on conflict (user_id) do nothing;
  return new;
end $$;
drop trigger if exists trg_novo_usuario on auth.users;
create trigger trg_novo_usuario after insert on auth.users for each row execute function public.novo_usuario();

alter table public.papeis enable row level security;
alter table public.perfis enable row level security;

drop policy if exists "papeis leitura" on public.papeis;
create policy "papeis leitura" on public.papeis for select to authenticated using (true);

drop policy if exists "perfis leitura" on public.perfis;
drop policy if exists "perfis atualizacao admin" on public.perfis;
drop policy if exists "perfis exclusao admin" on public.perfis;
create policy "perfis leitura" on public.perfis for select to authenticated using (user_id = auth.uid() or public.eh_admin());
create policy "perfis atualizacao admin" on public.perfis for update to authenticated using (public.eh_admin()) with check (public.eh_admin());
create policy "perfis exclusao admin" on public.perfis for delete to authenticated using (public.eh_admin());
