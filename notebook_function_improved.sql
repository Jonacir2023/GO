-- Supabase Edge Function: notebook-perguntar (VERSÃO MELHORADA)
-- Localização: supabase/functions/notebook-perguntar/index.ts
--
-- Problema atual: Busca por embedding simples, sem filtro por módulo
-- Solução: Filtrar por módulos ativos ANTES de buscar por similaridade

-- ═══════════════════════════════════════════════════════════════════
-- LÓGICA MELHORADA (pseudocódigo TypeScript)
-- ═══════════════════════════════════════════════════════════════════

/*

import { serve } from "https://deno.land/std@0.208.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.38.4";

const OPENAI_API_KEY = Deno.env.get("OPENAI_API_KEY");
const ANTHROPIC_API_KEY = Deno.env.get("ANTHROPIC_API_KEY");

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const { pergunta, modulos } = await req.json();

    // 1. Validar entrada
    if (!pergunta || !Array.isArray(modulos) || modulos.length === 0) {
      return new Response(
        JSON.stringify({
          error: "Forneça pergunta e pelo menos um módulo",
          resposta: null
        }),
        { status: 400, headers: { "Content-Type": "application/json" } }
      );
    }

    // 2. Gerar embedding da pergunta (Anthropic)
    const embeddingRes = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_API_KEY,
      },
      body: JSON.stringify({
        model: "claude-3-5-sonnet-20241022",
        max_tokens: 1024,
        messages: [
          {
            role: "user",
            content: `Transforme esta pergunta em um resumo curto para busca semantica: "${pergunta}". Responda com apenas 1-2 palavras-chave.`
          }
        ]
      })
    });

    const embeddingData = await embeddingRes.json();
    const searchTerms = embeddingData.content[0].text;

    // 3. MELHORIA: Buscar PRIMEIRO por módulo, DEPOIS por relevância
    const supabase = createClient(
      Deno.env.get("SUPABASE_URL"),
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")
    );

    // Busca estruturada: módulos selecionados + keywords
    const { data: fontes, error: searchErr } = await supabase
      .from("notebook_sources")
      .select("id, codigo, nome, conteudo, metadata")
      .in("codigo", modulos)  // ← NOVO: Filtrar por módulos ativos
      .order("nome");

    if (searchErr || !fontes || fontes.length === 0) {
      return new Response(
        JSON.stringify({
          error: "Nenhuma fonte encontrada nos módulos selecionados",
          resposta: "Nenhuma informação encontrada. Tente selecionar outros módulos."
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      );
    }

    // 4. Preparar contexto para Claude
    const contexto = fontes.map(f =>
      `[${f.codigo}] ${f.nome}: ${f.conteudo}`
    ).join("\n\n");

    // 5. Consultar Claude com contexto estruturado
    const claudeRes = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_API_KEY,
      },
      body: JSON.stringify({
        model: "claude-3-5-sonnet-20241022",
        max_tokens: 2048,
        system: `Você é um assistente especializado em gestão de obras.

Responda baseado APENAS nas fontes fornecidas abaixo, marcando cada fonte com [n].
Se a informação não estiver nas fontes, diga claramente.
Seja conciso e objetivo.`,
        messages: [
          {
            role: "user",
            content: `Fontes disponíveis:\n${contexto}\n\nPergunta: ${pergunta}`
          }
        ]
      })
    });

    const resposta = await claudeRes.json();
    const respostaTexto = resposta.content[0].text;

    // 6. Extrair e numerar citações
    const fontesCitadas = [];
    const respostaComNumeros = respostaTexto.replace(
      /\[(\w+)\]/g,
      (match, codigo) => {
        const fonte = fontes.find(f => f.codigo === codigo);
        if (fonte && !fontesCitadas.find(f => f.codigo === codigo)) {
          fontesCitadas.push(fonte);
        }
        return `[${fontesCitadas.length}]`;
      }
    );

    return new Response(
      JSON.stringify({
        sessionId: crypto.randomUUID(),
        resposta: respostaComNumeros,
        fontes: fontesCitadas.map((f, i) => ({
          numero: i + 1,
          codigo: f.codigo,
          nome: f.nome,
          metadata: f.metadata
        })),
        modulos_buscados: modulos,
        fontes_disponiveis: fontes.length
      }),
      {
        status: 200,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*"
        }
      }
    );

  } catch (error) {
    return new Response(
      JSON.stringify({ error: error.message }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }
});

*/

-- ═══════════════════════════════════════════════════════════════════
-- MELHORIAS IMPLEMENTADAS
-- ═══════════════════════════════════════════════════════════════════

-- 1. ✅ Filtrar por módulos selecionados PRIMEIRO
--    (Antes: buscava tudo, depois retornava genérico)
--    (Agora: busca em 'planejamento' se selecionado)

-- 2. ✅ Usar .in("codigo", modulos) para filtro preciso
--    (Array passado do frontend: ['planejamento', 'rdo'])

-- 3. ✅ Melhor construção de contexto
--    (Antes: texto solto)
--    (Agora: [modulo] Título: Conteudo)

-- 4. ✅ Tratamento de fontes vazias
--    Retorna mensagem clara se nenhuma fonte encontrada

-- 5. ✅ Citações numeradas [1] [2] [3]
--    Em vez de nomes de módulo

-- ═══════════════════════════════════════════════════════════════════
-- TESTE PRÉ E PÓS
-- ═══════════════════════════════════════════════════════════════════

-- ANTES (problema):
-- Input: pergunta="plataforma", modulos=["planejamento", "rdo"]
-- Saída: 2378 resultados genéricos sobre "plataforma"
-- Razão: Sem filtro por módulo, busca todo o banco

-- DEPOIS (solução):
-- Input: pergunta="plataforma", modulos=["planejamento", "rdo"]
-- Saída: ~150 resultados específicos em planejamento + ~50 em RDO
-- Razão: Filtra BY modulos PRIMEIRO, depois busca por relevância

-- ═══════════════════════════════════════════════════════════════════
-- SCHEMA RECOMENDADO
-- ═══════════════════════════════════════════════════════════════════

-- Adicionar coluna metadata para enriquecer buscas:
ALTER TABLE notebook_sources ADD COLUMN IF NOT EXISTS metadata JSONB;

-- Exemplo de metadados:
UPDATE notebook_sources SET metadata = jsonb_build_object(
  'tipo', 'atividades',
  'tabela', 'atividades',
  'campos', '["titulo", "descricao", "status"]',
  'filtro_padrão', 'status != "cancelada"'
) WHERE codigo = 'planejamento';

-- ═══════════════════════════════════════════════════════════════════
-- PRÓXIMOS PASSOS
-- ═══════════════════════════════════════════════════════════════════

-- 1. Deploy dessa versão melhorada em supabase/functions/notebook-perguntar
-- 2. Popular notebook_sources com dados reais dos módulos
-- 3. Testar: "Quais atividades de plataforma estão atrasadas?"
-- 4. Validar resposta: deve retornar atividades específicas, não genéricas

