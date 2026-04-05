"""Tab Análise Financeira — renda bruta/líquida, ticket médio, custo."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ui.theme import (
    COLORS,
    fmt_brl,
    fmt_num,
    style_clube,
    fmt_brl_cell,
    fmt_num_cell,
    gradient_red,
    build_metric_card,
)


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

    st.markdown(
        '<div class="section-header">Análise Financeira</div>',
        unsafe_allow_html=True,
    )

    # Cálculos base
    _total_bruta = df["gross_revenue"].sum()
    _total_liquida = df["monitored_net_revenue"].sum()
    _total_att_fin = df["attendance"].sum()
    _avg_tk = df_avg["avg_ticket"].mean() if not df_avg.empty else 0
    _despesa_total = _total_bruta - _total_liquida
    _custo_torcedor = (_despesa_total / _total_att_fin) if _total_att_fin > 0 else 0

    # ── 1. Cards ─────────────────────────────────────────────────────────
    _fc1, _fc2, _fc3, _fc4 = st.columns(4)
    with _fc1:
        st.markdown(
            build_metric_card(
                title="Renda Bruta",
                value=fmt_brl(_total_bruta, 0),
                subtitle=f"Média: {fmt_brl(df_avg['gross_revenue'].mean(), 0)}/jogo"
                if not df_avg.empty
                else "",
                icon="payments",
                color=COLORS["primary"],
            ),
            unsafe_allow_html=True,
        )
    with _fc2:
        _liq_color = COLORS["accent"] if _total_liquida < 0 else COLORS["success"]
        st.markdown(
            build_metric_card(
                title="Renda Líquida",
                value=fmt_brl(_total_liquida, 0),
                subtitle=f"Média: {fmt_brl(df_avg['monitored_net_revenue'].mean(), 0)}/jogo"
                if not df_avg.empty
                else "",
                icon="account_balance",
                color=_liq_color,
            ),
            unsafe_allow_html=True,
        )
    with _fc3:
        st.markdown(
            build_metric_card(
                title="Ticket Médio",
                value=fmt_brl(_avg_tk),
                subtitle="Média dos jogos (portões abertos)",
                icon="sell",
                color=COLORS["primary"],
            ),
            unsafe_allow_html=True,
        )
    with _fc4:
        _custo_color = COLORS["accent"] if _custo_torcedor > 0 else COLORS["success"]
        st.markdown(
            build_metric_card(
                title="Custo por Torcedor",
                value=fmt_brl(_custo_torcedor),
                subtitle="(Bruta − Líquida) ÷ público",
                icon="trending_down",
                color=_custo_color,
            ),
            unsafe_allow_html=True,
        )

    st.divider()

    # ── 2. Evolução bruta vs líquida por ano ─────────────────────────────
    st.markdown("**Renda Bruta vs Líquida por ano**")
    _yr_fin = (
        df.groupby("year")
        .agg(bruta=("gross_revenue", "sum"), liquida=("monitored_net_revenue", "sum"))
        .reset_index()
    )
    fig_bl = go.Figure()
    fig_bl.add_trace(
        go.Bar(
            x=_yr_fin["year"],
            y=_yr_fin["bruta"],
            name="Renda Bruta",
            marker_color=COLORS["primary"],
            opacity=0.8,
            text=_yr_fin["bruta"],
            texttemplate="%{text:.2s}",
            textposition="outside",
            textfont=dict(size=10),
        )
    )
    fig_bl.add_trace(
        go.Bar(
            x=_yr_fin["year"],
            y=_yr_fin["liquida"],
            name="Renda Líquida",
            marker_color=COLORS["success"],
            opacity=0.8,
            text=_yr_fin["liquida"],
            texttemplate="%{text:.2s}",
            textposition="outside",
            textfont=dict(size=10),
        )
    )
    fig_bl.update_layout(height=380, barmode="group", **chart_layout)
    st.plotly_chart(fig_bl, use_container_width=True)

    _col_bl1, _col_bl2 = st.columns(2)
    with _col_bl1:
        st.markdown("**Renda Bruta vs Líquida — média por ano**")
        _yr_fin_avg = pd.DataFrame()
        if not df_avg.empty:
            _yr_fin_avg = (
                df_avg.groupby("year")
                .agg(
                    bruta=("gross_revenue", "mean"),
                    liquida=("monitored_net_revenue", "mean"),
                )
                .reset_index()
            )
        if not _yr_fin_avg.empty:
            fig_bl_avg = go.Figure()
            fig_bl_avg.add_trace(
                go.Bar(
                    x=_yr_fin_avg["year"],
                    y=_yr_fin_avg["bruta"],
                    name="Bruta (méd)",
                    marker_color=COLORS["primary"],
                    opacity=0.8,
                    text=_yr_fin_avg["bruta"],
                    texttemplate="%{text:.2s}",
                    textposition="outside",
                    textfont=dict(size=10),
                )
            )
            fig_bl_avg.add_trace(
                go.Bar(
                    x=_yr_fin_avg["year"],
                    y=_yr_fin_avg["liquida"],
                    name="Líquida (méd)",
                    marker_color=COLORS["success"],
                    opacity=0.8,
                    text=_yr_fin_avg["liquida"],
                    texttemplate="%{text:.2s}",
                    textposition="outside",
                    textfont=dict(size=10),
                )
            )
            fig_bl_avg.update_layout(height=350, barmode="group", **chart_layout)
            st.plotly_chart(fig_bl_avg, use_container_width=True)

    with _col_bl2:
        st.markdown("**Evolução do custo por torcedor**")
        _yr_custo = (
            df.groupby("year")
            .agg(
                bruta=("gross_revenue", "sum"),
                liquida=("monitored_net_revenue", "sum"),
                publico=("attendance", "sum"),
            )
            .reset_index()
        )
        _yr_custo["custo"] = (_yr_custo["bruta"] - _yr_custo["liquida"]) / _yr_custo[
            "publico"
        ].replace(0, 1)
        fig_custo = px.line(
            _yr_custo,
            x="year",
            y="custo",
            markers=True,
            labels={"year": "", "custo": "R$/torcedor"},
            color_discrete_sequence=[COLORS["accent"]],
            text="custo",
        )
        fig_custo.update_layout(height=350, **chart_layout)
        fig_custo.update_traces(fill="tozeroy", fillcolor="rgba(196,30,58,0.1)", texttemplate="R$ %{text:.2f}", textposition="top center", textfont_size=10)
        st.plotly_chart(fig_custo, use_container_width=True)

    st.divider()

    # ── 3. Scatter: público x renda ──────────────────────────────────────
    st.markdown("**Público × Renda Bruta — correlação**")
    _df_scatter = df[df["gates"] != "FECHADO"].copy()
    if not _df_scatter.empty:
        fig_scatter = px.scatter(
            _df_scatter,
            x="attendance",
            y="gross_revenue",
            color="monitored_club"
            if _df_scatter["monitored_club"].nunique() > 1
            else None,
            color_discrete_map=club_colors,
            trendline="ols",
            labels={
                "attendance": "Público Total",
                "gross_revenue": "Renda Bruta (R$)",
                "monitored_club": "",
            },
            hover_data=["competition", "date"],
        )
        fig_scatter.update_layout(height=400, **chart_layout)
        st.plotly_chart(fig_scatter, use_container_width=True)

    st.divider()

    # ── 4. Ticket médio e custo por competição ───────────────────────────
    _col_f1, _col_f2 = st.columns(2)

    with _col_f1:
        st.markdown("**Ticket médio por competição**")
        _tk_comp = (
            df_avg.groupby("competition")
            .agg(jogos=("id", "count"), ticket=("avg_ticket", "mean"))
            .reset_index()
            .sort_values("ticket", ascending=False)
            .head(10)
        )
        if not _tk_comp.empty:
            fig_tk = px.bar(
                _tk_comp,
                x="ticket",
                y="competition",
                orientation="h",
                color_discrete_sequence=[COLORS["primary"]],
                labels={"ticket": "Ticket Médio (R$)", "competition": ""},
                text_auto=".2f",
            )
            fig_tk.update_traces(textfont_size=10, textangle=0, textposition="outside", cliponaxis=False)
            fig_tk.update_layout(
                height=350, yaxis=dict(autorange="reversed"), **chart_layout
            )
            st.plotly_chart(fig_tk, use_container_width=True)

    with _col_f2:
        st.markdown("**Custo por torcedor — por competição**")
        _cpc = (
            df_avg.groupby("competition")
            .agg(
                bruta=("gross_revenue", "sum"),
                liquida=("monitored_net_revenue", "sum"),
                publico=("attendance", "sum"),
            )
            .reset_index()
        )
        _cpc["custo"] = (_cpc["bruta"] - _cpc["liquida"]) / _cpc["publico"].replace(
            0, 1
        )
        _cpc = _cpc.sort_values("custo", ascending=False).head(10)
        if not _cpc.empty:
            fig_cpc = px.bar(
                _cpc,
                x="custo",
                y="competition",
                orientation="h",
                color_discrete_sequence=[COLORS["accent"]],
                labels={"custo": "R$/torcedor", "competition": ""},
                text_auto=".2f",
            )
            fig_cpc.update_traces(textfont_size=10, textangle=0, textposition="outside", cliponaxis=False)
            fig_cpc.update_layout(
                height=350, yaxis=dict(autorange="reversed"), **chart_layout
            )
            st.plotly_chart(fig_cpc, use_container_width=True)

    st.divider()

    # ── 5. Top 10 maior custo por torcedor ───────────────────────────────
    st.markdown(
        '<div class="section-header">Top 10 — Maior Custo por Torcedor</div>',
        unsafe_allow_html=True,
    )
    _df_eff = df[df["attendance"] > 0].copy()
    _df_eff["custo_torc"] = (
        _df_eff["gross_revenue"] - _df_eff["monitored_net_revenue"]
    ) / _df_eff["attendance"]
    _top_eff = _df_eff.nlargest(10, "custo_torc")[
        [
            "date",
            "monitored_club",
            "home",
            "away",
            "competition",
            "attendance",
            "gross_revenue",
            "monitored_net_revenue",
            "custo_torc",
        ]
    ].copy()
    _top_eff["date"] = pd.to_datetime(_top_eff["date"]).dt.strftime("%d/%m/%Y")
    _top_eff.columns = [
        "Data",
        "Clube",
        "Mandante",
        "Visitante",
        "Competição",
        "Público",
        "Renda Bruta",
        "Renda Líquida",
        "Custo/Torc.",
    ]
    styled_eff = (
        _top_eff.style.format(
            {
                "Público": fmt_num_cell,
                "Renda Bruta": fmt_brl_cell,
                "Renda Líquida": fmt_brl_cell,
                "Custo/Torc.": fmt_brl_cell,
            }
        )
        .map(style_clube, subset=["Clube"])
        .apply(gradient_red, subset=["Custo/Torc."])
    )
    st.dataframe(
        styled_eff,
        use_container_width=True,
        hide_index=True,
        height=390,
        column_config={"Clube": st.column_config.TextColumn(width=55)},
    )
