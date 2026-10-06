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
PNG = bytes.fromhex("89504e470d0a1a0a0000000d4948445200000001000000010806000000" "1f15c4890000000d49444154789c6360f8cfc0f01f0005000201" "e221bc330000000049454e44ae426082")


def preencher(page, equipe_g, equipe_n, tipo, resp, desc, local="", hora=None):
    page.evaluate("abrirModalEventoDiaNovo()")
    if hora:
        page.fill("#evdHora", hora)
    page.click(f'#evdEquipes .evd-chip[data-g="{equipe_g}"][data-n="{equipe_n}"]')
    page.click(f'#evdTipos .evd-chip[data-t="{tipo}"]')
    page.fill("#evdResp", resp)
    page.fill("#evdDesc", desc)
    if local:
        page.fill("#evdLocal", local)


with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    ctx = contexto(b, viewport={"width": 480, "height": 900}, accept_downloads=True)
    page = ctx.new_page()
    erros = []
    page.on("pageerror", lambda e: erros.append(str(e)))
    page.on("dialog", lambda d: d.dismiss())
    page.route("**/script.google.com/**", lambda r: r.fulfill(
        status=200, content_type="application/json", body=json.dumps({"ok": True})))
    page.goto(f"{BASE}/rdo.html")
    page.wait_for_timeout(1000)
    page.evaluate("currentDay.apontador = %s" % json.dumps(APONTADOR))
    DATA = page.evaluate("currentDay.data")

    # ---- estrutura ----
    check(page.locator("#observacoesDia").count() == 0, "campo Observações do Dia não existe mais")
    check(page.locator("#eventosDiaList").count() == 1, "seção Eventos do Dia existe no Diário")
    diario = page.text_content("#view-diario")
    check("Eventos do Dia" in diario and "Observações do Dia" not in diario, "título 'Eventos do Dia' (o antigo não aparece)")
    check("Acidentes de Segurança do Trabalho" in diario and "Acidentes de Meio Ambiente" in diario
          and "Eventos de Segurança" not in diario and "Eventos de Meio Ambiente" not in diario,
          "seções de segurança e meio ambiente chamam-se Acidentes")

    # ---- catálogo padrão e migração do catálogo antigo ----
    tipos = page.evaluate("state.eventosDia.map(e => e.desc)")
    check(len(tipos) == 11 and "Liberação de trabalho" in tipos and "Paralisação de trabalho" in tipos and "Marcação de acesso" in tipos,
          f"catálogo padrão com 11 tipos de evento ({tipos})")
    eqs = page.evaluate("state.equipesEvento.map(e => e.grupo + '|' + e.nome)")
    check(len(eqs) == 10 and "Fiscalização|Topografia" in eqs and "Cesbe|Laboratório" in eqs, f"10 equipes (4 da Fiscalização + 6 da Cesbe) ({eqs})")
    mig = page.evaluate("""() => {
      const antigo = { obra: { nome: 'X' }, eventosDia: [{ id: 'ed1', desc: 'Chegada de material' }, { id: 'ed9', desc: 'Liberação de trabalho' }] };
      const a = mergeDefaults(antigo);
      const b = mergeDefaults(JSON.parse(JSON.stringify(a)));
      return { a: a.eventosDia.map(t => t.desc), b: b.eventosDia.length, eq: a.equipesEvento.length, v2: a.eventosV2 };
    }""")
    check("Chegada de material" in mig["a"] and mig["a"].count("Liberação de trabalho") == 1 and len(mig["a"]) == 12 and mig["eq"] == 10 and mig["v2"] is True,
          f"catálogo antigo mantém o que tinha e ganha os novos sem duplicar ({mig})")
    check(mig["b"] == 12, "migrar de novo não acrescenta nada")

    # ---- registrar um evento ----
    page.evaluate("abrirModalEventoDiaNovo()")
    check(page.is_visible("#modalEvDia") and page.input_value("#evdHora") != "", "janela abre com a hora já preenchida")
    check(page.locator("#evdEquipes .evd-grp").count() == 2, "equipes aparecem separadas em Fiscalização e Cesbe")
    check(not page.is_visible("#evdRetomada"), "retomada começa escondida")
    page.click("#evdSalvarBtn")
    check(page.evaluate("eventosAtivos(currentDay).length") == 0, "sem equipe, evento e responsável não salva")
    page.evaluate("fecharModal('modalEvDia')")

    preencher(page, "Fiscalização", "Segurança do Trabalho", "Liberação de trabalho", "Fiscal Souza",
              "Escavação da vala V-03 liberada após o DDS", "Frente 2", "07:30")
    page.click("#evdSalvarBtn")
    ev = page.evaluate("eventosAtivos(currentDay)")
    check(len(ev) == 1 and ev[0]["tipo"] == "Liberação de trabalho" and ev[0]["grupo"] == "Fiscalização" and ev[0]["equipe"] == "Segurança do Trabalho"
          and ev[0]["responsavel"] == "Fiscal Souza" and ev[0]["local"] == "Frente 2" and ev[0]["hora"] == "07:30"
          and ev[0]["detalhe"] == "Escavação da vala V-03 liberada após o DDS" and ev[0]["paralisacao"] is False and ev[0]["fotos"] == [],
          f"evento grava hora, equipe, evento, descrição, responsável e local ({ev})")
    card = page.inner_text("#eventosDiaList")
    check("07:30" in card and "Liberação de trabalho" in card and "Fiscalização · Segurança do Trabalho" in card and "Fiscal Souza" in card and "Frente 2" in card,
          "o cartão do Diário mostra tudo")

    # ---- paralisação ----
    page.evaluate("abrirModalEventoDiaNovo()")
    page.click('#evdEquipes .evd-chip[data-g="Fiscalização"][data-n="Meio Ambiente"]')
    page.click('#evdTipos .evd-chip[data-t="Paralisação de trabalho"]')
    check(page.is_checked("#evdPar") and page.is_visible("#evdRetomada"), "escolher 'Paralisação de trabalho' marca o checkbox e abre a retomada")
    page.fill("#evdHora", "14:05"); page.fill("#evdResp", "Fiscal Lima"); page.fill("#evdDesc", "Supressão paralisada até conferir a licença")
    page.fill("#evdRetData", DATA)
    page.click("#evdSalvarBtn")
    check(page.evaluate("eventosAtivos(currentDay).length") == 1, "data da retomada sem hora é recusada")
    page.fill("#evdRetHora", "13:00")
    page.click("#evdSalvarBtn")
    check(page.evaluate("eventosAtivos(currentDay).length") == 1, "retomada antes da paralisação é recusada")
    page.fill("#evdRetHora", "16:35")
    page.click("#evdSalvarBtn")
    ev = page.evaluate("eventosAtivos(currentDay)[1]")
    check(ev["paralisacao"] is True and ev["retomadaData"] == DATA and ev["retomadaHora"] == "16:35", f"paralisação grava data e hora da retomada ({ev})")
    check(page.evaluate("minutosParadoEvento(eventosAtivos(currentDay)[1], currentDay.data)") == 150, "tempo parado: 14:05 a 16:35 = 150 min")
    check("2h30" in page.inner_text("#eventosDiaList") and "⛔" in page.inner_text("#eventosDiaList"), "o cartão mostra a paralisação e o tempo parado")

    # paralisação em aberto (sem retomada)
    preencher(page, "Cesbe", "Civil", "Visita / vistoria", "Enc. Lima", "Parada para troca de mangueira", "Frente 1", "10:00")
    page.check("#evdPar")
    page.click("#evdSalvarBtn")
    aberto = page.evaluate("eventosAtivos(currentDay)[2]")
    check(aberto["paralisacao"] is True and aberto["retomadaData"] == "" and "Retomada em aberto" in page.evaluate("textoParalisacaoEvento(eventosAtivos(currentDay)[2], currentDay.data)"),
          "paralisação pode ficar com a retomada em aberto")
    # editar: registrar a retomada depois
    ordem = page.evaluate("[...currentDay.eventosDia].findIndex(e => e.hora === '10:00')")
    page.evaluate(f"abrirModalEventoDiaNovo({ordem})")
    check(page.input_value("#evdResp") == "Enc. Lima" and page.is_checked("#evdPar") and page.input_value("#evdLocal") == "Frente 1", "editar abre com os dados do evento")
    page.fill("#evdRetData", DATA); page.fill("#evdRetHora", "11:20")
    page.click("#evdSalvarBtn")
    ed = page.evaluate(f"currentDay.eventosDia[{ordem}]")
    check(ed["retomadaHora"] == "11:20" and page.evaluate("eventosAtivos(currentDay).length") == 3, "editar atualiza o mesmo evento (não duplica)")

    # ---- fotos (até 3) ----
    page.evaluate("abrirModalEventoDiaNovo()")
    for _ in range(4):
        if page.locator("#evdFotos .evd-foto-add").count():
            page.set_input_files("#evdFotoInput", files=[{"name": "f.png", "mimeType": "image/png", "buffer": PNG}])
            page.wait_for_timeout(250)
    check(page.evaluate("evdFotos.length") == 3 and page.locator("#evdFotos .evd-foto").count() == 3 and page.locator("#evdFotos .evd-foto-add").count() == 0,
          "até 3 fotos por evento (o botão + some no limite)")
    page.click('#evdEquipes .evd-chip[data-g="Cesbe"][data-n="Topografia"]')
    page.click('#evdTipos .evd-chip[data-t="Marcação de acesso"]')
    page.fill("#evdHora", "09:40"); page.fill("#evdResp", "Topógrafo Reis"); page.fill("#evdDesc", "Acesso à jazida marcado da estaca 12 à 18"); page.fill("#evdLocal", "Jazida")
    page.click("#evdSalvarBtn")
    check(page.evaluate("eventosAtivos(currentDay).find(e => e.hora === '09:40').fotos.length") == 3 and page.locator("#eventosDiaList .evc-fotos img").count() == 3,
          "fotos ficam no evento e aparecem no cartão")

    # equipe e evento novos direto da janela
    page.evaluate("abrirModalEventoDiaNovo()")
    page.click("#evdEquipes .evd-chip.mais")
    page.fill("#evdNovoGrupo", "Terceiros"); page.fill("#evdNovoEquipeNome", "Meteorologia")
    page.click("#evdNovoEquipe .btn-primary")
    page.click("#evdTipos .evd-chip.mais")
    page.fill("#evdNovoTipoNome", "Alerta de chuva")
    page.click("#evdNovoTipo .btn-primary")
    check(page.evaluate("evdSel.equipe === 'Meteorologia' && evdSel.tipo === 'Alerta de chuva'") and
          page.evaluate("state.equipesEvento.some(e => e.nome === 'Meteorologia' && e.grupo === 'Terceiros') && state.eventosDia.some(t => t.desc === 'Alerta de chuva')"),
          "+ equipe e + evento cadastram e já selecionam")
    page.evaluate("fecharModal('modalEvDia')")

    # ---- baixa lógica do evento do dia ----
    n_antes = page.evaluate("currentDay.eventosDia.length")
    idx = page.evaluate("currentDay.eventosDia.findIndex(e => e.hora === '10:00')")
    page.evaluate(f"removerEventoDoDia({idx})")
    page.click("#modalConfirmYes")
    check(page.evaluate("currentDay.eventosDia.length") == n_antes and page.evaluate("eventosAtivos(currentDay).length") == 3,
          "remover é baixa lógica: o evento continua nos dados, some das telas e dos relatórios")
    check("Parada para troca de mangueira" not in page.inner_text("#eventosDiaList"), "evento removido some da lista do Diário")

    # ---- dados antigos (transporte, fornecedor, valor) — nada se perde ----
    page.evaluate("""() => { currentDay.eventosDia.push({ id: 'leg1', tipoId: 'ed1', tipo: 'Chegada de material', hora: '11:00', detalhe: 'Brita 1', custom: false,
        fornecedor: 'Pedreira Exemplo', valorCarga: '4.800,00', transporte: true, placa: 'ABC1D23', volume: '12', peso: '18' }); salvarDiarioDia(false); renderEventosDoDia(); }""")
    leg = "Dados antigos: Fornecedor Pedreira Exemplo · Valor R$ 4.800,00 · Placa ABC1D23 · Volume 12 m³ · Peso 18 t"
    check(leg in page.inner_text("#eventosDiaList"), "evento antigo mostra os dados de carga como 'Dados antigos'")
    page.evaluate("currentDay.eventosDia.find(e => e.id === 'leg1').transporte = false")
    check("Placa ABC1D23" in page.evaluate("textoLegadoEvento(currentDay.eventosDia.find(e => e.id === 'leg1'))"), "desmarcar o transporte antigo não esconde a placa")
    page.evaluate("currentDay.eventosDia.find(e => e.id === 'leg1').transporte = true")

    # ---- Cadastro → Eventos ----
    page.click('.tab[data-view="config"]')
    page.click('.subtab[data-pane="eventosdia"]')
    cfg = page.inner_text("#pane-eventosdia")
    check("Fiscalização" in cfg and "Segurança do Trabalho" in cfg and "Liberação de trabalho" in cfg and "Adicionar Equipe" in cfg, "Cadastro lista equipes e tipos de evento")
    check(page.locator("#configEventosDiaList input[type=checkbox]").count() == 0, "a lista de tipos com caixinha ✓ acabou")
    page.evaluate("abrirModalEquipeEv()")
    page.fill("#equipeEvGrupo", "Cesbe"); page.fill("#equipeEvNome", "Geotecnia")
    page.evaluate("salvarEquipeEv()")
    check(page.evaluate("state.equipesEvento.some(e => e.nome === 'Geotecnia' && e.grupo === 'Cesbe')"), "equipe nova entra no catálogo")
    eid = page.evaluate("state.equipesEvento.find(e => e.nome === 'Geotecnia').id")
    page.evaluate(f"removerEquipeEv('{eid}')")
    page.click("#modalConfirmYes")
    check(page.evaluate(f"state.equipesEvento.find(e => e.id === '{eid}').inativo") is True, "remover equipe do cadastro é baixa lógica")
    page.evaluate("removerEventoCadastro('eventosDia', 'et2')")
    page.click("#modalConfirmYes")
    check(page.evaluate("state.eventosDia.find(t => t.id === 'et2').inativo") is True and page.evaluate("eventosAtivos(currentDay).some(e => e.tipo === 'Paralisação de trabalho')"),
          "remover tipo do cadastro: sai das opções e o evento já registrado continua")
    page.evaluate("abrirModalEventoDiaNovo()")
    check(page.locator('#evdTipos .evd-chip[data-t="Paralisação de trabalho"]').count() == 0, "tipo removido não aparece mais na janela de registro")
    page.evaluate("fecharModal('modalEvDia')")
    page.evaluate("reativarNoCadastro(state.eventosDia.find(t => t.id === 'et2')); saveState()")
    page.click('.tab[data-view="diario"]')

    # ---- WhatsApp ----
    wa = page.evaluate("buildRelatorio(currentDay)")
    check("Eventos do Dia — 4" in wa and "07:30 — *Liberação de trabalho*" in wa and "Equipe: Fiscalização · Segurança do Trabalho" in wa
          and "Resp.: Fiscal Souza · 📍 Frente 2" in wa and "Escavação da vala V-03 liberada após o DDS" in wa, "WhatsApp traz hora, evento, equipe, descrição, responsável e local")
    check("⛔ Paralisação. Retomada" in wa and "(2h30 parado)" in wa, "WhatsApp traz a paralisação com retomada e tempo parado")
    check("📷 3 fotos" in wa and leg in wa, "WhatsApp traz o número de fotos e os dados antigos")
    check("_Resumo dos eventos_" in wa and "Fiscalização · Meio Ambiente: *1x* · 1 paralisação · 2h30 parado" in wa, "WhatsApp traz o resumo por equipe")
    check("Parada para troca de mangueira" not in wa, "evento removido não vai no WhatsApp")
    check("Acidentes de Segurança do Trabalho" in page.evaluate("(() => { const d = JSON.parse(JSON.stringify(currentDay)); d.eventosSeguranca = [{tipo: 'Quase-acidente', gravidade: 'leve', desc: 'x', acao: 'y'}]; return buildRelatorio(d); })()"),
          "WhatsApp chama de Acidentes de Segurança do Trabalho")

    # ---- PDF ----
    page.evaluate("gerarPdfRDO()")
    page.wait_for_timeout(600)
    pdf = page.inner_text("#pdfOverlay")
    for trecho, nome in [("EVENTOS DO DIA", "título"), ("Equipe", "coluna Equipe"), ("Responsável", "coluna Responsável"), ("Local", "coluna Local"),
                         ("Fiscal Souza", "responsável"), ("Frente 2", "local"), ("Fiscalização · Meio Ambiente", "equipe"),
                         ("Retomada 16:35 (2h30)", "retomada e tempo parado"), ("Resumo: 4 eventos", "resumo"), ("Por equipe:", "resumo por equipe"),
                         ("FOTOS DOS EVENTOS — 3", "bloco de fotos"), ("09:40 · Marcação de acesso (1/3)", "legenda da foto"), (leg, "dados antigos"),
                         ("Escavação da vala V-03 liberada após o DDS", "descrição")]:
        check(trecho.lower() in pdf.lower(), f"PDF traz: {nome}")
    check("Parada para troca de mangueira" not in pdf, "evento removido não vai no PDF")
    horas = page.evaluate("[...document.querySelectorAll('#pdfOverlay .cx-tit')].find(e => /eventos do dia/i.test(e.textContent)).parentElement.querySelectorAll('tr td:first-child')")
    seq = page.evaluate("[...[...document.querySelectorAll('#pdfOverlay .cx-tit')].find(e => /^eventos do dia/i.test(e.textContent)).parentElement.querySelectorAll('tr')].slice(1, -1).map(r => r.children[0].textContent)")
    check(seq == sorted(seq), f"planilha do PDF em ordem cronológica ({seq})")
    page.evaluate("fecharPdfRDO()")

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

    # ---- planilha de eventos do período na aba Resumo e em .csv ----
    page.click('.tab[data-view="resumo"]')
    page.evaluate("setResumoPeriodo('ano'); resumoOffset = 0; renderResumo();")
    tela = page.inner_text("#resumoEventosList")
    check("Liberação de trabalho" in tela and "Fiscal Souza" in tela and "Frente 2" in tela and "Marcação de acesso" in tela
          and "Retomada" in tela and "Fiscalização · Meio Ambiente" in tela, "aba Resumo traz a planilha de eventos do período (equipe, responsável, local, retomada)")
    check("1 paralisação" in tela or "paralisaç" in tela.lower(), "aba Resumo conta as paralisações")
    check("Parada para troca de mangueira" not in tela, "evento removido não entra no Resumo")
    with page.expect_download() as dl:
        page.evaluate("baixarCsvEventos()")
    nome = dl.value.suggested_filename
    csv = open(dl.value.path(), encoding="utf-8-sig").read()
    cab = csv.splitlines()[0]
    check(nome.startswith("eventos-do-dia_") and nome.endswith(".csv"), f"nome do arquivo .csv ({nome})")
    check(cab == '"Data";"Hora";"Grupo";"Equipe";"Evento";"Descrição";"Responsável";"Local";"Paralisação";"Data da retomada";"Hora da retomada";"Tempo parado";"Fotos";"Dados antigos";"Apontador"',
          "colunas do .csv")
    check('"Fiscal Souza";"Frente 2"' in csv and '"Sim"' in csv and '"2h30"' in csv and "Fornecedor Pedreira Exemplo" in csv and '"3"' in csv,
          "o .csv leva todos os campos (responsável, local, paralisação, tempo parado, fotos e dados antigos)")
    check("Parada para troca de mangueira" not in csv, "evento removido fora do .csv")
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
