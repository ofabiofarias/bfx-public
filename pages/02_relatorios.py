"""Page: Relatórios — Painéis analíticos com filtros e gráficos."""

from datetime import date

import pandas as pd
import streamlit as st
from sqlmodel import select

from ui.theme import CHART_LAYOUT, CLUB_COLORS, COLORS
from core.database import (
    get_session,
    get_distinct_competitions,
    get_distinct_visitors,
    get_distinct_stadiums,
    get_all_clubs_dict,
)
from models.models import Club, Match, MonitoredAs
from ui.components.relatorios import (
    render_painel_geral,
    render_for_vs_cea,
    render_competicao,
    render_composicao,
    render_financeiro,
    render_sazonalidade,
)


# Data Loading


@st.cache_data(ttl=60)
def load_data(
    club_id, competition, date_from, date_to, adversario=None, tipo=None, stadium=None
) -> pd.DataFrame:
    with get_session() as session:
        query = select(Match)
        if club_id:
            query = query.where(Match.monitored_club_id == club_id)
        if competition:
            query = query.where(Match.competition == competition)
        if adversario:
            adv_club = session.exec(select(Club).where(Club.name == adversario)).first()
            if adv_club:
                query = query.where(
                    (Match.away_club_id == adv_club.id)
                    | (Match.home_club_id == adv_club.id)
                )
        if tipo == "Mandante":
            query = query.where(Match.monitored_as == MonitoredAs.home)
        elif tipo == "Visitante":
            query = query.where(Match.monitored_as == MonitoredAs.away)
        if stadium:
            query = query.where(Match.stadium == stadium)
        query = query.where(Match.date >= date_from, Match.date <= date_to).order_by(
            Match.date
        )
        matches = session.exec(query).all()
        clubs = {c.id: c for c in session.exec(select(Club)).all()}
        _classic_shorts = {"FOR", "CEA"}

        rows = []
        for m in matches:
            mon = clubs.get(m.monitored_club_id)
            home_c = clubs.get(m.home_club_id)
            away_c = clubs.get(m.away_club_id)
            is_classico = (
                {(home_c.short_name if home_c else ""), (away_c.short_name if away_c else "")}
                == _classic_shorts
            )
            rows.append(
                {
                    "id": m.id,
                    "date": m.date,
                    "competition": m.competition,
                    "stadium": m.stadium,
                    "monitored_club": mon.short_name if mon else "?",
                    "monitored_as": m.monitored_as.value if m.monitored_as else "home",
                    "home": home_c.name if home_c else "?",
                    "away": away_c.name if away_c else "?",
                    "attendance": m.attendance,
                    "members": m.members,
                    "complimentary": m.complimentary,
                    "free": m.free,
                    "ingressos": m.ingressos,
                    "gross_revenue": float(m.gross_revenue),
                    "net_revenue": float(m.net_revenue),
                    "monitored_net_revenue": float(m.monitored_net_revenue),
                    "avg_ticket": float(m.avg_ticket),
                    "external_ref": m.external_ref,
                    "bordero_url": m.bordero_url,
                    "sumula_url": m.sumula_url,
                    "gates": m.gates or "",
                    "match_type": m.match_type or "",
                    "_classico": is_classico,
                }
            )
        return pd.DataFrame(rows)


# Header

st.markdown("# :material/bar_chart: Relatórios")
st.caption("Painéis analíticos com filtros por clube, competição e período.")

st.divider()

# Filters

clubs_map = get_all_clubs_dict()
monitored = {cid: c for cid, c in clubs_map.items() if c.monitored}

col1, col2, col3, col4 = st.columns(4)
with col1:
    filter_club = st.selectbox(
        "Clube",
        options=[None] + list(monitored.keys()),
        format_func=lambda x: "Todos" if x is None else f"{monitored[x].short_name}",
        key="r_club",
    )
with col2:
    visitors = get_distinct_visitors()
    filter_adversario = st.selectbox(
        "Adversário",
        options=[None] + visitors,
        format_func=lambda x: "Todos" if x is None else x,
        key="r_adv",
    )
with col3:
    competitions = get_distinct_competitions()
    filter_comp = st.selectbox(
        "Competição",
        options=[None] + competitions,
        format_func=lambda x: "Todas" if x is None else x,
        key="r_comp",
    )
with col4:
    stadiums = get_distinct_stadiums()
    filter_stadium = st.selectbox(
        "Estádio",
        options=[None] + stadiums,
        format_func=lambda x: "Todos" if x is None else x,
        key="r_stad",
    )

col5, col6, col7, col8 = st.columns(4)
with col5:
    filter_from = st.date_input(
        "De",
        value=date.today().replace(day=1, month=1),
        format="DD/MM/YYYY",
        key="r_from",
        min_value=date(2012, 1, 1),
        max_value=date.today(),
    )
with col6:
    filter_to = st.date_input(
        "Até",
        value=date.today(),
        format="DD/MM/YYYY",
        key="r_to",
        min_value=date(2012, 1, 1),
        max_value=date.today(),
    )
with col7:
    filter_tipo = st.selectbox(
        "Tipo",
        options=["Mandante", "Visitante", "Todos"],
        index=0,
        key="r_tipo",
    )
with col8:
    filter_classico = st.selectbox(
        "Clássico",
        options=[None, "Sim", "Não"],
        format_func=lambda x: "Todos" if x is None else x,
        key="r_classico",
    )

tipo_val = None if filter_tipo == "Todos" else filter_tipo
df = load_data(
    filter_club,
    filter_comp,
    filter_from,
    filter_to,
    filter_adversario,
    tipo_val,
    filter_stadium,
)

if df.empty:
    st.info("Nenhum jogo encontrado com os filtros selecionados.")
    st.stop()

if filter_classico is not None:
    df = df[df["_classico"]] if filter_classico == "Sim" else df[~df["_classico"]]
    if df.empty:
        st.info("Nenhum jogo encontrado com os filtros selecionados.")
        st.stop()

# Plotly defaults (Design System)

club_colors = CLUB_COLORS
chart_layout = CHART_LAYOUT

# Subset for averages (exclude closed gates, neutral, visitor)

df_avg = df[
    (df["gates"] != "FECHADO")
    & (df["match_type"] != "NEUTRO")
    & (df["monitored_as"] != "away")
]

_n_aberto = len(df[df["gates"] == "ABERTO"])
_n_fechado = len(df[df["gates"] == "FECHADO"])
_gates_subtitle = f"aberto: {_n_aberto}" + (
    f" | fechado: {_n_fechado}" if _n_fechado > 0 else ""
)

# Tabs

tab1, tab2, tab3, tab5, tab6, tab7 = st.tabs(
    [
        ":material/dashboard: Painel Geral",
        ":material/compare_arrows: FOR vs CEA",
        ":material/emoji_events: Por Competição",
        ":material/groups: Composição",
        ":material/attach_money: Financeiro",
        ":material/calendar_month: Sazonalidade",
    ]
)

with tab1:
    render_painel_geral(df, df_avg, chart_layout, club_colors, _gates_subtitle)

with tab2:
    render_for_vs_cea(df, df_avg, chart_layout, club_colors)

with tab3:
    render_competicao(df, df_avg, chart_layout, club_colors)

with tab5:
    render_composicao(df, df_avg, chart_layout, club_colors)

with tab6:
    render_financeiro(df, df_avg, chart_layout, club_colors)

with tab7:
    render_sazonalidade(df, df_avg, chart_layout, club_colors)
