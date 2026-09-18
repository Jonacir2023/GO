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

**Atenção ao trocar do `buildly2` para este endereço:** os dois moram na mesma origem
(`jonacir2023.github.io`) e compartilham o mesmo `localStorage`. A troca é segura — nada se
perde — mas a migração do histórico (`data` → `data#apontador`) é de mão única: depois de abrir
este app num aparelho, o `buildly2` não enxerga mais os RDOs daquele aparelho. Ver
`vault/Projetos/BUILDLy Premium.md`.

## 📦 Arquivos

- `buildly-completo.html` — App principal com todas as abas integradas
- `pauta.html` — App de Pauta (pode ser usado standalone)
- `Check-in.html` — App de Check-in (pode ser usado standalone)
- `custos.html` — App de Custos (pode ser usado standalone)
- `rdo.html` — App de RDO/Diário de Obras (pode ser usado standalone)

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
