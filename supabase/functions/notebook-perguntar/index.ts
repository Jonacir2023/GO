import { createClient } from 'jsr:@supabase/supabase-js@2';

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
};
const K_TRECHOS = 12;
const MAX_CONTEXTO = 40_000;
// Fusão por rank (RRF). A busca híbrida acerta código exato (GS_01, item 1796) e termo técnico,
// onde o embedding gte-small devolve trechos quase aleatórios (similaridade plana de 0,80 a 0,86).
const RRF_K = 60;
const PESO_HIBRIDA = 2;
const PESO_VETOR = 1;

const json = (obj: unknown, status = 200) =>
  new Response(JSON.stringify(obj), { status, headers: { ...CORS, 'Content-Type': 'application/json' } });

type Trecho = Record<string, any>;

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: CORS });
  if (req.method !== 'POST') return json({ erro: 'método não permitido' }, 405);
  const inicio = Date.now();

  try {
    const auth = req.headers.get('Authorization') ?? '';
    if (!auth) return json({ erro: 'não autenticado' }, 401);

    const { pergunta, sessionId, modulos } = await req.json();
    if (typeof pergunta !== 'string' || !pergunta.trim()) return json({ erro: 'pergunta ausente' }, 400);

    // Fontes ativas escolhidas no Notebook. Lista vazia = nenhuma fonte = erro (não buscar em tudo)
    let modulosFiltro: string[] | null = null;
    if (Array.isArray(modulos)) {
      modulosFiltro = modulos.filter((m: unknown) => typeof m === 'string' && m.length > 0);
      if (!modulosFiltro.length) return json({ erro: 'nenhuma fonte ativa' }, 400);
    }

    // Cliente com o JWT do usuário: as policies (RLS) e pode_modulo() valem para a busca
    const sb = createClient(Deno.env.get('SUPABASE_URL')!, Deno.env.get('SUPABASE_ANON_KEY')!, {
      global: { headers: { Authorization: auth } },
      auth: { persistSession: false },
    });
    const { data: { user }, error: erroUser } = await sb.auth.getUser();
    if (erroUser || !user) return json({ erro: 'não autenticado' }, 401);

    // Embedding da pergunta com o modelo gte-small (roda dentro do Supabase)
    const session = new Supabase.ai.Session('gte-small');
    const emb = await session.run(pergunta, { mean_pool: true, normalize: true });

    // Duas buscas em paralelo: vetorial (sentido) e híbrida (código exato + palavras)
    const [vet, hib] = await Promise.all([
      sb.rpc('notebook_buscar', { q: emb, k: K_TRECHOS, p_modulos: modulosFiltro }),
      sb.rpc('notebook_buscar_hibrido', { p_pergunta: pergunta, k: K_TRECHOS, p_modulos: modulosFiltro }),
    ]);
    // A híbrida pode não existir numa obra sem a migração 015: segue só com o vetor.
    if (vet.error && hib.error) return json({ erro: 'falha na busca' }, 500);

    const pontos = new Map<string, { t: Trecho; score: number; hib: boolean }>();
    const somar = (lista: Trecho[] | null, peso: number, ehHib: boolean) => {
      (lista ?? []).forEach((t, i) => {
        const atual = pontos.get(t.id) ?? { t, score: 0, hib: false };
        atual.score += peso / (RRF_K + i + 1);
        atual.hib = atual.hib || ehHib;
        pontos.set(t.id, atual);
      });
    };
    somar(hib.error ? null : hib.data, PESO_HIBRIDA, true);
    somar(vet.error ? null : vet.data, PESO_VETOR, false);
    const achados = [...pontos.values()].sort((a, b) => b.score - a.score).slice(0, K_TRECHOS);

    // Monta o contexto numerado para o modelo citar [1], [2]...
    const fontes: Array<Record<string, unknown>> = [];
    let contexto = '';
    for (const { t } of achados) {
      const n = fontes.length + 1;
      const bloco = `[${n}] ${t.titulo} (${t.modulo}${t.data_ref ? ', ' + t.data_ref : ''})\n${t.texto}\n\n`;
      if (contexto.length + bloco.length > MAX_CONTEXTO) break;
      contexto += bloco;
      fontes.push({ n, id: t.id, modulo: t.modulo, titulo: t.titulo, data_ref: t.data_ref, similaridade: t.similaridade });
    }

    let resposta: string;
    if (!fontes.length) {
      resposta = 'Não encontrei dados sobre isso nas fontes ativas desta obra.';
    } else {
      const apiKey = Deno.env.get('ANTHROPIC_API_KEY');
      if (!apiKey) return json({ erro: 'ANTHROPIC_API_KEY não configurada no Supabase' }, 500);

      const system =
        'Você é o assistente do BUILDLy, app de gestão de obras. Responda em português do Brasil, ' +
        'SOMENTE com base nos trechos numerados fornecidos. Cite a fonte logo após cada afirmação, no formato [n]. ' +
        'Se a resposta não estiver nos trechos, diga que não encontrou. Nunca invente informações.';

      const r = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: { 'x-api-key': apiKey, 'anthropic-version': '2023-06-01', 'content-type': 'application/json' },
        body: JSON.stringify({
          model: 'claude-haiku-4-5-20251001',
          max_tokens: 1024,
          system,
          messages: [{ role: 'user', content: `Trechos:\n${contexto}\nPergunta: ${pergunta}` }],
        }),
      });
      if (!r.ok) return json({ erro: 'falha ao consultar o modelo', status: r.status }, 502);
      const j = await r.json();
      resposta = (j.content ?? []).filter((c: { type: string }) => c.type === 'text').map((c: { text: string }) => c.text).join('\n');
    }

    // Histórico da conversa e log automático de cada consulta
    let sid: string | null = typeof sessionId === 'string' ? sessionId : null;
    if (!sid) {
      const { data: s } = await sb.from('notebook_sessions').insert({ user_id: user.id, title: pergunta.slice(0, 80) }).select('id').single();
      sid = s?.id ?? null;
    }
    if (sid) {
      await sb.from('notebook_messages').insert([
        { session_id: sid, sender_role: 'user', content: pergunta },
        { session_id: sid, sender_role: 'assistant', content: resposta, sources_referenced: fontes },
      ]);
    }
    const { error: erroLog } = await sb.from('notebook_query_logs').insert({
      session_id: sid, user_id: user.id, question: pergunta, answer: resposta,
      sources_used: fontes, response_time_ms: Date.now() - inicio,
    });

    return json({ resposta, fontes, sessionId: sid, logSalvo: !erroLog, busca: hib.error ? 'vetorial' : 'hibrida+vetorial' });
  } catch (_e) {
    return json({ erro: 'erro interno' }, 500);
  }
});
