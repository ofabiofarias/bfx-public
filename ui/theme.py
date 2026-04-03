"""Shared UI helpers — Design System BFX.

Paleta de cores:
    Azul Marinho (primary)  : #1B2A4A
    Vermelho (accent)       : #C41E3A
    Branco                  : #FFFFFF
    Cinza claro (background): #F5F6FA
    Cinza médio (borders)   : #E2E4EA
    Cinza texto secundário  : #6B7280
"""

import streamlit as st

# Paleta de cores

# Cores por clube (para gráficos Plotly)
CLUB_COLORS = {"FOR": "#1B2A4A", "CEA": "#C41E3A"}

# Layout padrão para gráficos Plotly (Design System)
CHART_LAYOUT = dict(
    margin=dict(l=0, r=0, t=10, b=0),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    legend=dict(orientation="h", y=1.1),
)

# Categorias do Borderô

CATEGORY_ORDER = [
    "INGRESSO",
    "B1 - ALUGUEIS E SEGUROS",
    "B2 - TAXAS E IMPOSTOS",
    "B3 - DESPESAS OPERACIONAIS",
    "B4 - DESPESAS EVENTUAIS / DEDUÇÕES",
    "B5 - AJUSTE BORDERÔ",
    "DESCONTOS",
]

CATEGORY_LABELS = {
    "INGRESSO": "Ingresso (Receita)",
    "B1 - ALUGUEIS E SEGUROS": "B1 - Aluguéis e Seguros",
    "B2 - TAXAS E IMPOSTOS": "B2 - Taxas e Impostos",
    "B3 - DESPESAS OPERACIONAIS": "B3 - Despesas Operacionais",
    "B4 - DESPESAS EVENTUAIS / DEDUÇÕES": "B4 e B5 - Eventuais / Ajuste",
    "B5 - AJUSTE BORDERÔ": None,  # merged into B4
    "DESCONTOS": "Descontos",
}

CATEGORY_COLORS = {
    "INGRESSO": ("#dbeafe", "#1e40af"),
    "B1 - ALUGUEIS E SEGUROS": ("#fee2e2", "#991b1b"),
    "B2 - TAXAS E IMPOSTOS": ("#fca5a5", "#7f1d1d"),
    "B3 - DESPESAS OPERACIONAIS": ("#f87171", "#450a0a"),
    "B4 - DESPESAS EVENTUAIS / DEDUÇÕES": ("#ef4444", "#ffffff"),
    "DESCONTOS": ("#f3f4f6", "#4B5563"),
}


COLORS = {
    "primary": "#1B2A4A",  # Azul Marinho
    "primary_light": "#2C4370",  # Azul Marinho claro (hover)
    "accent": "#C41E3A",  # Vermelho
    "accent_light": "#E8354F",  # Vermelho claro
    "bg": "#F5F6FA",  # Fundo cinza claro
    "white": "#FFFFFF",
    "border": "#E2E4EA",  # Bordas
    "text": "#1B2A4A",  # Texto principal (= primary)
    "text_secondary": "#6B7280",  # Texto secundário
    "success": "#16A34A",  # Verde
    "warning": "#D97706",  # Amarelo escuro
    "error": "#DC2626",  # Vermelho erro
}

# Formatação PT-BR


def fmt_brl(value, decimals=2) -> str:
    """Formata número como moeda brasileira: R$ 1.234,56"""
    if value is None:
        return "R$ 0,00"
    formatted = f"{float(value):,.{decimals}f}"
    formatted = formatted.replace(",", "@").replace(".", ",").replace("@", ".")
    return f"R$ {formatted}"


def fmt_num(value) -> str:
    """Formata inteiro com separador de milhar PT-BR: 1.234"""
    if value is None:
        return "0"
    formatted = f"{int(value):,}".replace(",", ".")
    return formatted


# Configuração padrão de colunas para tabelas

