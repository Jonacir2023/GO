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
    page = contexto(b, viewport={"width": 480, "height": 900}).new_page()
    erros = []
    toasts = []
    page.on("pageerror", lambda e: erros.append(str(e)))
    page.on("dialog", lambda d: d.accept())
    page.route("**/script.google.com/**", lambda r: r.fulfill(
        status=200, content_type="application/json", body=json.dumps({"ok": True})))
    page.goto(f"{BASE}/rdo.html")
    page.wait_for_timeout(900)
    page.evaluate("""window.linhasAtivas = id =>
        [...document.querySelectorAll('#' + id + ' .item-row .item-name')]
          .map(e => e.textContent).join(' | ');""")
    page.evaluate("""window.__toasts = []; toast = m => { window.__toasts.push(m); };
      window.confirmarSim = () => document.getElementById('modalConfirmYes').click();""")

    # cenário: categoria com 2 pessoas, uma marcada como presente hoje
    setup = """(() => {
      const hoje = todayISO();
      currentDay.data = hoje;
      state.colaboradores.categorias = [{id:'c1', nome:'Operacional', icon:'📁', itens:[
        {id:'p1', mat:'101', nome:'José Silva',  funcao:'Pedreiro'},
        {id:'p2', mat:'102', nome:'Ana Souza',   funcao:'Serralheira'}
      ]}];
      S.set('efetivoDia_' + hoje, {p1:true});   // José marcado presente HOJE
      renderConfigColab();
      return document.getElementById('configColabList').innerText;
    })()"""
    antes = page.evaluate(setup)
    check("José Silva" in antes and "Ana Souza" in antes, "os dois aparecem antes")

    # --- o caso que o usuário relatou: remover quem está marcado presente ---
    r = page.evaluate("""(() => {
      window.__toasts = [];
      removerColaborador('c1', 'p1'); confirmarSim();
      const txt = document.getElementById('configColabList').innerText;
      const cat = state.colaboradores.categorias[0];
      const jose = cat.itens.find(c => c.id === 'p1');
      return {
        naTela: linhasAtivas('configColabList').includes('José Silva'),
        temBlocoRemovidos: txt.includes('Removidos (1)'),
        inativo: !!jose.inativo,
        aindaNoCadastro: cat.itens.length,
        desmarcado: !(S.get('efetivoDia_' + todayISO()) || {})['p1'],
        toast: window.__toasts.join(' | ')
      };
    })()""")
    check(not r["naTela"], "José sai da lista ao clicar no 🗑️ (era o bug)")
    check(r["temBlocoRemovidos"], f"aparece o bloco 'Removidos (1)'")
    check(r["inativo"] and r["aindaNoCadastro"] == 2, "é baixa, não exclusão — nada apagado")
    check(r["desmarcado"], "sai também da marcação de presença de hoje")
    check(r["toast"] == "Removido", f"aviso simples quando o dia é hoje: {r['toast']!r}")

    # --- restaurar volta ---
    volta = page.evaluate("""(() => {
      const btn = [...document.querySelectorAll('#configColabList button')]
                    .find(b => b.textContent.includes('↩'));
      btn.click();
      const txt = document.getElementById('configColabList').innerText;
      return {naTela: linhasAtivas('configColabList').includes('José Silva'),
              inativo: !!state.colaboradores.categorias[0].itens.find(c=>c.id==='p1').inativo};
    })()""")
    check(volta["naTela"] and not volta["inativo"], "o ↩️ traz o colaborador de volta")

    # --- dia passado: continua na tela, mas o app explica ---
    passado = page.evaluate("""(() => {
      currentDay.data = '2020-01-15';
      window.__toasts = [];
      removerColaborador('c1', 'p2'); confirmarSim();
      const txt = document.getElementById('configColabList').innerText;
      return {naTela: linhasAtivas('configColabList').includes('Ana Souza'), toast: window.__toasts.join(' | ')};
    })()""")
    check(passado["naTela"], "editando 2020, quem foi baixado hoje continua listado (correto)")
    check("a partir de hoje" in passado["toast"] and "15/01/2020" in passado["toast"],
          f"e o aviso explica por quê: {passado['toast']!r}")

    # --- categoria inteira ---
    cat = page.evaluate("""(() => {
      currentDay.data = todayISO();
      state.colaboradores.categorias[0].itens.forEach(c => reativarNoCadastro(c));
      S.set('efetivoDia_' + todayISO(), {p1:true, p2:true});
      removerCategoria('c1'); confirmarSim();
      const txt = document.getElementById('configColabList').innerText;
      const sel = S.get('efetivoDia_' + todayISO()) || {};
      return {naTela: txt.includes('Operacional') && !txt.includes('Removidos'),
              bloco: txt.includes('📁 Operacional'),
              itensIntactos: state.colaboradores.categorias[0].itens.length,
              selVazia: Object.keys(sel).length === 0};
    })()""")
    check(not cat["naTela"], "a categoria sai da lista")
    check(cat["bloco"], "e aparece no bloco de removidos")
    check(cat["itensIntactos"] == 2, "os colaboradores da categoria não foram apagados")
    check(cat["selVazia"], "ninguém da categoria fica marcado presente hoje")

    restaura = page.evaluate("""(() => {
      const btn = [...document.querySelectorAll('#configColabList button')]
                    .find(b => b.textContent.includes('↩'));
      btn.click();
      const c = state.colaboradores.categorias[0];
      return {cat: !c.inativo, pessoas: c.itens.filter(i => !i.inativo).length,
              txt: document.getElementById('configColabList').innerText.includes('Ana Souza')};
    })()""")
    check(restaura["cat"] and restaura["pessoas"] == 2 and restaura["txt"],
          f"restaurar a categoria traz a equipe junto ({restaura})")

    # --- equipamento e veículo: mesma correção de desmarcar ---
    outros = page.evaluate("""(() => {
      const hoje = todayISO(); currentDay.data = hoje;
      state.equipamentos = [{id:'e1', numero:'ESC-1', desc:'Escavadeira'}];
      state.veiculosFrota = [{id:'v1', desc:'Uno', placa:'AAA-1111'}];
      S.set('equipDia_' + hoje, {e1:true});
      S.set('vlDia_' + hoje, {v1:true});
      renderConfigEquip(); renderConfigVL();
      removerEquipamento('e1'); confirmarSim(); removerVeiculoFrota('v1'); confirmarSim();
      return {
        equip: !linhasAtivas('configEquipList').includes('Escavadeira'),
        vl:    !linhasAtivas('configVLList').includes('Uno'),
        selE: !(S.get('equipDia_' + hoje) || {})['e1'],
        selV: !(S.get('vlDia_' + hoje) || {})['v1']
      };
    })()""")
    check(outros["equip"] and outros["selE"], "equipamento marcado hoje também sai ao remover")
    check(outros["vl"] and outros["selV"], "veículo marcado hoje também sai ao remover")

    check(not erros, f"sem erros de JS ({erros})")
    b.close()

print()
print("FALHAS:", falhas if falhas else "nenhuma")
