#!/usr/bin/env python3
"""Mantém os arquivos compartilhados (tema.css, supabase-config.js) ligados às
páginas, com ?v=<hash> na URL para furar o cache do Safari.

O GitHub Pages deixa o navegador reaproveitar um arquivo por até 10 minutos.
Sem o hash na URL, uma mudança no tema.css chega ao iPhone só depois disso — e
cada app em iframe é um arquivo à parte, então a casca pode aparecer nova com
o app de dentro velho. Rode depois de qualquer edição nesses arquivos:

    python3 scripts/versionar_estaticos.py

É idempotente: sem mudança nos arquivos, não altera nenhuma página.
Também garante, em toda página, o <link> do tema e o detector de iframe
(`html.embutido`), que o tema usa para esconder o cabeçalho próprio do app
quando ele está dentro da casca.
"""
import hashlib
import pathlib
import re
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
ESTATICOS = ['tema.css', 'supabase-config.js']
DETECTOR = ("<script>/*embutido*/if(window.top!==window.self)"
            "document.documentElement.classList.add('embutido')</script>")
PAGINAS_IGNORADAS = {'index.html'}


def hash_de(nome):
    return hashlib.md5((RAIZ / nome).read_bytes()).hexdigest()[:8]


ARQUIVOS_DO_BUILD = ['tema.css', 'supabase-config.js', 'assinatura-gerente.png', 'hero-obra.svg']
BUILD_RE = re.compile(r'window\.BUILD_ID="[0-9a-f]*"')


def build_id():
    """Hash de tudo que o usuário enxerga: páginas (a casca com o BUILD_ID zerado), tema, config e imagens."""
    h = hashlib.md5()
    for p in sorted(RAIZ.glob('*.html')):
        if p.name == 'index.html':
            continue
        t = p.read_text(encoding='utf-8')
        if p.name == 'buildly-completo.html':
            t = BUILD_RE.sub('window.BUILD_ID=""', t)
        h.update(p.name.encode() + t.encode('utf-8'))
    for n in ARQUIVOS_DO_BUILD:
        if (RAIZ / n).exists():
            h.update(n.encode() + (RAIZ / n).read_bytes())
    return h.hexdigest()[:8]


def main():
    hashes = {n: hash_de(n) for n in ESTATICOS if (RAIZ / n).exists()}
    alteradas = []
    for pagina in sorted(RAIZ.glob('*.html')):
        if pagina.name in PAGINAS_IGNORADAS:
            continue
        s = pagina.read_text(encoding='utf-8')
        if '</head>' not in s:
            continue
        novo = s
        # detector de iframe: logo depois de <head>, antes de qualquer CSS
        if '/*embutido*/' not in novo:
            novo = re.sub(r'(<head[^>]*>)', lambda m: m.group(1) + '\n' + DETECTOR, novo, count=1)
        # <link> do tema: por último no <head>, para vencer os estilos do arquivo.
        # media="screen": o tema não entra na impressão/PDF (a folha do RDO, da pauta e do
        # check-in tem layout próprio e cabe em 1 página só sem ele)
        if 'tema.css' in hashes:
            link = f'<link rel="stylesheet" href="tema.css?v={hashes["tema.css"]}" media="screen">'
            if re.search(r'<link[^>]+href="tema\.css[^"]*"', novo):
                novo = re.sub(r'<link[^>]+href="tema\.css[^"]*"[^>]*>', link, novo, count=1)
            else:
                novo = novo.replace('</head>', link + '\n</head>', 1)
        # scripts versionados
        if 'supabase-config.js' in hashes:
            novo = re.sub(r'supabase-config\.js(\?v=[0-9a-f]+)?"', f'supabase-config.js?v={hashes["supabase-config.js"]}"', novo)
        if novo != s:
            pagina.write_text(novo, encoding='utf-8')
            alteradas.append(pagina.name)
    # iframes da casca: cada app ganha ?v=<hash do arquivo>. Sem isso o Safari reaproveita o
    # rdo.html velho por até 10 min dentro da casca nova (visto em 05/10/2026: PDF do RDO
    # sem o Kanban recém-publicado).
    casca = RAIZ / 'buildly-completo.html'
    if casca.exists():
        t = casca.read_text(encoding='utf-8')

        def versao_iframe(m):
            alvo = RAIZ / m.group(2)
            if not alvo.exists():
                return m.group(0)
            return f'{m.group(1)}{m.group(2)}?v={hash_de(m.group(2))}"'
        novo = re.sub(r'(<iframe[^>]*\bsrc=")([A-Za-z0-9_-]+\.html)(?:\?v=[0-9a-f]+)?"', versao_iframe, t)
        if novo != t:
            casca.write_text(novo, encoding='utf-8')
            if casca.name not in alteradas:
                alteradas.append(casca.name)
    # carimbo do build: a casca carrega BUILD_ID e confere com versao.json (que o navegador não
    # guarda em cache). Se diferirem, ela recarrega sozinha — acaba com "publiquei e não apareceu".
    if casca.exists():
        t = casca.read_text(encoding='utf-8')
        marca = '<script>/*build*/window.BUILD_ID=""</script>'
        if '/*build*/' not in t:
            t = re.sub(r'(<head[^>]*>)', lambda m: m.group(1) + '\n' + marca, t, count=1)
            casca.write_text(t, encoding='utf-8')
        bid = build_id()
        novo = BUILD_RE.sub(f'window.BUILD_ID="{bid}"', t)
        if novo != t:
            casca.write_text(novo, encoding='utf-8')
            if casca.name not in alteradas:
                alteradas.append(casca.name)
        versao = '{"v":"%s"}\n' % bid
        if not (RAIZ / 'versao.json').exists() or (RAIZ / 'versao.json').read_text(encoding='utf-8') != versao:
            (RAIZ / 'versao.json').write_text(versao, encoding='utf-8')
    print('hashes:', ', '.join(f'{n}={h}' for n, h in hashes.items()))
    print(f'{len(alteradas)} página(s) atualizada(s)' + (': ' + ', '.join(alteradas) if alteradas else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main())