TABLE_COL_CONFIG = {
    "Verificado": st.column_config.TextColumn("Ver.", help="Jogo totalmente revisado"),
    "ID": st.column_config.NumberColumn(),
    "BF": st.column_config.TextColumn(),
    "Clube": st.column_config.TextColumn(),
    "Data": st.column_config.DateColumn(format="DD/MM/YYYY"),
    "Competição": st.column_config.TextColumn(),
    "Visitante": st.column_config.TextColumn(),
    "Público": st.column_config.NumberColumn(),
    "Bruta": st.column_config.NumberColumn(),
    "Liquida": st.column_config.NumberColumn(),
    "Tipo": st.column_config.TextColumn(),
    "Docs": st.column_config.TextColumn(),
    "Preço": st.column_config.TextColumn(),
    "Arrecadação": st.column_config.TextColumn(),
}

# Config padrão para data_editor de linhas do borderô
LINES_COL_CONFIG = {
    "category": st.column_config.SelectboxColumn(
        "Categoria",
        options=[
            "INGRESSO",
            "B1 - ALUGUEIS E SEGUROS",
            "B2 - TAXAS E IMPOSTOS",
            "B3 - DESPESAS OPERACIONAIS",
            "B4 - DESPESAS EVENTUAIS / DEDUÇÕES",
            "B5 - AJUSTE BORDERÔ",
            "DESCONTOS",
        ],
    ),
    "description": st.column_config.TextColumn("Descrição"),
    "available": st.column_config.NumberColumn("Disponível"),
    "returned": st.column_config.NumberColumn("Devolvidos"),
    "sold": st.column_config.NumberColumn("Vendidos"),
    "price": st.column_config.NumberColumn("Preço", format="R$ %.2f"),
    "revenue": st.column_config.NumberColumn("Arrecadação", format="R$ %.2f"),
    "is_visitor_line": st.column_config.CheckboxColumn("Visitante?"),
}


# ── Estilos para DataFrames (pandas Styler) ─────────────────────────────────


def style_clube(val: str) -> str:
    """Cell style: club badge (FOR=red, CEA=navy)."""
    if val == "CEA":
        return "background-color: #1B2A4A; color: #FFFFFF; font-weight: 700;"
    if val == "FOR":
        return "background-color: #C41E3A; color: #FFFFFF; font-weight: 700;"
    return ""


def verification_level(is_info: bool, is_details: bool) -> str | None:
    """Return verification level: 'full', 'partial', or None."""
    if is_info and is_details:
        return "full"
    if is_info or is_details:
        return "partial"
    return None


def verification_cell(is_info: bool, is_details: bool) -> str:
    """Return cell text for the Verificado column."""
    level = verification_level(is_info, is_details)
    if level == "full":
        return "✓"
    if level == "partial":
        return "½"
    return ""


def verification_badge_html(is_info: bool, is_details: bool) -> str:
    """Return inline HTML badge for verification status."""
    level = verification_level(is_info, is_details)
    if level == "full":
        return (
            '<span style="background-color:#0284c7;color:white;padding:2px 10px;'
            "border-radius:20px;font-size:0.72rem;font-weight:700;margin-left:8px;"
            "display:inline-flex;align-items:center;gap:4px;"
            'box-shadow:0 1px 2px rgba(0,0,0,0.1);">'
            "<span style=\"font-family:'Material Symbols Rounded';font-size:1.2em;"
            'font-weight:normal;">verified</span> VERIFICADO</span>'
        )
    if level == "partial":
        return (
            '<span style="background-color:#dc2626;color:white;padding:2px 10px;'
            "border-radius:20px;font-size:0.72rem;font-weight:700;margin-left:8px;"
            "display:inline-flex;align-items:center;gap:4px;"
            'box-shadow:0 1px 2px rgba(0,0,0,0.1);">'
            "<span style=\"font-family:'Material Symbols Rounded';font-size:1.2em;"
            'font-weight:normal;">verified</span> PARCIAL</span>'
        )
    return ""


