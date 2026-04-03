# Público e Renda

Visualização pública de dados de **público e renda** dos jogos de **Fortaleza EC** e **Ceará SC**, extraídos dos boletins financeiros oficiais (borderôs).

## Stack

- **Streamlit** — interface web
- **SQLModel** — ORM (SQLite local)
- **Supabase** — fonte de verdade (PostgreSQL, sync unidirecional)
- **Plotly** — gráficos interativos
- **Render** — deploy

## Arquitetura

**Local-first, read-only.** O app mantém uma cópia local em SQLite e sincroniza (pull-only) do Supabase no startup. Zero operações de escrita — apenas visualização.

```
app.py                  # Entry point
core/
  config.py             # Database URLs, clubes monitorados
  database.py           # Engine, session, cache de referência
  sync.py               # Pull-only do Supabase
  services.py           # Stats para dashboard
  calculator.py         # Cálculos derivados (público, ingressos, ticket)
  match_service.py      # Queries de jogos (read-only)
models/
  models.py             # SQLModel (Club, Match, MatchLine, LineTag)
pages/
  00_inicio.py          # Home com KPIs e sobre
  01_jogos.py           # Lista de jogos (view-only)
  02_relatorios.py      # Relatórios com tabs analíticas
  03_bordero.py         # Borderô individual por jogo
ui/
  theme.py              # Design System (cores, formatação, CSS)
  match_card.py         # Card HTML de cabeçalho do jogo
  components/           # Componentes de UI (borderô, relatórios)
```

## Pages

| Page | Descrição |
|------|-----------|
| **Início** | KPIs do ano, visão geral da base, sobre o projeto |
| **Jogos** | Tabela filtrada com seleção e visualização detalhada |
| **Relatórios** | Painel Geral, FOR vs CEA, Competição, Composição, Financeiro, Sazonalidade |
| **Borderô** | Detalhamento financeiro por jogo + análise por rubrica |

## Setup local

```bash
pip install -r requirements.txt
```

Criar `.env`:
```
DATABASE_URL=postgresql://postgres.PROJETO:SENHA@host:6543/postgres
DB_PASSWORD=sua_senha
```

```bash
streamlit run app.py
```

## Deploy (Render)

O `render.yaml` configura o serviço web. Defina `DATABASE_URL` e `DB_PASSWORD` como variáveis de ambiente no dashboard do Render.

---

[r.lab] | fabio farias
