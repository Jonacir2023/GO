// ============================================================
// Google Apps Script — BUILDLy Premium (plataforma)
// Módulos: Pauta · CheckIn · Diário · Custos/NF · Fotos (Drive) · Backup (Drive)
// Planilha: https://docs.google.com/spreadsheets/d/19SDuzU_CLzDRfbNZWJZQzchLDCeQYHgiSC_FxDSdhOw
//
// ⚠️ ESTE SCRIPT É EXCLUSIVO DA PLATAFORMA BUILDLy2.
//    Não substitui nem altera o script do "JC - Gestão de Obras" (19fTP_qy...),
//    que continua atendendo o app de produção em /diario-obras/.
//    São dois projetos independentes, cada um com sua planilha.
//
// Como implantar:
// 1. Abra a planilha BUILDLy Premium → Extensões → Apps Script
// 2. Cole este código substituindo todo o conteúdo existente
// 3. Configurações do projeto (⚙️) → marque "Mostrar o arquivo appsscript.json"
//    e cole os oauthScopes de apps-script/appsscript.json
// 4. Selecione qualquer função → Executar → aprove a autorização
//    (inclui "Conectar-se a um serviço externo", necessária para o robô 🤖)
// 5. Implantar → Nova implantação → Web app
//    Executar como: Eu · Quem tem acesso: Qualquer pessoa
// 6. Copie a URL /exec gerada — ela vai em APPS_SCRIPT_URL_DIARIO (rdo.html)
//    e APPS_SCRIPT_URL (buildly-completo.html)
// 7. Para o robô: Configurações do projeto → Propriedades do script →
//    adicione ANTHROPIC_API_KEY
//
// Restaurado em 2026-08-21 a partir da Lixeira do Google Drive, depois que o
// projeto foi apagado por engano durante a limpeza da obra encerrada — o que
// estava versionado no repo até então (apps-script/BuildlyBackend.gs numa
// versão anterior) era uma reconstrução parcial baseada só no que os
// fetch() do front-end deixavam ver; este é o original de verdade.
// Única mudança em relação ao que foi recuperado: a função errorResponse()
// no fim do arquivo, que não veio na cópia recuperada (só faltava essa —
// o padrão é óbvio pelo uso em toda parte e pelo espelho de successResponse).
// ============================================================

const SHEET_ID           = '19SDuzU_CLzDRfbNZWJZQzchLDCeQYHgiSC_FxDSdhOw';

// Os nomes abaixo são resolvidos por getSheet() ignorando maiúscula, acento,
// hífen, espaço e plural. Então 'Pauta' encontra a aba "Pautas", e 'CheckIn'
// encontra "Check-ins". Não é preciso renomear abas na planilha.
const SHEET_NAME_PAUTA   = 'Pauta';
const SHEET_NAME_CHECKIN = 'CheckIn';
const SHEET_NAME_DIARIO  = 'Diário';
const SHEET_NAME_NF      = 'Notas Fiscais';
const SHEET_NAME_ITENSNF = 'Itens NF';

// 24 colunas
const COLUNAS_DIARIO = [
  'Data',                    // A
  'Dia da Semana',           // B
  'Obra',                    // C
  'Empresa',                 // D
  'Cidade',                  // E
  'Local da Obra',           // F  ← local diário onde os trabalhos foram executados
  'Descrição do Local',      // G  ← descrição do local
  'Tempo / Clima',           // H
  'Jornada',                 // I
  'DSS — Horário',           // J
  'DSS — Ministrado Por',    // K
  'DSS — Tema',              // L
  'Atividades do Dia',       // M
  'Efetivo Total',           // N
  'Efetivo por Função',      // O
  'Colaboradores Presentes', // P
  'Equipamentos Utilizados', // Q
  'Veículos Leves',          // R
  'Veículos/Equip. Parados', // S
  'Eventos de Segurança',    // T
  'Eventos de Meio Ambiente',// U
  'Observações do Dia',      // V
  'Apontador',               // W
  'Fotos',                   // X  ← links das fotos no Google Drive
  'RDO Nº'                   // Y  ← numeração sequencial do relatório
];

// ============================================================
// CONTROLE DE ACESSO
//
// O web app é publicado como "qualquer pessoa" — é o único modo em que o
// fetch() de uma página estática funciona sem fluxo de login OAuth. Sem mais
// nada, isso deixa a planilha inteira aberta a quem descobrir a URL /exec, que
// está dentro do HTML publicado (repositório público). Além de ler e alterar
// os dados da obra, um estranho poderia chamar ia/perguntar à vontade, gastando
// a chave da Anthropic.
//
// A trava é um código de acesso combinado, guardado em Propriedades do script
// (APP_TOKEN) e enviado pelo app em toda chamada. Nunca fica no HTML nem no
// repositório: o usuário digita uma vez por aparelho e o app guarda localmente.
//
// IMPORTANTE — a checagem é opcional de propósito: enquanto APP_TOKEN não
// existir nas Propriedades do script, tudo passa como antes. Isso permite
// implantar backend e front-end sem janela de app quebrado; a proteção liga no
// momento em que a propriedade é criada. Ver apps-script/README.md.
// ============================================================

function tokenConfigurado() {
  return PropertiesService.getScriptProperties().getProperty('APP_TOKEN') || '';
}

// Devolve null quando pode seguir, ou a resposta de erro quando deve barrar.
function barrarSemToken(e, body) {
  const esperado = tokenConfigurado();
  if (!esperado) return null; // proteção ainda não ativada

  const recebido = (e && e.parameter && e.parameter.token) ||
                   (body && body.token) || '';
  if (String(recebido) === String(esperado)) return null;

  return ContentService
    .createTextOutput(JSON.stringify({
      ok: false,
      status: 'erro',
      codigo: 'token_invalido',
      error: 'Código de acesso ausente ou incorreto.'
    }))
    .setMimeType(ContentService.MimeType.JSON);
}

// ============================================================
// ROTEAMENTO
// ============================================================

function doGet(e) {
  const path   = e.parameter.path   || '';
  const action = e.parameter.action || '';
  const data   = e.parameter.data   || '';
  const mes    = e.parameter.mes    || '';
  const barrado = barrarSemToken(e, null);
  if (barrado) return barrado;
  try {
    if (path === 'pauta'   && action === 'listar')      return listarPautas();
    if (path === 'checkin' && action === 'historico')   return listarCheckIns();
    if (path === 'diario'  && action === 'carregar' && data) return carregarDiario(data);
    if (path === 'diario'  && action === 'lista-mes' && mes) return listarDiariosMes(mes);
    if (path === 'diario'  && action === 'salvar'   && e.parameter.dados) {
      return salvarDiario(JSON.parse(e.parameter.dados));
    }
    if (path === 'diario'  && action === 'limpar-duplicatas') {
      const resultado = limparDuplicatasDiario();
      return successResponse({ ok: true, ...resultado });
    }
    if (path === 'pauta'   && action === 'limpar-duplicatas') {
      const resultado = limparDuplicatasPauta();
      return successResponse({ ok: true, ...resultado });
    }
    if (path === 'checkin' && action === 'limpar-duplicatas') {
      const resultado = limparDuplicatasCheckin();
      return successResponse({ ok: true, ...resultado });
    }
    if (path === 'backup'  && action === 'buscar-ultimo') {
      return buscarUltimoBackup(e.parameter.obra || 'Obra');
    }
    return successResponse({ ok: true, msg: 'API Diário de Obras ativa' });
  } catch (err) { return errorResponse(err.message); }
}

