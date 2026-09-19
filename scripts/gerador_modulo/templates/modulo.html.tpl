<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{{TITULO}} — BUILDLy Premium</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#4a5162;--bg-card:#5a6272;--bg-dark:#3a3f49;--bg-mid:#454c59;
  --ink:#ffffff;--accent:#dda583;--accent2:#89ab9d;--line:#666f80;
  --green:#7cb083;--red:#d98a7c;--blue:#8ea3c9;--yellow:#d9b26a;
  --sans:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,system-ui,sans-serif;
  --serif:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,system-ui,sans-serif;
  --radius:10px
}
html,body{background:var(--bg);color:var(--ink);font-family:var(--sans);font-size:15px;line-height:1.5;min-height:100vh}
body{max-width:480px;margin:0 auto;padding-bottom:40px}
.hdr{background:var(--bg-dark);color:#fff;padding:16px;display:flex;align-items:center;gap:10px;border-bottom:3px solid var(--accent)}
.hdr-back{width:34px;height:34px;border-radius:8px;background:rgba(255,255,255,.08);border:none;color:#fff;font-size:18px;cursor:pointer;flex-shrink:0}
.hdr-title{font-family:var(--serif);font-size:19px;font-weight:800}
.wrap{padding:16px}

.sec{background:var(--bg-card);border-radius:var(--radius);padding:16px;margin-bottom:14px;border:1px solid var(--line);box-shadow:0 2px 10px rgba(0,0,0,.3)}
.sec-title{font-family:var(--serif);font-size:16px;font-weight:700;color:#fff;margin-bottom:12px}

.frow{margin-bottom:12px}
.frow label{display:block;font-size:12px;font-weight:600;color:#fff;margin-bottom:4px;text-transform:uppercase}
.frow input,.frow select,.frow textarea{width:100%;min-width:0;padding:9px 11px;border:1.5px solid var(--line);border-radius:8px;font-family:var(--sans);font-size:14px;background:#454c59;color:var(--ink);outline:none;-webkit-appearance:none;appearance:none}
.frow input:focus,.frow select:focus,.frow textarea:focus{border-color:var(--accent)}
.frow textarea{resize:vertical;min-height:60px}

.btn{-webkit-appearance:none;appearance:none;box-sizing:border-box;display:flex;align-items:center;justify-content:center;gap:6px;width:100%;padding:12px 16px;border-radius:8px;font-family:var(--serif);font-size:14px;font-weight:700;cursor:pointer;border:none;background:var(--accent);color:#fff;text-transform:uppercase}
.btn:active{background:#c68f6d}

.item{background:#454c59;border-radius:8px;padding:11px 12px;margin-bottom:8px;border:1px solid var(--line)}
.item-top{display:flex;justify-content:space-between;align-items:flex-start;gap:8px}
.item-titulo{font-family:var(--serif);font-size:14px;font-weight:700}
.item-desc{font-size:12px;color:#fff;margin-top:3px;line-height:1.4}
.item-meta{font-size:11px;color:#fff;margin-top:6px;display:flex;gap:10px;flex-wrap:wrap}
.item-acoes{display:flex;gap:4px;flex-shrink:0}
.item-acoes button{background:none;border:none;color:#fff;font-size:15px;cursor:pointer;padding:2px 4px}
.badge{display:inline-block;padding:2px 8px;border-radius:20px;font-size:10px;font-weight:700;text-transform:uppercase}
.badge-aberto{background:#38414f;color:var(--blue)}
.badge-concluido{background:#384a3d;color:var(--green)}
.vazio{text-align:center;color:#fff;font-size:13px;padding:16px}
</style>
</head>
<body>

<div class="hdr">
  <button class="hdr-back" onclick="voltar()">←</button>
  <div class="hdr-title">{{TITULO}}</div>
</div>

<div class="wrap">
  <div class="sec">
    <div class="sec-title">📝 Novo registro</div>
    <form id="form-{{ID}}" onsubmit="return criar(event)">
      <div class="frow">
        <label>Título</label>
        <input type="text" id="f-titulo" required/>
      </div>
      <div class="frow">
        <label>Descrição</label>
        <textarea id="f-descricao"></textarea>
      </div>
      <div class="frow">
        <label>Responsável</label>
        <input type="text" id="f-responsavel"/>
      </div>
      <button type="submit" class="btn">✔ Salvar</button>
    </form>
  </div>

  <div class="sec">
    <div class="sec-title">📋 Lista</div>
    <div id="lista"></div>
    <div class="vazio" id="vazio" style="display:none">Nada registrado ainda.</div>
  </div>
</div>

<script>
/* ============================================================
   ESPAÇO PRÓPRIO DO BUILDLy — BUILDLY_ESPACO_PROPRIO
   Ver limpar-tudo.html para a versão comentada por extenso. Precisa rodar
   antes de qualquer outro script tocar no armazenamento.
   ============================================================ */
(function () {
  var P = 'buildly3::';
  var real;
  try { real = window.localStorage; } catch (e) { return; }
  if (!real || real.__buildly3) return;
  function nossas() {
    var out = [];
    for (var i = 0; i < real.length; i++) {
      var k = real.key(i);
      if (k && k.indexOf(P) === 0) out.push(k);
    }
    return out;
  }
  var espaco = {
    __buildly3: true,
    get length() { return nossas().length; },
    key: function (i) { var k = nossas()[i]; return k === undefined ? null : k.slice(P.length); },
    getItem: function (k) { return real.getItem(P + k); },
    setItem: function (k, v) { real.setItem(P + k, v); },
    removeItem: function (k) { real.removeItem(P + k); },
    clear: function () { nossas().forEach(function (k) { real.removeItem(k); }); }
  };
  try {
    Object.defineProperty(window, 'localStorage', { value: espaco, configurable: true, writable: false });
  } catch (e) {}
})();
</script>
<script>
/* Código de acesso do backend (APP_TOKEN) — shim sobre fetch(), igual ao
   resto do app. Ver apps-script/README.md. */
(function () {
  var CHAVE = 'b3_token';
  function ler() { try { return localStorage.getItem(CHAVE) || ''; } catch (e) { return ''; } }
  var _fetch = window.fetch.bind(window);
  window.fetch = function (url, opts) {
    if (typeof url !== 'string' || url.indexOf('script.google.com') === -1) return _fetch(url, opts);
    var t = ler();
    var alvo = t ? url + (url.indexOf('?') === -1 ? '?' : '&') + 'token=' + encodeURIComponent(t) : url;
    return _fetch(alvo, opts);
  };
})();

const APPS_SCRIPT_URL = 'https://script.google.com/macros/s/AKfycbwrSC_cQQW5IDu7Yrub0wnfMx7aInCX37U3BpiouC0qbFk6qgOwQpJzLXzH1XUX9lGEOA/exec';
const S = {
  get(k) { try { return JSON.parse(localStorage.getItem('{{PREFIXO}}' + k)); } catch { return null; } },
  set(k, v) { localStorage.setItem('{{PREFIXO}}' + k, JSON.stringify(v)); }
};

let itens = S.get('itens') || [];

function voltar() {
  try { if (parent && parent.switchTab) { parent.switchTab('home'); return; } } catch (e) {}
  location.href = 'buildly-completo.html';
}

function render() {
  const lista = document.getElementById('lista');
  lista.innerHTML = [...itens].reverse().map(it => `
    <div class="item">
      <div class="item-top">
        <div>
          <div class="item-titulo">${escapeHtml(it.titulo)}</div>
          ${it.descricao ? `<div class="item-desc">${escapeHtml(it.descricao)}</div>` : ''}
        </div>
        <div class="item-acoes">
          <button onclick="alternarStatus('${it.id}')" title="Concluir/reabrir">🔁</button>
          <button onclick="remover('${it.id}')" title="Remover">🗑️</button>
        </div>
      </div>
      <div class="item-meta">
        <span class="badge badge-${it.status}">${it.status === 'concluido' ? 'Concluído' : 'Aberto'}</span>
        ${it.responsavel ? `<span>${escapeHtml(it.responsavel)}</span>` : ''}
      </div>
    </div>`).join('');
  document.getElementById('vazio').style.display = itens.length ? 'none' : '';
}

function escapeHtml(s) {
  return String(s || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

async function criar(ev) {
  ev.preventDefault();
  const item = {
    id: '{{ID}}-' + Date.now(),
    titulo: document.getElementById('f-titulo').value.trim(),
    descricao: document.getElementById('f-descricao').value.trim(),
    responsavel: document.getElementById('f-responsavel').value.trim(),
    status: 'aberto',
    criadoEm: Date.now()
  };
  if (!item.titulo) return false;
  itens.push(item);
  S.set('itens', itens);
  render();
  document.getElementById('form-{{ID}}').reset();
  fetch(APPS_SCRIPT_URL, {
    method: 'POST',
    body: JSON.stringify({ path: '{{ID}}', action: 'criar', ...item })
  }).catch(e => console.warn('{{ID}}: não foi possível gravar na planilha:', e.message));
  return false;
}

function alternarStatus(id) {
  const it = itens.find(i => i.id === id);
  if (!it) return;
  it.status = it.status === 'concluido' ? 'aberto' : 'concluido';
  S.set('itens', itens);
  render();
  fetch(APPS_SCRIPT_URL, {
    method: 'POST',
    body: JSON.stringify({ path: '{{ID}}', action: 'atualizar-status', id, status: it.status })
  }).catch(e => console.warn('{{ID}}: não foi possível atualizar na planilha:', e.message));
}

function remover(id) {
  itens = itens.filter(i => i.id !== id);
  S.set('itens', itens);
  render();
  fetch(APPS_SCRIPT_URL, {
    method: 'POST',
    body: JSON.stringify({ path: '{{ID}}', action: 'remover', id })
  }).catch(e => console.warn('{{ID}}: não foi possível remover na planilha:', e.message));
}

async function carregarDaPlanilha() {
  try {
    const r = await fetch(APPS_SCRIPT_URL + '?path={{ID}}&action=listar');
    const d = await r.json();
    const doServidor = d.dados || d.itens || [];
    const ids = new Set(itens.map(i => i.id));
    doServidor.forEach(i => { if (!ids.has(i.id)) itens.push(i); });
    S.set('itens', itens);
    render();
  } catch (e) { console.warn('{{ID}}: não foi possível carregar da planilha:', e.message); }
}

render();
carregarDaPlanilha();
</script>
</body>
</html>
