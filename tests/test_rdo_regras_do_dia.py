import json
import os
from playwright.sync_api import sync_playwright

BASE = os.environ.get("BUILDLY_URL", "http://localhost:8795")
falhas = []


def check(cond, msg):
    print(("  OK   " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    ctx = b.new_context(viewport={"width": 480, "height": 900})
    page = ctx.new_page()
    erros = []
    page.on("pageerror", lambda e: erros.append(str(e)))
    page.on("dialog", lambda d: d.dismiss())
    page.route("**/script.google.com/**", lambda r: r.fulfill(
        status=200, content_type="application/json", body=json.dumps({"ok": True})))
    page.goto(f"{BASE}/rdo.html")
    page.wait_for_timeout(1000)

    # ---- Item 5: lista fechada de locais, vinda do cadastro da obra ----
    check(page.eval_on_selector("#localObra", "e => e.tagName") == "SELECT",
          "Local da Obra virou <select>")

    # sem locais cadastrados na obra, não pode aparecer lista nenhuma (nem de outro projeto)
    page.evaluate("locaisPorObra[B3Obras.atualId()] = []; _atualizarLocalObraDatalist();")
    page.wait_for_timeout(200)
    vazio = page.eval_on_selector_all("#localObra option", "es => es.map(e => e.value)")
    check(vazio == [""], f"obra sem locais cadastrados: só o placeholder (obtido: {vazio})")

    # com locais cadastrados (rdo_locais), o seletor mostra exatamente eles
    page.evaluate("""() => {
        locaisPorObra[B3Obras.atualId()] = ['Acesso 1', 'Base Aerogerador 1', 'Base Aerogerador 2']
          .map((nome, i) => ({ id: 'id-' + i, nome }));
        _atualizarLocalObraDatalist();
    }""")
    page.wait_for_timeout(200)
    opts = page.eval_on_selector_all("#localObra option", "es => es.map(e => e.value)")
    check(opts == ["", "Acesso 1", "Base Aerogerador 1", "Base Aerogerador 2"],
          f"seletor mostra só os locais cadastrados da obra (obtido: {opts})")

    # valor antigo fora da lista tem que sobreviver
    page.evaluate("currentDay.localObra = 'Filtros ETA (grafia antiga)'; _atualizarLocalObraDatalist();")
    check(page.eval_on_selector("#localObra", "e => e.value") == "Filtros ETA (grafia antiga)",
          "valor antigo fora da lista é preservado e fica selecionado")
    page.evaluate("currentDay.localObra = 'Filtro 9'; _atualizarLocalObraDatalist();")
    check(page.eval_on_selector("#localObra", "e => e.value") == "Filtro 9",
          "valor da lista seleciona normalmente")

    # ---- Item 3: só grava com responsável ----
    r = page.evaluate("""() => {
        currentDay.apontador = '';
        currentDay.observacoesDia = 'texto sem responsavel';
        const antes = JSON.stringify(history[currentDay.data] || null);
        salvarDiarioDia(false);
        const depois = JSON.stringify(history[currentDay.data] || null);
        return {igual: antes === depois, pode: diarioPodeSerSalvo(currentDay)};
    }""")
    check(not r["pode"] and r["igual"],
          "salvamento automático não grava sem responsável")

    r2 = page.evaluate("""() => {
        currentDay.apontador = '501 – Marcelo Dias (Qualidade / Apontamento)';
        salvarDiarioDia(false);
        // chave agora é data#apontador (item 2)
        return !!history[chaveDiario(currentDay.data, currentDay.apontador)];
    }""")
    check(r2, "com responsável, grava normalmente")

    papeis = page.evaluate("""() => ({
        apontador: _ehResponsavelValido('Apontador'),
        apontamento: _ehResponsavelValido('Qualidade / Apontamento'),
        supervisor: _ehResponsavelValido('Supervisor de Obra'),
        supervisao: _ehResponsavelValido('Engenharia / Supervisão'),
        pedreiro: _ehResponsavelValido('Pedreiro'),
        vazio: _ehResponsavelValido('')
    })""")
    check(all([papeis["apontador"], papeis["apontamento"], papeis["supervisor"], papeis["supervisao"]])
          and not papeis["pedreiro"] and not papeis["vazio"],
          f"papéis aceitos/recusados corretamente ({papeis})")

    lista = page.evaluate("_apontadoresFiltrados()")
    check(any("Marcelo Dias" in x for x in lista) and any("Roberto Silva" in x for x in lista),
          f"lista inclui Apontador e Supervisor ({len(lista)} nomes)")

    # ---- Item 6: dois locais na atividade ----
    txt = page.evaluate("""() => {
        const a = state.atividades[0];
        a.local = 'ETA'; a.unidade = 'un';
        const day = JSON.parse(JSON.stringify(currentDay));
        day.localObra = 'Filtro 9';
        day.atividadesMarcadas = {}; day.atividadesMarcadas[a.id] = true;
        day.atividadesQtd = {}; day.atividadesQtd[a.id] = 5;
        day.atividadesAvulsas = []; day.atividadesExtra = ''; day.atividadesParalisadas = [];
        return textoAtividadesDia(day);
    }""")
    check(" – ETA – Filtro 9 (5 un)" in txt, f"dois locais + quantidade: {txt!r}")

    txt2 = page.evaluate("""() => {
        const a = state.atividades[0];
        a.local = 'ETA'; a.unidade = '';
        const day = JSON.parse(JSON.stringify(currentDay));
        day.localObra = 'ETA';
        day.atividadesMarcadas = {}; day.atividadesMarcadas[a.id] = true;
        day.atividadesQtd = {};
        day.atividadesAvulsas = []; day.atividadesExtra = ''; day.atividadesParalisadas = [];
        return textoAtividadesDia(day);
    }""")
    check(txt2.count("ETA") == 1 and "(" not in txt2,
          f"locais iguais aparecem uma vez, sem parênteses sem quantidade: {txt2!r}")

    txt3 = page.evaluate("""() => {
        const a = state.atividades[0];
        a.local = '';
        const day = JSON.parse(JSON.stringify(currentDay));
        day.localObra = '';
        day.atividadesMarcadas = {}; day.atividadesMarcadas[a.id] = true;
        day.atividadesQtd = {};
        day.atividadesAvulsas = []; day.atividadesExtra = ''; day.atividadesParalisadas = [];
        return textoAtividadesDia(day);
    }""")
    check(" – " not in txt3, f"sem local, não escreve travessão: {txt3!r}")

    # ---- Item 7: legenda da foto ----
    legendas = page.evaluate("""() => {
        const a = state.atividades[0];
        a.desc = 'Enchimento de bags';
        return {
          comAtiv: legendaFoto({ativId: a.id}, 0),
          sem: legendaFoto({}, 1),
          legado: legendaFoto({legenda: 'texto antigo'}, 2),
          ativVence: legendaFoto({ativId: a.id, legenda: 'texto antigo'}, 3)
        };
    }""")
    check(legendas["comAtiv"] == "Foto 1 - Enchimento de bags", f"legenda da atividade: {legendas['comAtiv']!r}")
    check(legendas["sem"] == "Foto 2", f"sem atividade fica só o número: {legendas['sem']!r}")
    check(legendas["legado"] == "Foto 3 - texto antigo", f"legenda antiga preservada: {legendas['legado']!r}")
    check(legendas["ativVence"] == "Foto 4 - Enchimento de bags", "atividade tem precedência sobre legenda antiga")

    check(not erros, f"sem erros de JS ({erros})")
    b.close()

print()
print("FALHAS:", falhas if falhas else "nenhuma")
