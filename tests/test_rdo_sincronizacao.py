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


with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    page = contexto(b, viewport={"width": 480, "height": 900}).new_page()
    erros = []
    page.on("pageerror", lambda e: erros.append(str(e)))
    page.on("dialog", lambda d: d.accept())
    page.route("**/script.google.com/**", lambda r: r.fulfill(
        status=200, content_type="application/json", body=json.dumps({"ok": True})))
    page.goto(f"{BASE}/rdo.html")
    page.wait_for_timeout(900)

    # ---- identidade do aparelho ----
    ap = page.evaluate("() => ({a: aparelhoId(), b: aparelhoId()})")
    check(ap["a"] == ap["b"] and ap["a"].startswith("ap-"),
          f"aparelho tem id estável: {ap['a']}")

    # ---- A REGRA: nunca sobrescrever trabalho alheio ----
    r = page.evaluate("""() => {
        history = {};
        // O que o Renan já tinha aqui
        history['2026-08-24#renan-de-souza'] =
          {data:'2026-08-24', apontador:'Renan de Souza', observacoesDia:'meu trabalho',
           atualizadoEm:'2026-08-24T10:00:00.000Z'};
        // Chega da nuvem: um RDO do Jekyll (novo) e uma versão ANTIGA do Renan
        const remoto = {
          '2026-08-24#jekyll-vinente':
            {data:'2026-08-24', apontador:'Jekyll Vinente', observacoesDia:'trabalho do Jekyll',
             atualizadoEm:'2026-08-24T09:00:00.000Z'},
          '2026-08-24#renan-de-souza':
            {data:'2026-08-24', apontador:'Renan de Souza', observacoesDia:'versao velha',
             atualizadoEm:'2026-08-24T08:00:00.000Z'}
        };
        const res = mesclarDaNuvem({history: remoto});
        return {res, meu: history['2026-08-24#renan-de-souza'].observacoesDia,
                dele: (history['2026-08-24#jekyll-vinente']||{}).observacoesDia,
                total: Object.keys(history).length};
    }""")
    check(r["meu"] == "meu trabalho",
          "versão antiga da nuvem NÃO sobrescreve o trabalho local mais recente")
    check(r["dele"] == "trabalho do Jekyll", "o RDO do outro apontador entra")
    check(r["total"] == 2 and r["res"]["novos"] == 1, f"1 novo, nada perdido ({r['res']})")

    # ---- mais recente vence ----
    novo = page.evaluate("""() => {
        history = {};
        history['2026-08-25#renan-de-souza'] =
          {data:'2026-08-25', observacoesDia:'antigo', atualizadoEm:'2026-08-25T08:00:00.000Z'};
        mesclarDaNuvem({history: {'2026-08-25#renan-de-souza':
          {data:'2026-08-25', observacoesDia:'corrigido no outro celular',
           atualizadoEm:'2026-08-25T12:00:00.000Z'}}});
        return history['2026-08-25#renan-de-souza'].observacoesDia;
    }""")
    check(novo == "corrigido no outro celular", "versão mais recente vence")

    # ---- RDO idêntico não conta como conflito ----
    ig = page.evaluate("""() => {
        const a = {data:'2026-08-26', observacoesDia:'x', atualizadoEm:'2026-08-26T08:00:00.000Z', atualizadoPor:'ap-1'};
        const b = {data:'2026-08-26', observacoesDia:'x', atualizadoEm:'2026-08-26T09:00:00.000Z', atualizadoPor:'ap-2'};
        history = {'2026-08-26#r': a};
        const res = mesclarDaNuvem({history: {'2026-08-26#r': b}});
        return {igual: mesmoConteudoDiario(a,b), res};
    }""")
    check(ig["igual"] is True, "mesmoConteudoDiario ignora os carimbos")
    check(ig["res"]["atualizados"] == 0, "RDO idêntico não é contado como atualização")

    # ---- cadastro: só acrescenta, nunca apaga ----
    cad = page.evaluate("""() => {
        state.atividades = [{id:'a1', desc:'Só minha'}];
        mesclarDaNuvem({state: {atividades: [{id:'a2', desc:'Do outro celular'}]}});
        return state.atividades.map(a => a.id);
    }""")
    check(sorted(cad) == ["a1", "a2"],
          f"cadastro ganha o do outro sem perder o local: {cad}")

    # ---- baixa viaja entre aparelhos, statusEm mais recente vence ----
    st = page.evaluate("""() => {
        state.equipamentos = [{id:'e1', desc:'Escavadeira', statusEm:'2026-08-24T08:00:00.000Z'}];
        mesclarDaNuvem({state: {equipamentos: [
          {id:'e1', desc:'Escavadeira', inativo:true, inativoEm:'2026-08-25',
           statusEm:'2026-08-25T10:00:00.000Z'}]}});
        const depoisDaBaixa = !!state.equipamentos[0].inativo;
        // agora chega um retorno AINDA MAIS recente
        mesclarDaNuvem({state: {equipamentos: [
          {id:'e1', desc:'Escavadeira', inativo:false, inativoEm:'',
           statusEm:'2026-08-26T10:00:00.000Z'}]}});
        return {depoisDaBaixa, depoisDoRetorno: !!state.equipamentos[0].inativo};
    }""")
    check(st["depoisDaBaixa"] is True, "baixa feita em outro aparelho chega aqui")
    check(st["depoisDoRetorno"] is False, "retorno mais recente desfaz a baixa")

    velho = page.evaluate("""() => {
        state.equipamentos = [{id:'e1', inativo:true, inativoEm:'2026-08-25',
                               statusEm:'2026-08-25T10:00:00.000Z'}];
        mesclarDaNuvem({state: {equipamentos: [
          {id:'e1', inativo:false, statusEm:'2026-08-20T10:00:00.000Z'}]}});
        return !!state.equipamentos[0].inativo;
    }""")
    check(velho is True,
          "aparelho desatualizado NÃO desfaz uma baixa mais recente")

    # ---- seleções do dia nunca por cima do local ----
    sel = page.evaluate("""() => {
        history = {};
        localStorage.setItem('equipDia_2026-08-27', JSON.stringify({meu:true}));
        mesclarDaNuvem({
          history: {'2026-08-27#outro': {data:'2026-08-27', atualizadoEm:'2026-08-27T10:00:00.000Z'}},
          chavesDia: {'equipDia_2026-08-27': JSON.stringify({doOutro:true})}
        });
        return JSON.parse(localStorage.getItem('equipDia_2026-08-27'));
    }""")
    check("meu" in sel and "doOutro" not in sel,
          f"seleção do dia que já existe aqui não é sobrescrita: {sel}")

    novaSel = page.evaluate("""() => {
        history = {};
        localStorage.removeItem('vlDia_2026-08-28');
        mesclarDaNuvem({
          history: {'2026-08-28#outro': {data:'2026-08-28', atualizadoEm:'2026-08-28T10:00:00.000Z'}},
          chavesDia: {'vlDia_2026-08-28': JSON.stringify({v1:true})}
        });
        return JSON.parse(localStorage.getItem('vlDia_2026-08-28') || 'null');
    }""")
    check(novaSel == {"v1": True},
          "seleção que não existe aqui entra junto com o diário novo")

    check(not erros, f"sem erros de JS ({erros})")
    b.close()

print()
print("FALHAS:", falhas if falhas else "nenhuma")
