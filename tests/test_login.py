"""Login: sem sessão o app não abre; cada papel vê só o que lhe cabe; páginas avulsas voltam ao login."""
import os
from playwright.sync_api import sync_playwright
from _login import contexto

BASE = os.environ.get("BUILDLY_URL", "http://localhost:8795")
falhas = []


def check(cond, msg):
    print(("  OK    " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


def cartoes_visiveis(page):
    return page.evaluate("() => [...document.querySelectorAll('.home-card[data-mod]')].filter(c => c.getBoundingClientRect().width > 0 && getComputedStyle(c).display !== 'none').map(c => c.dataset.mod)")


def login_visivel(page):
    return page.evaluate("() => { const l = document.getElementById('login'); const r = l.getBoundingClientRect(); return getComputedStyle(l).display !== 'none' && r.width > 0; }")


with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    erros = []

    def novo(papel=None, **kw):
        ctx = contexto(b, papel, **kw) if papel else b.new_context(**kw)
        pg = ctx.new_page()
        pg.on("pageerror", lambda e: erros.append(str(e)))
        pg.on("dialog", lambda d: d.accept())
        return ctx, pg

    # ── sem sessão ──
    ctx, page = novo(viewport={"width": 390, "height": 844})
    page.goto(f"{BASE}/buildly-completo.html")
    page.wait_for_timeout(1200)
    check(login_visivel(page), "sem sessão, a tela de login aparece")
    check(cartoes_visiveis(page) == [], "sem sessão, nenhum módulo fica visível atrás do login")
    check(page.evaluate("() => document.querySelector('.fab-ia-btn').getBoundingClientRect().width") == 0 or
          page.evaluate("() => getComputedStyle(document.querySelector('.fab-ia-wrap')).display") == "none",
          "sem sessão, o robô também fica escondido")
    page.fill("#login-email", "isso-nao-e-email")
    page.fill("#login-senha", "12345678")
    page.click("#login-btn")
    check("e-mail válido" in page.inner_text("#login-msg"), "e-mail inválido é recusado antes de ir ao servidor")
    page.click('#login-abas [data-aba="criar"]')
    check(page.locator("#login-f-nome").is_visible() and page.locator("#login-f-senha2").is_visible(), "aba Criar acesso pede nome e repetição da senha")
    page.fill("#login-nome", "Fulano de Tal")
    page.fill("#login-email", "fulano@cesbe.com.br")
    page.fill("#login-senha", "curta")
    page.fill("#login-senha2", "curta")
    page.click("#login-btn")
    check("8 caracteres" in page.inner_text("#login-msg"), "senha curta é recusada")
    ctx.close()

    # ── páginas avulsas sem sessão voltam ao login e depois ao destino ──
    for destino in ["custos.html", "envio-pauta.html?id=abc", "rdo.html"]:
        ctx, page = novo(viewport={"width": 390, "height": 844})
        page.goto(f"{BASE}/{destino}")
        page.wait_for_timeout(1500)
        alvo = page.url
        check("buildly-completo.html" in alvo and "next=" in alvo, f"{destino} sem sessão redireciona para o login ({alvo})")
        check(login_visivel(page), f"{destino}: a tela de login aparece")
        ctx.close()

    # ── administrador ──
    ctx, page = novo("admin", viewport={"width": 390, "height": 844})
    page.goto(f"{BASE}/buildly-completo.html")
    page.wait_for_timeout(1200)
    check(not login_visivel(page), "administrador logado não vê o login")
    check(len(cartoes_visiveis(page)) == 14, f"administrador vê os 14 módulos ({len(cartoes_visiveis(page))})")
    check(page.evaluate("() => getComputedStyle(document.querySelector('.fab-ia-wrap')).display") != "none", "administrador vê o robô")
    page.evaluate("abrirPerfil()")
    txt = page.inner_text("#sheet-corpo")
    check("Administrador" in txt and "Usuários e acessos" in txt and "Trocar senha" in txt and "Sair" in txt,
          "perfil do administrador mostra papel, Usuários e acessos, Trocar senha e Sair")
    page.evaluate("loginSair()")
    page.wait_for_timeout(500)
    check(login_visivel(page), "Sair volta para a tela de login")
    check(page.evaluate("() => Object.keys(localStorage).filter(k => k.indexOf('sb-') === 0 || k === 'b3_auth' && localStorage.getItem(k) !== '{}').length") == 0,
          "Sair apaga a sessão guardada")
    ctx.close()

    # ── portaria: só Entradas ──
    ctx, page = novo("portaria", viewport={"width": 390, "height": 844})
    page.goto(f"{BASE}/buildly-completo.html")
    page.wait_for_timeout(1200)
    check(cartoes_visiveis(page) == ["custos"], f"portaria vê só o módulo Entradas ({cartoes_visiveis(page)})")
    check(page.evaluate("() => getComputedStyle(document.querySelector('.fab-ia-wrap')).display") == "none", "portaria não vê o robô")
    page.evaluate("switchTab('rdo')")
    check(page.evaluate("() => currentTab") == "home", "portaria não consegue abrir o RDO nem por script")
    page.evaluate("switchTab('custos')")
    check(page.evaluate("() => currentTab") == "custos", "portaria abre Entradas")
    page.evaluate("abrirMais()")
    check(page.locator("#sheet-corpo .sheet-item").count() == 0, "Mais não lista módulos para a portaria")
    page.evaluate("abrirRelatorios()")
    check(page.locator("#sheet-corpo .sheet-item").count() == 0, "Relatórios não lista nada para a portaria")
    page.evaluate("abrirPerfil()")
    txt = page.inner_text("#sheet-corpo")
    check("Portaria" in txt and "Usuários e acessos" not in txt, "perfil da portaria não oferece administração")
    check(page.evaluate("() => getComputedStyle(document.querySelector('.hero-btn[aria-label=\"Pendências\"]')).display") == "none", "portaria não vê o sino do Check-in")
    ctx.close()

    # ── pendente: aguarda liberação ──
    ctx, page = novo("pendente", viewport={"width": 390, "height": 844})
    page.goto(f"{BASE}/buildly-completo.html")
    page.wait_for_timeout(1200)
    check(login_visivel(page) and "Aguardando liberação" in page.inner_text("#login"), "pendente vê 'Aguardando liberação'")
    check(cartoes_visiveis(page) == [], "pendente não vê módulo nenhum")
    ctx.close()

    # ── volta para a página de origem depois de entrar ──
    ctx, page = novo("admin", viewport={"width": 390, "height": 844})
    page.goto(f"{BASE}/buildly-completo.html?next=custos.html")
    page.wait_for_timeout(1500)
    check(page.url.endswith("/custos.html"), f"depois do login volta para a página pedida ({page.url})")
    for ruim in ["https://evil.example/x.html", "//evil.example/x.html", "javascript:alert(1)"]:
        page.goto(f"{BASE}/buildly-completo.html?next=" + ruim)
        page.wait_for_timeout(800)
        check(page.url.split("?")[0].endswith("/buildly-completo.html"), f"destino fora da lista é ignorado ({ruim})")
    ctx.close()

    check(not erros, f"sem erros de JS ({erros[:3]})")
    b.close()

print()
print("FALHAS:", falhas if falhas else "nenhuma")
