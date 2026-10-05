import json
import os
import re
import tempfile
from playwright.sync_api import sync_playwright

BASE = os.environ.get("BUILDLY_URL", "http://localhost:8795")
falhas = []


def check(cond, msg):
    print(("  OK   " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


AP = "501 – Marcelo Dias (Qualidade / Apontamento)"

SEMEAR = """([ap]) => {
  const cv = document.createElement('canvas'); cv.width = 400; cv.height = 300;
  const x = cv.getContext('2d'); x.fillStyle = '#78965a'; x.fillRect(0, 0, 400, 300);
  const foto = cv.toDataURL('image/jpeg', 0.7);
  const d = currentDay; d.apontador = ap; d.localObra = 'Base Aerogerador 2'; d.descricaoLocal = 'Escavação para fundação';
  d.cafeFim = '07:00'; d.almocoInicio = '12:00'; d.almocoFim = '13:00'; d.encerramento = '17:00';
  d.dssHorario = '06:50'; d.dssTema = 'Trabalho em altura e içamento';
  d.tempoManha = 'sol'; d.pratManha = 'praticavel'; d.tempoTarde = 'chuva'; d.pratTarde = 'impraticavel'; d.chuvaTardeQtd = '12';
  let c = 0; state.colaboradores.categorias.forEach(cat => cat.itens.forEach(i => { if (c < 14) { d.efetivo[i.id] = true; c++; } }));
  const sv = {}; state.equipamentos.slice(0, 3).forEach(e => sv[e.id] = true); S.set('equipDia_' + d.data, sv);
  state.atividades.slice(0, 4).forEach((a, i) => { d.atividadesMarcadas[a.id] = true; d.atividadesQtd[a.id] = String(10 * (i + 1)); });
  d.atividadesAvulsas = [{ id: 'av1', desc: 'Atendimento à fiscalização', local: 'Acesso 1' }];
  d.atividadesParalisadas = [{ id: 'p1', desc: 'Concretagem de laje', just: 'Chuva forte na tarde' }];
  d.eventosSeguranca = [{ id: 's', tipo: 'Quase-acidente', gravidade: 'media', desc: 'Queda de material a 2 m', acao: 'Isolamento e DDS extra' }];
  d.eventosAmbiente = [{ id: 'm', tipo: 'Emissão de poeira excessiva', gravidade: 'leve', desc: 'Via de acesso', acao: 'Umectação' }];
  d.eventosDia = [
    { id: 'e1', tipo: 'Chegada de material', hora: '08:30', detalhe: 'Cimento CP-II NF 1234', fornecedor: 'Votorantim', valorCarga: '4.850,00', transporte: true, placa: 'ABC1D23', volume: '12,5', peso: '18' },
    { id: 'e2', tipo: 'Quebra de equipamento', hora: '14:10', detalhe: 'Escavadeira PC200 - mangueira hidráulica' }];
  d.fotos = [1, 2, 3, 4, 5, 6, 7].map(i => ({ id: 'f' + i, dataUrl: foto, legenda: 'Frente de serviço ' + i }));
  salvarDiarioDia(false);
}"""


def paginas(page, gerar):
    page.evaluate(gerar)
    page.wait_for_timeout(600)
    page.emulate_media(media="print")
    caminho = os.path.join(tempfile.gettempdir(), "rdo_teste.pdf")
    page.pdf(path=caminho, format="A4", margin={"top": "10mm", "bottom": "10mm", "left": "10mm", "right": "10mm"},
             print_background=True)
    n = len(re.findall(rb"/Type\s*/Page[^s]", open(caminho, "rb").read()))
    page.emulate_media(media="screen")
    return n


with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    ctx = b.new_context(viewport={"width": 794, "height": 1123})
    page = ctx.new_page()
    erros = []
    page.on("pageerror", lambda e: erros.append(str(e)))
    page.on("dialog", lambda d: d.dismiss())
    page.route("**/script.google.com/**", lambda r: r.fulfill(
        status=200, content_type="application/json", body=json.dumps({"ok": True})))
    page.goto(f"{BASE}/rdo.html")
    page.wait_for_timeout(1000)
    page.evaluate(SEMEAR, [AP])

    # ---- botões na aba Gerar ----
    gerar = page.text_content("#view-gerar")
    check("Gerar PDF do RDO" in gerar and "PDF resumido" not in gerar and "PDF completo" not in gerar,
          "aba Gerar tem um botão só: Gerar PDF do RDO")

    # ---- conteúdo do PDF condensado ----
    page.evaluate("gerarPdfRDO()")
    page.wait_for_timeout(500)
    doc = page.inner_text("#pdfOverlay .pdf-doc")
    check(page.locator("#pdfOverlay .pdf-doc.pdf-compacto").count() == 1, "o PDF abre com a folha condensada")
    for trecho, nome in [
        ("RELATÓRIO DIÁRIO DE OBRA", "título"), ("Base Aerogerador 2 — Escavação para fundação", "local da obra do dia"),
        ("07:00 às 17:00", "jornada correta (início/fim)"), ("Trabalho em altura e içamento", "tema do DSS"),
        ("Acompanhamento de fiscalização", "atividade do cadastro"), ("Atendimento à fiscalização", "atividade avulsa"),
        ("Concretagem de laje — Chuva forte na tarde", "atividade paralisada com justificativa"),
        ("Quase-acidente", "evento de segurança"), ("Umectação", "ação do evento de meio ambiente"),
        ("Cimento CP-II NF 1234", "evento do dia"), ("Valor R$ 4.850,00", "valor da carga"),
        ("Placa ABC1D23", "placa do transporte"), ("Votorantim", "fornecedor"),
        ("ACUMULADOS", "tabela de acumulados"), ("Cargas de material", "cargas nos acumulados"),
        ("501 – Marcelo Dias", "apontador"), ("Gerado pelo App Diário de Obras", "rodapé"),
    ]:
        check(trecho.lower() in doc.lower(), f"PDF traz: {nome}")
    ordem = page.evaluate("""() => [...document.querySelectorAll('#pdfOverlay .cx-tit')].map(e => e.textContent.trim().toUpperCase())""")
    ia = next(i for i, t in enumerate(ordem) if t.startswith("ATIVIDADES DO DIA"))
    check(ia + 1 < len(ordem) and ordem[ia + 1].startswith("EVENTOS DO DIA"),
          f"Atividades do dia vem logo acima de Eventos do dia (ordem: {ordem})")
    check(page.locator("#pdfOverlay .cx-fotos img").count() == 7, "fotos entram como miniaturas (7)")
    check(page.locator("#pdfOverlay .cx-kpi td").count() == 7, "faixa de indicadores com 7 itens")
    check(page.locator("#pdfOverlay .pdf-page").count() == 1 and page.locator("#pdfOverlay .quebra-pagina").count() == 0,
          "sem quebras forçadas de página: uma folha contínua")
    page.evaluate("fecharPdfRDO()")

    # ---- Kanban de Assuntos do Check-in, logo acima das assinaturas ----
    page.evaluate("""() => localStorage.setItem('chk_assuntos', JSON.stringify([
      {id: 'k1', assunto: 'Liberar frente de concretagem', desc: 'Aguardando projeto revisado', prioridade: 'alta', setor: 'Engenharia',
       status: 'fazendo', dataLanc: '2026-10-05', dataTerm: '2099-10-10', resp: 'Jonacir Cazelli', criador: 'Marcelo Dias', criadoEm: Date.now()},
      {id: 'k2', assunto: 'Solicitar aço CA-50', desc: '', prioridade: 'media', setor: 'Suprimentos', status: 'afazer',
       dataLanc: '2026-10-04', dataTerm: '2020-01-01', resp: '', criador: '', criadoEm: Date.now()},
      {id: 'k3', assunto: 'Emitir ART da fundação', status: 'concluido', prioridade: 'baixa', criadoEm: Date.now()},
      {id: 'k4', assunto: 'Compra de formas descartada', status: 'cancelado', prioridade: 'baixa', criadoEm: Date.now()}]))""")
    page.evaluate("gerarPdfRDO()")
    page.wait_for_timeout(400)
    kb = page.locator("#pdfOverlay table.kb")
    check(kb.count() == 1, "PDF traz o Kanban de Assuntos")
    check(kb.locator("td").count() == 4, "Kanban com 4 colunas (A fazer, Fazendo, Concluído, Cancelado)")
    heads = page.evaluate("""() => [...document.querySelectorAll('#pdfOverlay table.kb .kb-hdr')].map(h => h.querySelector('span').textContent.trim() + ' ' + h.querySelector('b').textContent.trim())""")
    check([h.split(' ')[-1] for h in heads] == ["1", "1", "1", "1"] and "A FAZER" in heads[0] and "CANCELADO" in heads[3], f"colunas e contagens ({heads})")
    k = page.inner_text("#pdfOverlay table.kb").lower()
    check("liberar frente de concretagem" in k and "aguardando projeto revisado" in k and "engenharia" in k
          and "05/10/2026" in k and "10/10/2099" in k and "jonacir cazelli" in k and "restante" in k,
          "cartão de Fazendo traz descrição, setor, datas, responsável e prazo restante")
    check("atrasado" in k, "prazo vencido aparece como atrasado")
    check(page.locator("#pdfOverlay .kb-concluido .kb-card").first.inner_text().strip() == "Emitir ART da fundação",
          "Concluído mostra só o nome, como na tela do Check-in")
    pos = page.evaluate("""() => { const d = document.querySelector('#pdfOverlay .pdf-doc'); const f = [...d.children[0].children];
      const i = f.findIndex(e => e.querySelector && e.querySelector('table.kb') || e.classList.contains('cx-kb'));
      return [i, f.findIndex(e => e.classList.contains('cx-ass')), f.findIndex(e => e.querySelector && e.querySelector('.cx-fotos'))]; }""")
    check(pos[0] >= 0 and pos[0] + 1 == pos[1], f"Kanban fica imediatamente acima das assinaturas ({pos})")
    check(pos[2] < pos[0], "Kanban vem depois do registro fotográfico")
    ass = page.inner_text("#pdfOverlay .cx-ass")
    check("Jonacir Cazelli" in ass and "Gerência" in ass and "Marcelo Dias" in ass and "Apontador" in ass,
          "assinaturas do RDO: Apontador (esquerda) e Gerência — Jonacir Cazelli (direita)")
    page.wait_for_timeout(300)
    check(page.evaluate("() => { const i = document.querySelector('#pdfOverlay .cx-ass img'); return !!i && i.complete && i.naturalWidth > 100; }"),
          "assinatura do Gerente de Obras (imagem) carrega no PDF")
    check("Fiscalização" not in ass and "Cliente" not in ass, "a assinatura de Fiscalização/Cliente saiu")
    check("Check-in — pendências" not in page.inner_text("#pdfOverlay .pdf-doc"), "a lista curta de pendências foi substituída pelo Kanban")
    page.evaluate("fecharPdfRDO()")

    # ---- assinaturas escolhíveis: toque no campo abre a escolha; desenhar, guardar, trocar, apagar ----
    page.evaluate("localStorage.removeItem('diario_assinaturasSalvas')")
    page.evaluate("gerarPdfRDO()")
    page.wait_for_timeout(500)
    cel = lambda i: page.locator("#pdfOverlay .cx-ass td").nth(i)
    check(page.locator("#pdfOverlay .cx-ass .ass-clic").count() == 2 and page.locator("#pdfOverlay .ass-dica").count() == 2,
          "os dois campos de assinatura são tocáveis e trazem a dica")
    check("Apontador" in cel(0).inner_text() and "Gerência" in cel(1).inner_text(), "esquerda = Apontador, direita = Gerência")
    page.emulate_media(media="print")
    check(page.evaluate("getComputedStyle(document.querySelector('#pdfOverlay .ass-dica')).display") == "none", "a dica não sai na impressão")
    page.emulate_media(media="screen")
    check(cel(1).locator("img").count() == 1 and "assinatura-gerente.png" in cel(1).locator("img").get_attribute("src"),
          "Gerência abre com a assinatura padrão do Jonacir Cazelli")
    check(cel(0).locator("img").count() == 0, "Apontador abre sem assinatura (linha para assinar)")

    def desenhar(nome):
        cv = page.locator("#padAssCanvas")
        bb = cv.bounding_box()
        page.mouse.move(bb["x"] + 30, bb["y"] + 100)
        page.mouse.down()
        for k in range(1, 12):
            page.mouse.move(bb["x"] + 30 + k * 25, bb["y"] + 100 + (30 if k % 2 else -30))
        page.mouse.up()
        page.fill("#padAssNome", nome)

    cel(0).click()
    check(page.locator("#escAssOverlay").count() == 1 and "Nenhuma assinatura guardada" in page.inner_text("#escAssOverlay"),
          "tocar no Apontador abre a escolha (sem nada guardado ainda)")
    page.click("#escAssOverlay [data-acao=nova]")
    check(page.locator("#padAssOverlay").count() == 1 and page.input_value("#padAssNome") != "", "desenhar nova abre o quadro de assinatura com o nome sugerido")
    desenhar("Marcelo Dias")
    page.click("#padAssOverlay .pad-btns button:last-child")
    page.wait_for_timeout(500)
    check(cel(0).locator("img").count() == 1 and cel(0).locator("img").get_attribute("src").startswith("data:image/png"),
          "assinatura desenhada aparece no campo do Apontador")
    g = page.evaluate("JSON.parse(localStorage.getItem('diario_assinaturasSalvas'))")
    check(len(g["apontador"]) == 1 and g["apontador"][0]["nome"] == "Marcelo Dias", "assinatura guardada na lista do aparelho")
    check(page.evaluate("currentDay.assinaturas.apontador").startswith("data:image/png"), "e gravada no dia")

    cel(0).click()
    page.click("#escAssOverlay [data-acao=branco]")
    page.wait_for_timeout(400)
    check(cel(0).locator("img").count() == 0, "'Deixar em branco' tira a assinatura do dia")
    cel(0).click()
    page.click("#escAssOverlay .esc-item")
    page.wait_for_timeout(400)
    check(cel(0).locator("img").count() == 1, "escolher a assinatura guardada devolve ao campo")

    cel(1).click()
    page.click("#escAssOverlay [data-acao=branco]")
    page.wait_for_timeout(400)
    check(cel(1).locator("img").count() == 0 and "Gerente de Obras" in cel(1).inner_text(), "Gerência pode ficar em branco")
    cel(1).click()
    page.click("#escAssOverlay [data-acao=padrao]")
    page.wait_for_timeout(400)
    check(cel(1).locator("img").count() == 1, "e volta ao padrão (Jonacir Cazelli)")
    cel(1).click()
    page.click("#escAssOverlay [data-acao=nova]")
    desenhar("Outro Gerente")
    page.click("#padAssOverlay .pad-btns button:last-child")
    page.wait_for_timeout(500)
    check("Outro Gerente" in cel(1).inner_text() and cel(1).locator("img").get_attribute("src").startswith("data:image/png"),
          "Gerência com outra pessoa: assinatura e nome acompanham a escolha")
    cel(1).click()
    check(page.locator("#escAssOverlay .esc-item").count() == 2, "lista da Gerência: padrão + a nova")
    page.click("#escAssOverlay .esc-del")
    page.wait_for_timeout(300)
    check(page.locator("#escAssOverlay .esc-item").count() == 1, "apagar tira a assinatura da lista")
    page.click("#escAssOverlay [data-acao=fechar]")
    page.evaluate("fecharPdfRDO()")
    page.evaluate("() => { delete currentDay.assinaturas; delete currentDay.assinaturaNomes; }")
    page.evaluate("localStorage.removeItem('diario_assinaturasSalvas')")
    # ---- Notas recebidas no dia (módulo Custos): planilha completa + resumo, logo abaixo do Kanban ----
    page.evaluate("""() => { const d = currentDay.data;
      localStorage.setItem('chk_assuntos', JSON.stringify([{id: 'kc', assunto: 'Assunto p/ posição', status: 'afazer', prioridade: 'media', criadoEm: Date.now()}]));
      const e = (id, hh, nf, forn, cat, sub, desc, un, q, pu, mede, st, dia, em) => ({id, recebido_em: (dia || d) + 'T' + hh + ':00', numero_nf: nf, data_emissao: em || d, fornecedor: forn, categoria: cat, subcategoria: sub,
        descricao: desc, unidade: un, quantidade: q, preco_unitario: pu, total: pu == null ? null : pu * q, responsavel: 'Carlos', mede_por: mede, status: st || 'ativo', data_recebimento: dia || d});
      localStorage.setItem('custo_entradas', JSON.stringify([
        e('4', '10:20', '8891', 'Elétrica Central', 'Elétrico', 'Kit elétrico', 'Kit material elétrico – QD-02', 'kit', 1, 4320, 'unidade'),
        e('1', '07:42', '2340', 'Pedreira Boa Vista', 'Agregados', 'Areia', 'Areia média lavada', 'm³', 12, 85, 'carga'),
        e('3', '08:15', '2341', 'Pedreira Boa Vista', 'Agregados', 'Brita 1', 'Brita 1', 'm³', 12, 95, 'carga'),
        e('2', '09:05', '2345', 'Pedreira Boa Vista', 'Agregados', 'Areia', 'Areia média lavada', 'm³', 12, 85, 'carga', 'ativo', null, '2020-01-01'),
        e('5', '11:00', '77', 'Águas do Vale', 'Água', 'Caminhão-pipa', 'Água', 'm³', 10, null, 'viagem', 'cancelado'),
        e('7', '12:00', '78', 'Águas do Vale', 'Água', 'Caminhão-pipa', 'Água p/ umectação', 'm³', 10, null, 'viagem'),
        e('6', '08:00', '999', 'Outro Dia', 'Terra', 'Saibro', 'Saibro', 'm³', 8, 40, 'carga', 'ativo', '2020-01-01')])); }""")
    page.evaluate("gerarPdfRDO()")
    page.wait_for_timeout(400)
    check(page.locator("#pdfOverlay .cx-cust").count() == 1, "PDF traz a seção de notas recebidas no dia")
    heads = page.evaluate("""() => [...document.querySelector('#pdfOverlay .cx-cust table.cx-plan').rows[0].cells].map(c => c.textContent.trim())""")
    check(heads == ["Hora", "Nº nota", "Emissão", "Fornecedor", "Categoria", "Subcateg.", "Descrição da nota", "Un.", "Qtde", "Preço unit.", "Total", "Respons."], f"colunas da planilha ({heads})")
    rows = page.evaluate("""() => [...document.querySelector('#pdfOverlay .cx-cust table.cx-plan').rows].slice(1, -1).map(r => [...r.cells].map(c => c.textContent.trim()))""")
    check([r[1] for r in rows] == ["2340", "2341", "2345", "8891", "78"], f"planilha em ordem de chegada; cancelada e outro dia fora ({[r[1] for r in rows]})")
    check(rows[2][2] == "01/01" and rows[0][0] == "07:42", "emissão e hora de chegada por linha")
    check(rows[0][8] == "12" and rows[0][9] == "85,00" and rows[0][10] == "1.020,00", f"qtde, preço unitário e total da linha ({rows[0]})")
    check(rows[4][9] == "—" and rows[4][10] == "—", "sem valor aparece como —")
    ptxt = page.inner_text("#pdfOverlay .cx-cust")
    check("total lançado" in ptxt.lower() and "7.500,00" in ptxt and "1 sem valor" in ptxt.lower(), "total lançado e itens sem valor")
    res = page.evaluate("""() => [...document.querySelectorAll('#pdfOverlay .cx-cust table.cx')[1].rows].slice(1).map(r => [...r.cells].map(c => c.textContent.trim()))""")
    check([r[:2] for r in res] == [["Agregados", "Areia"], ["Agregados", "Brita 1"], ["Água", "Caminhão-pipa"], ["Elétrico", "Kit elétrico"]] or [r[:2] for r in res] == [["Água", "Caminhão-pipa"], ["Agregados", "Areia"], ["Agregados", "Brita 1"], ["Elétrico", "Kit elétrico"]],
          f"resumo por categoria e subcategoria ({[r[:2] for r in res]})")
    areia = next(r for r in res if r[1] == "Areia")
    check(areia[2] == "24 m³" and areia[3] == "2 cargas" and "2340" in areia[4], f"resumo soma a mesma subcategoria (24 m³, 2 cargas) ({areia})")
    check(next(r for r in res if r[1] == "Kit elétrico")[2] == "1 kit", "kit em unidades")
    pos3 = page.evaluate("""() => { const f = [...document.querySelector('#pdfOverlay .pdf-doc').children[0].children];
      return [f.findIndex(e => e.classList.contains('cx-kb')), f.findIndex(e => e.classList.contains('cx-cust')), f.findIndex(e => e.classList.contains('cx-ass'))]; }""")
    check(pos3[0] >= 0 and pos3[0] + 1 == pos3[1] and pos3[1] + 1 == pos3[2], f"notas recebidas ficam logo abaixo do Kanban e acima das assinaturas ({pos3})")
    page.evaluate("fecharPdfRDO()")
    # vindo do servidor quando o aparelho não tem as entradas
    page.evaluate("""() => { localStorage.removeItem('custo_entradas'); window.__cliOrig = B3Obras.cliente;
      const rows = [{id: 's1', recebido_em: currentDay.data + 'T10:00:00-03:00', data_recebimento: currentDay.data, numero_nf: '77', data_emissao: currentDay.data, fornecedor: 'Águas do Vale', categoria: 'Água', subcategoria: 'Caminhão-pipa', descricao: 'Água p/ umectação', unidade: 'm³', quantidade: 30, preco_unitario: null, total: null, responsavel: 'Carlos', mede_por: 'viagem', status: 'ativo'}];
      const q = linhas => { const o = { eq: () => o, in: () => o, then: (res) => res({ data: linhas, error: null }) }; return o; };
      B3Obras.cliente = () => ({ from: t => ({ select: () => q(t === 'custos_entradas' ? rows : []) }) }); }""")
    page.evaluate("gerarPdfRDO()")
    page.wait_for_timeout(1000)
    check(page.locator("#pdfOverlay .cx-cust").count() == 1 and "30 m³" in page.inner_text("#pdfOverlay .cx-cust"),
          "sem entradas no aparelho, o resumo do dia vem do servidor")
    page.evaluate("() => { B3Obras.cliente = window.__cliOrig; }")
    page.evaluate("fecharPdfRDO()")
    page.evaluate("localStorage.removeItem('custo_entradas'); localStorage.removeItem('chk_assuntos'); entradasMateriaisServidor = {}; assuntosCheckinServidor = null")
    page.evaluate("gerarPdfRDO()")
    page.wait_for_timeout(300)
    check(page.locator("#pdfOverlay .cx-cust").count() == 0, "dia sem entradas: a seção não aparece (não gasta papel)")
    page.evaluate("fecharPdfRDO()")

    # com Kanban pequeno, o dia cheio ainda cabe em 2 folhas (o quadro é conteúdo pedido, não desperdício)
    page.evaluate("""() => localStorage.setItem('chk_assuntos', JSON.stringify([
      {id: 'k1', assunto: 'Liberar frente de concretagem', desc: 'Aguardando projeto revisado', prioridade: 'alta', setor: 'Engenharia', status: 'fazendo', dataLanc: '2026-10-05', dataTerm: '2099-10-10', resp: 'Jonacir Cazelli', criador: 'Marcelo Dias', criadoEm: Date.now()},
      {id: 'k2', assunto: 'Solicitar aço CA-50', prioridade: 'media', setor: 'Suprimentos', status: 'afazer', dataTerm: '2020-01-01', criadoEm: Date.now()},
      {id: 'k3', assunto: 'Emitir ART da fundação', status: 'concluido', prioridade: 'baixa', criadoEm: Date.now()},
      {id: 'k4', assunto: 'Compra descartada', status: 'cancelado', prioridade: 'baixa', criadoEm: Date.now()}]))""")
    n_kb = paginas(page, "gerarPdfRDO()")
    page.evaluate("fecharPdfRDO()")
    check(n_kb <= 2, f"dia cheio com Kanban de 4 assuntos cabe em até 2 folhas (obtido: {n_kb})")
    page.evaluate("localStorage.removeItem('chk_assuntos')")

    # ---- aparelho que nunca abriu o Check-in: o Kanban vem do servidor (Supabase) ----
    servidor = [
        {"id": "s1", "assunto": "Assunto só no servidor", "descricao": "veio do Supabase", "prioridade": "alta", "setor": "Engenharia",
         "status": "fazendo", "data_lancamento": "2026-10-05", "data_termino": "2099-01-01", "responsavel": "Jonacir Cazelli",
         "criador": "Marcelo Dias", "criado_em": "2026-10-05T12:00:00Z"},
        {"id": "s2", "assunto": "Concluído no servidor", "status": "concluido", "prioridade": "baixa", "criado_em": "2026-10-04T12:00:00Z"}]
    # o CDN do supabase-js é bloqueado no ambiente de teste: troca o cliente por um falso que devolve as linhas
    page.evaluate("""(linhas) => { window.__clienteOriginal = B3Obras.cliente;
      B3Obras.cliente = () => ({ from: () => ({ select: async () => ({ data: linhas, error: null }) }) }); }""", servidor)
    page.evaluate("localStorage.removeItem('rdo_chk_servidor'); assuntosCheckinServidor = null")
    page.evaluate("gerarPdfRDO()")
    page.wait_for_timeout(1200)
    k2 = page.inner_text("#pdfOverlay table.kb") if page.locator("#pdfOverlay table.kb").count() else ""
    check("Assunto só no servidor" in k2 and "Concluído no servidor" in k2,
          "sem Check-in local, o Kanban do PDF vem do servidor (e se refaz quando os dados chegam)")
    pos2 = page.evaluate("""() => { const d = document.querySelector('#pdfOverlay .pdf-doc').children[0]; const f = [...d.children];
      return [f.findIndex(e => e.classList.contains('cx-kb')), f.findIndex(e => e.classList.contains('cx-ass'))]; }""")
    check(pos2[0] >= 0 and pos2[0] + 1 == pos2[1], f"Kanban vindo do servidor também fica acima das assinaturas ({pos2})")
    page.evaluate("fecharPdfRDO()")
    # o que está só no Check-in local (ainda não sincronizado) soma ao do servidor
    page.evaluate("""() => localStorage.setItem('chk_assuntos', JSON.stringify([{id: 'l1', assunto: 'Só local', status: 'afazer', prioridade: 'media', criadoEm: Date.now()}]))""")
    check(page.evaluate("lerAssuntosCheckin().map(a => a.assunto).sort().join('|')") == "Assunto só no servidor|Concluído no servidor|Só local",
          "Kanban junta o servidor com o que só existe no Check-in local")
    page.evaluate("localStorage.setItem('chk_removidos', JSON.stringify(['s2']))")
    check("Concluído no servidor" not in page.evaluate("lerAssuntosCheckin().map(a => a.assunto).join('|')"), "assunto apagado no Check-in não volta pelo servidor")
    page.evaluate("() => { B3Obras.cliente = window.__clienteOriginal; }")
    page.evaluate("localStorage.removeItem('chk_assuntos'); localStorage.removeItem('chk_removidos'); localStorage.removeItem('rdo_chk_servidor'); assuntosCheckinServidor = null")

    # ---- economia de papel ----
    n = paginas(page, "gerarPdfRDO()")
    page.evaluate("fecharPdfRDO()")
    check(n == 1, f"dia cheio (efetivo 14, 7 fotos, eventos, SSMA, acumulados) cabe em 1 folha (obtido: {n})")

    # ---- dia vazio e dia sem fotos ----
    vazio = page.evaluate("""() => {
        const d = EMPTY_DAY(); d.data = '2024-05-06'; d.apontador = '501 – Marcelo Dias (Qualidade / Apontamento)';
        currentDay = d; gerarPdfRDO();
        return document.querySelector('#pdfOverlay .pdf-doc').innerText.length;
    }""")
    check(vazio > 100 and not erros, f"dia vazio gera sem erro ({vazio} caracteres, erros={erros})")
    page.evaluate("fecharPdfRDO()")

    # ---- horário vindo do banco com segundos ("16:00:00") sai como 16:00 ----
    seg = page.evaluate("""() => {
        currentDay.cafeFim = '07:00:00'; currentDay.encerramento = '16:00:00'; currentDay.almocoInicio = '12:00:00'; currentDay.almocoFim = '13:00:00'; currentDay.dssHorario = '06:50:00';
        gerarPdfRDO();
        const pdf = document.querySelector('#pdfOverlay .pdf-doc').innerText;
        fecharPdfRDO();
        return { pdf, wa: buildRelatorio(currentDay) };
    }""")
    check("07:00 às 16:00" in seg["pdf"] and ":00:00" not in seg["pdf"].replace("06:50", "") and "16:00:00" not in seg["pdf"],
          "PDF: jornada sem segundos")
    check("Encerramento: 16:00\n" in seg["wa"] and "16:00:00" not in seg["wa"], "WhatsApp: encerramento sem segundos")
    check(page.evaluate("state.obra.encerramentoSexta = '16:00:00'; jornadaPadraoPorDia('2026-10-02')") == "16:00",
          "encerramento padrão da sexta vindo do banco é cortado para HH:MM")

    # ---- jornada com os rótulos certos e layout antigo removido ----
    page.evaluate("""(ap) => { currentDay = JSON.parse(JSON.stringify(history[chaveDiario(todayISO(), ap)] || currentDay)); }""", AP)
    page.evaluate("gerarPdfRDO()")
    page.wait_for_timeout(400)
    txt = page.inner_text("#pdfOverlay .pdf-doc")
    check("07:00 às 17:00" in txt and "Café" not in txt, "jornada mostra início 07:00 e fim 17:00, sem 'Café'")
    check(page.locator("#pdfOverlay .quebra-pagina, #pdfOverlay .kanban-grid, #pdfOverlay .data-table").count() == 0,
          "o layout antigo (páginas forçadas, kanban, tabelas grandes) não existe mais")
    page.evaluate("fecharPdfRDO()")

    # ---- "Salvar PDF (abre no Safari)" e abertura direta por ?rdo= ----
    page2 = ctx.new_page()
    page2.on("dialog", lambda d: d.dismiss())
    page2.goto(f"{BASE}/rdo.html?rdo=2024-05-06")
    page2.wait_for_timeout(1800)
    check(page2.locator("#pdfOverlay .pdf-doc.pdf-compacto").count() == 1, "?rdo=AAAA-MM-DD abre direto o PDF")
    page2.close()

    check(not erros, f"sem erros de JS ({erros})")
    b.close()

print()
print("FALHAS:", falhas if falhas else "nenhuma")
