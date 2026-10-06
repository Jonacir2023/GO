import json
import os
from playwright.sync_api import sync_playwright
from _login import contexto

BASE = os.environ.get("BUILDLY_URL", "http://localhost:8795")
falhas = []
def check(c, m):
    print(("  OK    " if c else "  FALHA ") + m)
    if not c: falhas.append(m)

with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    page = contexto(b, viewport={"width": 480, "height": 900}).new_page()
    erros = []
    page.on("pageerror", lambda e: erros.append(str(e)))
    page.on("dialog", lambda d: d.accept())
    page.route("**/script.google.com/**", lambda r: r.fulfill(
        status=200, content_type="application/json", body=json.dumps({"ok": True})))
    page.goto(f"{BASE}/buildly-completo.html")
    page.wait_for_timeout(1200)

    abas = page.eval_on_selector_all(".atabs .atab", "es => es.map(e => e.textContent.trim())")
    check(abas and not any("Sync" in a for a in abas), f"aba Sync removida; sobraram: {abas}")
    check(page.evaluate("() => !document.getElementById('pauta-admin-sync')"),
          "a tela do token do GitHub não existe mais")
    check(page.evaluate("() => !document.getElementById('pauta-sync-token')"),
          "o campo de token não existe mais")

    # cada aba restante ainda abre, sem erro
    for i in range(len(abas)):
        page.evaluate(f"""() => {{
          const t = document.querySelectorAll('.atabs .atab')[{i}];
          t.click();
        }}""")
        page.wait_for_timeout(120)
    ativas = page.evaluate(
        "() => [...document.querySelectorAll('.admin-section.active')]"
        "        .filter(e => (e.id || '').indexOf('pauta-admin-') === 0)"
        "        .map(e => e.id)")
    # As três seções ficarem ativas ao mesmo tempo é BUG ANTERIOR a esta mudança:
    # pautaAbaAdmin() limpa por "#page-pauta .admin-section", mas as seções não
    # estão dentro de #page-pauta. Verificado no main antes da remoção — lá são as
    # mesmas quatro. Aqui só se confere que a remoção não alterou esse comportamento.
    check(ativas == ['pauta-admin-membros', 'pauta-admin-setores', 'pauta-admin-backup'],
          f"abas restantes se comportam como antes, sem a de Sync: {ativas}")

    check(not erros, f"sem erros de JS ({erros})")
    b.close()

print()
print("FALHAS:", falhas if falhas else "nenhuma")
