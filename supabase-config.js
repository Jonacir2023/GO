// BUILDLy Premium — registro de obras + cliente Supabase.
// Cada obra é um projeto Supabase totalmente separado (banco próprio, sem
// coluna obra_id compartilhada). Substitui o backend Google Apps Script/Sheets.
// Ver vault/Notas/Contrato do Backend.md.
(function (global) {
  'use strict';

  var CHAVE_OBRA_ATUAL = 'buildly3::obra_atual_id';

  // Chave "publishable/anon": segura para expor em HTML estático — RLS no
  // banco decide o que pode ser lido/escrito, não o sigilo da chave.
  var OBRAS = [
    {
      id: 'obra1',
      nome: 'Obra 1',
      url: 'https://ivssgstckfcuiyetxdze.supabase.co',
      anonKey: 'sb_publishable_vSuTiXWhcgCGx2kyj-BZ-Q_kjhoAlSA'
    },
    {
      id: 'obra2',
      nome: 'Obra 2',
      url: 'https://lwjbuzubnxnzkofcrhah.supabase.co',
      anonKey: 'sb_publishable_Un6wOWgITD22F2O-hqj91w_lVT9Beok'
    }
  ];

  var _clientes = {}; // cache de cliente supabase-js por id de obra

  function listar() {
    return OBRAS.slice();
  }

  function porId(id) {
    var i;
    for (i = 0; i < OBRAS.length; i++) if (OBRAS[i].id === id) return OBRAS[i];
    return null;
  }

  function atualId() {
    var id = null;
    try { id = localStorage.getItem(CHAVE_OBRA_ATUAL); } catch (e) {}
    if (id && porId(id)) return id;
    return OBRAS.length ? OBRAS[0].id : null;
  }

  function atual() {
    return porId(atualId());
  }

  function trocar(id) {
    if (!porId(id)) throw new Error('Obra desconhecida: ' + id);
    localStorage.setItem(CHAVE_OBRA_ATUAL, id);
  }

  function cliente(idOpcional) {
    var id = idOpcional || atualId();
    if (!id) throw new Error('Nenhuma obra configurada');
    if (_clientes[id]) return _clientes[id];
    var o = porId(id);
    if (!o) throw new Error('Obra desconhecida: ' + id);
    if (!global.supabase || !global.supabase.createClient) {
      throw new Error('supabase-js não carregado — inclua o CDN antes deste script');
    }
    var c = global.supabase.createClient(o.url, o.anonKey);
    _clientes[id] = c;
    return c;
  }

  global.B3Obras = {
    listar: listar,
    porId: porId,
    atual: atual,
    atualId: atualId,
    trocar: trocar,
    cliente: cliente
  };
})(window);