function doPost(e) {
  try {
    const raw  = (e && e.postData && e.postData.contents) ? e.postData.contents : '{}';
    const body = JSON.parse(raw);

    // Aceita path/action tanto na query string (?path=x&action=y) quanto dentro
    // do corpo JSON. O buildly-completo.html manda no corpo e o rdo.html manda
    // na query — sem isto, metade das chamadas do app caía em "Endpoint não
    // encontrado" e o dado se perdia em silêncio.
    const path   = (e && e.parameter && e.parameter.path)   || body.path   || '';
    const action = (e && e.parameter && e.parameter.action) || body.action || '';

    // Depois do JSON.parse: o token também é aceito dentro do corpo, para o
    // caso de alguma chamada futura não conseguir usar a query string.
    const barrado = barrarSemToken(e, body);
    if (barrado) return barrado;

    if (path === 'foto')                                     return salvarFoto(body);
    if (path === 'backup')                                   return salvarBackup(body);
    if (path === 'pauta'   && action === 'criar')            return criarPauta(body);
    if (path === 'pauta'   && action === 'atualizar-status') return atualizarStatusPauta(body);
    if (path === 'pauta'   && action === 'remover')          return removerPauta(body);
    if (path === 'checkin' && action === 'salvar')           return salvarCheckIn(body);
    if (path === 'checkin' && action === 'remover')          return removerCheckIn(body);
    if (path === 'diario'  && action === 'salvar')           return salvarDiario(body);
    if (path === 'custos'  && action === 'salvar')           return salvarNotaFiscal(body);
    if (path === 'ia'      && action === 'perguntar')        return perguntarIA(body);
    return errorResponse('Endpoint não encontrado: ' + path + '/' + action);
  } catch (err) { return errorResponse(err.message); }
}

// ============================================================
// PAUTA
// ============================================================

function listarPautas() {
  const sheet = getSheet(SHEET_NAME_PAUTA);
  if (!sheet) return errorResponse('Aba Pauta não encontrada');
  const values  = sheet.getDataRange().getValues();
  const headers = values[0];
  const lista   = [];
  for (let i = 1; i < values.length; i++) {
    if (!values[i][0]) break;
    const bruto = {};
    headers.forEach((h, j) => bruto[h] = values[i][j]);
    lista.push(normalizarPauta(bruto));
  }
  // 'pautas' e 'dados' apontam para a mesma lista, e 'status' vai junto de 'ok'.
  // O checkinCarregarAssuntosDaPauta() procura data.status e data.dados; sem os
  // dois ele caia sempre no ramo de erro e nunca importava assunto nenhum.
  return successResponse({ ok: true, status: 'ok', pautas: lista, dados: lista });
}

// Caminho inverso da rotularStatus: da planilha de volta ao codigo do app.
// A aba tem linhas antigas gravadas em minusculo ('afazer') e as novas saem
// como rotulo ('Aberta'); as duas formas precisam chegar iguais no app.
function codigoStatus(s) {
  var mapa = {
    aberta: 'afazer',       afazer: 'afazer',
    emandamento: 'fazendo', fazendo: 'fazendo',
    concluido: 'concluido', cancelado: 'cancelado'
  };
  var chave = String(s || '').toLowerCase()
    .normalize('NFD').replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z]/g, '');
  return mapa[chave] || chave || 'afazer';
}

// Casa os nomes das colunas da planilha com os campos que o app usa, mantendo
// tambem as chaves originais do cabecalho para quem preferir le-las. Aceita
// variacao de acento porque o cabecalho pode ter sido digitado a mao.
function normalizarPauta(bruto) {
  var pega = function() {
    for (var i = 0; i < arguments.length; i++) {
      var v = bruto[arguments[i]];
      if (v !== undefined && v !== null && v !== '') return v;
    }
    return '';
  };
  var o = {};
  Object.keys(bruto).forEach(function(k) { o[k] = bruto[k]; });
  o.id         = pega('ID', 'id');
  o.assunto    = pega('Assunto', 'assunto');
  o.desc       = pega('Descrição', 'Descricao', 'descricao', 'desc');
  o.criador    = pega('Criador', 'criador');
  o.resp       = pega('Responsável', 'Responsavel', 'responsavel', 'resp');
  o.setor      = pega('Setor', 'setor');
  o.prioridade = String(pega('Prioridade', 'prioridade')).toLowerCase();
  o.status     = codigoStatus(pega('Status', 'status'));
  o.dataLanc   = normalizarData(pega('Data Lançamento', 'Data Lancamento', 'dataLanc'));
  o.dataTerm   = normalizarData(pega('Data Término', 'Data Termino', 'dataTerm'));
  return o;
}

// O app usa códigos internos minúsculos ('afazer', 'fazendo'...) e a planilha
// guarda o rótulo legível. Converte um no outro; se vier já legível, mantém.
function rotularStatus(s) {
  var mapa = {
    afazer: 'Aberta', fazendo: 'Em Andamento',
    concluido: 'Concluído', cancelado: 'Cancelado'
  };
  var chave = String(s || '').toLowerCase().replace(/[^a-z]/g, '');
  return mapa[chave] || s || 'Aberta';
}

function criarPauta(data) {
  const sheet = getSheet(SHEET_NAME_PAUTA);
  if (!sheet) return errorResponse('Aba Pauta não encontrada');
  // Usa o ID que o app já gerou localmente (Date.now() no momento da
  // criação), se vier. Sem isto, o servidor sempre mintava um ID próprio,
  // diferente do local — então apagar localmente (e lembrar do ID local)
  // nunca correspondia à linha real na planilha, que voltava a aparecer na
  // próxima sincronização como se fosse um item novo.
  const id    = data.id || ('PAUTA-' + Date.now());
  const agora = new Date().toISOString();

  // Upsert por ID: se a linha já existe, atualiza no lugar em vez de
  // duplicar. Sem isto, reenviar o mesmo assunto — por exemplo a
  // sincronização automática de 2 em 2 minutos do buildly-completo.html —
  // criava uma linha nova a cada vez, multiplicando os assuntos sem parar.
  const valores = sheet.getDataRange().getValues();
  let linhaExistente = -1;
  let criadoOriginal = agora;
  for (let i = 1; i < valores.length; i++) {
    if (String(valores[i][0]) === String(id)) {
      linhaExistente = i + 1;
      criadoOriginal = valores[i][10] || agora; // coluna K = Criado Em
      break;
    }
  }

  const linha = [
    id,
    data.assunto        || '',
    data.descricao      || data.desc || '',
    data.criador        || '',
    data.responsavel    || data.resp || '',
    data.setor          || '',
    data.prioridade     || 'Média',
    rotularStatus(data.status),
    // aceita os dois formatos de nome que os apps mandam
    data.data_lancamento || data.dataLanc || new Date().toISOString().slice(0,10),
    data.data_termino    || data.dataTerm || '',
    criadoOriginal,
    agora
  ];

  if (linhaExistente > 0) {
    sheet.getRange(linhaExistente, 1, 1, linha.length).setValues([linha]);
  } else {
    sheet.appendRow(linha);
  }

  // 'ok' para o rdo.html, 'status' para o buildly-completo.html — os dois checam
  // campos diferentes. O status do registro vai em statusRegistro.
  return successResponse({
    ok: true, status: 'ok', id,
    statusRegistro: rotularStatus(data.status), msg: 'Pauta criada'
  });
}

