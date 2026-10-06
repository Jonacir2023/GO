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

    # ---- simula o "outro app" da mesma origem, ANTES de abrir o BUILDLy ----
    page.goto(f"{BASE}/LEIA-ME.txt")
    page.evaluate("""() => {
      localStorage.setItem('diario_obras_v4_state_suzano_-_eta', JSON.stringify({obra:{nome:'Suzano - ETA'}}));
      localStorage.setItem('diario_obras_v4_history_suzano_-_eta', JSON.stringify({'2026-08-01':{data:'2026-08-01'}}));
      localStorage.setItem('pauta_assuntos', JSON.stringify([{t:'assunto do outro app'}]));
    }""")

    page.goto(f"{BASE}/rdo.html")
    page.wait_for_timeout(900)

    espaco = page.evaluate("""() => ({
      instalado: !!localStorage.__buildly3,
      // o RDO do BUILDLy enxerga a obra do outro app?
      veSuzano: localStorage.getItem('diario_obras_v4_state_suzano_-_eta'),
      obraAtual: (state.obra && state.obra.nome) || '',
      chaves: (() => { const o = []; for (let i=0;i<localStorage.length;i++) o.push(localStorage.key(i)); return o; })()
    })""")
    check(espaco["instalado"], "espaço próprio instalado")
    check(espaco["veSuzano"] is None,
          f"o BUILDLy NÃO enxerga a obra do outro app: {espaco['veSuzano']!r}")
    check("Suzano" not in espaco["obraAtual"],
          f"a obra do BUILDLy não virou a do outro app: {espaco['obraAtual']!r}")
    check(not any("suzano" in k.lower() for k in espaco["chaves"]),
          "nenhuma chave do outro app aparece na listagem")

    # ---- o BUILDLy grava no espaço dele ----
    grav = page.evaluate("""() => {
      localStorage.setItem('teste_b3', 'valor do buildly');
      return {
        pelaApi: localStorage.getItem('teste_b3'),
        // olha o armazenamento real, por baixo do espaço
        real: Object.keys(window.top === window.self ? {} : {}) // placeholder
      };
    }""")
    check(grav["pelaApi"] == "valor do buildly", "o BUILDLy lê o que ele mesmo grava")

    # confere no armazenamento REAL, com um documento sem o espaço instalado
    outra = ctx.new_page()
    outra.goto(f"{BASE}/LEIA-ME.txt")
    real = outra.evaluate("""() => {
      const o = {};
      for (let i = 0; i < localStorage.length; i++) {
        const k = localStorage.key(i);
        o[k] = true;
      }
      return Object.keys(o);
    }""")
    check(any(k == "buildly3::teste_b3" for k in real),
          f"por baixo, a chave real é prefixada: {[k for k in real if 'teste_b3' in k]}")
    check("diario_obras_v4_state_suzano_-_eta" in real,
          "o dado do outro app continua intacto — o BUILDLy não apagou nada")
    check("pauta_assuntos" in real, "a pauta do outro app continua intacta")

    # ---- clear() não toca no que é dos outros ----
    page.evaluate("localStorage.clear()")
    depois = outra.evaluate("""() => {
      const o = [];
      for (let i = 0; i < localStorage.length; i++) o.push(localStorage.key(i));
      return o;
    }""")
    check("diario_obras_v4_state_suzano_-_eta" in depois and "pauta_assuntos" in depois,
          "clear() do BUILDLy não apaga o armazenamento dos outros apps")
    check(not any(k.startswith("buildly3::") for k in depois),
          f"clear() apaga o que é do BUILDLy: {[k for k in depois if k.startswith('buildly3::')]}")

    check(not erros, f"sem erros de JS ({erros})")
    b.close()

print()
print("FALHAS:", falhas if falhas else "nenhuma")
