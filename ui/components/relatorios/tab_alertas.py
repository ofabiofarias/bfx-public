"""Tab Alertas — jogos sem detalhado, borderô ou súmula."""

import pandas as pd
import streamlit as st
from sqlmodel import select

from ui.theme import (
    COLORS,
    fmt_num_cell,
    build_metric_card,
)
from core.database import get_session
from models.models import MatchLine


def render(
    df: pd.DataFrame,
    df_avg: pd.DataFrame,
    chart_layout: dict,
    club_colors: dict,
) -> None:
    filtered_ids = set(df["id"].tolist())
    with get_session() as session:
        with_lines = {ml.match_id for ml in session.exec(select(MatchLine)).all()}
    without = filtered_ids - with_lines

    no_bordero = df[df["bordero_url"].isna() | (df["bordero_url"] == "")]
    no_sumula = df[df["sumula_url"].isna() | (df["sumula_url"] == "")]

    total_filtered = len(df)

    # Cards de alerta
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            build_metric_card(
                title="Sem detalhado",
                value=f"{len(without)}",
                subtitle=f"de {total_filtered} jogos",
                icon="warning",
                color=COLORS["warning"] if len(without) > 0 else "#9CA3AF",
            ),
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            build_metric_card(
                title="Sem borderô",
                value=f"{len(no_bordero)}",
                subtitle=f"de {total_filtered} jogos",
                icon="description",
                color=COLORS["accent"] if len(no_bordero) > 0 else "#9CA3AF",
            ),
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            build_metric_card(
                title="Sem súmula",
                value=f"{len(no_sumula)}",
                subtitle=f"de {total_filtered} jogos",
                icon="description",
                color=COLORS["accent"] if len(no_sumula) > 0 else "#9CA3AF",
            ),
            unsafe_allow_html=True,
        )
    st.markdown("<br>", unsafe_allow_html=True)

    alert_cols = [
        "id",
        "date",
        "competition",
        "stadium",
        "monitored_club",
        "home",
        "away",
        "attendance",
    ]

    _col_config = {
        "id": st.column_config.NumberColumn("ID", width=50),
        "date": st.column_config.DateColumn(
            "Data", format="DD/MM/YYYY", width="small"
        ),
        "competition": st.column_config.TextColumn("Competição", width="small"),
        "stadium": st.column_config.TextColumn("Estádio", width="small"),
        "monitored_club": st.column_config.TextColumn("Clube", width=60),
        "home": st.column_config.TextColumn("Mandante", width="medium"),
        "away": st.column_config.TextColumn("Visitante", width="medium"),
        "attendance": st.column_config.NumberColumn("Público", width="small"),
    }

    tab_a1, tab_a2, tab_a3 = st.tabs(
        [
            f"Sem detalhado ({len(without)})",
            f"Sem borderô ({len(no_bordero)})",
            f"Sem súmula ({len(no_sumula)})",
        ]
    )
    with tab_a1:
        no_det = df[df["id"].isin(without)][alert_cols].sort_values(
            "date", ascending=False
        )
        if not no_det.empty:
            st.dataframe(
                no_det.style.format({"attendance": fmt_num_cell}),
                use_container_width=True,
                hide_index=True,
                height=min(35 * len(no_det) + 38, 500),
                column_config=_col_config,
            )
        else:
            st.success("Todos os jogos filtrados têm detalhado.")
    with tab_a2:
        if not no_bordero.empty:
            st.dataframe(
                no_bordero[alert_cols]
                .sort_values("date", ascending=False)
                .style.format({"attendance": fmt_num_cell}),
                use_container_width=True,
                hide_index=True,
                height=min(35 * len(no_bordero) + 38, 500),
                column_config=_col_config,
            )
        else:
            st.success("Todos os jogos filtrados têm URL de borderô.")
    with tab_a3:
        if not no_sumula.empty:
            st.dataframe(
                no_sumula[alert_cols]
                .sort_values("date", ascending=False)
                .style.format({"attendance": fmt_num_cell}),
                use_container_width=True,
                hide_index=True,
                height=min(35 * len(no_sumula) + 38, 500),
                column_config=_col_config,
            )
        else:
            st.success("Todos os jogos filtrados têm URL de súmula.")