function atualizarStatusPauta(data) {
  const sheet = getSheet(SHEET_NAME_PAUTA);
  if (!sheet) return errorResponse('Aba Pauta não encontrada');
  const novo = rotularStatus(data.novo_status || data.status);
  const values = sheet.getDataRange().getValues();
  for (let i = 1; i < values.length; i++) {
    if (String(values[i][0]) === String(data.id)) {
      sheet.getRange(i+1, 8).setValue(novo);
      sheet.getRange(i+1, 12).setValue(new Date().toISOString());
      return successResponse({ ok: true, status: 'ok', statusRegistro: novo });
    }
  }
  return errorResponse('Pauta não encontrada: ' + data.id);
}

// Apaga a linha pelo ID. Sem isto, remover um assunto no app só escondia
// ele localmente — a linha continuava na planilha e voltava a aparecer na
// próxima sincronização.
function removerPauta(data) {
  const sheet = getSheet(SHEET_NAME_PAUTA);
  if (!sheet) return errorResponse('Aba Pauta não encontrada');
  const values = sheet.getDataRange().getValues();
  for (let i = 1; i < values.length; i++) {
    if (String(values[i][0]) === String(data.id)) {
      sheet.deleteRow(i + 1);
      return successResponse({ ok: true, status: 'ok', msg: 'Pauta removida' });
    }
  }
  return successResponse({ ok: true, status: 'ok', msg: 'Pauta já não existia na planilha' });
}

// ============================================================
// CHECKIN
// ============================================================

// Colunas usadas se a aba estiver vazia. Se ja tiver cabecalho, ele manda:
// appendPorCabecalho casa os campos pelo nome, entao a ordem das colunas na
// planilha pode ser qualquer uma.
const COLUNAS_CHECKIN = [
  'ID', 'Assunto', 'Descrição', 'Criador', 'Responsável', 'Setor',
  'Prioridade', 'Status', 'Data Término', 'Concluído Em', 'Criado Em', 'Atualizado Em'
];

// A aba Check-ins guarda ASSUNTOS, com as mesmas colunas da aba Pautas — nao
// reunioes. A versao anterior desta funcao vinha do script antigo e gravava
// por posicao no formato de reuniao (data, hora, obra, JSON de assuntos,
// resumo), o que jogava "[]" na coluna Responsavel e o timestamp na coluna
// Prioridade.
//
// Aceita os dois formatos que o app envia:
//   - assunto plano, um por chamada, vindo de sincronizarComGoogleSheets
//   - reuniao com lista de assuntos, vinda de checkinSalvarReuniao; nesse caso
//     grava uma linha por assunto, que e o que a aba representa
function salvarCheckIn(body) {
  const sheet = getSheet(SHEET_NAME_CHECKIN);
  if (!sheet) return errorResponse('Aba CheckIn não encontrada');

  const d = body.dados || body;
  const lista = (d.assuntos && d.assuntos.length) ? d.assuntos : [d];
  const validos = lista.filter(function(a) {
    return a && String(a.assunto || '').trim();
  });
  // Sem isto, uma reuniao sem assuntos gravava uma linha em branco.
  if (!validos.length) return errorResponse('Nenhum assunto para gravar');

  const ids = [];
  validos.forEach(function(a, i) {
    // Usa o ID que o app já gerou localmente, se vier — mesmo motivo do
    // criarPauta: sem isto, apagar localmente nunca correspondia à linha
    // real na planilha, que reaparecia como item "novo" na sincronização.
    const id    = a.id || ('CHECKIN-' + Date.now() + (validos.length > 1 ? '-' + (i + 1) : ''));
    const agora = new Date().toISOString();
    const rotulo = rotularStatus(a.status);
    // Upsert por ID — sem isto, reenviar o mesmo assunto (por exemplo a
    // sincronização automática de 2 em 2 minutos do buildly-completo.html)
    // criava uma linha nova a cada vez, multiplicando os assuntos sem parar.
    upsertPorCabecalho(sheet, COLUNAS_CHECKIN, id, {
      'ID': id,
      'Assunto': a.assunto || '',
      'Descrição': a.descricao || a.desc || '',
      'Criador': a.criador || '',
      'Responsável': a.responsavel || a.resp || '',
      'Setor': a.setor || '',
      'Prioridade': String(a.prioridade || 'media').toLowerCase(),
      'Status': rotulo,
      'Data Término': normalizarData(a.data_termino || a.dataTerm || ''),
      'Concluído Em': rotulo === 'Concluído' ? agora : '',
      'Criado Em': agora,
      'Atualizado Em': agora
    });
    ids.push(id);
  });

  return successResponse({
    ok: true, status: 'ok', id: ids[0], ids: ids,
    linhas: ids.length, msg: 'Check-in salvo'
  });
}

// Mesmo padrão de normalizarPauta: casa os nomes das colunas da planilha com
// os campos que o app usa (id, assunto, desc...), mantendo as chaves originais
// do cabeçalho também. Sem isto o app não sabia ler de volta o que a própria
// planilha guardava — checkinCarregarHistoricoDoServidor() sempre vinha vazio.
function normalizarCheckin(bruto) {
  var pega = function() {
    for (var i = 0; i < arguments.length; i++) {
      var v = bruto[arguments[i]];
      if (v !== undefined && v !== null && v !== '') return v;
    }
    return '';
  };
  var o = {};
  Object.keys(bruto).forEach(function(k) { o[k] = bruto[k]; });
  o.id          = pega('ID', 'id');
  o.assunto     = pega('Assunto', 'assunto');
  o.desc        = pega('Descrição', 'Descricao', 'descricao', 'desc');
  o.criador     = pega('Criador', 'criador');
  o.resp        = pega('Responsável', 'Responsavel', 'responsavel', 'resp');
  o.setor       = pega('Setor', 'setor');
  o.prioridade  = String(pega('Prioridade', 'prioridade')).toLowerCase();
  o.status      = codigoStatus(pega('Status', 'status'));
  o.dataTerm    = normalizarData(pega('Data Término', 'Data Termino', 'dataTerm'));
  o.concluidoEm = pega('Concluído Em', 'Concluido Em', 'concluidoEm');
  o.criadoEm    = pega('Criado Em', 'criadoEm');
  o._origem     = 'checkin';
  return o;
}

function listarCheckIns() {
  const sheet = getSheet(SHEET_NAME_CHECKIN);
  if (!sheet) return errorResponse('Aba CheckIn não encontrada');
  const values  = sheet.getDataRange().getValues();
  const headers = values[0];
  const checkins = [];
  for (let i = 1; i < values.length; i++) {
    if (!values[i][0]) break;
    const bruto = {};
    headers.forEach((h, j) => bruto[h] = values[i][j]);
    checkins.push(normalizarCheckin(bruto));
  }
  return successResponse({ ok: true, status: 'ok', checkins: checkins, dados: checkins });
}

