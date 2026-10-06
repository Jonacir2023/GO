"""Ajuda das suítes: entrar no BUILDLy sem passar pela tela de login.

As suítes testam regras do app (RDO, Entradas, Pauta…), não o login. Este módulo grava, antes de
qualquer página carregar, uma sessão de mentira nas duas obras e o perfil guardado em cache — o
mesmo que o app grava depois de um login de verdade. O login em si é testado em test_login.py.
"""
import json
import pathlib
import re

RAIZ = pathlib.Path(__file__).resolve().parent.parent
_CFG = (RAIZ / "supabase-config.js").read_text(encoding="utf-8")
REFS = re.findall(r"url:\s*'https://([a-z0-9]+)\.supabase\.co'", _CFG)
IDS = re.findall(r"id:\s*'(obra\d+)'", _CFG)

PAPEIS = {
    "admin": {"papel": "admin", "rotulo": "Administrador", "modulos": ["*"]},
    "portaria": {"papel": "portaria", "rotulo": "Portaria", "modulos": ["custos"]},
    "pendente": {"papel": "pendente", "rotulo": "Sem acesso", "modulos": []},
}


def script_semear(papel="admin", obras=None, so_se_vazio=True):
    """JS que grava sessão + perfil. `obras`: ids com acesso (padrão: todas)."""
    obras = IDS if obras is None else obras
    perfis = {}
    for i, oid in enumerate(IDS):
        if oid in obras:
            perfis[oid] = dict(PAPEIS[papel], nome="Teste", email="teste@cesbe.com.br", em=0)
    sessao = json.dumps({"access_token": "t.t.t", "refresh_token": "r", "expires_at": 4102444800,
                         "user": {"id": "00000000-0000-0000-0000-000000000001", "email": "teste@cesbe.com.br"}})
    refs = json.dumps(REFS)
    guard = "if (localStorage.getItem('buildly3::b3_auth')) return;" if so_se_vazio else ""
    return f"""(() => {{ try {{
      {guard}
      for (const r of {refs}) localStorage.setItem('buildly3::sb-' + r + '-auth-token', {json.dumps(sessao)});
      localStorage.setItem('buildly3::b3_auth', {json.dumps(json.dumps(perfis))});
    }} catch (e) {{}} }})();"""


def semear(ctx, papel="admin", obras=None):
    ctx.add_init_script(script_semear(papel, obras))
    return ctx


def contexto(browser, papel="admin", **kw):
    """Substitui browser.new_context(...): já entra logado como `papel`."""
    return semear(browser.new_context(**kw), papel)
