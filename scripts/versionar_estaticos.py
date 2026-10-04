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
    print('hashes:', ', '.join(f'{n}={h}' for n, h in hashes.items()))
    print(f'{len(alteradas)} página(s) atualizada(s)' + (': ' + ', '.join(alteradas) if alteradas else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main())