// Apaga a linha pelo ID. Sem isto, remover um assunto no Check-in só
// escondia ele localmente — a linha continuava na planilha e voltava a
// aparecer na próxima sincronização.
function removerCheckIn(data) {
  const sheet = getSheet(SHEET_NAME_CHECKIN);
  if (!sheet) return errorResponse('Aba CheckIn não encontrada');
  const values = sheet.getDataRange().getValues();
  for (let i = 1; i < values.length; i++) {
    if (String(values[i][0]) === String(data.id)) {
      sheet.deleteRow(i + 1);
      return successResponse({ ok: true, status: 'ok', msg: 'Check-in removido' });
    }
  }
  return successResponse({ ok: true, status: 'ok', msg: 'Check-in já não existia na planilha' });
}

// ============================================================
// CUSTOS / NOTAS FISCAIS
// ============================================================

// Colunas usadas quando a aba ainda está vazia. Se a aba já tiver cabeçalho,
// ele é respeitado e os campos são casados pelo nome — assim a ordem das
// colunas na planilha pode ser qualquer uma sem quebrar a gravação.
const COLUNAS_NF = [
  'ID', 'Número NF', 'Série', 'Data Emissão', 'Fornecedor',
  'Categoria', 'Responsável', 'Observações', 'Total NF', 'Criado em'
];
const COLUNAS_ITENS_NF = [
  'ID Item', 'ID NF', 'Número NF', 'Descrição',
  'Quantidade', 'Preço Unitário', 'Total'
];

// Acrescenta uma linha casando os campos pelo cabeçalho existente na aba.
// Se a aba estiver vazia, escreve antes o cabeçalho padrão recebido.
function appendPorCabecalho(sheet, padrao, campos) {
  var norm = function(s) {
    return String(s || '').toLowerCase()
      .normalize('NFD').replace(/[̀-ͯ]/g, '')
      .replace(/[^a-z0-9]/g, '');
  };
  var cabecalho;
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(padrao);
    cabecalho = padrao;
  } else {
    cabecalho = sheet.getRange(1, 1, 1, Math.max(sheet.getLastColumn(), 1)).getValues()[0];
    if (!cabecalho.join('')) { // cabeçalho em branco
      sheet.getRange(1, 1, 1, padrao.length).setValues([padrao]);
      cabecalho = padrao;
    }
  }
  var porNome = {};
  Object.keys(campos).forEach(function(k) { porNome[norm(k)] = campos[k]; });
  var linha = cabecalho.map(function(h) {
    var v = porNome[norm(h)];
    return (v === undefined || v === null) ? '' : v;
  });
  sheet.appendRow(linha);
}

// Mesmo que appendPorCabecalho, mas atualiza a linha existente em vez de
// duplicar quando já existe uma linha com este ID. Sem isto, reenviar o
// mesmo assunto (por exemplo a sincronização automática de 2 em 2 minutos
// do buildly-completo.html) criava uma linha nova a cada vez, multiplicando
// os assuntos sem parar.
function upsertPorCabecalho(sheet, padrao, id, campos) {
  var norm = function(s) {
    return String(s || '').toLowerCase()
      .normalize('NFD').replace(/[̀-ͯ]/g, '')
      .replace(/[^a-z0-9]/g, '');
  };
  var cabecalho;
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(padrao);
    cabecalho = padrao;
  } else {
    cabecalho = sheet.getRange(1, 1, 1, Math.max(sheet.getLastColumn(), 1)).getValues()[0];
    if (!cabecalho.join('')) {
      sheet.getRange(1, 1, 1, padrao.length).setValues([padrao]);
      cabecalho = padrao;
    }
  }

  var idxId = -1;
  for (var h = 0; h < cabecalho.length; h++) {
    if (norm(cabecalho[h]) === 'id') { idxId = h; break; }
  }

  var linhaExistente = -1;
  if (idxId >= 0 && sheet.getLastRow() > 1) {
    var idsColuna = sheet.getRange(2, idxId + 1, sheet.getLastRow() - 1, 1).getValues();
    for (var i = 0; i < idsColuna.length; i++) {
      if (String(idsColuna[i][0]) === String(id)) { linhaExistente = i + 2; break; }
    }
  }

  var porNome = {};
  Object.keys(campos).forEach(function(k) { porNome[norm(k)] = campos[k]; });
  var linha = cabecalho.map(function(h) {
    var v = porNome[norm(h)];
    return (v === undefined || v === null) ? '' : v;
  });

  if (linhaExistente > 0) {
    // Preserva o "Criado Em" original — só atualiza o resto da linha.
    var idxCriado = -1;
    for (var c = 0; c < cabecalho.length; c++) {
      if (norm(cabecalho[c]) === 'criadoem') { idxCriado = c; break; }
    }
    if (idxCriado >= 0) {
      var criadoAtual = sheet.getRange(linhaExistente, idxCriado + 1).getValue();
      if (criadoAtual) linha[idxCriado] = criadoAtual;
    }
    sheet.getRange(linhaExistente, 1, 1, linha.length).setValues([linha]);
  } else {
    sheet.appendRow(linha);
  }
}

function salvarNotaFiscal(body) {
  var nf = body.dados || body;
  var numero = String(nf.numero || nf.numeroNF || '').trim();
  if (!numero) return errorResponse('Número da NF é obrigatório');

  var sheetNF = getSheet(SHEET_NAME_NF);
  if (!sheetNF) return errorResponse('Aba Notas Fiscais não encontrada');

  var itens = nf.itens || [];
  var total = nf.total_nf;
  if (total === undefined || total === null || total === '') {
    total = itens.reduce(function(s, i) { return s + (Number(i.total) || 0); }, 0);
  }

  var id    = 'NF-' + Date.now();
  var agora = new Date().toISOString();

  appendPorCabecalho(sheetNF, COLUNAS_NF, {
    'ID': id,
    'Número NF': numero,
    'Série': nf.serie || '',
    'Data Emissão': nf.data || '',
    'Fornecedor': nf.fornecedor || '',
    'Categoria': nf.categoria || '',
    'Responsável': nf.responsavel || '',
    'Observações': nf.observacoes || '',
    'Total NF': total,
    'Criado em': nf.criado_em || agora
  });

  // Os itens vão numa aba própria, uma linha por item, amarrados pelo ID da NF.
  var sheetItens = getSheet(SHEET_NAME_ITENSNF);
  if (sheetItens) {
    for (var i = 0; i < itens.length; i++) {
      var it = itens[i];
      appendPorCabecalho(sheetItens, COLUNAS_ITENS_NF, {
        'ID Item': id + '-' + (i + 1),
        'ID NF': id,
        'Número NF': numero,
        'Descrição': it.descricao || '',
        'Quantidade': it.quantidade || 0,
        'Preço Unitário': it.preco_unitario || it.precoUnitario || 0,
        'Total': it.total || 0
      });
    }
  }

  return successResponse({
    ok: true, status: 'ok', id,
    itens: itens.length, total: total, msg: 'Nota fiscal salva'
  });
}

// ============================================================
// DIÁRIO
// ============================================================

