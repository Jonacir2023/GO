-- BUILDLy GO — Migration: Planejamento (Cronogramas, Atividades, Restrições)

create table if not exists public.planejamento_cronogramas (
  id uuid primary key default gen_random_uuid(),
  obra_id uuid not null,
  nome text not null,
  tipo text not null default 'controle',
  data_status date,
  documento_base_id uuid,
  ativo boolean not null default true,
  criado_em timestamptz not null default now(),
  atualizado_em timestamptz not null default now(),

  constraint plan_crono_tipo_check
    check (tipo in ('baseline','controle','reprogramacao')),

  constraint planejamento_cronogramas_id_obra_uq
    unique (id, obra_id)
);

create table if not exists public.planejamento_atividades (
  id uuid primary key default gen_random_uuid(),
  obra_id uuid not null,
  cronograma_id uuid not null,
  eap_id uuid,
  codigo text,
  nome text not null,
  inicio_planejado date,
  fim_planejado date,
  inicio_real date,
  fim_real date,
  percentual_planejado numeric not null default 0,
  percentual_real numeric not null default 0,
  critica boolean not null default false,
  responsavel text,
  criado_em timestamptz not null default now(),
  atualizado_em timestamptz not null default now(),

  constraint plan_atividade_cronograma_obra_fkey
    foreign key (cronograma_id, obra_id)
    references public.planejamento_cronogramas(id, obra_id) on delete restrict,

  constraint plan_atividade_eap_obra_fkey
    foreign key (eap_id, obra_id)
    references public.eap_itens(id, obra_id) on delete restrict,

  constraint plan_pct_check
    check (percentual_planejado between 0 and 100 and percentual_real between 0 and 100),

  constraint planejamento_atividades_id_obra_uq
    unique (id, obra_id)
);

create table if not exists public.planejamento_restricoes (
  id uuid primary key default gen_random_uuid(),
  obra_id uuid not null,
  eap_id uuid,
  descricao text not null,
  responsavel text,
  prazo date,
  status text not null default 'aberta',
  criticidade text not null default 'media',
  criado_em timestamptz not null default now(),
  atualizado_em timestamptz not null default now(),

  constraint restr_status_check
    check (status in ('aberta','resolvida','cancelada')),

  constraint restr_crit_check
    check (criticidade in ('baixa','media','alta','critica')),

  constraint restr_eap_obra_fkey
    foreign key (eap_id, obra_id)
    references public.eap_itens(id, obra_id) on delete restrict,

  constraint planejamento_restricoes_id_obra_uq
    unique (id, obra_id)
);

create index if not exists idx_planej_crono_obra on public.planejamento_cronogramas(obra_id);
create index if not exists idx_planej_ativ_cronograma on public.planejamento_atividades(cronograma_id);
create index if not exists idx_planej_ativ_eap on public.planejamento_atividades(eap_id);
create index if not exists idx_planej_rest_obra on public.planejamento_restricoes(obra_id);
create index if not exists idx_planej_rest_eap on public.planejamento_restricoes(eap_id);
