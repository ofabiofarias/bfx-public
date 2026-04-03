"""Tab Por Competição — análise agrupada por campeonato."""

import pandas as pd
import plotly.express as px
import streamlit as st

from ui.theme import (
    COLORS,
    fmt_brl,
    fmt_num,
    fmt_brl_cell,
    fmt_num_cell,
    gradient_blue,
    gradient_red,
    build_metric_card,
)


def render(
    df: pd.DataFrame,
    df_avg: pd.DataFrame,
    chart_layout: dict,
    club_colors: dict,
) -> None:
    comp_agg = (
        df_avg.groupby("competition")
        .agg(
            jogos=("id", "count"),
            publico_medio=("attendance", "mean"),
            renda_media=("gross_revenue", "mean"),
            publico_total=("attendance", "sum"),
            renda_total=("gross_revenue", "sum"),
        )
        .reset_index()
        .sort_values("jogos", ascending=False)
    )

    if not comp_agg.empty:
        best_attendance_row = comp_agg.sort_values(
            "publico_medio", ascending=False
        ).iloc[0]
        best_revenue_row = comp_agg.sort_values("renda_media", ascending=False).iloc[0]

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(
                build_metric_card(
                    title="Maior Público Médio",
                    value=f"{fmt_num(best_attendance_row['publico_medio'])}",
                    subtitle=best_attendance_row["competition"],
                    icon="groups",
                    color=COLORS["primary"],
                ),
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                build_metric_card(
                    title="Maior Renda Média",
                    value=f"{fmt_brl(best_revenue_row['renda_media'])}",
                    subtitle=best_revenue_row["competition"],
                    icon="attach_money",
                    color="#3B82F6",
                ),
                unsafe_allow_html=True,
            )
        st.markdown("<br>", unsafe_allow_html=True)

    comp_agg.columns = [
        "Competição",
        "Jogos",
        "Público médio",
        "Renda média",
        "Público total",
        "Renda total",
    ]

    styled_comp_tab = (
        comp_agg.style.format(
            {
                "Público médio": fmt_num_cell,
                "Público total": fmt_num_cell,
                "Renda média": fmt_brl_cell,
                "Renda total": fmt_brl_cell,
            }
        )
        .apply(gradient_red, subset=["Público médio"])
        .apply(gradient_blue, subset=["Renda total"])
    )

    st.dataframe(
        styled_comp_tab,
        use_container_width=True,
        hide_index=True,
        height=400,
    )

    top10 = comp_agg.head(10)
    fig_c = px.bar(
        top10,
        x="Competição",
        y="Público médio",
        color="Competição",
        text_auto=".2s",
    )
    fig_c.update_traces(textposition="outside", textfont_size=10)
    fig_c.update_layout(
        height=350,
        showlegend=False,
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        colorway=[
            COLORS["primary"],
            COLORS["accent"],
            "#3B82F6",
            "#8B5CF6",
            "#06B6D4",
            "#F59E0B",
            "#10B981",
            "#EF4444",
            "#6366F1",
            "#EC4899",
        ],
    )
    st.plotly_chart(fig_c, use_container_width=True)