function salvarDiario(payload) {
  const ss  = SpreadsheetApp.openById(SHEET_ID);
  let sheet = getSheet(SHEET_NAME_DIARIO);
  if (!sheet) sheet = ss.insertSheet(SHEET_NAME_DIARIO);

  // Cria o cabeçalho só se a aba estiver genuinamente vazia. NUNCA limpa uma
  // aba que já tem dados — um clearContents() incondicional aqui já causou
  // perda de dados de produção (histórico inteiro de RDO apagado).
  if (sheet.getLastRow() === 0) {
    const hr = sheet.getRange(1, 1, 1, COLUNAS_DIARIO.length);
    hr.setValues([COLUNAS_DIARIO]);
    hr.setBackground('#2c2c2c');
    hr.setFontColor('#f5b334');
    hr.setFontWeight('bold');
    sheet.setFrozenRows(1);
    const larguras = [100,110,160,160,120,180,220,130,230,80,160,230,280,80,200,300,220,180,260,240,240,320,180,260,80];
    larguras.forEach((w, i) => sheet.setColumnWidth(i+1, w));
  }

  // Migração automática: garante todos os cabeçalhos (colunas novas em planilhas antigas)
  COLUNAS_DIARIO.forEach(function(titulo, i) {
    const cel = sheet.getRange(1, i + 1);
    if (cel.getValue() !== titulo) {
      cel.setValue(titulo);
      cel.setBackground('#2c2c2c');
      cel.setFontColor('#f5b334');
      cel.setFontWeight('bold');
    }
  });

  const linha = [
    payload.data                   || '',  // A Data
    payload.diaSemana              || '',  // B Dia da Semana
    payload.obra                   || '',  // C Obra
    payload.empresa                || '',  // D Empresa
    payload.local                  || '',  // E Cidade
    payload.localObra              || '',  // F Local da Obra
    payload.descricaoLocal         || '',  // G Descrição do Local
    payload.tempo                  || '',  // H Tempo / Clima
    payload.jornada                || '',  // I Jornada
    payload.dssHorario             || '',  // J DSS — Horário
    payload.dssMinistrou           || '',  // K DSS — Ministrado Por
    payload.dssTema                || '',  // L DSS — Tema
    payload.atividades             || '',  // M Atividades do Dia
    payload.efetivoTotal           || 0,   // N Efetivo Total
    payload.efetivoPorFuncao       || '',  // O Efetivo por Função
    payload.colaboradoresPresentes || '',  // P Colaboradores Presentes
    payload.equipamentos           || '',  // Q Equipamentos Utilizados
    payload.veiculosLeves          || '',  // R Veículos Leves
    payload.veiculosParados        || '',  // S Veículos/Equip. Parados
    payload.eventosSeguranca       || '',  // T Eventos de Segurança
    payload.eventosMeioAmbiente    || '',  // U Eventos de Meio Ambiente
    payload.observacoes            || '',  // V Observações do Dia
    payload.apontador              || '',  // W Apontador
    payload.fotos                  || '',  // X Fotos (links do Drive)
    payload.rdoNum                 || ''   // Y RDO Nº
  ];

  // Upsert por data + apontador (mantém apenas o mais recente)
  // Datas são normalizadas: a célula pode estar como tipo Data ou como texto
  const tz = ss.getSpreadsheetTimeZone();
  const apontadorCol = COLUNAS_DIARIO.indexOf('Apontador'); // coluna W
  const dados = sheet.getDataRange().getValues();
  const dataAlvo  = normalizarData(payload.data, tz);
  const apontAlvo = normalizarApontador(payload.apontador);
  const rowsParaDeletar = [];
  let linhaIdx = -1;
  for (let i = 1; i < dados.length; i++) {
    const mesmaData      = normalizarData(dados[i][0], tz) === dataAlvo;
    const mesmoApontador = normalizarApontador(dados[i][apontadorCol]) === apontAlvo;
    if (mesmaData && mesmoApontador) {
      if (linhaIdx === -1) { linhaIdx = i + 1; }
      else { rowsParaDeletar.push(i + 1); }
    }
  }
  rowsParaDeletar.reverse().forEach(r => sheet.deleteRow(r));

  if (linhaIdx > 0) {
    sheet.getRange(linhaIdx, 1, 1, linha.length).setValues([linha]);
  } else {
    sheet.appendRow(linha);
    const nr = sheet.getLastRow();
    sheet.getRange(nr, 1, 1, linha.length).setWrap(true);
  }

  // Ordenar por data decrescente
  const lastRow = sheet.getLastRow();
  if (lastRow > 2) {
    sheet.getRange(2, 1, lastRow - 1, COLUNAS_DIARIO.length)
         .sort({ column: 1, ascending: false });
  }

  return successResponse({ ok: true, status: 'ok', msg: 'Diário salvo' });
}

function carregarDiario(data) {
  const sheet = getSheet(SHEET_NAME_DIARIO);
  if (!sheet) return errorResponse('Aba Diário não encontrada');
  const valores = sheet.getDataRange().getValues();
  const headers = valores[0];
  for (let i = 1; i < valores.length; i++) {
    if (valores[i][0] === data) {
      const diario = {};
      headers.forEach((h, j) => diario[h] = valores[i][j]);
      return successResponse({ ok: true, diario });
    }
  }
  return successResponse({ ok: false, msg: 'Diário não encontrado para ' + data });
}

function listarDiariosMes(mes) {
  const sheet = getSheet(SHEET_NAME_DIARIO);
  if (!sheet) return errorResponse('Aba Diário não encontrada');
  const valores  = sheet.getDataRange().getValues();
  const headers  = valores[0];
  const diarios  = [];
  for (let i = 1; i < valores.length; i++) {
    if (valores[i][0] && String(valores[i][0]).startsWith(mes)) {
      const d = {};
      headers.forEach((h, j) => d[h] = valores[i][j]);
      diarios.push(d);
    }
  }
  return successResponse({ ok: true, mes, diarios });
}

// ============================================================
// LIMPEZA DE DUPLICATAS
// ============================================================

/**
 * Remove duplicatas da aba Diário, mantendo apenas o registro mais recente
 * por combinação de Data + Apontador.
 *
 * Como usar:
 *   - No editor do Apps Script: selecione esta função e clique em ▶ Executar
 *   - Via API: GET ?path=diario&action=limpar-duplicatas
 *
 * Retorna um resumo de quantas linhas foram removidas.
 */
function limparDuplicatasDiario() {
  const sheet = getSheet(SHEET_NAME_DIARIO);
  if (!sheet) {
    Logger.log('Aba Diário não encontrada');
    return;
  }

  const dados = sheet.getDataRange().getValues();
  if (dados.length <= 1) {
    Logger.log('Nenhum dado para limpar.');
    return { removidas: 0 };
  }

  const tz = SpreadsheetApp.openById(SHEET_ID).getSpreadsheetTimeZone();
  const idxData = 0;                                    // coluna A = Data
  const idxApon = COLUNAS_DIARIO.indexOf('Apontador');  // coluna W = Apontador

  // Agrupa linhas por chave "data|apontador" (valores normalizados)
  // Mantém apenas o ÚLTIMO índice encontrado para cada chave (mais recente no sheet)
  const mapaUltimo = {}; // chave → índice da linha (1-based, excluindo header)
  for (let i = 1; i < dados.length; i++) {
    const data  = normalizarData(dados[i][idxData], tz);
    const apon  = normalizarApontador(dados[i][idxApon]);
    if (!data) continue; // linha vazia, ignora
    const chave = `${data}|${apon}`;
    mapaUltimo[chave] = i; // sobrescreve → fica o último
  }

  // Linhas a deletar = todas que NÃO são o último de sua chave
  const linhasParaDeletar = [];
  for (let i = 1; i < dados.length; i++) {
    const data  = normalizarData(dados[i][idxData], tz);
    const apon  = normalizarApontador(dados[i][idxApon]);
    if (!data) continue;
    const chave = `${data}|${apon}`;
    if (mapaUltimo[chave] !== i) {
      linhasParaDeletar.push(i + 1); // +1 porque sheet é 1-based
    }
  }

  // Deletar de baixo para cima para não deslocar índices
  linhasParaDeletar.sort((a, b) => b - a).forEach(r => sheet.deleteRow(r));

  // Reordenar por data decrescente
  const lastRow = sheet.getLastRow();
  if (lastRow > 2) {
    sheet.getRange(2, 1, lastRow - 1, COLUNAS_DIARIO.length)
         .sort({ column: 1, ascending: false });
  }

  const msg = `Limpeza concluída: ${linhasParaDeletar.length} linha(s) duplicada(s) removida(s).`;
  Logger.log(msg);
  return { removidas: linhasParaDeletar.length, msg };
}

