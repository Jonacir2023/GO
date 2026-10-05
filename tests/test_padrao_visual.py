"""Padrão visual claro: casca (hero, grade, barra inferior, sheets, favoritos),
modo embutido dos módulos e tema fora da impressão."""
import json
import os
import re
from playwright.sync_api import sync_playwright

BASE = os.environ.get("BUILDLY_URL", "http://localhost:8795")
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
falhas = []


def check(cond, msg):
    print(("  OK    " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


def aberto(page):
    return page.evaluate("() => document.getElementById('sheet').classList.contains('aberto')")


# ---- estático: toda página liga o tema (só em tela) e o detector de iframe ----
paginas = [f for f in os.listdir(RAIZ) if f.endswith(".html") and f != "index.html"]
sem_tema, sem_screen, sem_detector = [], [], []
for f in paginas:
    s = open(os.path.join(RAIZ, f), encoding="utf-8").read()
    if "</head>" not in s:
        continue
    m = re.search(r'<link[^>]+href="tema\.css\?v=[0-9a-f]{8}"[^>]*>', s)
    if not m:
        sem_tema.append(f)
    elif 'media="screen"' not in m.group(0):
        sem_screen.append(f)
    if "/*embutido*/" not in s:
        sem_detector.append(f)
check(not sem_tema, f"toda página liga tema.css?v=hash ({sem_tema})")
check(not sem_screen, f"tema.css só vale em tela, nunca na impressão/PDF ({sem_screen})")
casca = open(os.path.join(RAIZ, "buildly-completo.html"), encoding="utf-8").read()
frames_sem_versao = [m for m in re.findall(r'<iframe[^>]*\bsrc="([^"]+)"', casca) if not re.search(r'\.html\?v=[0-9a-f]{8}$', m)]
check(not frames_sem_versao, f"iframes da casca levam ?v=hash do arquivo ({frames_sem_versao})")
import hashlib
velhos = []
for arq, v in re.findall(r'<iframe[^>]*\bsrc="([A-Za-z0-9_-]+\.html)\?v=([0-9a-f]{8})"', casca):
    if hashlib.md5(open(os.path.join(RAIZ, arq), "rb").read()).hexdigest()[:8] != v:
        velhos.append(arq)
check(not velhos, f"hash dos iframes está em dia — rode scripts/versionar_estaticos.py ({velhos})")
import importlib.util
_sp = importlib.util.spec_from_file_location("versionar", os.path.join(RAIZ, "scripts", "versionar_estaticos.py"))
_vz = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(_vz)
bid_casca = (re.search(r'window\.BUILD_ID="([0-9a-f]+)"', casca) or [None, ""])[1]
bid_json = json.load(open(os.path.join(RAIZ, "versao.json")))["v"]
check(bid_casca == bid_json == _vz.build_id(), f"carimbo de build em dia: casca={bid_casca} versao.json={bid_json} calculado={_vz.build_id()} — rode scripts/versionar_estaticos.py")
check(not sem_detector, f"toda página tem o detector de iframe ({sem_detector})")

with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    ctx = b.new_context(viewport={"width": 390, "height": 844})
    page = ctx.new_page()
    erros = []
    page.on("pageerror", lambda e: erros.append(str(e)))
    page.on("dialog", lambda d: d.dismiss())
    page.route("**/script.google.com/**", lambda r: r.fulfill(
        status=200, content_type="application/json", body=json.dumps({"ok": True})))
    page.goto(f"{BASE}/buildly-completo.html")
    page.wait_for_timeout(1500)

    # ---- home ----
    check(page.locator(".home-card").count() == 14, "home com 14 cartões de módulo")
    visiveis = page.evaluate("() => [...document.querySelectorAll('.home-card')].filter(c => c.offsetParent).length")
    check(visiveis == 14, f"celular mostra os 14 cartões, nenhum escondido ({visiveis})")
    check(page.locator('.home-card[data-mod="custos"] .selo').inner_text().strip().lower() == "ativo", "selo 'Ativo' do Custos")
    check(page.evaluate("() => getComputedStyle(document.body).backgroundColor") != "rgb(74, 81, 98)",
          "fundo da casca não é mais o escuro antigo")
    check(page.locator("#app-nav button").count() == 4, "barra inferior com 4 botões")
    check(page.locator("#obra-card-nome").inner_text().strip() != "", "cartão da obra atual preenchido")
    sem_corte = page.evaluate("""() => document.documentElement.scrollWidth <= window.innerWidth + 1""")
    check(sem_corte, "home sem rolagem horizontal")

    # ---- favoritos ----
    page.evaluate("localStorage.removeItem('favoritos')")
    page.locator('.home-card .fav[data-fav="rdo"]').click()
    check(page.evaluate("() => JSON.parse(localStorage.getItem('favoritos'))").count("rdo") == 1, "estrela grava o favorito")
    check(page.evaluate("() => document.querySelector('.fav[data-fav=rdo]').classList.contains('on')"), "estrela fica acesa")
    check(page.evaluate("() => document.body.classList.contains('modulo')") is False, "clicar na estrela não abre o módulo")
    page.locator('#app-nav [data-nav="favoritos"]').click()
    check(aberto(page) and "RDO" in page.locator("#sheet-corpo").inner_text(), "painel Favoritos lista o RDO")
    page.evaluate("fecharSheet()")
    page.locator('.home-card .fav[data-fav="rdo"]').click()
    page.locator('#app-nav [data-nav="favoritos"]').click()
    check("Nenhum favorito" in page.locator("#sheet-corpo").inner_text(), "sem favoritos mostra o aviso")
    page.evaluate("fecharSheet()")

    # ---- painéis ----
    page.locator('#app-nav [data-nav="relatorios"]').click()
    check(aberto(page) and page.locator("#sheet-corpo .sheet-item").count() == 6, "Relatórios com 6 atalhos")
    page.evaluate("fecharSheet()")
    page.locator('#app-nav [data-nav="mais"]').click()
    texto = page.locator("#sheet-corpo").inner_text()
    check(all(n in texto for n in ["EAP", "Financeiro", "Suprimentos", "Manutenção", "Resumo do Tempo"]),
          "Mais traz os módulos extras")
    page.evaluate("fecharSheet()")

    # sino = pendências do Check-in
    page.evaluate("""localStorage.setItem('chk_assuntos', JSON.stringify([
      {id:'a', assunto:'Concretar laje', status:'afazer', resp:'Ana'},
      {id:'b', assunto:'Item pronto', status:'feito'}]))""")
    page.evaluate("atualizarSino()")
    check(page.evaluate("() => !document.querySelector('.sino-ponto').hidden"), "sino mostra o ponto com pendência")
    page.locator("#main-hdr .hero-btn").first.click()
    check(aberto(page) and "Concretar laje" in page.locator("#sheet-corpo").inner_text()
          and "Item pronto" not in page.locator("#sheet-corpo").inner_text(), "sino lista só o que está em aberto")
    page.evaluate("fecharSheet()")
    page.evaluate("localStorage.removeItem('chk_assuntos'); atualizarSino()")
    check(page.evaluate("() => document.querySelector('.sino-ponto').hidden"), "sem pendência, o ponto some")

    page.locator("#main-hdr .hero-btn").nth(1).click()
    check(aberto(page) and "Apontador" in page.locator("#sheet-corpo").inner_text(), "perfil mostra o apontador do aparelho")
    page.evaluate("fecharSheet()")
    page.locator(".obra-card").click()
    check(aberto(page) and "Obra atual" in page.locator("#sheet-corpo").inner_text(), "cartão da obra abre a troca de obra")
    page.evaluate("fecharSheet()")

    # ---- módulos: hero compacto, barra, sem rolagem horizontal ----
    for mod in ["rdo", "custos", "medicao", "documentos", "eap", "planejamento", "financeiro", "suprimentos",
                "manutencao", "reuniao", "resumo-tempo", "pauta", "checkin", "obra"]:
        page.evaluate("t => switchTab(t)", mod)
        page.wait_for_timeout(500)
        ok_modulo = page.evaluate("() => document.body.classList.contains('modulo')")
        titulo = page.locator("#mod-title").inner_text().strip()
        largura = page.evaluate("() => document.documentElement.scrollWidth <= window.innerWidth + 1")
        check(ok_modulo and titulo and largura, f"{mod}: hero de módulo '{titulo}' e sem rolagem horizontal")
    page.evaluate("switchTab('home')")
    check(page.evaluate("() => !document.body.classList.contains('modulo')"), "voltar à home restaura o hero grande")

    # ---- modo embutido: app dentro do iframe esconde o próprio cabeçalho ----
    page.evaluate("switchTab('rdo')")
    page.wait_for_timeout(800)
    fr = next(f for f in page.frames if "/rdo.html" in f.url)
    check(fr.evaluate("() => document.documentElement.classList.contains('embutido')"), "iframe do RDO recebe html.embutido")
    check(fr.evaluate("() => { const h = document.querySelector('.header,.hdr'); return !h || getComputedStyle(h).display === 'none'; }"),
          "cabeçalho próprio do RDO fica oculto dentro da casca")
    check(fr.evaluate("() => document.documentElement.scrollWidth <= window.innerWidth + 1"), "RDO embutido sem rolagem horizontal")

    # ---- botões de ação do cabeçalho continuam acessíveis dentro da casca ----
    for mod, arq, acao in [("custos", "custos.html", "abrirConfig()"), ("eap", "eap.html", "abrirNovaEAP()"),
                           ("planejamento", "planejamento.html", "abrirNovoCronograma()"),
                           ("suprimentos", "suprimentos.html", "abrirNovaRequisicao()")]:
        page.evaluate("t => switchTab(t)", mod)
        page.wait_for_timeout(700)
        f2 = next(f for f in page.frames if ("/" + arq) in f.url)
        vis = f2.evaluate("""a => { const e = document.querySelector('[onclick="' + a + '"]'); if (!e) return false;
          const r = e.getBoundingClientRect(); return r.width > 20 && r.height > 20 && r.top >= 0 && r.right <= innerWidth + 1; }""", acao)
        check(vis, f"{mod}: botão {acao} visível dentro da casca")
    page.evaluate("switchTab('rdo')")
    page.wait_for_timeout(800)

    # ---- app aberto direto (fora do iframe) mantém o próprio cabeçalho ----
    solo = ctx.new_page()
    solo.goto(f"{BASE}/rdo.html")
    solo.wait_for_timeout(800)
    check(solo.evaluate("() => !document.documentElement.classList.contains('embutido')"), "RDO avulso não é 'embutido'")

    # ---- desktop ----
    page.set_viewport_size({"width": 1100, "height": 800})
    page.evaluate("switchTab('home')")
    page.wait_for_timeout(300)
    check(page.evaluate("() => document.querySelector('.hero-home').getBoundingClientRect().width > 900"),
          "desktop: hero ocupa a largura útil")
    visiveis = page.evaluate("() => [...document.querySelectorAll('.home-card')].filter(c => c.offsetParent).length")
    check(visiveis == 14, f"desktop mostra os 14 cartões ({visiveis})")

    # ---- auto-atualização: versao.json diferente do carimbo => recarrega uma única vez ----
    velha = ctx.new_page()
    velha.route("**/versao.json*", lambda r: r.fulfill(status=200, content_type="application/json", body='{"v":"deadbeef"}'))
    velha.on("dialog", lambda d: d.dismiss())
    velha.goto(f"{BASE}/buildly-completo.html")
    velha.wait_for_timeout(2500)
    check("b=deadbeef" in velha.url, f"casca desatualizada se recarrega sozinha numa URL nova ({velha.url})")
    n_antes = velha.url
    velha.wait_for_timeout(1500)
    check(velha.url == n_antes, "e só recarrega uma vez (sem laço)")
    ok = ctx.new_page()
    ok.goto(f"{BASE}/buildly-completo.html")
    ok.wait_for_timeout(1500)
    check("b=" not in ok.url, "casca em dia não recarrega")

    check(not erros, f"sem erros de JS ({erros[:3]})")
    b.close()

print("\nFALHAS:", falhas if falhas else "nenhuma")
raise SystemExit(1 if falhas else 0)
