"""Custos = controle de ENTRADA DE MATERIAIS (portaria): formulário curto, planilha cronológica,
resumo quantitativo, resumo R$, cadastro, fotos, cancelamento, CSV e sincronização."""
import json
import os
import re
from playwright.sync_api import sync_playwright
from _login import contexto

BASE = os.environ.get("BUILDLY_URL", "http://localhost:8795")
falhas = []


def check(cond, msg):
    print(("  OK    " if cond else "  FALHA ") + msg)
    if not cond:
        falhas.append(msg)


# 1x1 jpeg
JPG = bytes.fromhex("ffd8ffe000104a46494600010100000100010000ffdb0043000302020302020303030304030304050805050404050a070706080c0a0c0c0b0a0b0b0d0e12100d0e110e0b0b1016101113141515150c0f171816141812141514ffc0000b080001000101011100ffc4001f0000010501010101010100000000000000000102030405060708090a0bffc400b5100002010303020403050504040000017d01020300041105122131410613516107227114328191a1082342b1c11552d1f02433627282090a161718191a25262728292a3435363738393a434445464748494a535455565758595a636465666768696a737475767778797a838485868788898a92939495969798999aa2a3a4a5a6a7a8a9aab2b3b4b5b6b7b8b9bac2c3c4c5c6c7c8c9cad2d3d4d5d6d7d8d9dae1e2e3e4e5e6e7e8e9eaf1f2f3f4f5f6f7f8f9faffda0008010100003f00fbfcffd9")

