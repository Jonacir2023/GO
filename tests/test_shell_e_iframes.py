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


with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    ctx = contexto(b, viewport={"width": 480, "height": 900})
    page = ctx.new_page()
    erros = []
    page.on("pageerror", lambda e: erros.append(str(e)))
    page.on("dialog", lambda d: d.accept())
    page.route("**/script.google.com/**", lambda r: r.fulfill(
        status=200, content_type="application/json", body=json.dumps({"ok": True})))
    page.goto(f"{BASE}/buildly-completo.html")
    page.wait_for_timeout(1500)

    check(page.evaluate("() => !!localStorage.__buildly3"), "shell com espaço próprio")
    check(page.evaluate("() => !!document.querySelector('.fab-ia-btn')"), "robô flutuante presente")

    # o nome da obra é compartilhado ENTRE os apps do BUILDLy (mesmo prefixo)
    page.evaluate("localStorage.setItem('b3_obra', JSON.stringify({nome:'Obra Teste B3'}))")
    intra = page.evaluate("""async () => {
      const f = document.createElement('iframe');
      f.src = 'rdo.html';
      document.body.appendChild(f);
      await new Promise(r => f.onload = r);
      const w = f.contentWindow;
      return {
        temEspaco: !!w.localStorage.__buildly3,
        veObra: w.localStorage.getItem('b3_obra'),
        naoVeOutroApp: w.localStorage.getItem('diario_obras_v4_state_suzano_-_eta')
      };
    }""")
    check(intra["temEspaco"], "o app dentro do iframe também tem o espaço próprio")
    check(intra["veObra"] and "Obra Teste B3" in intra["veObra"],
          f"apps do BUILDLy continuam compartilhando entre si: {intra['veObra']}")
    check(intra["naoVeOutroApp"] is None, "e continuam sem enxergar o outro app")

    check(not erros, f"sem erros de JS ({erros})")
    b.close()

print()
print("FALHAS:", falhas if falhas else "nenhuma")
