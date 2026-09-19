#!/usr/bin/env python3
"""Gera o esqueleto de um módulo novo (levantamento/relatório) dentro do app.

Carimba as peças que todo módulo deste app precisa: página HTML isolada,
endpoint de backend pronto para colar, teste automatizado, e imprime o
checklist do que só dá para fazer à mão (aba na planilha, entrada no vault).

Ferramenta genérica por design: esta lógica não conhece nada deste projeto
além de escrever arquivo e substituir {{PLACEHOLDER}}. Todo o conhecimento
específico do BUILDLy (paleta, contrato de backend, bloco de isolamento)
mora nos arquivos de templates/ — para reaproveitar num próximo app, copie
esta pasta inteira e troque o conteúdo dos templates pelas convenções do
projeto novo. Ver LEIA-ME.md.

    python3 scripts/gerador_modulo/novo_modulo.py vistoria "Vistoria de Segurança"
"""
import pathlib
import re
import sys

AQUI = pathlib.Path(__file__).resolve().parent
TEMPLATES = AQUI / 'templates'
RAIZ = AQUI.parent.parent  # raiz do repositório

# Pontos de inserção das rotas no backend — específico do BUILDLy (o único
# bit de conhecimento do projeto que este script carrega; se um projeto
# futuro tiver outro arquivo/formato de backend, ajuste só estas 3 linhas).
BACKEND_GS = RAIZ / 'apps-script' / 'BuildlyBackend.gs'
MARCA_GET = "    return successResponse({ ok: true, msg: 'API Diário de Obras ativa' });"
MARCA_POST = "    return errorResponse('Endpoint não encontrado: ' + path + '/' + action);"


def slug(s):
    s = s.strip().lower()
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    if not s:
        sys.exit('id do módulo inválido')
    return s


def pascal(s):
    return ''.join(p.capitalize() for p in re.split(r'[^a-zA-Z0-9]+', s) if p)


def render(texto, contexto):
    for chave, valor in contexto.items():
        texto = texto.replace('{{' + chave + '}}', valor)
    return texto


def escrever(caminho, conteudo):
    if caminho.exists():
        print(f'  pulei   {caminho.relative_to(RAIZ)} (já existe — apague antes se quiser regerar)')
        return
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(conteudo, encoding='utf-8')
    print(f'  criei   {caminho.relative_to(RAIZ)}')


def inserir_rotas(id_modulo, contexto):
    if not BACKEND_GS.exists():
        print('  aviso   apps-script/BuildlyBackend.gs não encontrado — pulei a inserção de rotas')
        return False
    texto = BACKEND_GS.read_text(encoding='utf-8')
    if f'gerador:modulo:{id_modulo}' in texto:
        print(f'  pulei   rotas de "{id_modulo}" já estão em BuildlyBackend.gs')
        return True

    linha_get = f"    if (path === '{id_modulo}' && action === 'listar') return listar{contexto['PASCAL']}();\n"
    linhas_post = (
        f"    if (path === '{id_modulo}' && action === 'criar')            return criar{contexto['PASCAL']}(body);\n"
        f"    if (path === '{id_modulo}' && action === 'atualizar-status')  return atualizarStatus{contexto['PASCAL']}(body);\n"
        f"    if (path === '{id_modulo}' && action === 'remover')           return remover{contexto['PASCAL']}(body);\n"
    )

    if MARCA_GET not in texto or MARCA_POST not in texto:
        print('  aviso   marcas de rota não encontradas em BuildlyBackend.gs — cole manualmente')
        print(f'          (ver apps-script/novo-endpoint-{id_modulo}-rotas.txt)')
        return False

    texto = texto.replace(MARCA_GET, linha_get + MARCA_GET, 1)
    texto = texto.replace(MARCA_POST, linhas_post + MARCA_POST, 1)
    texto += '\n' + render((TEMPLATES / 'endpoint.gs.tpl').read_text(encoding='utf-8'), contexto)
    BACKEND_GS.write_text(texto, encoding='utf-8')
    print('  editei  apps-script/BuildlyBackend.gs (rotas + funções)')
    return True


def main():
    if len(sys.argv) < 3:
        sys.exit('uso: novo_modulo.py <id-do-modulo> "<Título>"')

    id_modulo = slug(sys.argv[1])
    titulo = sys.argv[2]
    nome_pascal = pascal(id_modulo)
    contexto = {
        'ID': id_modulo,
        'ID_UPPER': id_modulo.upper(),
        'TITULO': titulo,
        'PASCAL': nome_pascal,
        'PASCAL_UPPER': nome_pascal.upper(),
        'PREFIXO': id_modulo.replace('-', '_') + '_',
        'SHEET': nome_pascal,
    }

    print(f'Gerando módulo "{id_modulo}" ({titulo})\n')

    escrever(RAIZ / f'{id_modulo}.html',
             render((TEMPLATES / 'modulo.html.tpl').read_text(encoding='utf-8'), contexto))

    inseriu = inserir_rotas(id_modulo, contexto)
    if not inseriu:
        escrever(RAIZ / 'apps-script' / f'novo-endpoint-{id_modulo}-rotas.txt',
                 render((TEMPLATES / 'rotas.txt.tpl').read_text(encoding='utf-8'), contexto))
        escrever(RAIZ / 'apps-script' / f'novo-endpoint-{id_modulo}.gs',
                 render((TEMPLATES / 'endpoint.gs.tpl').read_text(encoding='utf-8'), contexto))

    escrever(RAIZ / 'tests' / f"test_{contexto['PREFIXO']}basico.py",
             render((TEMPLATES / 'test.py.tpl').read_text(encoding='utf-8'), contexto))

    print(f"""
Falta à mão (o gerador não faz por você):
  1. Criar a aba "{contexto['SHEET']}" na planilha, com as colunas de
     COLUNAS_{contexto['PASCAL_UPPER']} (veja o bloco gerado em BuildlyBackend.gs).
  2. Colar o conteúdo atualizado de BuildlyBackend.gs no editor do Apps Script
     (o arquivo do repositório é só cópia de referência — nunca é implantado
     por git). Ver vault/Notas/Contrato do Backend.md.
  3. Rodar: python3 scripts/verificar_sintaxe.py && python3 scripts/verificar_isolamento.py
  4. Rodar: python3 tests/executar.py {contexto['PREFIXO']}basico
  5. Se o módulo entrar no menu inicial, adicionar o botão em
     buildly-completo.html (home-grid) e o iframe correspondente.
  6. Documentar no vault: uma linha em Contrato do Backend.md (endpoint novo)
     e em Arquitetura do App.md (módulo novo, standalone/iframe).
  7. python3 scripts/registro_obsidian.py — e escrever o porquê, no mesmo commit.
""")


if __name__ == '__main__':
    main()