with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    ctx = contexto(b, viewport={"width": 390, "height": 844}, timezone_id="America/Sao_Paulo")
    page = ctx.new_page()
    erros = []
    page.on("pageerror", lambda e: erros.append(str(e)))
    page.on("dialog", lambda d: d.dismiss())
    page.goto(f"{BASE}/custos.html")
    page.wait_for_timeout(700)

    # ---- catálogo inicial ----
    cats = page.evaluate("[...document.querySelectorAll('#f-cats .chip:not(.plus)')].map(c => c.textContent)")
    check(cats[:3] == ["Agregados", "Terra", "Água"] and "Elétrico" in cats, f"catálogo inicial com as categorias ({cats})")
    subs = page.evaluate("[...document.querySelectorAll('#f-subs .chip:not(.plus)')].map(c => c.textContent)")
    check(all(x in subs for x in ["Areia", "Brita 1", "Rachão", "Pedrisco"]), f"subcategorias de Agregados ({subs})")
    check(page.locator("#f-cats .chip.plus").count() == 1 and page.locator("#f-subs .chip.plus").count() == 1, "botões ＋ Nova em categoria e subcategoria")
    check(page.locator("#btn-cam").count() == 1 and page.locator("#btn-gal").count() == 1, "botões de foto (tirar foto e galeria)")
    check(page.evaluate("document.getElementById('f-cam').getAttribute('capture')") == "environment", "tirar foto abre a câmera traseira")
    check([t.strip() for t in page.locator(".tab").all_inner_texts()] == ["Entrada", "Planilha", "Resumo", "Resumo R$"], "barra com 4 botões")
    check(page.evaluate("document.getElementById('f-un').value") == "m³", "unidade padrão vem da subcategoria (Areia = m³)")

    # ---- ＋ Nova subcategoria na hora ----
    page.click("#f-subs .chip.plus")
    page.fill("#sheet [data-campo=nome]", "Cascalho")
    page.click("#sheet .btn-primary")
    check(page.evaluate("document.querySelector('#f-subs .chip.on').textContent") == "Cascalho", "＋ Nova subcategoria já fica selecionada")
    # ---- ＋ Nova categoria ----
    page.click("#f-cats .chip.plus")
    page.fill("#sheet [data-campo=nome]", "Madeira")
    page.click("#sheet .btn-primary")
    check("Madeira" in page.evaluate("[...document.querySelectorAll('#f-cats .chip.on')].map(c => c.textContent)"), "＋ Nova categoria já fica selecionada")

    # ---- porteiro e fornecedor novos (rápidos) ----
    page.click("text=＋ novo >> nth=0")
    page.fill("#sheet [data-campo=nome]", "Pedreira Boa Vista")
    page.click("#sheet .btn-primary")
    check(page.input_value("#f-forn") == "Pedreira Boa Vista", "fornecedor novo entra no campo")
    page.evaluate("() => { document.getElementById('f-resp').value = '__novo'; document.getElementById('f-resp').dispatchEvent(new Event('change')); }")
    page.fill("#sheet [data-campo=nome]", "Carlos")
    page.click("#sheet .btn-primary")
    check(page.input_value("#f-resp") == "Carlos", "porteiro novo fica selecionado")

    def lancar(cat, sub, qtd, nf, forn, preco="", desc="", un=None, livre="", emissao=None, fotos=None):
        page.evaluate("(c) => escolherCat(c)", page.evaluate("(n) => catalogo.find(r => r.tipo === 'categoria' && r.nome === n).id", cat))
        sid = page.evaluate("([n, c]) => catalogo.find(r => r.tipo === 'subcategoria' && r.nome === n && r.pai_id === catalogo.find(x => x.tipo === 'categoria' && x.nome === c).id).id", [sub, cat])
        page.evaluate("(s) => escolherSub(s)", sid)
        if desc:
            did = page.evaluate("(n) => catalogo.find(r => r.tipo === 'descricao' && r.nome === n).id", desc)
            page.select_option("#f-desc", did)
            page.evaluate("aoMudarDescricao()")
        if un:
            page.select_option("#f-un", un)
        page.fill("#f-qtd", str(qtd)); page.fill("#f-nf", nf); page.fill("#f-forn", forn); page.fill("#f-preco", str(preco))
        page.fill("#f-desc-livre", livre)
        if emissao:
            page.fill("#f-emissao", emissao)
        if fotos:
            page.set_input_files("#f-gal", fotos)
            page.wait_for_timeout(600)
        page.click("#btn-salvar")
        page.wait_for_timeout(150)

    # ---- lançamentos (portaria) ----
    page.clock.install(time="2026-10-05T10:40:00Z")  # 07:40 em Brasília
    page.reload(); page.wait_for_timeout(500)
    page.evaluate("() => { const c = (t, n) => catalogo.find(r => r.tipo === t && r.nome === n); }")
    # porteiro cadastrado de novo após o reload (catálogo persiste no aparelho)
    check(page.evaluate("catalogo.filter(r => r.tipo === 'porteiro').length") == 1, "o cadastro persiste no aparelho")
    page.select_option("#f-resp", "Carlos")
    lancar("Agregados", "Areia", 12, "2340", "Pedreira Boa Vista", preco=85)
    page.clock.run_for(1800000)
    lancar("Agregados", "Brita 1", 12, "2341", "Pedreira Boa Vista", preco=95)
    page.clock.run_for(1800000)
    lancar("Agregados", "Areia", 12, "2345", "Pedreira Boa Vista", preco=85, emissao="2026-10-04")
    page.clock.run_for(1800000)
    lancar("Elétrico", "Kit elétrico", 1, "8891", "Elétrica Central", preco=4320, desc="Kit material elétrico", livre="QD-02")
    page.clock.run_for(1800000)
    lancar("Terra", "Saibro", 8, "2351", "Terraplena")          # sem valor
    page.clock.run_for(1800000)
    lancar("Água", "Caminhão-pipa", 10, "77", "Águas do Vale")  # sem valor
    es = page.evaluate("entradas")
    check(len(es) == 6, f"6 entradas gravadas ({len(es)})")
    check(all(e["data_recebimento"] == "2026-10-05" for e in es), "data de recebimento = dia local, hora automática")
    kit = next(e for e in es if e["numero_nf"] == "8891")
    check(kit["descricao"] == "Kit material elétrico – QD-02" and kit["unidade"] == "kit" and kit["total"] == 4320, "kit: descrição do cadastro + complemento, unidade kit, total")
    check(next(e for e in es if e["numero_nf"] == "2351")["total"] is None, "sem preço = sem valor")
    check(all(e["responsavel"] == "Carlos" for e in es), "‘Recebido por’ gravado em todas")

    # ---- validações e duplicidade ----
    page.fill("#f-qtd", "0"); page.fill("#f-nf", "1"); page.fill("#f-forn", "X")
    n0 = page.evaluate("entradas.length"); page.click("#btn-salvar")
    check(page.evaluate("entradas.length") == n0, "quantidade zero não grava")
    lancar("Agregados", "Areia", 12, "2340", "Pedreira Boa Vista", preco=85)
    check(page.locator("#sheet", has_text="Já existe um lançamento igual").count() == 1 and page.evaluate("entradas.length") == n0, "duplicidade pede confirmação")
    page.click("#sheet .btn-light")
    check(page.evaluate("entradas.length") == n0, "‘Voltar’ não lança")
    page.click("#btn-salvar"); page.click("#sheet .btn-primary")
    check(page.evaluate("entradas.length") == n0 + 1, "‘Lançar mesmo assim’ grava")
    page.evaluate("() => { const e = entradas.pop(); S.set('entradas', entradas); }")

    # ---- planilha cronológica ----
    page.click(".tab[data-pg=planilha]")
    heads = page.evaluate("[...document.querySelectorAll('#tbl thead th')].map(t => t.textContent)")
    check(heads == ["Hora", "Nº nota", "Emissão", "Fornecedor", "Categoria", "Subcategoria", "Descrição da nota", "Un.", "Qtde", "Preço unit.", "Total", "Responsável"], f"colunas da planilha ({heads})")
    rows = page.evaluate("[...document.querySelectorAll('#tbl tbody tr:not(.tot)')].map(r => [...r.cells].map(c => c.textContent.trim()))")
    check([r[1] for r in rows] == ["2340", "2341", "2345", "8891", "2351", "77"], f"ordem de chegada ({[r[1] for r in rows]})")
    check([r[0] for r in rows] == sorted(r[0] for r in rows), "horas crescentes")
    check(rows[2][2] == "04/10" and rows[2][0] != "", "nota emitida ontem entra na hora em que chegou")
    check(rows[4][9] == "—" and rows[4][10] == "—", "sem valor aparece como —")
    txt = page.inner_text("#p-tot")
    check("6 lançamentos" in txt and "R$ 7.500,00" in txt and "2 sem valor" in txt, f"total lançado e pendências ({txt})")
    page.select_option("#p-cat", "Agregados")
    check(page.evaluate("document.querySelectorAll('#tbl tbody tr:not(.tot)').length") == 3, "filtro por categoria")
    page.select_option("#p-cat", "")
    page.fill("#p-busca", "8891")
    check(page.evaluate("document.querySelectorAll('#tbl tbody tr:not(.tot)').length") == 1, "busca por nº da nota")
    page.fill("#p-busca", "")

    # ---- CSV ----
    csv = page.evaluate("gerarCsv()")
    linhas = csv.lstrip("﻿").split("\r\n")
    check(csv.startswith("﻿") and linhas[0].split(";")[:4] == ["Recebido em", "Número da nota", "Data de Emissão", "Fornecedor"], "CSV com BOM e cabeçalho da planilha")
    check(len(linhas) == 7 and "8891" in linhas[4] and "4320" in linhas[4], f"CSV com 6 linhas ({len(linhas)})")
    check("Preço unitário" in linhas[0] and "Quantidade" in linhas[0] and "Responsável" in linhas[0], "CSV traz Quantidade, Preço unitário, Responsável")

    # ---- detalhe: completar valor e cancelar ----
    page.click("#tbl tbody tr:nth-child(5)")
    page.fill("#det-preco", "40")
    page.click("text=SALVAR VALOR")
    e = page.evaluate("entradas.find(x => x.numero_nf === '2351')")
    check(e["total"] == 320 and e["preco_unitario"] == 40, "completar valor: total = qtde × preço (R$ 320,00)")
    page.click("#tbl tbody tr:nth-child(6)")
    page.click("text=CANCELAR >> nth=-1")
    check(page.evaluate("entradas.find(x => x.numero_nf === '77').status") == "ativo", "cancelar sem motivo não vale")
    page.fill("#det-motivo", "lançado em duplicidade")
    page.click("#sheet .btn-danger")
    c = page.evaluate("entradas.find(x => x.numero_nf === '77')")
    check(c["status"] == "cancelado" and c["cancelado_motivo"] == "lançado em duplicidade", "cancelamento é baixa lógica com motivo")
    check(page.evaluate("document.querySelectorAll('#tbl tbody tr:not(.tot)').length") == 5, "cancelada some da planilha")
    page.check("#p-canc")
    check(page.evaluate("document.querySelectorAll('#tbl tbody tr.cancel').length") == 1, "…e volta riscada com ‘canceladas’")
    page.uncheck("#p-canc")

    # ---- resumo quantitativo ----
    page.click(".tab[data-pg=resumo]")
    ctext = page.inner_text("#r-corpo")
    check("Agregados" in ctext and "24 m³" in ctext and "12 m³" in ctext, "resumo por categoria/subcategoria soma a mesma subcategoria (Areia 24 m³)")
    check("2 cargas" in ctext and "NF 2340, 2345" in ctext, "conta cargas e lista as NFs")
    check("1 kit" in ctext and "8 m³" in ctext, "kit em unidades e saibro 8 m³")
    check("Caminhão-pipa" not in ctext, "cancelada fora do resumo")
    page.click("#r-sg2")
    dtext = page.inner_text("#r-corpo")
    check("Kit material elétrico – QD-02" in dtext and "Areia" in dtext, "visão por descrição")

    # ---- resumo R$ ----
    page.click(".tab[data-pg=valores]")
    v = page.inner_text("#v-corpo")
    check("R$ 7.820,00" in v, "R$ lançado (R$ 7.820,00)")
    check("médio R$ 85,00/m³" in v and "Elétrica Central" in v, "preço médio por unidade e por fornecedor")
    check(re.search(r"Agregados.*R\$ 3\.180,00", v, re.S) is not None and "%" in v, "R$ por categoria com percentual")
    page.click(".tab[data-pg=resumo]")

    # ---- foto: até 4 ----
    page.click(".tab[data-pg=entrada]")
    open("/tmp/c_foto.jpg", "wb").write(JPG)
    page.set_input_files("#f-gal", ["/tmp/c_foto.jpg"] * 5)
    page.wait_for_timeout(1000)
    check(page.locator("#f-th img").count() == 4, "no máximo 4 fotos por lançamento")
    page.click("#f-th button >> nth=0")
    check(page.locator("#f-th img").count() == 3, "× remove a foto")
    page.fill("#f-qtd", "5"); page.fill("#f-nf", "9000"); page.fill("#f-forn", "Foto Ltda")
    page.click("#btn-salvar"); page.wait_for_timeout(200)
    ef = page.evaluate("entradas.find(x => x.numero_nf === '9000')")
    check(ef["n_fotos"] == 3 and len(page.evaluate("fotosLocais[entradas.find(x => x.numero_nf === '9000').id]")) == 3, "fotos anexadas ao lançamento")

    # ---- cadastro ----
    page.click(".hdr-settings")
    check(page.locator("#page-cadastro.active").count() == 1, "⚙️ Cadastro abre")
    check("Cascalho" in page.inner_text("#c-corpo") and "Madeira" in page.inner_text("#c-corpo"), "cadastro mostra o que foi criado na hora")
    page.click("#c-seg div >> nth=1")
    check("Kit material elétrico" in page.inner_text("#c-corpo"), "aba Descrições NF")
    page.click("#c-seg div >> nth=3"); check("Carlos" in page.inner_text("#c-corpo"), "aba Porteiros")
    page.click("#c-seg div >> nth=2"); check("Pedreira Boa Vista" in page.inner_text("#c-corpo"), "aba Fornecedores")
    page.click("#c-seg div >> nth=0")
    page.click("text=🗑 >> nth=0")
    check(page.evaluate("catalogo.filter(r => r.tipo === 'subcategoria' && !r.ativo).length") == 1, "🗑 só desativa (não apaga)")
    page.click(".tab[data-pg=entrada]")
    off = page.evaluate("catalogo.find(r => r.tipo === 'subcategoria' && !r.ativo)")
    page.evaluate("(c) => escolherCat(c)", off["pai_id"])
    check(off["nome"] not in page.evaluate("[...document.querySelectorAll('#f-subs .chip')].map(c => c.textContent)"), "subcategoria desativada some da entrada")

    # ---- sincronização (cliente falso) ----
    page.evaluate("""() => { window.__up = []; B3Obras.cliente = () => ({ from: t => ({
      upsert: async rows => { window.__up.push([t, Array.isArray(rows) ? rows.length : 1]); return { error: null }; },
      select: () => { const o = { gte: () => o, eq: () => o, then: r => r({ data: [], error: null }) }; return o; } }) });
      entradas.forEach(e => e._sinc = false); catalogo.forEach(r => r._sinc = false); }""")
    page.evaluate("carregarDoServidor()"); page.wait_for_timeout(400)
    up = page.evaluate("window.__up")
    check(any(t == "custos_entradas" for t, n in up) and any(t == "custos_catalogo" for t, n in up), "pendências são enviadas ao servidor")
    check(any(t == "custos_entradas_fotos" and n == 3 for t, n in up), "fotos enviadas (3) e liberadas do aparelho")
    check(page.evaluate("Object.keys(fotosLocais).length") == 0 and page.evaluate("entradas.every(e => e._sinc)"), "tudo marcado como sincronizado")

    # ---- resumo para o RDO ----
    page.click(".tab[data-pg=planilha]")
    check(page.evaluate("gerarCsv().split('\\r\\n').length") >= 6, "CSV continua disponível após sincronizar")
    check(not erros, f"sem erros de JS ({erros[:3]})")
    b.close()

print("\nFALHAS:", falhas if falhas else "nenhuma")
raise SystemExit(1 if falhas else 0)
