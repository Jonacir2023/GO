# BUILDLy Premium (Buildly3)

Sistema integrado de gestão de obras que combina 4 aplicativos em um só:

- **Pauta** — reuniões e agendas
- **Check-in** — tarefas derivadas da Pauta
- **RDO** — diário de obras
- **Custos** — controle de notas fiscais

Este repositório (`Jonacir2023/GO`, pasta local `~/Buildly3`) é a fonte única desta
plataforma — substitui `Jonacir2023/buildly2` e `Jonacir2023/buidly`. Ver `MANIFEST.md`.

## 🚀 Deployment

A aplicação é uma **Single Page Application (SPA)** hospedada via **GitHub Pages**,
publicada a partir de `main`/root deste repositório.

### URLs de Acesso

| App | URL |
|-----|-----|
| **BUILDLy Premium Completo** | https://jonacir2023.github.io/GO/buildly-completo.html |
| **Pauta (Standalone)** | https://jonacir2023.github.io/GO/pauta.html |
| **Check-in (Standalone)** | https://jonacir2023.github.io/GO/Check-in.html |
| **Custos (Standalone)** | https://jonacir2023.github.io/GO/custos.html |
| **RDO (Standalone)** | https://jonacir2023.github.io/GO/rdo.html |

**Este app é isolado do `buildly2` em toda camada — decisão de 26/08, travada por
`scripts/verificar_isolamento.py`.** Nem código (arquivo próprio), nem `localStorage` (prefixo
`buildly3::`, testado em `tests/test_espaco_proprio.py`), nem backend: este repositório tem seu
próprio `/exec` do Apps Script e sua própria planilha, exclusivos — não a mesma do `buildly2` nem
de qualquer outro app da conta. Consequência: **não existe, e não deve existir, nenhuma
importação automática de dado de outro app.** Trocar de endereço é seguro — nada se mistura —
mas o app abre com o histórico local vazio nesse aparelho, e não há caminho de restauração
que dependa de outro projeto. Ver `vault/Decisões/2026-08-26 Isolamento definitivo entre
projetos.md` e `vault/Notas/Armazenamento Local.md`.

## 📦 Arquivos

- `buildly-completo.html` — App principal com todas as abas integradas
- `pauta.html` — App de Pauta (pode ser usado standalone)
- `Check-in.html` — App de Check-in (pode ser usado standalone)
- `custos.html` — App de Custos (pode ser usado standalone)
- `rdo.html` — App de RDO/Diário de Obras (pode ser usado standalone)
- `envio-pauta.html` — Formulário público, sem o resto do app: um líder abre o link
  (`?lider=Nome` pré-preenche o campo) e envia um assunto direto para a planilha —
  cai na Pauta e no Check-in ao mesmo tempo, pronto para a próxima reunião. Não usa
  `localStorage`. Se o backend tiver código de acesso (`APP_TOKEN`) ativado, inclua
  `&token=SEUCODIGO` no link.

## 🔄 Sincronização

### Local (Browser)
- **Pauta → Check-in**: Automática via `localStorage`
- Novos assuntos criados em Pauta aparecem automaticamente em Check-in

### Remoto (Google Sheets)
- Sincronização automática a cada **2 minutos**
- Todos os dados são enviados para Google Sheets centralizado via **Google Apps Script**
- Dados persistem mesmo após fechar o navegador

## 💾 Armazenamento Local

Dados são salvos em `localStorage` com namespace:

```javascript
pauta_assuntos        // Array de assuntos da Pauta
chk_assuntos          // Array de check-ins (sincronizado de Pauta)
custo_notasfiscais    // Array de notas fiscais
custo_categorias      // Categorias de custos
```

## 🔐 Integração Google Sheets

A aplicação se integra com um Google Sheets centralizado via **Google Apps Script v2**.

**Endpoints do Google Apps Script:**
- `POST pauta/criar` — Salva assuntos da Pauta
- `POST checkin/salvar` — Salva check-ins
- `POST custos/salvar` — Salva notas fiscais
- `POST rdo/salvar` — Salva diário de obras

## 📝 Dados da Pauta

Estrutura de um assunto:

```javascript
{
  id: "1722972360383",           // Timestamp em string
  assunto: "Reunião de Obra",    // Título
  desc: "Descrição completa",    // Descrição
  criador: "Jonacir",            // Quem criou
  resp: "João",                  // Responsável
  setor: "Planejamento",         // Setor
  prioridade: "alta",            // alta|media|baixa
  status: "afazer",              // afazer|fazendo|concluido|cancelado
  dataLanc: "2026-08-07",        // Data de lançamento (YYYY-MM-DD)
  dataTerm: "2026-08-10",        // Data de término (YYYY-MM-DD)
  criadoEm: 1722972360383        // Timestamp JS
}
```

## 📊 Dados de Custos

Estrutura de uma nota fiscal:

```javascript
{
  id: "NF-1722972360383",
  numeroNF: "1234",
  serie: "A",
  data: "2026-08-07",
  fornecedor: "Fornecedor X",
  categoria: "Materiais",
  responsavel: "Jonacir",
  observacoes: "Observação aqui",
  totalNF: 1500.00,
  itens: [
    {
      descricao: "Cimento CP II",
      quantidade: 50,
      precoUnit: 25.00,
      total: 1250.00
    }
  ],
  foto: "data:image/jpeg;base64,...",  // opcional — foto da nota tirada pela câmera do iPhone; guardada localmente, sem leitura automática (OCR) dos dados
  criadoEm: 1722972360383
}
```

## 🛠️ Desenvolvimento Local

Se quiser testar localmente:

```bash
# Clone o repositório
git clone https://github.com/Jonacir2023/GO.git
cd GO

# Abra em um servidor local (opcional, para evitar CORS issues)
python -m http.server 8000

# Acesse em http://localhost:8000/buildly-completo.html
```

## 📞 Informações

- **GitHub**: https://github.com/Jonacir2023/GO
- **Google Sheets**: https://docs.google.com/spreadsheets/d/19SDuzU_CLzDRfbNZWJZQzchLDCeQYHgiSC_FxDSdhOw
- **Autor**: Jonacir (jonacir70@icloud.com)

---

**Versão:** 3.0 (Premium)
