"""Pauta -> Check-in: o assunto criado na Pauta chega ao Check-in com a data de lançamento
(e aparece no calendário no dia certo); o que já veio sem data é curado."""
import json
import os
from playwright.sync_api import sync_playwright

BASE = os.environ.get("BUILDLY_URL", "http://localhost:8795")
falhas = []


def check(cond, msg):
    print(("  OK    " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    # 05/10/2026 22:10 em Brasília = 06/10 01:10 UTC: o dia que o usuário vê é 05/10
    ctx = b.new_context(viewport={"width": 390, "height": 844}, timezone_id="America/Sao_Paulo")
    page = ctx.new_page()
    erros = []
    page.on("pageerror", lambda e: erros.append(str(e)))
    page.on("dialog", lambda d: d.dismiss())
    page.route("**/script.google.com/**", lambda r: r.fulfill(status=200, content_type="application/json", body="{}"))
    page.clock.install(time="2026-10-06T01:10:00Z")
    page.goto(f"{BASE}/buildly-completo.html")
    page.wait_for_timeout(1500)

    check(page.evaluate("dataLocalISO()") == "2026-10-05", "data local às 22h10 de Brasília é 05/10 (não 06/10 em UTC)")
    check(page.evaluate("dataLancDoAssunto('', Date.parse('2026-10-05T14:00:00-03:00'))") == "2026-10-05",
          "sem data de lançamento, usa a data de criação")

    # ---- Pauta: criar assunto de verdade pela tela ----
    page.evaluate("switchTab('pauta')")
    page.wait_for_timeout(600)
    check(page.evaluate("document.getElementById('pauta-f-data-lanc').value") == "2026-10-05", "Pauta sugere a data local de hoje")
    page.fill("#pauta-f-assunto", "Assunto criado hoje na Pauta")
    page.evaluate("""() => { const s = document.getElementById('pauta-f-setor');
      if (s && s.options.length > 1) s.selectedIndex = 1; }""")
    page.evaluate("pautaEnviarAssunto()")
    page.wait_for_timeout(400)
    na_pauta = page.evaluate("JSON.parse(localStorage.getItem('pauta_assuntos')).find(a => a.assunto === 'Assunto criado hoje na Pauta')")
    check(na_pauta and na_pauta["dataLanc"] == "2026-10-05", f"assunto da Pauta nasce com dataLanc 05/10 ({na_pauta and na_pauta.get('dataLanc')})")

    # Pauta antiga, sem data de lançamento + um já importado sem data (cenário do relato)
    page.evaluate("""() => {
      const t = Date.parse('2026-10-04T10:00:00-03:00');
      const pa = JSON.parse(localStorage.getItem('pauta_assuntos'));
      pa.push({id: 'velho-1', assunto: 'Pauta sem data', setor: 'X', prioridade: 'media', status: 'afazer', criadoEm: t});
      localStorage.setItem('pauta_assuntos', JSON.stringify(pa));
      localStorage.setItem('chk_assuntos', JSON.stringify([
        {id: 'ja-importado', assunto: 'Importado sem data', status: 'afazer', criadoEm: Date.parse('2026-10-03T09:00:00-03:00'), _origem: 'pauta'}]));
    }""")

    # ---- Check-in: abre, sincroniza, cura ----
    page.evaluate("switchTab('checkin')")
    page.wait_for_timeout(1500)
    chk = page.evaluate("JSON.parse(localStorage.getItem('chk_assuntos'))")
    por = {a["assunto"]: a for a in chk}
    check(por.get("Assunto criado hoje na Pauta", {}).get("dataLanc") == "2026-10-05", "Check-in recebeu o assunto com a data de lançamento da Pauta")
    check(por.get("Pauta sem data", {}).get("dataLanc") == "2026-10-04", "Pauta sem data: cai na data de criação (04/10)")
    check(por.get("Importado sem data", {}).get("dataLanc") == "2026-10-03", "já importado sem data é curado pela data de criação (03/10)")
    check(all(a.get("dataLanc") for a in chk), "nenhum assunto do Check-in fica sem data de lançamento")

    # ---- calendário: o dia de hoje lista o assunto ----
    page.evaluate("checkinGoTab('calendario', document.querySelectorAll('#checkin-tabs .tab')[2])")
    page.wait_for_timeout(400)
    page.evaluate("checkinSelecionarDiaCal('2026-10-05')")
    txt = page.locator("#checkin-cal-resumo-dia-lista").inner_text()
    check("Assunto criado hoje na Pauta" in txt, "calendário do Check-in mostra, no dia 05/10, o assunto criado hoje na Pauta")
    page.evaluate("checkinSelecionarDiaCal('2026-10-03')")
    check("Importado sem data" in page.locator("#checkin-cal-resumo-dia-lista").inner_text(), "calendário mostra o assunto curado no dia 03/10")

    check(not erros, f"sem erros de JS ({erros[:3]})")
    b.close()

print("\nFALHAS:", falhas if falhas else "nenhuma")
raise SystemExit(1 if falhas else 0)
