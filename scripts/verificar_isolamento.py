#!/usr/bin/env python3
"""Prova que o BUILDLy não está ligado a nenhum outro projeto.

Existe por causa de um incidente real: uma alteração no efetivo do RDO do
BUILDLy apareceu no diário de obras de outro projeto. A causa não foi
descuido de digitação — foi o app publicado apontar para o mesmo Apps
Script, e portanto para a mesma planilha, de outro sistema.

Promessa não impede isso de voltar. Verificação impede. Este script falha
(sai com código 1) se encontrar qualquer vínculo, e é para ser rodado antes
de qualquer entrega.

    python3 scripts/verificar_isolamento.py
"""
import pathlib
import re
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent

# O que é do BUILDLy, e só dele.
# EXEC_BUILDLY pode ser a versão antiga ou nova (redeployed com OAuth scopes para Anthropic)
EXEC_BUILDLY_ANTIGAS = [
    'AKfycbwrSC_cQQW5IDu7Yrub0wnfMx7aInCX37U3BpiouC0qbFk6qgOwQpJzLXzH1XUX9lGEOA',
    'AKfycbyvsYYiUd6ygW1WAswWTRL7P0nHDJKoIK_GatyGBKL8NDH_jP-e4jkGEj5kRyRvDY2fQg',
]
PLANILHA_BUILDLY = '19SDuzU_CLzDRfbNZWJZQzchLDCeQYHgiSC_FxDSdhOw'

# O que é de outro projeto e nunca pode aparecer aqui.
PROIBIDO = {
    'AKfycbwa_TMG_RFnsFPE1-Q-gmYN9nPAv6QLy4A5N5B_z8VNK31N7R_-J_rPJtkErhJMLfMzeA':
        'Apps Script do diário de obras de outro projeto',
    'AKfycbx4Ji0Ip0AKcobFyQn7fG26rC_5GkFUUd25IcWQZc_5qZWVEvGzvYtJQNqm5Z7M9lcW4w':
        'Apps Script de pauta/check-in de outro projeto',
    '19fTP_qyxv1QiLdxBz3jbvTb46DKedrkApEVExmSxKEM':
        'planilha de outro projeto',
    'Jonacir2023/JC': 'repositório de outro projeto',
    'api.github.com/repos/': 'escrita direta na API do GitHub',
    'jonacir2023.github.io/diario-obras': 'endereço publicado de outro projeto',
    'jonacir2023.github.io/buildly2': 'endereço da geração anterior',
}

# Superfície do app: o que de fato vai ao ar.
def arquivos_do_app():
    return sorted(list(RAIZ.glob('*.html')) + list((RAIZ / 'apps-script').glob('*.gs')))


def main():
    falhas = []
    avisos = []

    # ---- 1. nada de outro projeto na superfície do app ----
    for arq in arquivos_do_app():
        texto = arq.read_text(encoding='utf-8', errors='ignore')
        for agulha, motivo in PROIBIDO.items():
            if agulha in texto:
                falhas.append(f'{arq.name}: contém {motivo} ({agulha[:28]}…)')

    # ---- 2. o único Apps Script chamado é o do BUILDLy ----
    for arq in arquivos_do_app():
        texto = arq.read_text(encoding='utf-8', errors='ignore')
        for achado in set(re.findall(r'script\.google\.com/macros/s/([A-Za-z0-9_-]+)', texto)):
            if achado not in EXEC_BUILDLY_ANTIGAS:
                falhas.append(f'{arq.name}: chama um Apps Script que não é o do BUILDLy ({achado[:28]}…)')

    # ---- 3. o backend só abre a planilha do BUILDLy ----
    gs = RAIZ / 'apps-script' / 'BuildlyBackend.gs'
    if gs.exists():
        texto = gs.read_text(encoding='utf-8')
        for achado in set(re.findall(r"SHEET_ID\s*=\s*'([^']+)'", texto)):
            if achado != PLANILHA_BUILDLY:
                falhas.append(f'BuildlyBackend.gs: SHEET_ID não é a planilha do BUILDLy ({achado})')
        # pastas do Drive com nome próprio
        for nome, valor in re.findall(r"(PASTA_RAIZ_[A-Z]+)\s*=\s*'([^']+)'", texto):
            if not valor.startswith('BUILDLy'):
                falhas.append(f'BuildlyBackend.gs: {nome} = "{valor}" — nome genérico, '
                              'outro app do mesmo Drive cai na mesma pasta')

    # ---- 4. todo app tem o espaço próprio de localStorage ----
    for arq in RAIZ.glob('*.html'):
        texto = arq.read_text(encoding='utf-8', errors='ignore')
        if 'localStorage' not in texto:
            continue
        if 'BUILDLY_ESPACO_PROPRIO' not in texto:
            falhas.append(f'{arq.name}: usa localStorage sem o espaço próprio — '
                          'divide o armazenamento com os outros apps da mesma origem')

    # ---- 5. avisos: cópia de outro app guardada no repositório ----
    for arq in RAIZ.iterdir():
        if arq.is_file() and arq.suffix == '.zip':
            avisos.append(f'{arq.name}: arquivo de outro app guardado neste repositório — '
                          'não vai ao ar, mas confunde quem for procurar a origem de um problema')

    for a in avisos:
        print(f'  aviso   {a}')
    for f in falhas:
        print(f'  FALHA   {f}')

    if falhas:
        print(f'\n{len(falhas)} vínculo(s) encontrado(s). O BUILDLy NÃO está isolado.')
        sys.exit(1)

    print(f'\nOK — {len(arquivos_do_app())} arquivos verificados, nenhum vínculo com outro projeto.')


main()
