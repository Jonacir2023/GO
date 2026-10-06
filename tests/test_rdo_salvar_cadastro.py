import json
import os
from playwright.sync_api import sync_playwright
from _login import contexto

BASE = os.environ.get("BUILDLY_URL", "http://localhost:8795")
falhas = []


def check(cond, msg):
    print(("  OK   " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


AP = "501 – Marcelo Dias (Qualidade / Apontamento)"
ONTEM = "2026-10-01"

# Dia anterior já gravado: 1 atividade (qtd 5), 2 pessoas no efetivo, 1 equipamento, 1 veículo leve.
# Não grava os rascunhos (efetivoDia_/ativDia_/...), como num aparelho que nunca abriu esse dia.
SEMEAR_DIA = """([ap, data]) => {
  const d = Object.assign(EMPTY_DAY(), { data, apontador: ap });
  const a = state.atividades[0]; d.atividadesMarcadas[a.id] = true; d.atividadesQtd[a.id] = '5';
  const pessoas = []; state.colaboradores.categorias.forEach(c => c.itens.forEach(i => pessoas.push(i.id)));
  d.efetivo[pessoas[0]] = true; d.efetivo[pessoas[1]] = true;
  d.equipamentos[state.equipamentos[0].id] = { ativo: true, operadorMat: '', operadorNome: '', status: 'Operando' };
  d.veiculosLeves = [{ frotaId: (state.veiculosFrota[0] || {}).id || 'vl-teste', motoristaNome: '', motoristaMat: '' }];
  history[chaveDiario(data, ap)] = d; saveHistory();
  ['ativDia_', 'efetivoDia_', 'equipDia_', 'vlDia_'].forEach(p => localStorage.removeItem('diario_' + p + data));
}"""


def abrir(browser, semear_dia):
    ctx = contexto(browser, viewport={"width": 480, "height": 900})
    page = ctx.new_page()
    page.on("dialog", lambda d: d.dismiss())
    page.errs = []
    page.on("pageerror", lambda e: page.errs.append(str(e)))
    page.route("**/script.google.com/**", lambda r: r.fulfill(
        status=200, content_type="application/json", body=json.dumps({"ok": True})))
    page.goto(f"{BASE}/rdo.html")
    page.wait_for_timeout(900)
    if semear_dia:
        page.evaluate(SEMEAR_DIA, [AP, ONTEM])
    page.fill("#dataDiario", ONTEM)
    page.dispatch_event("#dataDiario", "input")
    page.wait_for_timeout(300)
    return page


with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")

    # ---------- dia anterior já gravado, sem rascunho neste aparelho ----------
    page = abrir(b, True)
    rasc = page.evaluate("""(d) => ({ ativ: S.get('ativDia_' + d), ef: S.get('efetivoDia_' + d), eq: S.get('equipDia_' + d), vl: S.get('vlDia_' + d) })""", ONTEM)
    check(rasc["ativ"] and len(rasc["ativ"]) == 1 and rasc["ef"] and len(rasc["ef"]) == 2 and rasc["eq"] and rasc["vl"],
          f"abrir um dia gravado cria os rascunhos do Cadastro a partir dele ({rasc})")

    page.click('.tab[data-view="config"]')
    page.click('.subtab[data-pane="atividades"]')
    check(page.locator("#configAtivList input[type=checkbox]:checked").count() == 1,
          "Cadastro > Atividades mostra marcada a atividade que o dia já tinha")
    page.locator("#configAtivList input[type=checkbox]").nth(1).check()
    page.click("text=Salvar Atividades do Dia")
    page.wait_for_timeout(1200)
    r = page.evaluate("({aba: document.querySelector('.tab.active').dataset.view, n: Object.keys(currentDay.atividadesMarcadas).length, hist: Object.keys(history[chaveDiario(currentDay.data, currentDay.apontador)].atividadesMarcadas).length})")
    check(r["aba"] == "diario" and r["n"] == 2 and r["hist"] == 2,
          f"Salvar Atividades: volta ao Diário com as DUAS atividades, no dia e no histórico ({r})")

    page.click('.tab[data-view="config"]')
    page.click('.subtab[data-pane="colaboradores"]')
    check(page.locator("#configColabList input[type=checkbox]:checked").count() == 2,
          "Cadastro > Equipe mostra marcados os 2 do efetivo do dia")
    page.locator("#configColabList input[type=checkbox]:not(:checked)").first.click()
    page.click("text=Salvar Efetivo do Dia")
    page.wait_for_timeout(1200)
    r = page.evaluate("Object.keys(history[chaveDiario(currentDay.data, currentDay.apontador)].efetivo).length")
    check(r == 3, f"Salvar Efetivo: 2 que já estavam + 1 novo = 3 ({r})")

    page.click('.tab[data-view="config"]')
    page.click('.subtab[data-pane="equipamentos"]')
    check(page.locator("#configEquipList input[type=checkbox]:checked").count() >= 1,
          "Cadastro > Equipamentos mostra marcado o equipamento do dia")
    page.click("text=Salvar Equipamentos do Dia")
    page.wait_for_timeout(1200)
    check(page.evaluate("document.querySelector('.tab.active').dataset.view") == "diario"
          and page.evaluate("Object.keys(currentDay.equipamentos).length") >= 1,
          "Salvar Equipamentos: volta ao Diário sem perder o equipamento")
    check(not page.errs, f"sem erros de JS ({page.errs})")
    page.context.close()

    # ---------- dia anterior NOVO, sem apontador ----------
    page = abrir(b, False)
    page.evaluate("window.__avisos = []; const _t = toast; toast = function (m) { window.__avisos.push(String(m)); return _t.apply(this, arguments); }")
    check(page.evaluate("currentDay.apontador") == "", "dia novo começa sem apontador")
    page.click('.tab[data-view="config"]')
    page.click('.subtab[data-pane="atividades"]')
    page.locator("#configAtivList input[type=checkbox]").nth(1).check()
    page.click("text=Salvar Atividades do Dia")
    page.wait_for_timeout(1200)
    r = page.evaluate("""() => ({ aba: document.querySelector('.tab.active').dataset.view,
        marcadas: Object.keys(currentDay.atividadesMarcadas).length,
        naTela: document.getElementById('atividadesList').innerText,
        noHistorico: Object.keys(history).filter(k => k.startsWith('%s')).length })""" % ONTEM)
    check(r["aba"] == "diario", "volta ao Diário")
    check(r["marcadas"] == 1 and "Nenhuma atividade selecionada" not in r["naTela"],
          f"a atividade marcada continua selecionada na tela (não volta vazio) ({r['naTela'][:40]!r})")
    check(r["noHistorico"] == 0, "sem apontador nada é gravado ainda (regra de responsável mantida)")
    avisos = page.evaluate("window.__avisos")
    check(any("NÃO gravado" in m for m in avisos) and any("Selecione o Apontador" in m for m in avisos)
          and not any(m.startswith("✓ Atividades salvas") for m in avisos),
          f"avisa que NÃO gravou e pede o apontador, sem dizer 'salvas' ({avisos})")

    # escolhido o apontador, o dia grava com o que foi marcado
    page.evaluate("selecionarApontadorDireto(%s)" % json.dumps(AP))
    r = page.evaluate("""(d) => { const k = chaveDiario(d, currentDay.apontador); return history[k] ? Object.keys(history[k].atividadesMarcadas).length : -1; }""", ONTEM)
    check(r == 1, f"ao escolher o apontador, o dia é gravado com a atividade marcada ({r})")
    check(not page.errs, f"sem erros de JS ({page.errs})")
    page.context.close()
    b.close()

print()
print("FALHAS:", falhas if falhas else "nenhuma")
