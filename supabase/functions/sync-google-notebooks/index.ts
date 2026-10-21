// Supabase Edge Function: sincronizar anotações do Google Notebooks
// Deploy: supabase functions deploy sync-google-notebooks

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
}

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders })
  }

  try {
    const { obraId, googleAccessToken } = await req.json()
    
    if (!obraId || !googleAccessToken) {
      return new Response(
        JSON.stringify({ error: "obraId e googleAccessToken requeridos" }),
        { status: 400, headers: corsHeaders }
      )
    }

    // 1. Buscar notebooks do Google Notebooks API
    const notebooksRes = await fetch(
      "https://notebooks.googleapis.com/v1/notebooks?parent=locations/us-central1",
      {
        headers: {
          "Authorization": `Bearer ${googleAccessToken}`,
          "Content-Type": "application/json",
        },
      }
    )

    if (!notebooksRes.ok) {
      throw new Error(`Google API error: ${notebooksRes.statusText}`)
    }

    const notebooksData = await notebooksRes.json()
    const notebooks = notebooksData.notebooks || []

    // 2. Para cada notebook, buscar anotações
    let totalNotes = 0
    for (const notebook of notebooks) {
      const notebookId = notebook.name.split("/").pop()
      
      // Buscar conteúdo do notebook
      const contentRes = await fetch(
        `https://notebooks.googleapis.com/v1/${notebook.name}/content`,
        {
          headers: {
            "Authorization": `Bearer ${googleAccessToken}`,
          },
        }
      )

      if (!contentRes.ok) continue

      const content = await contentRes.json()
      const cells = content.cells || []

      // 3. Processar células (anotações)
      for (const cell of cells) {
        if (cell.codeCell?.source || cell.textCell?.source) {
          const texto = cell.codeCell?.source?.[0] || cell.textCell?.source?.[0] || ""
          const timestamp = new Date(notebook.createTime || Date.now()).toISOString()

          // 4. Salvar no Supabase
          const supabaseUrl = Deno.env.get("SUPABASE_URL")
          const supabaseKey = Deno.env.get("SUPABASE_ANON_KEY")

          const supabase = createClient(supabaseUrl, supabaseKey)

          const { error } = await supabase
            .from("google_notebooks")
            .upsert(
              {
                obra_id: obraId,
                google_notebook_id: notebookId,
                titulo: notebook.displayName || "Sem título",
                conteudo: texto,
                data_anotacao: timestamp,
                data_sync: new Date().toISOString(),
              },
              { onConflict: "obra_id,google_notebook_id" }
            )

          if (error) console.error("Supabase error:", error)
          else totalNotes++
        }
      }
    }

    return new Response(
      JSON.stringify({
        ok: true,
        notebooks: notebooks.length,
        notes: totalNotes,
        timestamp: new Date().toISOString(),
      }),
      { status: 200, headers: corsHeaders }
    )
  } catch (error) {
    return new Response(
      JSON.stringify({ error: error.message }),
      { status: 500, headers: corsHeaders }
    )
  }
})