def style_verificado(val: str) -> str:
    """Cell style for Verified column (full=blue, partial=red)."""
    if val == "✓":
        return "background-color: #e0f2fe; color: #0284c7; font-weight: 800; text-align: center; border-radius: 4px;"
    if val == "½":
        return "background-color: #fee2e2; color: #dc2626; font-weight: 800; text-align: center; border-radius: 4px;"
    return ""


def style_tipo(val: str) -> str:
    """Cell style: MAN/VIS tag."""
    if val == "🏠︎":
        return "background-color: #dbeafe; color: #1e40af; text-align: center; border-radius: 4px;"
    if val == "✈︎":
        return "background-color: #fee2e2; color: #991b1b; text-align: center; border-radius: 4px;"
    return ""


def style_bf(val: str) -> str:
    """Cell style: BF status tag."""
    if val == "✓":
        return "color: #0284c7; text-align: center;"
    if val == "—":
        return "background-color: #fef2f2; color: #991b1b; text-align: center; border-radius: 4px;"
    return ""


def style_docs(val: str) -> str:
    """Cell style: Docs status tag."""
    if val == "✓":
        return "color: #0284c7; text-align: center;"
    if val == "—":
        return "background-color: #fef2f2; color: #991b1b; text-align: center; border-radius: 4px;"
    return ""


def style_categoria(val: str) -> str:
    """Cell style: tag style for categories."""
    if not isinstance(val, str):
        return ""

    base = "text-align: center; border-radius: 4px; font-weight: 600; font-size: 0.85rem; padding: 2px 6px;"

    if val == "INGRESSO":
        return f"background-color: #dbeafe; color: #1e40af; {base}"
    elif val.startswith("B1"):
        return f"background-color: #fee2e2; color: #991b1b; {base}"
    elif val.startswith("B2"):
        return f"background-color: #fca5a5; color: #7f1d1d; {base}"
    elif val.startswith("B3"):
        return f"background-color: #f87171; color: #450a0a; {base}"
    elif val.startswith("B4"):
        return f"background-color: #ef4444; color: #ffffff; {base}"
    elif val.startswith("B5"):
        return f"background-color: #dc2626; color: #ffffff; {base}"
    elif val == "DESCONTOS":
        return f"background-color: #f3f4f6; color: #4B5563; {base}"

    return ""


def style_negative(val) -> str:
    """Cell style: red for negative, navy for positive."""
    try:
        v = float(val)
        if v < 0:
            return "color: #C41E3A; font-weight: 600;"
        return "color: #1B2A4A; font-weight: 600;"
    except (TypeError, ValueError):
        return ""


