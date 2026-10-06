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


APONTADOR = "501 – Marcelo Dias (Qualidade / Apontamento)"

with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    ctx = contexto(b, viewport={"width": 480, "height": 900})
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

    # ---- transporte de material: placa, volume e peso ----
    page.click('.tab[data-view="diario"]')
    linha = page.locator("#eventosDiaList .item-row").nth(0)
    check(linha.locator("input[placeholder='Placa']").count() == 0,
          "sem marcar transporte, os campos de placa/volume/peso ficam escondidos")
    linha.locator("input[type=checkbox]").check()
    linha = page.locator("#eventosDiaList .item-row").nth(0)
    linha.locator("input[placeholder='Placa']").fill("abc1d23")
    linha.locator("input[placeholder='Volume (m³)']").fill("12,5")
    linha.locator("input[placeholder='Peso (t)']").fill("18")
    ev = page.evaluate("currentDay.eventosDia[0]")
    check(ev["transporte"] is True and ev["placa"] == "ABC1D23" and ev["volume"] == "12,5" and ev["peso"] == "18",
          f"transporte grava placa (maiúscula), volume e peso ({ev})")
    wa = page.evaluate("buildRelatorio(currentDay)")
    check("🚛 Placa ABC1D23 · Volume 12,5 m³ · Peso 18 t" in wa, "WhatsApp traz a linha de transporte")
    page.evaluate("gerarPdfRDO()")
    page.wait_for_timeout(500)
    pdf = page.inner_text("#pdfOverlay")
    check("ABC1D23" in pdf and "12,5 m³" in pdf and "18 t" in pdf, "PDF traz placa, volume e peso")
    page.evaluate("fecharPdfRDO()")

    # painel do Cadastro tem o mesmo marcador (tipo que ainda está no catálogo)
    page.click('.tab[data-view="config"]')
    page.click('.subtab[data-pane="eventosdia"]')
    page.locator("#configEventosDiaList .ativ-item-wrap").first.locator("input[type=checkbox]").first.check()
    wrap = page.locator("#configEventosDiaList .ativ-item-wrap").first
    check(wrap.locator("input[placeholder='Placa']").count() == 0, "painel: transporte começa desmarcado")
    wrap.locator("input[type=checkbox]").nth(1).check()
    wrap = page.locator("#configEventosDiaList .ativ-item-wrap").first
    wrap.locator("input[placeholder='Placa']").fill("pqr1s23")
    ev = page.evaluate("currentDay.eventosDia.find(e => e.tipoId === 'ed2')")
    check(ev and ev["transporte"] is True and ev["placa"] == "PQR1S23",
          f"painel do Cadastro grava o transporte do evento ({ev})")
    page.click('.tab[data-view="diario"]')

    # desmarcar esconde e tira dos relatórios, sem apagar o digitado
    page.locator("#eventosDiaList .item-row").nth(0).locator("input[type=checkbox]").uncheck()
    ev = page.evaluate("currentDay.eventosDia[0]")
    check(ev["transporte"] is False and ev["placa"] == "ABC1D23", "desmarcar mantém o digitado guardado")
    wa = page.evaluate("buildRelatorio(currentDay)")
    check("ABC1D23" not in wa, "sem transporte marcado, WhatsApp não traz placa")
    page.locator("#eventosDiaList .item-row").nth(0).locator("input[type=checkbox]").check()

    # avulso com transporte
    page.evaluate("abrirModalEventoDoDiaAvulso()")
    check(not page.is_visible("#modalEvDiaAvulsoPlaca"), "modal do avulso abre sem os campos de transporte")
    page.fill("#modalEvDiaAvulsoTipo", "Entrada de brita")
    page.check("#modalEvDiaAvulsoTransp")
    check(page.is_visible("#modalEvDiaAvulsoPlaca"), "marcar transporte no avulso mostra os campos")
    page.fill("#modalEvDiaAvulsoPlaca", "xyz9k88")
    page.fill("#modalEvDiaAvulsoVolume", "8")
    page.fill("#modalEvDiaAvulsoPeso", "13,2")
    page.evaluate("salvarEventoDoDiaAvulso()")
    ev = page.evaluate("currentDay.eventosDia[currentDay.eventosDia.length - 1]")
    check(ev["tipo"] == "Entrada de brita" and ev["transporte"] is True and ev["placa"] == "XYZ9K88"
          and ev["volume"] == "8" and ev["peso"] == "13,2", f"avulso grava o transporte ({ev})")

    # ---- fornecedor e valor da carga (independem do transporte) ----
    page.click('.tab[data-view="diario"]')
    linha = page.locator("#eventosDiaList .item-row").nth(0)
    linha.locator("input[placeholder='Fornecedor']").fill("Votorantim Cimentos")
    linha.locator("input[placeholder='Valor da carga (R$)']").fill("4.850,00")
    ev = page.evaluate("currentDay.eventosDia[0]")
    check(ev["fornecedor"] == "Votorantim Cimentos" and ev["valorCarga"] == "4.850,00",
          f"fornecedor e valor da carga gravados ({ev})")
    wa = page.evaluate("buildRelatorio(currentDay)")
    check("🏭 Fornecedor Votorantim Cimentos · Valor R$ 4.850,00" in wa, "WhatsApp traz fornecedor e valor")
    page.evaluate("gerarPdfRDO()")
    page.wait_for_timeout(500)
    pdf = page.inner_text("#pdfOverlay")
    check("Votorantim Cimentos" in pdf and "R$ 4.850,00" in pdf, "PDF traz fornecedor e valor")
    page.evaluate("fecharPdfRDO()")
    page.evaluate("currentDay.eventosDia[0].valorCarga = 'R$ 100'")
    check("Valor R$ 100" in page.evaluate("textoCargaEvento(currentDay.eventosDia[0])")
          and "R$ R$" not in page.evaluate("textoCargaEvento(currentDay.eventosDia[0])"),
          "se o usuário já digitou R$, não duplica o prefixo")
    page.evaluate("currentDay.eventosDia[0].valorCarga = '4.850,00'")

    page.click('.tab[data-view="config"]')
    page.click('.subtab[data-pane="eventosdia"]')
    check(page.locator("#configEventosDiaList input[placeholder='Fornecedor']").count() >= 1,
          "painel do Cadastro tem fornecedor e valor")
    page.click('.tab[data-view="diario"]')

    page.evaluate("abrirModalEventoDoDiaAvulso()")
    page.fill("#modalEvDiaAvulsoTipo", "Compra emergencial")
    page.fill("#modalEvDiaAvulsoFornecedor", "Casa do Construtor")
    page.fill("#modalEvDiaAvulsoValor", "980")
    page.evaluate("salvarEventoDoDiaAvulso()")
    ev = page.evaluate("currentDay.eventosDia[currentDay.eventosDia.length - 1]")
    check(ev["fornecedor"] == "Casa do Construtor" and ev["valorCarga"] == "980" and ev["transporte"] is False,
          f"avulso grava fornecedor e valor sem exigir transporte ({ev})")

    # ---- resumos de semana / mês / ano somam atividades e eventos ----
    seed = page.evaluate("""(ap) => {
        const ativ = state.atividades[0];
        const mk = (data, qtd, eventos) => {
          const d = Object.assign(EMPTY_DAY(), {data, apontador: ap, eventosDia: eventos});
          d.atividadesMarcadas[ativ.id] = true; d.atividadesQtd[ativ.id] = qtd;
          history[chaveDiario(data, ap)] = d;
        };
        const cim = (vol, peso, valor) => ({id: uid('ev'), tipoId: 'ed1', tipo: 'Chegada de material', hora: '', detalhe: '',
          fornecedor: 'X', valorCarga: valor, transporte: true, placa: 'AAA1A11', volume: vol, peso: peso, custom: false});
        const quebra = () => ({id: uid('ev'), tipoId: 'ed3', tipo: 'Quebra de equipamento', hora: '', detalhe: '',
          fornecedor: '', valorCarga: '', transporte: false, placa: '', volume: '', peso: '', custom: false});
        // semana de 11/03 a 16/03/2024 (referência: quarta 13/03; 2024 = ano sem outros dados do teste)
        mk('2024-03-11', 10, [cim('12,5', '18', '4.850,00')]);
        mk('2024-03-13', 20, [cim('10', '15,5', 'R$ 1.000'), quebra()]);
        // mesmo mês, outra semana
        mk('2024-03-20', 5, [cim('8', '12', '980')]);
        // mesmo ano, outro mês
        mk('2024-02-10', 7, [cim('20', '30', '2.000,50')]);
        // outro ano: não pode entrar em nada
        mk('2023-12-30', 100, [cim('999', '999', '999999')]);
        return {unid: ativ.unidade, id: ativ.id};
    }""", APONTADOR)

    def soma(ini, fim):
        return page.evaluate("(a) => { const r = calcResumoPeriodoPDF(a[0], a[1]); return {atv: r.acum[a[2]] || 0, ev: r.eventos, tot: r.totalEventos}; }",
                             [ini, fim, seed["id"]])

    sem = soma("2024-03-11", "2024-03-16")
    check(sem["atv"] == 30, f"semana: atividade soma 10+20 = 30 ({sem['atv']})")
    t = sem["tot"]
    check(t["ocorrencias"] == 3 and t["cargas"] == 2 and abs(t["volume"] - 22.5) < 1e-9
          and abs(t["peso"] - 33.5) < 1e-9 and abs(t["valor"] - 5850) < 1e-9,
          f"semana: 3 ocorrências, 2 cargas, 22,5 m³, 33,5 t, R$ 5.850 ({t})")
    check(sem["ev"]["Chegada de material"]["cargas"] == 2 and sem["ev"]["Quebra de equipamento"]["cargas"] == 0,
          "semana: quebra de equipamento conta como ocorrência, sem carga")
    mes = soma("2024-03-01", "2024-03-31")["tot"]
    check(mes["cargas"] == 3 and abs(mes["volume"] - 30.5) < 1e-9 and abs(mes["peso"] - 45.5) < 1e-9
          and abs(mes["valor"] - 6830) < 1e-9, f"mês: 3 cargas, 30,5 m³, 45,5 t, R$ 6.830 ({mes})")
    ano = soma("2024-01-01", "2024-12-31")
    check(ano["atv"] == 42 and ano["tot"]["cargas"] == 4 and abs(ano["tot"]["valor"] - 8830.5) < 1e-9
          and abs(ano["tot"]["volume"] - 50.5) < 1e-9, f"ano: atividade 42, 4 cargas, R$ 8.830,50 ({ano['atv']}, {ano['tot']})")
    check(page.evaluate("[numeroBR('4.850,00'), numeroBR('4.850'), numeroBR('12.5'), numeroBR('12,5'), numeroBR('R$ 980'), numeroBR('18 t'), numeroBR('')]")
          == [4850, 4850, 12.5, 12.5, 980, 18, 0], "leitura de números em pt-BR (milhar, vírgula, R$, unidade)")

    # relatórios do dia 11/03 trazem os três resumos
    page.evaluate("""(ap) => { currentDay = JSON.parse(JSON.stringify(history[chaveDiario('2024-03-13', ap)])); }""", APONTADOR)
    wa = page.evaluate("buildRelatorio(currentDay)")
    check("Resumo da Semana" in wa and "Resumo do Mês" in wa and "Resumo do Ano" in wa, "WhatsApp traz semana, mês e ano")
    check("• Chegada de material: *2x* — 2 cargas · 22,5 m³ · 33,5 t · R$ 5.850,00" in wa,
          "WhatsApp (semana): evento somado com cargas, volume, peso e valor")
    check("• *Total:* *3x* — 2 cargas · 22,5 m³ · 33,5 t · R$ 5.850,00" in wa, "WhatsApp (semana): linha de total")
    check("3 cargas · 30,5 m³ · 45,5 t · R$ 6.830,00" in wa, "WhatsApp (mês): totais do mês")
    check("4 cargas · 50,5 m³ · 75,5 t · R$ 8.830,50" in wa, "WhatsApp (ano): totais do ano")
    check("999" not in wa, "WhatsApp: dia de outro ano não entra")
    page.evaluate("gerarPdfRDO()")
    page.wait_for_timeout(600)
    pdf = page.inner_text("#pdfOverlay")
    check("ACUMULADOS" in pdf and "SEMANA" in pdf.upper() and "MÊS" in pdf.upper() and "ANO" in pdf.upper(),
          "PDF traz a tabela de acumulados com semana, mês e ano")
    check("R$ 5.850,00" in pdf and "R$ 6.830,00" in pdf and "R$ 8.830,50" in pdf,
          "PDF traz o valor somado de semana, mês e ano na mesma linha")
    check("Cargas de material" in pdf and "Volume (m³)" in pdf and "Peso (ton)" in pdf,
          "PDF traz cargas, volume e peso acumulados")
    page.evaluate("fecharPdfRDO()")

    # ---- aba Resumo (tela): eventos acumulados no período ----
    page.click('.tab[data-view="resumo"]')
    page.evaluate("setResumoPeriodo('ano'); resumoOffset = 2024 - new Date().getFullYear(); renderResumo();")
    tela = page.inner_text("#resumoEventosList")
    check("Chegada de material" in tela and "Quebra de equipamento" in tela and "TOTAL" in tela.upper(),
          "aba Resumo (ano 2024) lista os tipos de evento e o total")
    check("4 cargas" in tela and "50,5 m³" in tela and "75,5 t" in tela and "R$ 8.830,50" in tela,
          f"aba Resumo traz cargas, volume, peso e valor somados ({tela!r})")
    check(page.eval_on_selector("#resumoEventosList", "e => e.previousElementSibling.textContent").strip().endswith("Eventos do Período"),
          "seção chama 'Eventos do Período'")
    page.evaluate("resumoOffset = 2024 - new Date().getFullYear() + 5; renderResumo();")
    check("Nenhum evento registrado no período" in page.inner_text("#resumoEventosList"),
          "período sem eventos mostra a mensagem de vazio")
    page.evaluate("resumoOffset = 2024 - new Date().getFullYear(); renderResumo();")
    txt = page.evaluate("buildResumoTexto()")
    check("📌 Eventos do Período" in txt and "• Chegada de material: *4x* — 4 cargas · 50,5 m³ · 75,5 t · R$ 8.830,50" in txt
          and "• *Total:* *5x*" in txt, "Copiar/Enviar da aba Resumo traz os eventos acumulados")
    check("_Eventos acumulados_" not in txt, "texto da aba não repete o subtítulo do relatório do dia")
    page.click('.tab[data-view="diario"]')

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
