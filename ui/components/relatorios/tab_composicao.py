"""Tab Composição do Público — sócios, cortesias, gratuidades."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ui.theme import (
    COLORS,
    fmt_brl,
    fmt_num,
    fmt_num_cell,
    gradient_blue,
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

    _total_att = df["attendance"].sum()
    _total_socios = df["members"].sum()
    _total_ingressos_tab = df["ingressos"].sum()
    _total_cortesias = df["complimentary"].sum()
    _total_grat = df["free"].sum()
    _pct_socios = (_total_socios / _total_att * 100) if _total_att > 0 else 0
    _avg_socios = df_avg["members"].mean() if not df_avg.empty else 0

    # ── 1. Hero Sócios ──────────────────────────────────────────────────
    st.markdown(
        '<div class="section-header">Sócio Torcedor</div>',
        unsafe_allow_html=True,
    )

    _sc1, _sc2, _sc3, _sc4 = st.columns(4)
    with _sc1:
        st.markdown(
            build_metric_card(
                title="Total de Sócios",
                value=fmt_num(_total_socios),
                subtitle=f"{_pct_socios:.1f}% do público total",
                icon="badge",
                color=COLORS["primary"],
                bar_pct=_pct_socios,
            ),
            unsafe_allow_html=True,
        )
    with _sc2:
        _pct_avg = (_avg_socios / df_avg["attendance"].mean() * 100) if not df_avg.empty and df_avg["attendance"].mean() > 0 else 0
        st.markdown(
            build_metric_card(
                title="Média por Jogo",
                value=fmt_num(_avg_socios),
                subtitle="Portões abertos, mandante",
                icon="groups",
                color=COLORS["primary"],
                bar_pct=_pct_avg,
            ),
            unsafe_allow_html=True,
        )
    with _sc3:
        _max_soc_game = df.loc[df["members"].idxmax()] if not df.empty else None
        if _max_soc_game is not None:
            _msd = pd.to_datetime(_max_soc_game["date"]).strftime("%d/%m/%Y")
            st.markdown(
                build_metric_card(
                    title="Recorde de Sócios",
                    value=fmt_num(_max_soc_game["members"]),
                    subtitle=f"{_max_soc_game['home']} vs {_max_soc_game['away']}",
                    sub2=f"{_msd} · {_max_soc_game['competition']}",
                    icon="emoji_events",
                    color=COLORS["accent"],
                ),
                unsafe_allow_html=True,
            )
    with _sc4:
        _max_pct_game = None
        if not df.empty:
            _df_pct_calc = df[(df["attendance"] > 0) & (df["members"] < df["attendance"])].copy()
            if not _df_pct_calc.empty:
                _df_pct_calc["_pct_s"] = (
                    _df_pct_calc["members"] / _df_pct_calc["attendance"] * 100
                )
                _max_pct_game = _df_pct_calc.loc[_df_pct_calc["_pct_s"].idxmax()]
        if _max_pct_game is not None:
            _mpd = pd.to_datetime(_max_pct_game["date"]).strftime("%d/%m/%Y")
            st.markdown(
                build_metric_card(
                    title="Maior % Sócios",
                    value=f"{_max_pct_game['_pct_s']:.1f}%",
                    subtitle=f"{_max_pct_game['home']} vs {_max_pct_game['away']}",
                    sub2=f"{_mpd} · {fmt_num(_max_pct_game['members'])} sócios",
                    icon="trending_up",
                    color="#3B82F6",
                ),
                unsafe_allow_html=True,
            )

    st.divider()

    # ── 2. Evolução sócios por ano (total + média + %) ──────────────────
    _col_s1, _col_s2 = st.columns(2)

    with _col_s1:
        st.markdown("**Sócios por ano — total e média**")
        _yr_soc = df.groupby("year").agg(total=("members", "sum")).reset_index()
        _yr_soc_avg = (
            (df_avg.groupby("year").agg(media=("members", "mean")).reset_index())
            if not df_avg.empty
            else pd.DataFrame(columns=["year", "media"])
        )

        fig_soc = go.Figure()
        fig_soc.add_trace(
            go.Bar(
                x=_yr_soc["year"],
                y=_yr_soc["total"],
                name="Total",
                marker_color=COLORS["primary"],
                opacity=0.7,
                text=_yr_soc["total"],
                texttemplate="%{text:.2s}",
                textposition="outside",
                textfont=dict(size=10),
            )
        )
        if not _yr_soc_avg.empty:
            fig_soc.add_trace(
                go.Scatter(
                    x=_yr_soc_avg["year"],
                    y=_yr_soc_avg["media"],
                    name="Média/jogo",
                    mode="lines+markers+text",
                    yaxis="y2",
                    line=dict(color=COLORS["accent"], width=2),
                    marker=dict(size=7),
                    text=_yr_soc_avg["media"],
                    texttemplate="%{text:.2s}",
                    textposition="top center",
                    textfont=dict(size=10),
                )
            )
        fig_soc.update_layout(
            height=350,
            yaxis=dict(title="Total"),
            yaxis2=dict(title="Média/jogo", overlaying="y", side="right"),
            **chart_layout,
        )
        st.plotly_chart(fig_soc, use_container_width=True)

    with _col_s2:
        st.markdown("**Penetração de sócios no público (%)**")
        if not df_avg.empty:
            _df_pct = df_avg.copy()
            _df_pct["pct_socios"] = (
                _df_pct["members"] / _df_pct["attendance"] * 100
            ).fillna(0)
            _yearly_pct = _df_pct.groupby("year")["pct_socios"].mean().reset_index()
            fig_pct = px.line(
                _yearly_pct,
                x="year",
                y="pct_socios",
                markers=True,
                labels={"year": "", "pct_socios": "% Sócios"},
                color_discrete_sequence=[COLORS["primary"]],
                text="pct_socios",
            )
            fig_pct.update_layout(height=350, **chart_layout)
            fig_pct.update_traces(fill="tozeroy", fillcolor="rgba(27,42,74,0.1)", texttemplate="%{text:.1f}%", textposition="top center", textfont_size=10)
            st.plotly_chart(fig_pct, use_container_width=True)
        else:
            st.info("Sem dados suficientes.")

    st.divider()

    # ── 3. Scatter: sócios x público total ───────────────────────────────
    st.markdown("**Sócios × Público Total — correlação**")
    _df_sc = df[(df["attendance"] > 0) & (df["gates"] != "FECHADO")].copy()
    if not _df_sc.empty:
        fig_sc_soc = px.scatter(
            _df_sc,
            x="members",
            y="attendance",
            color="monitored_club" if _df_sc["monitored_club"].nunique() > 1 else None,
            color_discrete_map=club_colors,
            trendline="ols",
            labels={
                "members": "Sócios",
                "attendance": "Público Total",
                "monitored_club": "",
            },
            hover_data=["competition", "date"],
        )
        fig_sc_soc.update_layout(height=400, **chart_layout)
        st.plotly_chart(fig_sc_soc, use_container_width=True)

    st.divider()

    # ── 4. Sócios por competição ─────────────────────────────────────────
    st.markdown("**Sócios — média por competição**")
    _soc_comp = (
        df_avg.groupby("competition")
        .agg(
            jogos=("id", "count"),
            socios_media=("members", "mean"),
            socios_total=("members", "sum"),
        )
        .reset_index()
        .sort_values("socios_media", ascending=False)
        .head(10)
    )
    if not _soc_comp.empty:
        fig_soc_comp = px.bar(
            _soc_comp,
            x="socios_media",
            y="competition",
            orientation="h",
            color_discrete_sequence=[COLORS["primary"]],
            labels={"socios_media": "Sócios (média)", "competition": ""},
            text="jogos",
        )
        fig_soc_comp.update_traces(
            texttemplate="%{text} jogos", textposition="outside", textfont_size=10
        )
        fig_soc_comp.update_layout(
            height=350, yaxis=dict(autorange="reversed"), **chart_layout
        )
        st.plotly_chart(fig_soc_comp, use_container_width=True)

    st.divider()

    # ── 5. Composição geral (donut + stacked) ────────────────────────────
    st.markdown(
        '<div class="section-header">Composição Geral do Público</div>',
        unsafe_allow_html=True,
    )

    _comp_colors = {
        "Sócios": COLORS["primary"],
        "Ingressos": COLORS["accent"],
        "Cortesias": "#F59E0B",
        "Gratuidades": "#6B7280",
    }

    _col_d1, _col_d2 = st.columns([1, 2])

    with _col_d1:
        _comp_data = {
            "Categoria": ["Sócios", "Ingressos", "Cortesias", "Gratuidades"],
            "Total": [
                _total_socios,
                _total_ingressos_tab,
                _total_cortesias,
                _total_grat,
            ],
        }
        _comp_df = pd.DataFrame(_comp_data)
        fig_donut = px.pie(
            _comp_df,
            values="Total",
            names="Categoria",
            hole=0.55,
            color="Categoria",
            color_discrete_map=_comp_colors,
        )
        fig_donut.update_traces(
            textposition="outside", textinfo="label+percent", textfont_size=12
        )
        fig_donut.update_layout(
            height=350,
            showlegend=False,
            margin=dict(l=0, r=0, t=10, b=0),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            annotations=[
                dict(
                    text=f"<b>{fmt_num(_total_att)}</b><br><span style='font-size:10px'>Público Total</span>",
                    x=0.5,
                    y=0.5,
                    font_size=16,
                    showarrow=False,
                    font_color=COLORS["primary"],
                )
            ],
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with _col_d2:
        st.markdown("**Composição por ano**")
        _yearly_comp = (
            df.groupby("year")
            .agg(
                Sócios=("members", "sum"),
                Ingressos=("ingressos", "sum"),
                Cortesias=("complimentary", "sum"),
                Gratuidades=("free", "sum"),
            )
            .reset_index()
        )
        _yearly_melt = _yearly_comp.melt(
            id_vars="year", var_name="Categoria", value_name="Público"
        )
        fig_stack = px.bar(
            _yearly_melt,
            x="year",
            y="Público",
            color="Categoria",
            color_discrete_map=_comp_colors,
            labels={"year": "", "Público": ""},
            text_auto=".2s",
        )
        fig_stack.update_traces(textfont_size=10, textangle=0, textposition="inside")
        fig_stack.update_layout(height=350, barmode="stack", **chart_layout)
        st.plotly_chart(fig_stack, use_container_width=True)

    st.divider()

    # ── 6. Tabela completa por competição ────────────────────────────────
    st.markdown("**Composição média por competição**")
    _comp_comp = (
        df_avg.groupby("competition")
        .agg(
            jogos=("id", "count"),
            socios=("members", "mean"),
            socios_t=("members", "sum"),
            cortesias=("complimentary", "mean"),
            cortesias_t=("complimentary", "sum"),
            gratuidades=("free", "mean"),
            gratuidades_t=("free", "sum"),
        )
        .reset_index()
        .sort_values("jogos", ascending=False)
        .head(10)
    )
    _comp_comp.columns = [
        "Competição",
        "Jogos",
        "Sócios (méd)",
        "Sócios (total)",
        "Cortesias (méd)",
        "Cortesias (total)",
        "Gratuidades (méd)",
        "Gratuidades (total)",
    ]
    styled_cc = _comp_comp.style.format(
        {
            "Sócios (méd)": fmt_num_cell,
            "Sócios (total)": fmt_num_cell,
            "Cortesias (méd)": fmt_num_cell,
            "Cortesias (total)": fmt_num_cell,
            "Gratuidades (méd)": fmt_num_cell,
            "Gratuidades (total)": fmt_num_cell,
        }
    ).apply(gradient_blue, subset=["Sócios (méd)"])
    st.dataframe(styled_cc, use_container_width=True, hide_index=True, height=390)

    st.divider()

    # ── 7. Cortesias e Gratuidades por ano ───────────────────────────────
    st.markdown(
        '<div class="section-header">Cortesias e Gratuidades</div>',
        unsafe_allow_html=True,
    )
    _col_cg1, _col_cg2 = st.columns(2)
    with _col_cg1:
        st.markdown("**Cortesias por ano**")
        _yr_cort = (
            df.groupby("year")
            .agg(total=("complimentary", "sum"), media=("complimentary", "mean"))
            .reset_index()
        )
        fig_cort = go.Figure()
        fig_cort.add_trace(
            go.Bar(
                x=_yr_cort["year"],
                y=_yr_cort["total"],
                name="Total",
                marker_color="#F59E0B",
                opacity=0.7,
                text=_yr_cort["total"],
                texttemplate="%{text:.2s}",
                textposition="outside",
                textfont=dict(size=10),
            )
        )
        fig_cort.add_trace(
            go.Scatter(
                x=_yr_cort["year"],
                y=_yr_cort["media"],
                name="Média/jogo",
                mode="lines+markers",
                yaxis="y2",
                line=dict(color=COLORS["text_secondary"], width=2),
                marker=dict(size=6),
            )
        )
        fig_cort.update_layout(
            height=300,
            yaxis=dict(title="Total"),
            yaxis2=dict(title="Média", overlaying="y", side="right"),
            **chart_layout,
        )
        st.plotly_chart(fig_cort, use_container_width=True)

    with _col_cg2:
        st.markdown("**Gratuidades por ano**")
        _yr_grat = (
            df.groupby("year")
            .agg(total=("free", "sum"), media=("free", "mean"))
            .reset_index()
        )
        fig_grat = go.Figure()
        fig_grat.add_trace(
            go.Bar(
                x=_yr_grat["year"],
                y=_yr_grat["total"],
                name="Total",
                marker_color="#6B7280",
                opacity=0.7,
                text=_yr_grat["total"],
                texttemplate="%{text:.2s}",
                textposition="outside",
                textfont=dict(size=10),
            )
        )
        fig_grat.add_trace(
            go.Scatter(
                x=_yr_grat["year"],
                y=_yr_grat["media"],
                name="Média/jogo",
                mode="lines+markers",
                yaxis="y2",
                line=dict(color=COLORS["text_secondary"], width=2),
                marker=dict(size=6),
            )
        )
        fig_grat.update_layout(
            height=300,
            yaxis=dict(title="Total"),
            yaxis2=dict(title="Média", overlaying="y", side="right"),
            **chart_layout,
        )
        st.plotly_chart(fig_grat, use_container_width=True)