def fmt_brl_cell(val) -> str:
    """Format cell value as BRL currency (no decimals)."""
    try:
        return (
            f"R$ {float(val):,.0f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
    except (TypeError, ValueError):
        return str(val)


def fmt_num_cell(val) -> str:
    """Format cell value as PT-BR integer with thousand separators."""
    try:
        return f"{int(val):,}".replace(",", ".")
    except (TypeError, ValueError):
        return str(val)


def fmt_pct_cell(val) -> str:
    """Format cell value as percentage."""
    try:
        return f"{float(val):.1f}%"
    except (TypeError, ValueError):
        return str(val)


def gradient_blue(series):
    """Column gradient: white → navy, proportional to value magnitude."""
    vmax = series.max()
    styles = []
    for val in series:
        try:
            pct = float(val) / vmax if vmax > 0 else 0
            pct = max(0.0, min(1.0, pct))
            r = int(255 * (1 - pct) + 27 * pct)
            g = int(255 * (1 - pct) + 42 * pct)
            b = int(255 * (1 - pct) + 74 * pct)
            text = "#FFFFFF" if pct > 0.55 else "#1B2A4A"
            styles.append(
                f"background-color: rgb({r},{g},{b}); color: {text}; font-weight: 600;"
            )
        except (TypeError, ValueError):
            styles.append("")
    return styles


def gradient_red(series):
    """Column gradient: white → red, proportional to value magnitude."""
    vmax = series.max()
    styles = []
    for val in series:
        try:
            pct = float(val) / vmax if vmax > 0 else 0
            pct = max(0.0, min(1.0, pct))
            r = int(255 * (1 - pct) + 196 * pct)
            g = int(255 * (1 - pct) + 30 * pct)
            b = int(255 * (1 - pct) + 58 * pct)
            text = "#FFFFFF" if pct > 0.55 else "#C41E3A"
            styles.append(
                f"background-color: rgb({r},{g},{b}); color: {text}; font-weight: 600;"
            )
        except (TypeError, ValueError):
            styles.append("")
    return styles


def build_metric_card(
    title: str,
    value: str,
    color: str,
    icon: str = "",
    bg_color: str = "#FFFFFF",
    value_color: str | None = None,
    subtitle: str = "",
    sub2: str = "",
    bar_pct: float | None = None,
) -> str:
    """Builds a custom HTML metric card with optional subtitles, progress bar, and watermark icon."""
    _vc = value_color or color

    _sub_html = ""
    if subtitle:
        _sub_html += (
            f'<div style="font-size:0.75rem;color:{COLORS["text_secondary"]};'
            f'margin-top:4px;letter-spacing:.01em;">{subtitle}</div>'
        )
    if sub2:
        _sub_html += (
            f'<div style="font-size:0.75rem;color:{COLORS["text_secondary"]};'
            f'letter-spacing:.01em;">{sub2}</div>'
        )

    _bar_html = ""
    if bar_pct is not None:
        _bar_html = (
            f'<div style="margin-top:10px;height:4px;border-radius:2px;'
            f'background:#E2E4EA;overflow:hidden;">'
            f'<div style="width:{min(bar_pct, 100):.1f}%;height:100%;'
            f'background:{color};border-radius:2px;"></div></div>'
        )

    _icon_html = ""
    if icon:
        _icon_html = (
            f'<div style="position:absolute;top:-8px;right:-8px;font-size:5rem;'
            f"font-family:'Material Symbols Rounded';font-variation-settings:'FILL' 1;"
            f"opacity:0.06;line-height:1;pointer-events:none;color:{color};"
            f'user-select:none;">{icon}</div>'
        )

    return (
        f'<div style="position:relative;overflow:hidden;background:linear-gradient(135deg, {bg_color}, {color}11 100%);'
        f"border:1px solid {COLORS['border']};"
        f"border-top:4px solid {color};border-radius:12px;padding:20px 24px;"
        f'box-shadow:0 3px 10px rgba(0,0,0,0.05);height:100%;">'
        # Watermark icon
        f"{_icon_html}"
        # Title
        f'<div style="font-size:0.75rem;text-transform:uppercase;letter-spacing:.05em;'
        f'color:{COLORS["text_secondary"]};font-weight:600;margin-bottom:8px;">{title}</div>'
        # Value
        f'<div style="font-size:1.7rem;font-weight:800;color:{_vc};'
        f'letter-spacing:-0.02em;line-height:1.2;">{value}</div>'
        f"{_sub_html}{_bar_html}</div>"
    )


def inject_shared_css():
    """Inject the BFX Design System CSS across all pages."""
    st.markdown(
        f"""
    <style>
        /* ── Global: azul escuro como cor principal de texto ────────── */

        html, body, [data-testid="stAppViewContainer"],
        .stMarkdown, .stMarkdown p, .stMarkdown li,
        [data-testid="stHeader"],
        .stSelectbox label, .stDateInput label, .stTextInput label,
        .stMultiSelect label, .stNumberInput label {{
            color: {COLORS["primary"]} !important;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: {COLORS["primary"]} !important;
        }}

        /* ── Metric Cards ───────────────────────────────────────────── */

        [data-testid="stMetric"] {{
            background: #EEF2F9;
            border: 1px solid {COLORS["border"]};
            border-top: 3px solid {COLORS["accent"]};
            border-radius: 10px;
            padding: 16px 20px;
            box-shadow: 0 1px 3px rgba(27, 42, 74, 0.08);
        }}
        [data-testid="stMetric"] label {{
            font-size: 0.78rem !important;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            color: {COLORS["primary"]};
            opacity: 0.65;
        }}
        [data-testid="stMetric"] [data-testid="stMetricValue"] {{
            color: {COLORS["primary"]};
            font-size: 1.45rem !important;
            font-weight: 700;
            line-height: 1.3;
        }}

        /* ── Section Header (borda lateral azul marinho 5px) ────────── */

        .section-header {{
            padding: 10px 18px;
            border-radius: 6px;
            margin: 1.2rem 0 0.6rem 0;
            font-size: 1.05rem;
            font-weight: 600;
            color: {COLORS["primary"]};
            background: #EEF2F9;
            border-left: 5px solid {COLORS["primary"]};
        }}

        /* ── Card Containers ────────────────────────────────────────── */

        .bfx-card {{
            background: {COLORS["white"]};
            border: 1px solid {COLORS["border"]};
            border-radius: 10px;
            padding: 20px 24px;
            margin: 8px 0;
            box-shadow: 0 1px 3px rgba(27, 42, 74, 0.06);
        }}

        .bfx-card-accent {{
            background: {COLORS["white"]};
            border: 1px solid {COLORS["border"]};
            border-left: 4px solid {COLORS["accent"]};
            border-radius: 10px;
            padding: 20px 24px;
            margin: 8px 0;
            box-shadow: 0 1px 3px rgba(27, 42, 74, 0.06);
        }}

        /* ── Confidence Badges ──────────────────────────────────────── */

        .confidence-alto {{ color: {COLORS["success"]}; font-weight: 600; }}
        .confidence-medio {{ color: {COLORS["warning"]}; font-weight: 600; }}
        .confidence-baixo {{ color: {COLORS["error"]}; font-weight: 600; }}

        /* ── Tabs ───────────────────────────────────────────────────── */

        .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{
            border-bottom-color: {COLORS["accent"]} !important;
            color: {COLORS["accent"]} !important;
        }}

        /* ── Primary Button Accent ──────────────────────────────────── */

        .stButton button[kind="primary"],
        .stButton button[data-testid="stBaseButton-primary"] {{
            background-color: {COLORS["accent"]};
            border-color: {COLORS["accent"]};
        }}
        .stButton button[kind="primary"]:hover,
        .stButton button[data-testid="stBaseButton-primary"]:hover {{
            background-color: {COLORS["accent_light"]};
            border-color: {COLORS["accent_light"]};
        }}

        /* ── Dataframes ─────────────────────────────────────────────── */

        [data-testid="stDataFrame"] {{
            border: 1px solid {COLORS["border"]};
            border-left: 3px solid {COLORS["primary"]};
            border-radius: 10px;
            overflow: hidden;
        }}

        /* ── Navigation sidebar sections ─────────────────────────────── */

        [data-testid="stSidebarNav"] span {{
            font-weight: 500;
        }}
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] a {{
            color: {COLORS["text_secondary"]} !important;
            text-decoration: none;
        }}
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] a:hover {{
            color: {COLORS["accent"]} !important;
        }}

        /* ── Edit Mode Banner ─────────────────────────────────── */

        .edit-banner {{
            padding: 12px 18px;
            border-radius: 6px;
            margin: 1.2rem 0 0.6rem 0;
            font-size: 1.05rem;
            font-weight: 700;
            color: {COLORS["white"]};
            background: {COLORS["primary"]};
            border-left: 5px solid {COLORS["accent"]};
            letter-spacing: 0.02em;
        }}

        /* ── Hide Streamlit GitHub Icon ─────────────────────────── */

        #GithubIcon {{
            visibility: hidden;
        }}
    </style>
    """,
        unsafe_allow_html=True,
    )
