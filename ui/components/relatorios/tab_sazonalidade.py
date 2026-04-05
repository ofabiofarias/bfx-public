"""Tab Sazonalidade — visão por ano e por mês, heatmap."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ui.theme import (
    COLORS,
    fmt_brl_cell,
    fmt_num_cell,
    gradient_blue,
    gradient_red,
)

_MONTH_NAMES = {
    1: "Jan",
    2: "Fev",
    3: "Mar",
    4: "Abr",
    5: "Mai",
    6: "Jun",
    7: "Jul",
    8: "Ago",
    9: "Set",
    10: "Out",
    11: "Nov",
    12: "Dez",
}


def render(
    df: pd.DataFrame,
    df_avg: pd.DataFrame,
    chart_layout: dict,
    club_colors: dict,
) -> None:
    if "year" not in df.columns:
        df["year"] = pd.to_datetime(df["date"]).dt.year
    if "year" not in df_avg.columns:
        df_avg["year"] = pd.to_datetime(df_avg["date"]).dt.year

    _df_saz = df_avg.copy()
    _df_all = df.copy()

    if _df_saz.empty:
        st.info("Sem dados suficientes para análise de sazonalidade.")
        return

    _df_saz["month"] = pd.to_datetime(_df_saz["date"]).dt.month
    _df_saz["month_name"] = _df_saz["month"].map(_MONTH_NAMES)

    # ── 1. Visão por Ano ─────────────────────────────────────────────
    st.markdown(
        '<div class="section-header">Visão por Ano</div>',
        unsafe_allow_html=True,
    )

    _col_a1, _col_a2 = st.columns(2)

    with _col_a1:
        st.markdown("**Público total por ano**")
        _yr_total = _df_all.groupby("year")["attendance"].sum().reset_index()
        fig_yt = px.bar(
            _yr_total,
            x="year",
            y="attendance",
            color_discrete_sequence=[COLORS["primary"]],
            labels={"year": "", "attendance": "Público total"},
            text_auto=".2s",
        )
        fig_yt.update_traces(textfont_size=10, textangle=0, textposition="outside", cliponaxis=False)
        fig_yt.update_layout(height=350, **chart_layout)
        st.plotly_chart(fig_yt, use_container_width=True)

    with _col_a2:
        st.markdown("**Média de público por ano**")
        _yr_avg = _df_saz.groupby("year")["attendance"].mean().reset_index()
        fig_ya = px.bar(
            _yr_avg,
            x="year",
            y="attendance",
            color_discrete_sequence=[COLORS["accent"]],
            labels={"year": "", "attendance": "Público médio"},
            text_auto=".2s",
        )
        fig_ya.update_traces(textfont_size=10, textangle=0, textposition="outside", cliponaxis=False)
        fig_ya.update_layout(height=350, **chart_layout)
        st.plotly_chart(fig_ya, use_container_width=True)

    # Tabela resumo por ano
    st.markdown("**Resumo por ano**")
    _yr_summary = (
        _df_saz.groupby("year")
        .agg(
            jogos=("id", "count"),
            publico_total=("attendance", "sum"),
            publico_medio=("attendance", "mean"),
            renda_total=("gross_revenue", "sum"),
            renda_media=("gross_revenue", "mean"),
            ticket=("avg_ticket", "mean"),
        )
        .reset_index()
        .sort_values("year", ascending=False)
    )
    _yr_summary.columns = [
        "Ano",
        "Jogos",
        "Público Total",
        "Público Médio",
        "Renda Total",
        "Renda Média",
        "Ticket Médio",
    ]
    styled_yr = (
        _yr_summary.style.format(
            {
                "Público Total": fmt_num_cell,
                "Público Médio": fmt_num_cell,
                "Renda Total": fmt_brl_cell,
                "Renda Média": fmt_brl_cell,
                "Ticket Médio": fmt_brl_cell,
            }
        )
        .apply(gradient_red, subset=["Público Médio"])
        .apply(gradient_blue, subset=["Renda Média"])
    )
    st.dataframe(
        styled_yr,
        use_container_width=True,
        hide_index=True,
        height=min(35 * len(_yr_summary) + 38, 500),
    )

    st.divider()

    # ── 2. Visão por Mês ────────────────────────────────────────────
    st.markdown(
        '<div class="section-header">Visão por Mês</div>',
        unsafe_allow_html=True,
    )

    # Heatmap mês x ano
    st.markdown("**Público médio — mês × ano**")
    _heat = _df_saz.groupby(["year", "month"])["attendance"].mean().reset_index()
    _heat_pivot = _heat.pivot(index="month", columns="year", values="attendance")
    _heat_pivot.index = _heat_pivot.index.map(_MONTH_NAMES)

    fig_heat = go.Figure(
        data=go.Heatmap(
            z=_heat_pivot.values,
            x=[str(c) for c in _heat_pivot.columns],
            y=list(_heat_pivot.index),
            colorscale=[
                [0, "#FFFFFF"],
                [0.5, "rgb(224,143,156)"],
                [1, COLORS["accent"]],
            ],
            hovertemplate="Ano: %{x}<br>Mês: %{y}<br>Público médio: %{z:,.0f}<extra></extra>",
            showscale=True,
            colorbar=dict(title="Público"),
        )
    )
    fig_heat.update_layout(
        height=400,
        yaxis=dict(autorange="reversed"),
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    st.divider()

    # Bar charts mensais
    _col_s1, _col_s2 = st.columns(2)

    with _col_s1:
        st.markdown("**Público médio por mês (todos os anos)**")
        _monthly = (
            _df_saz.groupby("month")
            .agg(publico=("attendance", "mean"), jogos=("id", "count"))
            .reset_index()
        )
        _monthly["month_name"] = _monthly["month"].map(_MONTH_NAMES)
        fig_month = px.bar(
            _monthly,
            x="month_name",
            y="publico",
            color_discrete_sequence=[COLORS["primary"]],
            labels={"month_name": "", "publico": "Público médio"},
            text="jogos",
        )
        fig_month.update_traces(
            texttemplate="%{text} jogos", textposition="outside", textfont_size=10
        )
        fig_month.update_layout(height=380, **chart_layout)
        st.plotly_chart(fig_month, use_container_width=True)

    with _col_s2:
        st.markdown("**Renda bruta média por mês (todos os anos)**")
        _monthly_rev = (
            _df_saz.groupby("month")
            .agg(renda=("gross_revenue", "mean"), jogos=("id", "count"))
            .reset_index()
        )
        _monthly_rev["month_name"] = _monthly_rev["month"].map(_MONTH_NAMES)
        fig_month_rev = px.bar(
            _monthly_rev,
            x="month_name",
            y="renda",
            color_discrete_sequence=[COLORS["accent"]],
            labels={"month_name": "", "renda": "Renda média (R$)"},
            text="jogos",
        )
        fig_month_rev.update_traces(
            texttemplate="%{text} jogos", textposition="outside", textfont_size=10
        )
        fig_month_rev.update_layout(height=380, **chart_layout)
        st.plotly_chart(fig_month_rev, use_container_width=True)
