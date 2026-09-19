Cole estas duas linhas dentro de BuildlyBackend.gs (o gerador tenta inserir
sozinho; se não achar o ponto exato, faça à mão nos dois lugares abaixo):

Em doGet(), antes de "return successResponse({ ok: true, msg: 'API Diário de Obras ativa' });":
    if (path === '{{ID}}' && action === 'listar') return listar{{PASCAL}}();

Em doPost(), antes de "return errorResponse('Endpoint não encontrado: ' + path + '/' + action);":
    if (path === '{{ID}}' && action === 'criar')            return criar{{PASCAL}}(body);
    if (path === '{{ID}}' && action === 'atualizar-status')  return atualizarStatus{{PASCAL}}(body);
    if (path === '{{ID}}' && action === 'remover')           return remover{{PASCAL}}(body);