/**
 * Limpeza única: junta linhas duplicadas da aba Pauta que representam o
 * mesmo assunto (mesmo Assunto + Criador + Setor, ignorando maiúscula e
 * espaços nas pontas), mantendo apenas a mais recente. Isto existiu por um
 * bug de sincronização que reenviava o mesmo assunto repetidamente sem
 * upsert — já corrigido em criarPauta(), mas as linhas já duplicadas na
 * planilha continuam lá até esta função rodar uma vez.
 *
 * Como usar:
 *   - No editor do Apps Script: selecione esta função e clique em ▶ Executar
 *   - Via API: GET ?path=pauta&action=limpar-duplicatas
 */
function limparDuplicatasPauta() {
  const sheet = getSheet(SHEET_NAME_PAUTA);
  if (!sheet) { Logger.log('Aba Pauta não encontrada'); return { removidas: 0 }; }

  const dados = sheet.getDataRange().getValues();
  if (dados.length <= 1) return { removidas: 0 };

  const chaveDe = (linha) =>
    [linha[1], linha[3], linha[5]].map(v => String(v || '').trim().toLowerCase()).join('|');

  const mapaUltimo = {};
  for (let i = 1; i < dados.length; i++) {
    const chave = chaveDe(dados[i]);
    if (!chave.replace(/\|/g, '')) continue;
    mapaUltimo[chave] = i;
  }

  const linhasParaDeletar = [];
  for (let i = 1; i < dados.length; i++) {
    const chave = chaveDe(dados[i]);
    if (!chave.replace(/\|/g, '')) continue;
    if (mapaUltimo[chave] !== i) linhasParaDeletar.push(i + 1);
  }
  linhasParaDeletar.sort((a, b) => b - a).forEach(r => sheet.deleteRow(r));

  const msg = `Limpeza da Pauta concluída: ${linhasParaDeletar.length} linha(s) duplicada(s) removida(s).`;
  Logger.log(msg);
  return { removidas: linhasParaDeletar.length, msg };
}

/**
 * Mesma limpeza única, para a aba CheckIn. Veja limparDuplicatasPauta().
 *
 * Como usar:
 *   - No editor do Apps Script: selecione esta função e clique em ▶ Executar
 *   - Via API: GET ?path=checkin&action=limpar-duplicatas
 */
function limparDuplicatasCheckin() {
  const sheet = getSheet(SHEET_NAME_CHECKIN);
  if (!sheet) { Logger.log('Aba CheckIn não encontrada'); return { removidas: 0 }; }

  const dados = sheet.getDataRange().getValues();
  if (dados.length <= 1) return { removidas: 0 };

  const chaveDe = (linha) =>
    [linha[1], linha[3], linha[5]].map(v => String(v || '').trim().toLowerCase()).join('|');

  const mapaUltimo = {};
  for (let i = 1; i < dados.length; i++) {
    const chave = chaveDe(dados[i]);
    if (!chave.replace(/\|/g, '')) continue;
    mapaUltimo[chave] = i;
  }

  const linhasParaDeletar = [];
  for (let i = 1; i < dados.length; i++) {
    const chave = chaveDe(dados[i]);
    if (!chave.replace(/\|/g, '')) continue;
    if (mapaUltimo[chave] !== i) linhasParaDeletar.push(i + 1);
  }
  linhasParaDeletar.sort((a, b) => b - a).forEach(r => sheet.deleteRow(r));

  const msg = `Limpeza do CheckIn concluída: ${linhasParaDeletar.length} linha(s) duplicada(s) removida(s).`;
  Logger.log(msg);
  return { removidas: linhasParaDeletar.length, msg };
}

// ============================================================
// FOTOS DO DIÁRIO — Google Drive
// ============================================================

// Nome próprio: 'Diario de Obras - ...' é genérico e qualquer outro app do
// mesmo Drive cairia na mesma pasta.
var PASTA_RAIZ_FOTOS = 'BUILDLy - Fotos';

function salvarFoto(dados) {
  var raiz = obterOuCriarPasta(DriveApp.getRootFolder(), PASTA_RAIZ_FOTOS);
  var pastaObra = obterOuCriarPasta(raiz, dados.obra || 'Obra');
  var pastaData = obterOuCriarPasta(pastaObra, dados.data || 'sem-data');

  var bytes = Utilities.base64Decode(dados.base64);
  var nome = 'foto_' + dados.data + '_' + new Date().getTime() + '.jpg';
  var arquivo = pastaData.createFile(Utilities.newBlob(bytes, 'image/jpeg', nome));
  arquivo.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);

  return successResponse({
    fileId: arquivo.getId(),
    url: 'https://drive.google.com/file/d/' + arquivo.getId() + '/view'
  });
}

function obterOuCriarPasta(pai, nome) {
  var it = pai.getFoldersByName(nome);
  return it.hasNext() ? it.next() : pai.createFolder(nome);
}

// ============================================================
// BACKUP NA NUVEM — JSON completo do app no Google Drive
// Mantém apenas os 30 backups mais recentes por obra
// ============================================================
var PASTA_RAIZ_BACKUPS = 'BUILDLy - Backups';

function salvarBackup(dados) {
  var raiz = obterOuCriarPasta(DriveApp.getRootFolder(), PASTA_RAIZ_BACKUPS);
  var pastaObra = obterOuCriarPasta(raiz, dados.obra || 'Obra');

  var agora = new Date();
  var nome = 'backup_' + Utilities.formatDate(agora, Session.getScriptTimeZone(), 'yyyy-MM-dd_HHmm') + '.json';
  pastaObra.createFile(nome, dados.conteudo || '{}', 'application/json');

  // Limpeza: manter só os 30 mais recentes
  var arquivos = [];
  var it = pastaObra.getFiles();
  while (it.hasNext()) arquivos.push(it.next());
  arquivos.sort(function(a, b) { return b.getDateCreated() - a.getDateCreated(); });
  for (var i = 30; i < arquivos.length; i++) arquivos[i].setTrashed(true);

  return successResponse({ ok: true, arquivo: nome });
}

function buscarUltimoBackup(obra) {
  var raiz = obterOuCriarPasta(DriveApp.getRootFolder(), PASTA_RAIZ_BACKUPS);
  var pastaObra = obterOuCriarPasta(raiz, obra);
  var arquivos = [];
  var it = pastaObra.getFiles();
  while (it.hasNext()) arquivos.push(it.next());
  if (!arquivos.length) return successResponse({ ok: false, msg: 'Nenhum backup encontrado' });
  arquivos.sort(function(a, b) { return b.getDateCreated() - a.getDateCreated(); });
  var mais = arquivos[0];
  return successResponse({
    ok: true,
    conteudo: mais.getBlob().getDataAsString(),
    data: mais.getDateCreated().toISOString(),
    arquivo: mais.getName()
  });
}

