// ============================================================
// {{PASCAL_UPPER}} — gerado por scripts/gerador_modulo/novo_modulo.py
// ============================================================
// gerador:modulo:{{ID}} — marca de idempotência, não apagar esta linha

const SHEET_NAME_{{PASCAL_UPPER}} = '{{SHEET}}';
const COLUNAS_{{PASCAL_UPPER}} = [
  'ID', 'Título', 'Descrição', 'Responsável', 'Status', 'Criado Em', 'Atualizado Em'
];

function listar{{PASCAL}}() {
  const sheet = getSheet(SHEET_NAME_{{PASCAL_UPPER}});
  if (!sheet) return errorResponse('Aba {{SHEET}} não encontrada');
  const values = sheet.getDataRange().getValues();
  const headers = values[0];
  const itens = [];
  for (let i = 1; i < values.length; i++) {
    if (!values[i][0]) break;
    const bruto = {};
    headers.forEach((h, j) => bruto[h] = values[i][j]);
    itens.push({
      id: bruto['ID'],
      titulo: bruto['Título'],
      descricao: bruto['Descrição'],
      responsavel: bruto['Responsável'],
      status: codigoStatus(bruto['Status'])
    });
  }
  return successResponse({ ok: true, status: 'ok', itens: itens, dados: itens });
}

function criar{{PASCAL}}(data) {
  const sheet = getSheet(SHEET_NAME_{{PASCAL_UPPER}});
  if (!sheet) return errorResponse('Aba {{SHEET}} não encontrada');
  const id = data.id || ('{{ID_UPPER}}-' + Date.now());
  const agora = new Date().toISOString();
  upsertPorCabecalho(sheet, COLUNAS_{{PASCAL_UPPER}}, id, {
    'ID': id,
    'Título': data.titulo || '',
    'Descrição': data.descricao || '',
    'Responsável': data.responsavel || '',
    'Status': rotularStatus(data.status || 'aberto'),
    'Criado Em': agora,
    'Atualizado Em': agora
  });
  return successResponse({ ok: true, status: 'ok', id: id });
}

function atualizarStatus{{PASCAL}}(data) {
  // Escreve só as duas células (por nome de cabeçalho, não por posição fixa
  // — a ordem das colunas na planilha pode ser qualquer uma). Um upsert de
  // linha inteira aqui apagaria Título/Descrição/Responsável, que não
  // vieram no payload.
  const sheet = getSheet(SHEET_NAME_{{PASCAL_UPPER}});
  if (!sheet) return errorResponse('Aba {{SHEET}} não encontrada');
  const values = sheet.getDataRange().getValues();
  const headers = values[0];
  const norm = h => String(h || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]/g, '');
  const idxStatus = headers.findIndex(h => norm(h) === 'status');
  const idxAtualizado = headers.findIndex(h => norm(h) === 'atualizadoem');
  for (let i = 1; i < values.length; i++) {
    if (String(values[i][0]) === String(data.id)) {
      if (idxStatus >= 0) sheet.getRange(i + 1, idxStatus + 1).setValue(rotularStatus(data.status));
      if (idxAtualizado >= 0) sheet.getRange(i + 1, idxAtualizado + 1).setValue(new Date().toISOString());
      return successResponse({ ok: true, status: 'ok' });
    }
  }
  return errorResponse('{{SHEET}} não encontrado: ' + data.id);
}

function remover{{PASCAL}}(data) {
  const sheet = getSheet(SHEET_NAME_{{PASCAL_UPPER}});
  if (!sheet) return errorResponse('Aba {{SHEET}} não encontrada');
  const values = sheet.getDataRange().getValues();
  for (let i = 1; i < values.length; i++) {
    if (String(values[i][0]) === String(data.id)) {
      sheet.deleteRow(i + 1);
      return successResponse({ ok: true, status: 'ok', msg: '{{SHEET}} removido' });
    }
  }
  return successResponse({ ok: true, status: 'ok', msg: '{{SHEET}} já não existia na planilha' });
}
