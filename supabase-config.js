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

  // ── obra_config — cadastro compartilhado (Identificação, Logo, Jornada) ──
  // Fonte de verdade é o Supabase da obra ativa; o cache em localStorage
  // existe só para leitura síncrona (cabeçalhos, robô) entre um
  // configCarregar() e o próximo, e é o mesmo formato usado desde a versão
  // Google Sheets — quem já lê `obraCompartilhada().nome` não muda.
  var CHAVE_CACHE_PREFIX = 'buildly3::obra_config_cache::';

  function _cacheLer(id) {
    try {
      var raw = localStorage.getItem(CHAVE_CACHE_PREFIX + id);
      return raw ? (JSON.parse(raw) || {}) : {};
    } catch (e) { return {}; }
  }

  function _cacheGravar(id, obj) {
    try { localStorage.setItem(CHAVE_CACHE_PREFIX + id, JSON.stringify(obj)); } catch (e) {}
  }

  function _linhaParaObjeto(row) {
    if (!row) return {};
    return {
      nome: row.nome || '',
      empresa: row.empresa || '',
      local: row.local || '',
      descricao: row.descricao || '',
      contrato: row.contrato || '',
      cliente: row.cliente || '',
      gestor: row.gestor || '',
      gerenciadora: row.gerenciadora || '',
      logo: row.logo_url || '',
      dataInicio: row.data_inicio || '',
      dataTermino: row.data_termino || '',
      encerramentoNormal: row.encerramento_normal || '17:00',
      encerramentoSexta: row.encerramento_sexta || '16:00',
      encerramentoSabado: row.encerramento_sabado || '16:00',
      _atualizadoEm: row.atualizado_em ? Date.parse(row.atualizado_em) : Date.now()
    };
  }

  function _objetoParaLinha(o) {
    return {
      id: 1,
      nome: o.nome || null,
      empresa: o.empresa || null,
      local: o.local || null,
      descricao: o.descricao || null,
      contrato: o.contrato || null,
      cliente: o.cliente || null,
      gestor: o.gestor || null,
      gerenciadora: o.gerenciadora || null,
      logo_url: o.logo || null,
      data_inicio: o.dataInicio || null,
      data_termino: o.dataTermino || null,
      encerramento_normal: o.encerramentoNormal || '17:00',
      encerramento_sexta: o.encerramentoSexta || '16:00',
      encerramento_sabado: o.encerramentoSabado || '16:00',
      atualizado_em: new Date().toISOString()
    };
  }

  function config(idOpcional) {
    return _cacheLer(idOpcional || atualId());
  }

  async function configCarregar(idOpcional) {
    var id = idOpcional || atualId();
    var resp = await cliente(id).from('obra_config').select('*').eq('id', 1).maybeSingle();
    if (resp.error) throw resp.error;
    var obj = _linhaParaObjeto(resp.data);
    _cacheGravar(id, obj);
    return obj;
  }

  async function configSalvar(patch, idOpcional) {
    var id = idOpcional || atualId();
    var mesclado = Object.assign({}, _cacheLer(id), patch);
    var linha = _objetoParaLinha(mesclado);
    var resp = await cliente(id).from('obra_config').upsert(linha).select().maybeSingle();
    if (resp.error) throw resp.error;
    var obj = _linhaParaObjeto(resp.data || linha);
    _cacheGravar(id, obj);
    return obj;
  }

  global.B3Obras = {
    listar: listar,
    porId: porId,
    atual: atual,
    atualId: atualId,
    trocar: trocar,
    cliente: cliente,
    config: config,
    configCarregar: configCarregar,
    configSalvar: configSalvar
  };

  // Nome mantido por compatibilidade: todo módulo já chama
  // `obraCompartilhada()` para ler nome/logo/etc. da obra em uso.
  global.obraCompartilhada = config;
})(window);