// ============================================================
// PERGUNTAS SOBRE OS DADOS — via API da Anthropic (Claude)
//
// Configuração necessária (uma vez só):
//   No editor do Apps Script → ⚙️ Configurações do projeto → Propriedades do script
//   → Adicionar propriedade de script: ANTHROPIC_API_KEY = sk-ant-...
// ============================================================

// Modelo usado para responder perguntas. Trocar aqui se quiser outro.
var MODELO_IA_PERGUNTAS = 'claude-haiku-4-5-20251001';

// Quantos meses de Diario e Notas Fiscais entram no contexto de cada
// pergunta. Aumente se precisar alcancar mais longe no passado; o custo e
// o tempo de resposta sobem junto.
var MESES_CONTEXTO_IA = 3;

// Rode esta funcao no editor, uma vez, para o Google conceder a permissao de
// chamada externa. O Apps Script so descobre que precisa do escopo
// script.external_request quando algum codigo tenta usar UrlFetchApp: rodar
// listarPautas nao dispara o pedido, porque ela so toca na planilha. Declarar
// o escopo no appsscript.json tambem nao basta se a autorizacao ja tiver sido
// dada antes com um conjunto menor.
function autorizarChamadaExterna() {
  var r = UrlFetchApp.fetch('https://example.com', { muteHttpExceptions: true });
  Logger.log('Chamada externa autorizada — HTTP ' + r.getResponseCode());
  return r.getResponseCode();
}

function perguntarIA(body) {
  var pergunta = String(body.pergunta || '').trim();
  if (!pergunta) return errorResponse('Pergunta vazia');

  var deviceId = String(body.deviceId || '').trim();
  if (!deviceId) return errorResponse('Identificador do aparelho não informado');

  var apiKey = PropertiesService.getScriptProperties().getProperty('ANTHROPIC_API_KEY');
  if (!apiKey) {
    return successResponse({
      ok: false,
      resposta: '⚠️ A chave de API da Anthropic ainda não foi configurada neste Apps Script. ' +
        'Vá em Configurações do projeto → Propriedades do script e adicione ANTHROPIC_API_KEY.'
    });
  }

  var rateLimitError = verificarRateLimit(deviceId);
  if (rateLimitError) {
    return successResponse({ ok: false, resposta: rateLimitError });
  }

  try {
    // contextoLocal traz Medições, Documentos e Mural, que só existem no
    // navegador do usuário e não têm aba na planilha — por isso viajam junto
    // da pergunta. Se não vier (app em versão antiga), o robô segue com o
    // contexto da planilha exatamente como antes.
    var contexto = montarContextoParaIA(body.contextoLocal);
    var resposta = chamarClaude(pergunta, contexto, apiKey);
    return successResponse({ ok: true, resposta: resposta });
  } catch (err) {
    return successResponse({ ok: false, resposta: '❌ Erro ao consultar: ' + err.message });
  }
}

function verificarRateLimit(deviceId) {
  var LIMIT_DIARIO = 20;
  var props = PropertiesService.getScriptProperties();
  var agora = new Date();
  var chaveData = Utilities.formatDate(agora, Session.getScriptTimeZone(), 'yyyy-MM-dd');
  var chaveRateLimit = 'rate_limit:' + deviceId + ':' + chaveData;

  var contador = parseInt(props.getProperty(chaveRateLimit) || '0');
  if (contador >= LIMIT_DIARIO) {
    return '⚠️ Limite de ' + LIMIT_DIARIO + ' perguntas por dia atingido. Tente novamente amanhã.';
  }

  props.setProperty(chaveRateLimit, String(contador + 1));
  return null;
}

// Monta um resumo em JSON de tudo que existe na aba Diário (fonte oficial e mais atual),
// mais Pauta e CheckIn, para servir de contexto à IA.
// Le uma aba inteira como lista de objetos, casando cada celula com o
// cabecalho da linha 1. Opcionalmente descarta as linhas anteriores a
// "desde" (formato YYYY-MM-DD), olhando a coluna informada em colunaData.
function lerAbaParaIA(nomeAba, colunasData, desde) {
  var sheet = getSheet(nomeAba);
  if (!sheet) return null;
  var v = sheet.getDataRange().getValues();
  if (v.length < 2) return [];
  var h = v[0];
  var linhas = [];
  for (var i = 1; i < v.length; i++) {
    if (!v[i][0]) continue;
    var obj = {};
    h.forEach(function(nome, j) { obj[nome] = v[i][j]; });
    if (desde && colunasData) {
      var data = '';
      for (var c = 0; c < colunasData.length && !data; c++) {
        if (obj[colunasData[c]]) data = normalizarData(obj[colunasData[c]]);
      }
      if (data && data < desde) continue;
    }
    linhas.push(obj);
  }
  return linhas;
}

// Monta o pacote de dados que vai junto da pergunta. Recortado por periodo:
// o contexto inteiro viaja dentro do prompt a cada pergunta, e as abas de
// Diario e Notas Fiscais crescem todo dia — sem corte, cada pergunta ficaria
// mais cara e mais lenta que a anterior ate estourar o limite do modelo.
// Desde a migração para Supabase (ver Contrato do Backend), nenhum módulo
// grava mais nesta planilha — RDO, Pauta, Check-in e Notas Fiscais moram
// cada um no banco da obra ativa, um por obra. Este script não tem acesso a
// esses bancos (nem sabe qual obra está ativa no navegador de quem
// perguntou), então o app manda os quatro já prontos dentro de
// contextoLocal (ver montarContextoNuvem() em buildly-completo.html) e esta
// função usa isso quando vier. Só cai para a leitura da planilha (dados
// cada vez mais velhos) se o app estiver numa versão antiga sem esse envio,
// para o robô não quebrar de uma hora para outra.
function montarContextoParaIA(contextoLocal) {
  var partes = {};
  var cl = (contextoLocal && typeof contextoLocal === 'object') ? contextoLocal : {};

  // Dados que vivem só no app (Medições, Documentos, Mural). Entram primeiro
  // para ficarem visíveis mesmo que o resto do contexto seja longo.
  if (cl.obra) partes.obra = cl.obra;
  if (cl.medicoes) partes.medicoes = cl.medicoes;
  if (cl.documentos) partes.documentos = cl.documentos;
  if (cl.mural_da_obra) partes.mural_da_obra = cl.mural_da_obra;

  var corte = new Date();
  corte.setMonth(corte.getMonth() - MESES_CONTEXTO_IA);
  var desde = Utilities.formatDate(corte, Session.getScriptTimeZone(), 'yyyy-MM-dd');

  if (cl.rdos_diario) {
    partes.rdos_diario = cl.rdos_diario;
  } else {
    var rdos = lerAbaParaIA(SHEET_NAME_DIARIO, ['Data'], desde);
    if (rdos) {
      rdos.sort(function(a, b) {
        return String(a['Data']).localeCompare(String(b['Data']));
      });
      partes.rdos_diario = rdos;
    }
  }

  // Pauta e CheckIn sao listas de acompanhamento, nao series historicas:
  // vao inteiras, porque uma pendencia antiga continua valendo hoje.
  if (cl.pautas) {
    partes.pautas = cl.pautas;
  } else {
    var pautas = lerAbaParaIA(SHEET_NAME_PAUTA);
    if (pautas) partes.pautas = pautas;
  }

  if (cl.checkins) {
    partes.checkins = cl.checkins;
  } else {
    var checkins = lerAbaParaIA(SHEET_NAME_CHECKIN);
    if (checkins) partes.checkins = checkins;
  }

  if (cl.notas_fiscais) {
    partes.notas_fiscais = cl.notas_fiscais;
    if (cl.itens_nf) partes.itens_nf = cl.itens_nf;
  } else {
    var nfs = lerAbaParaIA(SHEET_NAME_NF, ['Data Emissão', 'Data Emissao', 'Data'], desde);
    if (nfs) {
      partes.notas_fiscais = nfs;
      // Os itens acompanham as notas que passaram no corte, senao sobrariam
      // itens soltos sem a nota correspondente no contexto.
      var idsNF = {};
      nfs.forEach(function(nf) { if (nf['ID']) idsNF[String(nf['ID'])] = true; });
      var itens = lerAbaParaIA(SHEET_NAME_ITENSNF);
      if (itens) {
        partes.itens_nf = itens.filter(function(it) {
          return idsNF[String(it['ID NF'])];
        });
      }
    }
  }

  // Avisa o modelo do recorte, para ele dizer que nao tem o dado em vez de
  // responder que aquilo nao aconteceu.
  partes.periodo_coberto = {
    diario_e_notas_desde: desde,
    observacao: 'Diário e Notas Fiscais contêm apenas os últimos ' +
      MESES_CONTEXTO_IA + ' meses. Pautas e Check-ins vêm completos.'
  };

  return JSON.stringify(partes);
}

