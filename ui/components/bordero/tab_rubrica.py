"""Tab: Análise por Rubrica — pivots, charts and ranking for tagged borderô lines."""

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlmodel import select

from core.database import get_session
from models.models import LineTag, MatchLine
from ui.theme import COLORS, build_metric_card, fmt_brl, fmt_brl_cell, fmt_num_cell


def render(matches: list[dict]):
    """Render the Rubrica analysis tab inside an already-opened st.tabs context."""

    with get_session() as session:
        tags = list(session.exec(select(LineTag).order_by(LineTag.name)).all())
        tag_map = {t.id: t for t in tags}

    if not tags:
        st.warning(
            "Nenhuma rubrica cadastrada. "
            "Acesse **Cadastros → Rubricas** para criar e vincular rubricas."
        )
        return

    match_ids = [m["id"] for m in matches]
    match_info = {m["id"]: m for m in matches}

    with get_session() as session:
        tagged_lines = session.exec(
            select(MatchLine).where(
                MatchLine.match_id.in_(match_ids),
                MatchLine.tag_id != None,  # noqa: E711
            )
        ).all()

    if not tagged_lines:
        st.info(
            "Nenhuma linha com rubrica vinculada nos jogos filtrados. "
            "Vincule descrições em **Cadastros → Rubricas**."
        )
        return

    # Build DataFrame
    line_rows = []
    for ln in tagged_lines:
        tag = tag_map.get(ln.tag_id)
        mi = match_info.get(ln.match_id, {})
        m_date = mi.get("date")
        line_rows.append(
            {
                "rubrica": tag.name if tag else "?",
                "grupo": ln.category,
                "categoria": ln.category,
                "descricao": ln.description,
                "valor": float(ln.revenue or 0),
                "data": m_date,
                "ano": m_date.year if m_date else None,
                "competicao": mi.get("competition", ""),
                "clube": mi.get("mon_short", ""),
                "estadio": mi.get("stadium", ""),
                "match_id": ln.match_id,
                "attendance": mi.get("attendance", 0),
            }
        )

    ldf = pd.DataFrame(line_rows)
    n_total_jogos = len(match_ids)

    # ── Filtros de rubrica ──
    tag_names = sorted(ldf["rubrica"].unique())
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        sel_rubricas = st.multiselect(
            "Rubricas",
            options=tag_names,
            key="brd_tag_filter",
        )
    with col_f2:
        grupos = sorted(ldf["grupo"].unique())
        sel_grupo = st.selectbox(
            "Grupo",
            options=["Todos"] + grupos,
            key="brd_tag_grupo",
        )

    mask = ldf["rubrica"].isin(sel_rubricas)
    if sel_grupo != "Todos":
        mask = mask & (ldf["grupo"] == sel_grupo)
    fdf = ldf[mask]

    if fdf.empty:
        st.info("Nenhum dado para os filtros selecionados.")
        return

    total_valor = fdf["valor"].sum()
    n_rubricas = fdf["rubrica"].nunique()
    n_jogos = fdf["match_id"].nunique()
    media_jogo = total_valor / n_jogos if n_jogos else 0

    # ── Métricas Sintéticas ──
    fdf_receita = fdf[fdf["categoria"] == "INGRESSO"]
    fdf_despesa = fdf[fdf["categoria"] != "INGRESSO"]
    total_receita = fdf_receita["valor"].sum()
    total_despesa = fdf_despesa["valor"].sum()

    mc1, mc2, mc3, mc4 = st.columns(4)
    with mc1:
        st.markdown(
            build_metric_card(
                "Receita (Rubricas)",
                fmt_brl(total_receita),
                COLORS["primary"],
                icon="payments",
                subtitle=f"{fdf_receita['rubrica'].nunique()} rubricas",
            ),
            unsafe_allow_html=True,
        )
    with mc2:
        st.markdown(
            build_metric_card(
                "Despesas (Rubricas)",
                fmt_brl(total_despesa),
                COLORS["accent"],
                icon="money_off",
                subtitle=f"{fdf_despesa['rubrica'].nunique()} rubricas",
            ),
            unsafe_allow_html=True,
        )
    with mc3:
        if not fdf_despesa.empty:
            desp_by_rub = fdf_despesa.groupby("rubrica").agg(
                total=("valor", "sum"),
                jogos=("match_id", "nunique"),
            )
            desp_by_rub["media"] = desp_by_rub["total"] / desp_by_rub["jogos"]
            top_desp = desp_by_rub["media"].idxmax()
            top_media = desp_by_rub.loc[top_desp, "media"]
            st.markdown(
                build_metric_card(
                    "Maior Despesa/Jogo",
                    fmt_brl(top_media),
                    COLORS["accent"],
                    icon="arrow_upward",
                    subtitle=top_desp,
                ),
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                build_metric_card(
                    "Maior Despesa/Jogo",
                    "—",
                    COLORS["accent"],
                    icon="arrow_upward",
                    subtitle="Sem despesas",
                ),
                unsafe_allow_html=True,
            )
    with mc4:
        media_desp_jogo = total_despesa / n_jogos if n_jogos else 0
        st.markdown(
            build_metric_card(
                "Média Despesa/Jogo",
                fmt_brl(media_desp_jogo),
                COLORS["primary"],
                icon="avg_pace",
                subtitle=f"{n_jogos} jogos",
            ),
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── VISÃO SINTÉTICA ──
    st.markdown(
        '<div class="section-header">Visão Sintética — Rubrica × Ano</div>',
        unsafe_allow_html=True,
    )

    pivot = (
        fdf.groupby(["rubrica", "ano"])["valor"]
        .sum()
        .reset_index()
        .pivot(index="rubrica", columns="ano", values="valor")
        .fillna(0)
    )
    pivot["TOTAL"] = pivot.sum(axis=1)
    pivot = pivot.sort_values("TOTAL", ascending=False)

    st.dataframe(
        pivot.style.format({c: fmt_brl_cell for c in pivot.columns}),
        use_container_width=True,
        height=min(35 * len(pivot) + 38, 500),
    )

    # ── Média por Jogo × Ano ──
    st.markdown(
        '<div class="section-header">Média por Jogo × Ano</div>',
        unsafe_allow_html=True,
    )

    jogos_por_ano = {}
    for m in matches:
        yr = m["date"].year
        jogos_por_ano[yr] = jogos_por_ano.get(yr, 0) + 1

    pivot_avg = pivot.drop(columns=["TOTAL"]).copy()
    for col in pivot_avg.columns:
        n = jogos_por_ano.get(col, 1)
        pivot_avg[col] = pivot_avg[col] / n
    pivot_avg["MÉDIA GERAL"] = pivot.drop(columns=["TOTAL"]).sum(axis=1) / n_total_jogos

    st.dataframe(
        pivot_avg.style.format({c: fmt_brl_cell for c in pivot_avg.columns}),
        use_container_width=True,
        height=min(35 * len(pivot_avg) + 38, 400),
    )

    # ── Rubrica × Estádio ──
    st.markdown(
        '<div class="section-header">Rubrica × Estádio</div>',
        unsafe_allow_html=True,
    )

    pivot_stad = (
        fdf.groupby(["rubrica", "estadio"])["valor"]
        .sum()
        .reset_index()
        .pivot(index="rubrica", columns="estadio", values="valor")
        .fillna(0)
    )
    pivot_stad["TOTAL"] = pivot_stad.sum(axis=1)
    pivot_stad = pivot_stad.sort_values("TOTAL", ascending=False)

    st.dataframe(
        pivot_stad.style.format({c: fmt_brl_cell for c in pivot_stad.columns}),
        use_container_width=True,
        height=min(35 * len(pivot_stad) + 38, 400),
    )

    # ── Rubrica × Competição ──
    st.markdown(
        '<div class="section-header">Rubrica × Competição</div>',
        unsafe_allow_html=True,
    )

    pivot_comp = (
        fdf.groupby(["rubrica", "competicao"])["valor"]
        .sum()
        .reset_index()
        .pivot(index="rubrica", columns="competicao", values="valor")
        .fillna(0)
    )
    pivot_comp["TOTAL"] = pivot_comp.sum(axis=1)
    pivot_comp = pivot_comp.sort_values("TOTAL", ascending=False)

    st.dataframe(
        pivot_comp.style.format({c: fmt_brl_cell for c in pivot_comp.columns}),
        use_container_width=True,
        height=min(35 * len(pivot_comp) + 38, 400),
    )

    # ── GRÁFICOS ──
    st.markdown(
        '<div class="section-header">Evolução Temporal</div>',
        unsafe_allow_html=True,
    )

    chart_data = fdf.groupby(["ano", "rubrica"])["valor"].sum().reset_index()
    fig_bar = px.bar(
        chart_data,
        x="ano",
        y="valor",
        color="rubrica",
        barmode="group",
        labels={"ano": "Ano", "valor": "Valor (R$)", "rubrica": "Rubrica"},
    )
    fig_bar.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(dtick=1),
        yaxis=dict(tickformat=",.0f"),
        legend=dict(orientation="h", y=-0.2),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # ── Composição (proporção) ──
    st.markdown(
        '<div class="section-header">Composição</div>',
        unsafe_allow_html=True,
    )

    col_pie1, col_pie2 = st.columns(2)
    with col_pie1:
        comp_data = (
            fdf.groupby("rubrica")["valor"]
            .sum()
            .reset_index()
            .sort_values("valor", ascending=False)
        )
        fig_pie = px.pie(
            comp_data,
            values="valor",
            names="rubrica",
            hole=0.4,
            title="Por Rubrica",
        )
        fig_pie.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_pie2:
        grupo_data = (
            fdf.groupby("grupo")["valor"]
            .sum()
            .reset_index()
            .sort_values("valor", ascending=False)
        )
        fig_pie2 = px.pie(
            grupo_data,
            values="valor",
            names="grupo",
            hole=0.4,
            title="Por Grupo",
        )
        fig_pie2.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
        )
        st.plotly_chart(fig_pie2, use_container_width=True)

    # ── Ranking de Rubricas ──
    st.markdown(
        '<div class="section-header">Ranking de Rubricas</div>',
        unsafe_allow_html=True,
    )

    ranking = (
        fdf.groupby("rubrica")
        .agg(
            total=("valor", "sum"),
            jogos=("match_id", "nunique"),
            ocorrencias=("valor", "count"),
        )
        .reset_index()
    )
    ranking["media_jogo"] = ranking["total"] / ranking["jogos"]
    ranking["media_ocorrencia"] = ranking["total"] / ranking["ocorrencias"]
    ranking = ranking.sort_values("total", ascending=False)
    ranking.columns = [
        "Rubrica",
        "Total",
        "Jogos",
        "Ocorrências",
        "Média/Jogo",
        "Média/Ocorrência",
    ]

    st.dataframe(
        ranking.style.format(
            {
                "Total": fmt_brl_cell,
                "Jogos": fmt_num_cell,
                "Ocorrências": fmt_num_cell,
                "Média/Jogo": fmt_brl_cell,
                "Média/Ocorrência": fmt_brl_cell,
            }
        ),
        use_container_width=True,
        hide_index=True,
        height=min(35 * len(ranking) + 38, 500),
    )

    # ── VISÃO ANALÍTICA — Detalhamento ──
    st.markdown(
        '<div class="section-header">Visão Analítica — Detalhamento</div>',
        unsafe_allow_html=True,
    )

    detail = fdf[
        [
            "data",
            "clube",
            "estadio",
            "competicao",
            "rubrica",
            "grupo",
            "categoria",
            "descricao",
            "valor",
        ]
    ].sort_values(["rubrica", "data"], ascending=[True, False])
    st.dataframe(
        detail.style.format({"valor": fmt_brl_cell}),
        use_container_width=True,
        hide_index=True,
        height=min(35 * len(detail) + 38, 600),
        column_config={
            "data": st.column_config.DateColumn(
                "Data", format="DD/MM/YYYY", width="small"
            ),
            "clube": st.column_config.TextColumn("Clube", width=60),
            "estadio": st.column_config.TextColumn("Estádio", width="small"),
            "competicao": st.column_config.TextColumn("Competição", width="small"),
            "rubrica": st.column_config.TextColumn("Rubrica", width="medium"),
            "grupo": st.column_config.TextColumn("Grupo", width="small"),
            "categoria": st.column_config.TextColumn("Categoria", width="small"),
            "descricao": st.column_config.TextColumn("Descrição", width="medium"),
            "valor": st.column_config.NumberColumn(
                "Valor", format="R$ %.2f", width="small"
            ),
        },
    )
