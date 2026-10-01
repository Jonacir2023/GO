import json
import os
from playwright.sync_api import sync_playwright

BASE = os.environ.get("BUILDLY_URL", "http://localhost:8795")
falhas = []


def check(cond, msg):
    print(("  OK   " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


APONTADOR = "501 – Marcelo Dias (Qualidade / Apontamento)"

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

    # ---- Observações do Dia virou Eventos do Dia ----
    check(page.locator("#observacoesDia").count() == 0, "campo Observações do Dia não existe mais")
    check(page.locator("#eventosDiaList").count() == 1, "seção Eventos do Dia existe no Diário")
    diario = page.text_content("#view-diario")
    check("Eventos do Dia" in diario, "título 'Eventos do Dia' aparece")
    check("Observações do Dia" not in diario, "título antigo não aparece")

    tipos = page.evaluate("state.eventosDia.map(e => e.desc)")
    check(tipos == ["Chegada de material", "Chegada de equipamentos", "Quebra de equipamento",
                    "Mudança de estratégia"], f"catálogo padrão com 4 tipos ({tipos})")

    # ---- cadastro: marcar um tipo cria o evento no dia ----
    page.evaluate("currentDay.apontador = %s" % json.dumps(APONTADOR))
    page.click('.tab[data-view="config"]')
    page.click('.subtab[data-pane="eventosdia"]')
    check(page.locator("#configEventosDiaList input[type=checkbox]").count() == 4,
          "painel do cadastro lista os 4 tipos com caixinha")
    page.locator("#configEventosDiaList input[type=checkbox]").nth(0).check()
    ev = page.evaluate("currentDay.eventosDia")
    check(len(ev) == 1 and ev[0]["tipo"] == "Chegada de material" and ev[0]["tipoId"] == "ed1",
          f"marcar o tipo registra o evento no dia ({ev})")
    page.locator("#configEventosDiaList input[type=time]").first.fill("08:30")
    page.locator("#configEventosDiaList input[type=text]").first.fill("Cimento CP-II, NF 1234")
    page.locator("#configEventosDiaList input[type=text]").first.blur()
    ev = page.evaluate("currentDay.eventosDia[0]")
    check(ev["hora"] == "08:30" and ev["detalhe"] == "Cimento CP-II, NF 1234",
          f"horário e detalhe gravados ({ev})")

    # ---- Diário mostra o evento ----
    page.click('.tab[data-view="diario"]')
    txt = page.inner_text("#eventosDiaList")
    check("Chegada de material" in txt, "evento aparece na lista do Diário")
    check(page.eval_on_selector("#eventosDiaList input[type=time]", "e => e.value") == "08:30",
          "horário aparece no Diário")

    # ---- evento avulso ----
    page.evaluate("abrirModalEventoDoDiaAvulso()")
    page.fill("#modalEvDiaAvulsoTipo", "Visita da fiscalização")
    page.fill("#modalEvDiaAvulsoHora", "14:00")
    page.fill("#modalEvDiaAvulsoDetalhe", "Vistoria da armação")
    page.evaluate("salvarEventoDoDiaAvulso()")
    ev = page.evaluate("currentDay.eventosDia")
    check(len(ev) == 2 and ev[1]["custom"] is True and ev[1]["tipo"] == "Visita da fiscalização",
          "evento avulso entra na lista")

    # ---- baixa: remover o tipo do cadastro não apaga o evento do dia ----
    page.evaluate("removerEventoCadastro('eventosDia', 'ed1')")
    page.click("#modalConfirmYes")
    check(page.evaluate("state.eventosDia.length") == 3, "tipo sai do cadastro")
    check(page.evaluate("currentDay.eventosDia.some(e => e.tipo === 'Chegada de material')"),
          "o evento já registrado no dia continua lá (cópia do nome)")

    # ---- WhatsApp e PDF ----
    wa = page.evaluate("buildRelatorio(currentDay)")
    check("Eventos do Dia — 2" in wa and "08:30 — Chegada de material: Cimento CP-II, NF 1234" in wa
          and "Visita da fiscalização: Vistoria da armação" in wa, "texto do WhatsApp traz os eventos")
    check("Observações do Dia" not in wa, "WhatsApp não traz mais 'Observações do Dia'")
    page.evaluate("gerarPdfRDO()")
    page.wait_for_timeout(500)
    pdf = page.inner_text("#pdfOverlay")
    check("EVENTOS DO DIA" in pdf and "Cimento CP-II, NF 1234" in pdf and "08:30" in pdf,
          "PDF traz a tabela de eventos do dia")
    page.evaluate("fecharPdfRDO()")

    # ---- dado antigo: observacoesDia vira eventos "Observação" ----
    leg = page.evaluate("""() => {
        const dia = {data: '2026-05-05', observacoesDia: 'Chuva forte * Visita do cliente', eventosDia: []};
        return eventosDoDia(dia).map(e => [e.tipo, e.detalhe]);
    }""")
    check(leg == [["Observação", "Chuva forte"], ["Observação", "Visita do cliente"]],
          f"observações antigas viram eventos 'Observação' ({leg})")
    r = page.evaluate("""(ap) => {
        history[chaveDiario('2026-05-05', ap)] = Object.assign(EMPTY_DAY(), {data: '2026-05-05',
          apontador: ap, observacoesDia: 'Chuva forte * Visita do cliente'});
        initCurrentDay('2026-05-05');
        return {n: currentDay.eventosDia.length, obs: currentDay.observacoesDia};
    }""", APONTADOR)
    check(r["n"] == 2 and r["obs"] == "", f"abrir dia antigo migra o texto e zera o campo antigo ({r})")

    check(not erros, f"sem erros de JS ({erros})")
    b.close()

print()
print("FALHAS:", falhas if falhas else "nenhuma")
