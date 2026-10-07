"""Planejamento: aba Atividades (previsto × real) e aba Restrições.

Simula o supabase-js no navegador (sem rede) com um banco em memória e confere:
- lê as atividades em lotes de 1000 (o Supabase corta em 1000 por consulta);
- situação calculada pela data LOCAL (concluída / atrasada / em andamento / planejada);
- filtros (atrasadas, hoje, busca por WTG) e paginação "Mostrar mais";
- KPIs de avanço físico ponderado pela duração;
- gravar % real atualiza o banco, marca início real e, em 100%, fim real;
- restrição nova é gravada com obra_id da obra ativa e o status muda pela lista.
"""
import json
import os
from playwright.sync_api import sync_playwright
from _login import contexto

BASE = os.environ.get("BUILDLY_URL", "http://localhost:8795")
falhas = []


def check(cond, msg):
    print(("  OK    " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


# 1.205 atividades (passa de 1000 → obriga a leitura em lotes)
ativs = []
for i in range(1, 1206):
    if i == 1:
        a = {"inicio_planejado": "2026-10-01", "fim_planejado": "2026-10-03", "percentual_real": 0}    # atrasada
    elif i == 2:
        a = {"inicio_planejado": "2026-10-01", "fim_planejado": "2026-10-10", "percentual_real": 40}   # em andamento
    elif i == 3:
        a = {"inicio_planejado": "2026-09-20", "fim_planejado": "2026-09-30", "percentual_real": 100}  # concluída
    else:
        a = {"inicio_planejado": "2027-01-04", "fim_planejado": "2027-01-10", "percentual_real": 0}    # planejada
    a.update({"id": f"a{i}", "obra_id": "obra1", "cronograma_id": "c1", "codigo": str(i),
              "nome": f"Atividade {i}" + (" - GS_27" if i == 2 else ""), "eap_id": "e1",
              "inicio_real": None, "fim_real": None, "critica": False})
    ativs.append(a)

BANCO = {
    "planejamento_cronogramas": [{"id": "c1", "obra_id": "obra1", "nome": "Rev. 05 (linha de base)",
                                  "tipo": "baseline", "data_status": "2026-10-06", "criado_em": "2026-10-06"}],
    "planejamento_atividades": ativs,
    "eap_itens": [{"id": "e1", "obra_id": "obra1", "nome": "FUNDAÇÃO DOS AEROGERADORES"}],
    "planejamento_restricoes": [],
}

FAKE = """
window.__banco = %s; window.__consultas = [];
(function(){
  function Q(t){ this.t=t; this.f=[]; this.op='select'; this.r=null; this.ord=[]; this.dados=null; }
  Q.prototype.select=function(){ return this; };
  Q.prototype.eq=function(c,v){ this.f.push([c,v]); return this; };
  Q.prototype.order=function(c,o){ this.ord.push([c,(o&&o.ascending===false)?-1:1]); return this; };
  Q.prototype.range=function(a,b){ this.r=[a,b]; return this; };
  Q.prototype.maybeSingle=function(){ this.um=true; return this; };
  Q.prototype.insert=function(l){ this.op='insert'; this.dados=l; return this; };
  Q.prototype.update=function(d){ this.op='update'; this.dados=d; return this; };
  Q.prototype.then=function(ok,err){
    var tab = window.__banco[this.t] || (window.__banco[this.t]=[]), self=this;
    var casa = function(x){ return self.f.every(function(f){ return x[f[0]]===f[1]; }); };
    window.__consultas.push({t:this.t, op:this.op, r:this.r});
    var res;
    if (this.op==='insert') { this.dados.forEach(function(l,i){ l.id = l.id || ('n'+Date.now()+i); l.status=l.status||'aberta'; tab.push(l); }); res={data:null,error:null}; }
    else if (this.op==='update') { tab.filter(casa).forEach(function(x){ Object.assign(x,self.dados); }); res={data:null,error:null}; }
    else {
      var d = tab.filter(casa).map(function(x){ return Object.assign({},x); });
      this.ord.forEach(function(o){ d.sort(function(a,b){ return (a[o[0]]>b[o[0]]?1:a[o[0]]<b[o[0]]?-1:0)*o[1]; }); });
      if (this.r) d = d.slice(this.r[0], this.r[1]+1); else d = d.slice(0,1000);
      res = {data: this.um ? (d[0]||null) : d, error:null};
    }
    return Promise.resolve(res).then(ok,err);
  };
  window.supabase = { createClient: function(){ return { from:function(t){ return new Q(t); },
    auth:{ getSession:function(){return Promise.resolve({data:{session:null}});}, onAuthStateChange:function(){return {data:{subscription:{unsubscribe:function(){}}}};} } }; } };
})();
""" % json.dumps(BANCO)

with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    ctx = contexto(b, viewport={"width": 390, "height": 844}, timezone_id="America/Sao_Paulo")
    page = ctx.new_page()
    erros = []
    page.on("pageerror", lambda e: erros.append(str(e)))
    page.on("dialog", lambda d: d.dismiss())
    page.route("**/cdn.jsdelivr.net/**", lambda r: r.fulfill(status=200, content_type="text/javascript", body=""))
    page.add_init_script(FAKE)
    # 06/10/2026 21:00 em Brasília (= 07/10 00:00 UTC): o "hoje" do app tem que ser 06/10
    page.clock.install(time="2026-10-07T00:00:00Z")
    page.goto(f"{BASE}/planejamento.html")
    page.wait_for_timeout(1500)
    page.evaluate("document.querySelectorAll('.tab')[2].click()")
    page.wait_for_timeout(600)

    check(page.evaluate("hojeLocal()") == "2026-10-06", "hoje é a data local (06/10), não a UTC (07/10)")
    lotes = page.evaluate("window.__consultas.filter(c => c.t==='planejamento_atividades').map(c => c.r)")
    check([0, 999] in lotes and [1000, 1999] in lotes, f"atividades lidas em lotes de 1000: {lotes}")
    check(page.evaluate("_ativs.length") == 1205, "as 1.205 atividades chegaram (não parou em 1000)")
    check(page.locator("#atividades-tbody tr").count() == 200, "mostra as primeiras 200 linhas")
    cods = page.evaluate("Array.from(document.querySelectorAll('#atividades-tbody tr td:first-child')).slice(0,6).map(t => t.textContent)")
    check(cods[:3] == ["3", "1", "2"] and cods[3:6] == ["4", "5", "6"], f"ordem por início e ID numérico: {cods}")
    check(page.locator("#ativ-mais").is_visible(), "botão 'Mostrar mais' aparece")
    page.click("#ativ-mais")
    check(page.locator("#atividades-tbody tr").count() == 400, "'Mostrar mais' acrescenta mais 200")

    kpis = page.inner_text("#ativ-kpis")
    check("1205" in kpis and "atrasadas" in kpis, "KPIs mostram total e atrasadas")

    page.select_option("#ativ-filtro", "atrasadas")
    check(page.locator("#atividades-tbody tr").count() == 1 and "Atividade 1" in page.inner_text("#atividades-tbody"),
          "filtro Atrasadas mostra só a atividade vencida sem 100%")
    page.select_option("#ativ-filtro", "hoje")
    check(page.locator("#atividades-tbody tr").count() == 1, "filtro Em andamento hoje")
    page.select_option("#ativ-filtro", "todas")
    page.fill("#ativ-busca", "gs_27")
    check(page.locator("#atividades-tbody tr").count() == 1, "busca por WTG (gs_27) acha a atividade")
    check("Em andamento" in page.inner_text("#atividades-tbody"), "situação 'Em andamento' calculada")

    inp = page.locator("#atividades-tbody .pct-input").first
    inp.fill("100")
    inp.dispatch_event("change")
    page.wait_for_timeout(300)
    a2 = page.evaluate("window.__banco.planejamento_atividades.find(a => a.id==='a2')")
    check(a2["percentual_real"] == 100, "% real gravado no banco")
    check(a2["fim_real"] == "2026-10-06", "100% marca fim real com a data local")

    page.fill("#ativ-busca", "")
    page.select_option("#ativ-filtro", "atrasadas")
    inp1 = page.locator("#atividades-tbody .pct-input").first
    inp1.fill("150")
    inp1.dispatch_event("change")
    page.wait_for_timeout(300)
    a1 = page.evaluate("window.__banco.planejamento_atividades.find(a => a.id==='a1')")
    check(a1["percentual_real"] == 100, "% acima de 100 é limitado a 100")

    # ---- Restrições ----
    page.evaluate("document.querySelectorAll('.tab')[3].click()")
    page.fill("#restr-descricao", "Licença da central de concreto")
    page.select_option("#restr-criticidade", "critica")
    page.fill("#restr-responsavel", "Meio Ambiente")
    page.click("text=➕ Adicionar")
    page.wait_for_timeout(400)
    rs = page.evaluate("window.__banco.planejamento_restricoes")
    check(len(rs) == 1 and rs[0]["obra_id"] == "obra1" and rs[0]["criticidade"] == "critica",
          "restrição gravada com obra_id da obra ativa")
    check("Licença da central de concreto" in page.inner_text("#restricoes-tbody"), "restrição aparece na lista")
    page.select_option("#restricoes-tbody select", "resolvida")
    page.wait_for_timeout(400)
    check(page.evaluate("window.__banco.planejamento_restricoes[0].status") == "resolvida", "status da restrição muda pela lista")

    check(not erros, f"sem erros de JS ({erros})")
    b.close()

print("FALHAS:", falhas if falhas else "nenhuma")
if falhas:
    raise SystemExit(1)
