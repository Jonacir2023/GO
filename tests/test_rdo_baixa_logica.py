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
    page = b.new_context(viewport={"width": 480, "height": 900}).new_page()
    erros = []
    page.on("pageerror", lambda e: erros.append(str(e)))
    page.on("dialog", lambda d: d.accept())
    page.route("**/script.google.com/**", lambda r: r.fulfill(
        status=200, content_type="application/json", body=json.dumps({"ok": True})))
    page.goto(f"{BASE}/rdo.html")
    page.wait_for_timeout(900)

    # ---- a regra de vigência ----
    v = page.evaluate("""() => {
        const item = {id:'v1', desc:'Fusca', inativo:true, inativoEm:'2026-08-24'};
        return {
          antes:   itemVigenteNoDia(item, '2026-08-23', false),
          noDia:   itemVigenteNoDia(item, '2026-08-24', false),
          depois:  itemVigenteNoDia(item, '2026-08-25', false),
          usado:   itemVigenteNoDia(item, '2026-08-30', true),
          ativo:   itemVigenteNoDia({id:'v2', desc:'Uno'}, '2026-08-30', false)
        };
    }""")
    check(v["antes"] is True, "dia anterior à baixa: item ainda existia")
    check(v["noDia"] is False, "no dia da baixa em diante: sai das listas")
    check(v["depois"] is False, "dia posterior: fora")
    check(v["usado"] is True, "item lançado naquele dia aparece sempre, mesmo com baixa")
    check(v["ativo"] is True, "item sem baixa é sempre vigente")

    # ---- o cenário do Uno e do Fusca ----
    uno = page.evaluate("""() => {
        state.veiculosFrota = [
          {id:'uno', desc:'Uno', placa:'AAA-1111'},
          {id:'fusca', desc:'Fusca', placa:'BBB-2222'}
        ];
        // ontem os dois rodaram
        S.set('vlDia_2026-08-23', {uno:true, fusca:true});
        // hoje o Fusca sai da frota
        baixarDoCadastro(state.veiculosFrota.find(v => v.id === 'fusca'));
        state.veiculosFrota.find(v => v.id==='fusca').inativoEm = '2026-08-24';
        return {
          ontem: vigentesNoDia(state.veiculosFrota, '2026-08-23', S.get('vlDia_2026-08-23')).map(v=>v.id),
          hoje:  vigentesNoDia(state.veiculosFrota, '2026-08-24', {}).map(v=>v.id),
          nadaApagado: state.veiculosFrota.length
        };
    }""")
    check(sorted(uno["ontem"]) == ["fusca", "uno"],
          f"editando ontem, o Fusca continua nas opções: {uno['ontem']}")
    check(uno["hoje"] == ["uno"], f"hoje só o Uno: {uno['hoje']}")
    check(uno["nadaApagado"] == 2, "nada foi apagado do cadastro")

    # ---- "parados" não listam item que saiu da frota ----
    par = page.evaluate("""() => {
        const savedVL = {uno:true};   // hoje só o Uno rodou
        const parados = vigentesNoDia(state.veiculosFrota, '2026-08-25', savedVL)
                          .filter(v => !savedVL[v.id]).map(v=>v.id);
        const paradosOntem = (() => {
            const s = {uno:true};
            return vigentesNoDia(state.veiculosFrota, '2026-08-23', s)
                     .filter(v => !s[v.id]).map(v=>v.id);
        })();
        return {parados, paradosOntem};
    }""")
    check(par["parados"] == [],
          f"veículo com baixa não aparece como 'parado' hoje: {par['parados']}")
    check(par["paradosOntem"] == ["fusca"],
          f"ontem ele aparecia como parado, corretamente: {par['paradosOntem']}")

    # ---- remoção não apaga: as 4 funções ----
    rem = page.evaluate("""() => {
        state.equipamentos = [{id:'e1', numero:'ESC-1', desc:'Escavadeira'}];
        state.atividades   = [{id:'a1', desc:'Concretagem', local:'', unidade:'m3'}];
        state.colaboradores.categorias = [{id:'c1', nome:'Operacional', itens:[{id:'p1', mat:'1', nome:'José'}]}];
        baixarDoCadastro(state.equipamentos[0]);
        baixarDoCadastro(state.atividades[0]);
        baixarDoCadastro(state.colaboradores.categorias[0].itens[0]);
        return {
          equip: state.equipamentos.length, equipInativo: !!state.equipamentos[0].inativo,
          ativ: state.atividades.length,    ativInativo: !!state.atividades[0].inativo,
          colab: state.colaboradores.categorias[0].itens.length,
          colabInativo: !!state.colaboradores.categorias[0].itens[0].inativo,
          temData: !!state.equipamentos[0].inativoEm, temStatusEm: !!state.equipamentos[0].statusEm
        };
    }""")
    check(rem["equip"] == 1 and rem["ativ"] == 1 and rem["colab"] == 1,
          "baixa não remove nada do array")
    check(rem["equipInativo"] and rem["ativInativo"] and rem["colabInativo"],
          "os três grupos ficam marcados como inativos")
    check(rem["temData"] and rem["temStatusEm"], "grava inativoEm e statusEm")

    # ---- recadastrar reativa em vez de duplicar ----
    dup = page.evaluate("""() => {
        state.veiculosFrota = [{id:'f1', desc:'Fusca', placa:'BBB-2222', inativo:true, inativoEm:'2026-08-24'}];
        const voltou = reativarSeJaExiste(state.veiculosFrota, v => v.placa === 'BBB-2222');
        return {achou: !!voltou, total: state.veiculosFrota.length,
                inativo: !!state.veiculosFrota[0].inativo, id: state.veiculosFrota[0].id};
    }""")
    check(dup["achou"] and dup["total"] == 1 and not dup["inativo"],
          f"recadastrar pela placa reativa e não duplica ({dup})")
    check(dup["id"] == "f1", "mantém o mesmo id — RDOs antigos continuam apontando certo")

    naoCasa = page.evaluate("""() => {
        state.equipamentos = [{id:'e9', numero:'X-1', desc:'Outro', inativo:true, inativoEm:'2026-08-24'}];
        return reativarSeJaExiste(state.equipamentos, e => e.numero === 'NAO-EXISTE');
    }""")
    check(naoCasa is None, "item diferente não é reativado por engano")

    # ---- categoria leva os itens junto ----
    cat = page.evaluate("""() => {
        state.colaboradores.categorias = [{id:'c1', nome:'Elétrica',
          itens:[{id:'p1', nome:'A'}, {id:'p2', nome:'B'}]}];
        const c = state.colaboradores.categorias[0];
        baixarDoCadastro(c); (c.itens||[]).forEach(baixarDoCadastro);
        // inativoEm vem do relógio real (todayISO()) — comparar contra ele
        // mesmo, não contra uma data cravada que o tempo ultrapassa.
        const vis = categoriasVigentes(c.inativoEm, {}).length;
        const visAntes = categoriasVigentes('2020-01-01', {}).length;
        return {vis, visAntes, itens: c.itens.length};
    }""")
    check(cat["vis"] == 0 and cat["visAntes"] == 1,
          "categoria com baixa some de hoje e continua nos dias anteriores")
    check(cat["itens"] == 2, "os colaboradores da categoria não foram apagados")

    check(not erros, f"sem erros de JS ({erros})")
    b.close()

print()
print("FALHAS:", falhas if falhas else "nenhuma")
