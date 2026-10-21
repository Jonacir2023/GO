-- 015 — Notebook: busca híbrida (código exato + texto, sem acento)
-- Aplicar nas DUAS obras. Idempotente.
--
-- Por quê: a busca vetorial (notebook_buscar) falha com códigos como "GS_01" e a busca
-- notebook_buscar_fts só faz ILIKE com a frase inteira. O front (buildly-completo.html) já chama
-- notebook_buscar_hibrido(p_pergunta, k, p_modulos) antes de cair no FTS — esta função não existia.
--
-- Como pontua (similaridade 0..1):
--   • código na pergunta (token com dígito: gs_01, wtg12) casando como palavra inteira, tolerando
--     "gs_01" / "gs 01" / "gs-01": +2,0 no título, +1,0 no texto
--   • demais palavras (≥3 letras, sem stopwords): fração presente no título+texto
--   • frase inteira contida: +0,5
-- Só devolve linhas com código casado ou ≥ 50% das palavras. SECURITY INVOKER: a RLS vale.

create extension if not exists unaccent with schema extensions;

create or replace function public.notebook_buscar_hibrido(
  p_pergunta text,
  k integer default 12,
  p_modulos text[] default null
)
returns table(id uuid, modulo text, origem_id text, titulo text, texto text,
              data_ref date, similaridade double precision)
language sql
stable
security invoker
set search_path = public, extensions
as $$
  with q as (
    select unaccent(lower(btrim(coalesce(p_pergunta, '')))) as frase
  ),
  toks as (
    select distinct t
    from q, regexp_split_to_table(q.frase, '[^a-z0-9_]+') as t
    where length(t) >= 3
      and t not in ('que','para','com','uma','dos','das','por','como','qual','quais','quando',
                    'onde','sobre','tem','nos','nas','mais','ver','mostre','liste','todos','todas')
  ),
  codigos as (select t, replace(t, '_', '[ _-]?') as rx from toks where t ~ '[0-9]'),
  palavras as (select t from toks where t !~ '[0-9]'),
  n as (select (select count(*) from palavras)::float as np, (select count(*) from codigos) as nc),
  base as (
    select c.id, c.modulo, c.origem_id, c.titulo, c.texto, c.data_ref,
           unaccent(lower(coalesce(c.titulo, ''))) as ti,
           unaccent(lower(coalesce(c.texto, '')))  as tx
    from public.notebook_chunks c
    join public.notebook_sources s on s.codigo = c.modulo and s.ativo
    where (p_modulos is null or c.modulo = any(p_modulos))
  ),
  pont as (
    select b.id, b.modulo, b.origem_id, b.titulo, b.texto, b.data_ref,
      (select count(*) from codigos cd where b.ti ~ ('\m' || cd.rx || '\M')) as cod_ti,
      (select count(*) from codigos cd where b.tx ~ ('\m' || cd.rx || '\M')) as cod_tx,
      (select count(*) from palavras p where position(p.t in b.ti || ' ' || b.tx) > 0) as pal,
      (select position((select frase from q) in b.ti || ' ' || b.tx) > 0
         and length((select frase from q)) >= 3) as frase_ok
    from base b
  )
  select p.id, p.modulo, p.origem_id, p.titulo, p.texto, p.data_ref,
         least(1.0, (
           2.0 * p.cod_ti + 1.0 * p.cod_tx
           + case when n.np > 0 then p.pal / n.np else 0 end
           + case when p.frase_ok then 0.5 else 0 end
         ) / (case when n.nc > 0 then 3.0 else 1.5 end))::double precision as similaridade
  from pont p, n
  where (n.nc > 0 and (p.cod_ti + p.cod_tx) > 0)
     or (n.np > 0 and p.pal / n.np >= 0.5)
  order by similaridade desc, p.id
  limit least(k, 30);
$$;

revoke all on function public.notebook_buscar_hibrido(text, integer, text[]) from public, anon;
grant execute on function public.notebook_buscar_hibrido(text, integer, text[]) to authenticated;