function chamarClaude(pergunta, contextoJson, apiKey) {
  var systemPrompt =
    'Você é o assistente da plataforma BUILDLy, de gestão de obras. Responde perguntas com base ' +
    'EXCLUSIVAMENTE nos dados JSON fornecidos abaixo, vindos da planilha "BUILDLy Premium".\n\n' +
    'O JSON pode conter:\n' +
    '- rdos_diario: Relatórios Diários de Obra (efetivo, atividades, clima, equipamentos, DSS)\n' +
    '- pautas: assuntos e pendências, com responsável, prazo e status\n' +
    '- checkins: reuniões de acompanhamento registradas\n' +
    '- notas_fiscais e itens_nf: compras, com fornecedor, categoria e valores\n' +
    '- obra: dados do contrato da obra (cliente, gestor, datas de início e término)\n' +
    '- medicoes: contratos de medição com Cliente e Empreiteiros. Cada um traz\n' +
    '  itens_do_escopo (quantidade contratada, valor unitário, total do item) e\n' +
    '  medicoes_realizadas (o que já foi medido em cada período, acumulativo)\n' +
    '- documentos: Contrato, Cronograma, Programação Semanal e Orçamento cadastrados,\n' +
    '  com valor_do_orcamento e data_termino_cronograma quando informados\n' +
    '- mural_da_obra: avisos e decisões registrados pela equipe\n' +
    '- periodo_coberto: até onde os dados vão para trás\n\n' +
    'Responda sempre em português do Brasil, de forma direta e objetiva, citando datas, números e ' +
    'valores quando relevante. Ao somar dinheiro, apresente em reais.\n\n' +
    'Quando perguntarem se está tudo batendo / se há divergência entre contrato, orçamento, prazo, ' +
    'medições e atas, compare os dados entre si e aponte especificamente o que não fecha. Exemplos ' +
    'do que verificar: total já medido acima do valor_do_orcamento; quantidade medida acumulada ' +
    'acima da quantidade contratada de um item; data_termino_cronograma diferente da data de ' +
    'término em obra; decisão registrada em ata/mural que não aparece refletida nas medições ou no ' +
    'diário. Liste cada divergência encontrada com os números que a comprovam, e diga claramente ' +
    'quando não encontrar nenhuma.\n\n' +
    'Nunca invente números, datas ou nomes. Se a informação não estiver nos dados, diga que não ' +
    'encontrou. Atenção: rdos_diario e notas_fiscais trazem apenas o período recente indicado em ' +
    'periodo_coberto — se a pergunta for sobre data anterior a esse limite, explique que o dado ' +
    'existe na planilha mas está fora do período carregado, em vez de afirmar que não aconteceu.\n\n' +
    'Dados disponíveis (JSON):\n' + contextoJson;

  var payload = {
    // 2048: uma resposta listando divergências entre contrato, orçamento,
    // cronograma e medições é bem mais longa que uma consulta simples.
    model: MODELO_IA_PERGUNTAS,
    max_tokens: 2048,
    system: systemPrompt,
    messages: [{ role: 'user', content: pergunta }]
  };

  var options = {
    method: 'post',
    contentType: 'application/json',
    headers: {
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01'
    },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };

  var resp = UrlFetchApp.fetch('https://api.anthropic.com/v1/messages', options);
  var json = JSON.parse(resp.getContentText());
  if (json.error) throw new Error(json.error.message || 'Erro desconhecido da API Anthropic');
  if (json.content && json.content[0] && json.content[0].text) return json.content[0].text;
  return 'Sem resposta da IA.';
}

// ============================================================
// UTILITÁRIOS
// ============================================================

// Converte qualquer formato de data (célula tipo Data, "2026-07-10" ou "10/07/2026") para "yyyy-MM-dd"
function normalizarData(v, tz) {
  if (v instanceof Date) {
    return Utilities.formatDate(v, tz || Session.getScriptTimeZone(), 'yyyy-MM-dd');
  }
  const s = String(v || '').trim();
  const br = s.match(/^(\d{2})\/(\d{2})\/(\d{4})$/); // 10/07/2026
  if (br) return br[3] + '-' + br[2] + '-' + br[1];
  return s.slice(0, 10); // "2026-07-10..." → "2026-07-10"
}

// Apontador sem espaços extras e sem diferença de maiúsculas/minúsculas
function normalizarApontador(v) {
  return String(v || '').trim().toLowerCase();
}

// Procura a aba tolerando diferenças de escrita: maiúscula/minúscula, acento,
// hífen, espaço e plural. Assim 'Pauta' acha "Pautas" e 'CheckIn' acha "Check-ins",
// sem precisar renomear nada na planilha nem acertar a grafia exata.
function getSheet(nome) {
  var norm = function(s) {
    return String(s || '')
      .toLowerCase()
      .normalize('NFD').replace(/[̀-ͯ]/g, '') // remove acentos
      .replace(/[^a-z0-9]/g, '')                        // remove hífen, espaço, pontuação
      .replace(/s$/, '');                               // ignora plural
  };
  var alvo = norm(nome);
  var abas = SpreadsheetApp.openById(SHEET_ID).getSheets();
  for (var i = 0; i < abas.length; i++) {
    if (norm(abas[i].getName()) === alvo) return abas[i];
  }
  return null;
}

function successResponse(data) {
  return ContentService
    .createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}

function errorResponse(msg) {
  return ContentService
    .createTextOutput(JSON.stringify({ ok: false, status: 'erro', error: msg }))
    .setMimeType(ContentService.MimeType.JSON);
}
