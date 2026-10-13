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
      nome: 'Eólica GranSul',
      url: 'https://ivssgstckfcuiyetxdze.supabase.co',
      anonKey: 'sb_publishable_vSuTiXWhcgCGx2kyj-BZ-Q_kjhoAlSA'
    },
    {
      id: 'obra2',
      nome: 'Obra 2 (vazia)',
      url: 'https://lwjbuzubnxnzkofcrhah.supabase.co',
      anonKey: 'sb_publishable_Un6wOWgITD22F2O-hqj91w_lVT9Beok'
    }
  ];

  var _clientes = {}; // cache de cliente supabase-js por id de obra

  // Lista todas as obras (usada pelo login, que precisa tentar entrar nas duas).
  function listarTodas() {
    return OBRAS.slice();
  }

  // Obras que o usuário logado pode abrir (o administrador libera por pessoa). Sem login ainda,
  // devolve todas — quem decide o que abrir é a tela de login e, no banco, o RLS.
  function listar() {
    var todas = OBRAS.slice();
    try {
      var ok = global.B3Auth && global.B3Auth.obrasPermitidas ? global.B3Auth.obrasPermitidas() : null;
      if (ok && ok.length) return todas.filter(function (o) { return ok.indexOf(o.id) >= 0; });
    } catch (e) {}
    return todas;
  }

  function porId(id) {
    var i;
    for (i = 0; i < OBRAS.length; i++) if (OBRAS[i].id === id) return OBRAS[i];
    return null;
  }

  function atualId() {
    var id = null;
    try { id = localStorage.getItem(CHAVE_OBRA_ATUAL); } catch (e) {}
    var disp = listar();
    if (id && porId(id) && disp.some(function (o) { return o.id === id; })) return id;
    return disp.length ? disp[0].id : (OBRAS.length ? OBRAS[0].id : null);
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
    var c = global.supabase.createClient(o.url, o.anonKey, {
      auth: {
        storage: typeof localStorage !== 'undefined' ? localStorage : undefined,
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true
      }
    });
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


  // ══════════════════════════════════════════════════════════════════════
  // LOGIN (Supabase Auth) — e-mail + senha.
  // Cada obra é um projeto Supabase separado, com seus próprios usuários. A pessoa tem a MESMA
  // conta (e-mail e senha) nas duas; o administrador libera, obra por obra, o papel dela
  // (tabela `perfis`: admin, portaria, … ou "pendente" = sem acesso). O papel define os módulos
  // (tabela `papeis`). O que protege os dados de verdade é o RLS do banco (sql/010); esta camada
  // decide o que a tela mostra. Ver vault/Decisões/2026-10-06 Login e perfis de acesso.md.
  // ══════════════════════════════════════════════════════════════════════
  var CHAVE_AUTH = 'b3_auth';             // cache dos perfis (localStorage do app, com o prefixo próprio)
  var _perfis = null;                      // { obraId: { papel, rotulo, nome, email, modulos:[…], em } }

  function _chaveSB(o) { return 'sb-' + o.url.replace(/^https?:\/\//, '').split('.')[0] + '-auth-token'; }

  function _temSessaoLocal(o) {
    try {
      var raw = localStorage.getItem(_chaveSB(o));
      if (!raw) return false;
      var j = JSON.parse(raw);
      return !!(j && (j.access_token || (j.currentSession && j.currentSession.access_token)));
    } catch (e) { return false; }
  }

  function _perfisLer() {
    if (_perfis) return _perfis;
    try { _perfis = JSON.parse(localStorage.getItem(CHAVE_AUTH)) || {}; } catch (e) { _perfis = {}; }
    return _perfis;
  }

  function _perfisGravar() {
    try { localStorage.setItem(CHAVE_AUTH, JSON.stringify(_perfis || {})); } catch (e) {}
  }

  function _msgErro(e) {
    var m = String((e && (e.message || e.error_description)) || e || '');
    if (/invalid login credentials/i.test(m)) return 'E-mail ou senha incorretos.';
    if (/email not confirmed/i.test(m)) return 'Confirme o e-mail (o link foi enviado) antes de entrar.';
    if (/already registered|already been registered/i.test(m)) return 'Este e-mail já tem cadastro. Use "Entrar".';
    if (/password should be at least|weak/i.test(m)) return 'Senha fraca: use pelo menos 8 caracteres.';
    if (/rate limit|too many/i.test(m)) return 'Muitas tentativas. Aguarde alguns minutos.';
    if (/failed to fetch|network|load failed/i.test(m)) return 'Sem conexão com o servidor.';
    return m || 'Não foi possível concluir.';
  }

  // Obras onde há sessão guardada e o papel não é "pendente"
  function obrasPermitidas() {
    var p = _perfisLer(), out = [];
    OBRAS.forEach(function (o) {
      var pf = p[o.id];
      if (pf && pf.papel && pf.papel !== 'pendente' && _temSessaoLocal(o)) out.push(o.id);
    });
    return out;
  }

  function estado() {
    var p = _perfisLer();
    var comSessao = OBRAS.filter(_temSessaoLocal).map(function (o) { return o.id; });
    var permitidas = obrasPermitidas();
    var nome = '', email = '';
    comSessao.forEach(function (id) { if (p[id]) { nome = nome || p[id].nome; email = email || p[id].email; } });
    return { logado: comSessao.length > 0, comAcesso: permitidas.length > 0, obras: permitidas, comSessao: comSessao, nome: nome, email: email };
  }

  function _perfilDe(idOpcional) {
    var p = _perfisLer();
    var id = idOpcional || atualId();
    return (id && p[id]) || null;
  }
  function papel(idOpcional) { var pf = _perfilDe(idOpcional); return pf ? pf.papel : null; }
  function ehAdmin(idOpcional) { return papel(idOpcional) === 'admin'; }
  function podeModulo(modulo, idOpcional) {
    var pf = _perfilDe(idOpcional);
    if (!pf || !pf.modulos) return false;
    return pf.modulos.indexOf('*') >= 0 || pf.modulos.indexOf(modulo) >= 0;
  }

  // Busca no servidor o perfil de cada obra com sessão; sessão vencida/recusada = sai daquela obra.
  // Sem conexão: mantém o que está guardado (a portaria precisa continuar lançando).
  async function iniciar() {
    var p = _perfisLer();
    if (!global.supabase || !global.supabase.createClient) return estado();
    await Promise.all(OBRAS.map(async function (o) {
      if (!_temSessaoLocal(o)) { delete p[o.id]; return; }
      try {
        var cli = cliente(o.id);
        var sess = await cli.auth.getSession();
        var user = sess && sess.data && sess.data.session && sess.data.session.user;
        if (!user) { delete p[o.id]; try { localStorage.removeItem(_chaveSB(o)); } catch (e) {} return; }
        var r = await cli.from('perfis').select('papel,nome,email,papeis(rotulo,modulos)').eq('user_id', user.id).maybeSingle();
        if (r.error) throw r.error;
        if (!r.data) { p[o.id] = { papel: 'pendente', rotulo: 'Sem acesso', nome: '', email: user.email, modulos: [], em: Date.now() }; return; }
        var pap = r.data.papeis || {};
        p[o.id] = { papel: r.data.papel, rotulo: pap.rotulo || r.data.papel, nome: r.data.nome || '', email: r.data.email || user.email, modulos: pap.modulos || [], em: Date.now() };
      } catch (e) { /* sem conexão ou obra pausada: fica o último perfil conhecido */ }
    }));
    _perfis = p; _perfisGravar();
    return estado();
  }

  async function entrar(email, senha) {
    if (!global.supabase || !global.supabase.createClient) return { ok: false, erro: 'Sem conexão com o servidor de login.' };
    var erros = [], algum = false, parcial = [];
    await Promise.all(OBRAS.map(async function (o) {
      try {
        var r = await cliente(o.id).auth.signInWithPassword({ email: String(email).trim(), password: senha });
        if (r.error) throw r.error;
        algum = true;
      } catch (e) { erros.push(_msgErro(e)); parcial.push(o.nome); }
    }));
    if (!algum) return { ok: false, erro: erros[0] || 'Não foi possível entrar.' };
    var st = await iniciar();
    return { ok: true, estado: st, parcial: parcial };
  }

  async function cadastrar(nome, email, senha) {
    if (!global.supabase || !global.supabase.createClient) return { ok: false, erro: 'Sem conexão com o servidor de login.' };
    var erros = [], algum = false, precisaConfirmar = false;
    await Promise.all(OBRAS.map(async function (o) {
      try {
        var r = await cliente(o.id).auth.signUp({ email: String(email).trim(), password: senha,
          options: { data: { nome: nome }, emailRedirectTo: location.origin + location.pathname.replace(/[^/]*$/, '') + 'buildly-completo.html' } });
        if (r.error) throw r.error;
        algum = true;
        if (!(r.data && r.data.session)) precisaConfirmar = true;
      } catch (e) { erros.push(_msgErro(e)); }
    }));
    if (!algum) return { ok: false, erro: erros[0] || 'Não foi possível cadastrar.' };
    return { ok: true, precisaConfirmar: precisaConfirmar };
  }

  async function recuperarSenha(email) {
    var enviados = 0;
    await Promise.all(OBRAS.map(async function (o) {
      try {
        var r = await cliente(o.id).auth.resetPasswordForEmail(String(email).trim(), { redirectTo: location.origin + location.pathname.replace(/[^/]*$/, '') + 'buildly-completo.html' });
        if (!r.error) enviados++;
      } catch (e) {}
    }));
    return { ok: enviados > 0, enviados: enviados };
  }

  // Troca a senha em todas as obras onde há sessão (as duas contas precisam continuar iguais)
  async function trocarSenha(nova) {
    var falhas = [], feitas = 0;
    await Promise.all(OBRAS.filter(_temSessaoLocal).map(async function (o) {
      try {
        var r = await cliente(o.id).auth.updateUser({ password: nova });
        if (r.error) throw r.error;
        feitas++;
      } catch (e) { falhas.push(o.nome + ': ' + _msgErro(e)); }
    }));
    return { ok: feitas > 0 && !falhas.length, feitas: feitas, falhas: falhas };
  }

  async function sair() {
    await Promise.all(OBRAS.map(async function (o) {
      try { if (global.supabase && global.supabase.createClient) await cliente(o.id).auth.signOut(); } catch (e) {}
      try { localStorage.removeItem(_chaveSB(o)); } catch (e) {}
    }));
    _perfis = {}; _perfisGravar();
  }

  // ── Administração de acessos (só o papel admin enxerga as outras pessoas) ──
  async function listarPapeis(idOpcional) {
    var r = await cliente(idOpcional || atualId()).from('papeis').select('papel,rotulo,modulos').order('papel');
    if (r.error) throw r.error;
    return r.data || [];
  }

  // Une, por e-mail, os perfis das obras em que o usuário é admin
  async function listarUsuarios() {
    var mapa = {}, obras = OBRAS.filter(function (o) { return ehAdmin(o.id) && _temSessaoLocal(o); });
    await Promise.all(obras.map(async function (o) {
      var r = await cliente(o.id).from('perfis').select('user_id,email,nome,papel,criado_em').order('criado_em');
      if (r.error) throw r.error;
      (r.data || []).forEach(function (u) {
        var k = String(u.email || u.user_id).toLowerCase();
        var m = mapa[k] || (mapa[k] = { email: u.email, nome: u.nome || '', porObra: {} });
        if (u.nome && !m.nome) m.nome = u.nome;
        m.porObra[o.id] = { user_id: u.user_id, papel: u.papel };
      });
    }));
    return { usuarios: Object.keys(mapa).map(function (k) { return mapa[k]; }), obras: obras.map(function (o) { return { id: o.id, nome: o.nome }; }) };
  }

  async function definirPapel(obraId, userId, novoPapel) {
    var r = await cliente(obraId).from('perfis').update({ papel: novoPapel, atualizado_em: new Date().toISOString() }).eq('user_id', userId).select('user_id').maybeSingle();
    if (r.error) throw r.error;
    return true;
  }

  // Páginas abertas direto (fora da casca) exigem sessão; sem ela, voltam para a casca, que mostra o login
  // e, depois de entrar, devolve para cá (?next=).
  function guardar() {
    try {
      if (global.B3_CASCA || global.top !== global.self) return;
      if (estado().logado) return;
      var alvo = location.pathname.split('/').pop() + location.search;
      location.replace('buildly-completo.html?next=' + encodeURIComponent(alvo));
    } catch (e) {}
  }

  global.B3Auth = {
    estado: estado, iniciar: iniciar, entrar: entrar, cadastrar: cadastrar, recuperarSenha: recuperarSenha,
    trocarSenha: trocarSenha, sair: sair, obrasPermitidas: obrasPermitidas, papel: papel, ehAdmin: ehAdmin,
    podeModulo: podeModulo, perfil: _perfilDe, listarPapeis: listarPapeis, listarUsuarios: listarUsuarios,
    definirPapel: definirPapel, guardar: guardar
  };
  if (global.addEventListener) global.addEventListener('DOMContentLoaded', function () { guardar(); });

  global.B3Obras = {
    listar: listar,
    listarTodas: listarTodas,
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
