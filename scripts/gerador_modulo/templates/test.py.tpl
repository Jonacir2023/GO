import json
import os
from playwright.sync_api import sync_playwright

BASE = os.environ.get("BUILDLY_URL", "http://localhost:8795")
falhas = []
def check(c, m):
    print(("  OK    " if c else "  FALHA ") + m)
    if not c: falhas.append(m)

with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    page = b.new_context(viewport={"width": 390, "height": 844}).new_page()
    erros = []
    page.on("pageerror", lambda e: erros.append(str(e)))
    page.on("dialog", lambda d: d.accept())
    page.route("**/script.google.com/**", lambda r: r.fulfill(
        status=200, content_type="application/json", body=json.dumps({"ok": True, "status": "ok", "dados": []})))
    page.goto(f"{BASE}/{{ID}}.html")
    page.wait_for_timeout(600)

    check(page.evaluate("() => window.localStorage.__buildly3 === true"),
          "espaço próprio instalado (BUILDLY_ESPACO_PROPRIO)")
    check(page.locator("#form-{{ID}}").count() == 1, "formulário de novo registro está na página")

    page.fill("#f-titulo", "Item de teste")
    page.click("#form-{{ID}} button[type=submit]")
    page.wait_for_timeout(200)
    check(page.locator(".item").count() == 1, "item criado aparece na lista")

    page.click(".item .item-acoes button >> nth=0")
    page.wait_for_timeout(150)
    check("concluído" in page.locator(".item .badge").inner_text().lower(), "alternar status marca como concluído")

    page.click(".item .item-acoes button >> nth=1")
    page.wait_for_timeout(150)
    check(page.locator(".item").count() == 0, "remover tira o item da lista")

    check(not erros, f"sem erros de JS ({erros})")
    b.close()

print()
print("FALHAS:", falhas if falhas else "nenhuma")
