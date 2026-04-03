"""Tab Painel Geral — visão consolidada de público, renda e recordes."""

import pandas as pd
import plotly.express as px
import streamlit as st

from ui.theme import (
    COLORS,
    fmt_brl,
    fmt_num,
    style_clube,
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
    gates_subtitle: str,
) -> None:
    # ── Cálculos ────────────────────────────────────────────────────────
    total_games = len(df)
    total_att = df["attendance"].sum()
    avg_att = df_avg["attendance"].mean() if not df_avg.empty else 0
    total_free = df["free"].sum()
    total_pagante = total_att - total_free
    avg_pagante = (
        (df_avg["attendance"] - df_avg["free"]).mean() if not df_avg.empty else 0
    )
    total_members = df["members"].sum()
    avg_members = df_avg["members"].mean() if not df_avg.empty else 0
    pct_members = (total_members / total_att * 100) if total_att > 0 else 0
    total_gross = df["gross_revenue"].sum()
    total_mon_net = df["monitored_net_revenue"].sum()
    avg_gross = df_avg["gross_revenue"].mean() if not df_avg.empty else 0
    avg_net = df_avg["monitored_net_revenue"].mean() if not df_avg.empty else 0
    avg_ticket = df_avg["avg_ticket"].mean() if not df_avg.empty else 0
    total_ingressos = df["ingressos"].sum()
    avg_ingressos = df_avg["ingressos"].mean() if not df_avg.empty else 0
    pct_ingressos = (total_ingressos / total_pagante * 100) if total_pagante > 0 else 0
    total_complimentary = df["complimentary"].sum()
    avg_complimentary = df_avg["complimentary"].mean() if not df_avg.empty else 0
    pct_complimentary = (total_complimentary / total_att * 100) if total_att > 0 else 0
    avg_free = df_avg["free"].mean() if not df_avg.empty else 0
    pct_free = (total_free / total_att * 100) if total_att > 0 else 0
    _adv_home = df.loc[df["monitored_as"] == "home", "away"]
    _adv_away = df.loc[df["monitored_as"] == "away", "home"]
    n_adversarios = pd.concat([_adv_home, _adv_away]).nunique()
    df["year"] = pd.to_datetime(df["date"]).dt.year
    _games_per_year = df.groupby("year")["id"].count()
    avg_games_year = _games_per_year.mean()

    # ── Row 1: Público + Renda — borda navy ─────────────────────────────
    _net_color = "#16A34A" if total_mon_net >= 0 else "#DC2626"
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            build_metric_card(
                title="Público Pagante",
                value=fmt_num(total_pagante),
                color=COLORS["primary"],
                icon="group",
                subtitle=f"Média: {fmt_num(avg_pagante)}",
            ),
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            build_metric_card(
                title="Público Total",
                value=fmt_num(total_att),
                color=COLORS["primary"],
                icon="groups",
                subtitle=f"Média: {fmt_num(avg_att)}",
            ),
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            build_metric_card(
                title="Renda Bruta",
                value=fmt_brl(total_gross, 0),
                color=COLORS["primary"],
                icon="payments",
                subtitle=f"Média: {fmt_brl(avg_gross, 0)}",
            ),
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            build_metric_card(
                title="Renda Líquida",
                value=fmt_brl(total_mon_net, 0),
                color=COLORS["primary"],
                icon="account_balance_wallet",
                subtitle=f"Média: {fmt_brl(avg_net, 0)}",
                value_color=_net_color,
            ),
            unsafe_allow_html=True,
        )

    st.markdown("")

    # ── Row 2: Composição do público — borda vermelha + barras ──────────
    _red = "#C41E3A"
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            build_metric_card(
                title="Total de Sócios",
                value=fmt_num(total_members),
                color=_red,
                icon="workspace_premium",
                subtitle=f"Média: {fmt_num(avg_members)}",
                sub2=f"{pct_members:.0f}% do público",
                bar_pct=pct_members,
            ),
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            build_metric_card(
                title="Ingressos Vendidos",
                value=fmt_num(total_ingressos),
                color=_red,
                icon="local_activity",
                subtitle=f"Média: {fmt_num(avg_ingressos)}",
                sub2=f"{pct_ingressos:.0f}% dos pagantes",
                bar_pct=pct_ingressos,
            ),
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            build_metric_card(
                title="Cortesias",
                value=fmt_num(total_complimentary),
                color=_red,
                icon="redeem",
                subtitle=f"Média: {fmt_num(avg_complimentary)}",
                sub2=f"{pct_complimentary:.1f}% do público",
                bar_pct=pct_complimentary,
            ),
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            build_metric_card(
                title="Gratuidades",
                value=fmt_num(total_free),
                color=_red,
                icon="money_off",
                subtitle=f"Média: {fmt_num(avg_free)}",
                sub2=f"{pct_free:.1f}% do público",
                bar_pct=pct_free,
            ),
            unsafe_allow_html=True,
        )

    st.markdown("")

    # ── Row 3: Contexto — borda cinza ────────────────────────────────────
    _gray = "#868E96"

    if not _games_per_year.empty:
        _yr_max = _games_per_year.idxmax()
        _val_max = _games_per_year.max()
        _yr_min = _games_per_year.idxmin()
        _val_min = _games_per_year.min()
        _yr_sub = f"⬆ {_yr_max} ({_val_max}) · ⬇ {_yr_min} ({_val_min})"
    else:
        _yr_sub = ""

    _tickets_valid = df_avg[df_avg["avg_ticket"] > 0]["avg_ticket"]
    _min_ticket = _tickets_valid.min() if not _tickets_valid.empty else 0
    _max_ticket = df_avg["avg_ticket"].max() if not df_avg.empty else 0

    _adv_home_avg = df_avg.loc[df_avg["monitored_as"] == "home", "away"]
    _adv_away_avg = df_avg.loc[df_avg["monitored_as"] == "away", "home"]
    _adv_series_avg = pd.concat([_adv_home_avg, _adv_away_avg])

    if not _adv_series_avg.empty:
        _adv_col = pd.DataFrame(
            {
                "adversario": _adv_series_avg.values,
                "attendance": df_avg.loc[_adv_series_avg.index, "attendance"].values,
            }
        )
        _adv_grp = _adv_col.groupby("adversario")["attendance"].mean()
        _best_adv_name = _adv_grp.idxmax()
        _best_adv_val = _adv_grp.max()
        _adv_sub = f"★ {_best_adv_name} ({fmt_num(_best_adv_val)})"
    else:
        _adv_sub = ""

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            build_metric_card(
                title="Jogos",
                value=fmt_num(total_games),
                color=_gray,
                icon="sports_soccer",
                subtitle=gates_subtitle,
            ),
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            build_metric_card(
                title="Média de Jogos / Ano",
                value=fmt_num(avg_games_year),
                color=_gray,
                icon="calendar_month",
                subtitle=_yr_sub,
            ),
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            build_metric_card(
                title="Ticket Médio",
                value=fmt_brl(avg_ticket),
                color=_gray,
                icon="confirmation_number",
                subtitle=f"Menor: {fmt_brl(_min_ticket)} · Maior: {fmt_brl(_max_ticket)}",
            ),
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            build_metric_card(
                title="Adversários",
                value=fmt_num(n_adversarios),
                color=_gray,
                icon="shield",
                subtitle=_adv_sub,
            ),
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Recordes ────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Recordes</div>', unsafe_allow_html=True)
    df_pos = df[(df["attendance"] > 0) & (df["gross_revenue"] > 0)]
    if not df_pos.empty:

        def _record_card(title, value, row, color, icon="🏆"):
            _d = pd.to_datetime(row["date"]).strftime("%d/%m/%Y")
            st.markdown(
                f'<div style="position:relative;overflow:hidden;'
                f"background:linear-gradient(135deg, {COLORS['white']} 40%, {color}22 100%);"
                f"border:1px solid {COLORS['border']};"
                f"border-top:3px solid {color};border-radius:12px;padding:18px 20px;"
                f'box-shadow:0 2px 8px rgba(0,0,0,0.04);">'
                f'<div style="position:absolute;top:-8px;right:-4px;font-size:3.8rem;'
                f"opacity:0.12;line-height:1;pointer-events:none;"
                f'user-select:none;">{icon}</div>'
                f'<div style="font-size:0.72rem;text-transform:uppercase;letter-spacing:.04em;'
                f'color:{COLORS["text_secondary"]};font-weight:600;margin-bottom:6px;">{title}</div>'
                f'<div style="font-size:1.55rem;font-weight:700;color:{color};'
                f'margin:2px 0 6px;">{value}</div>'
                f'<div style="font-size:0.78rem;color:{COLORS["text_secondary"]};">'
                f"{row['home']} x {row['away']}</div>"
                f'<div style="font-size:0.72rem;color:{COLORS["text_secondary"]};">'
                f"{row['competition']} &bull; {_d}</div></div>",
                unsafe_allow_html=True,
            )

        _max_att = df_pos.loc[df_pos["attendance"].idxmax()]
        _min_att = df_pos.loc[df_pos["attendance"].idxmin()]
        _max_rev = df_pos.loc[df_pos["gross_revenue"].idxmax()]
        _max_ticket_row = df_pos.loc[df_pos["avg_ticket"].idxmax()]
        _max_ingressos = df_pos.loc[df_pos["ingressos"].idxmax()]
        _max_members = df_pos.loc[df_pos["members"].idxmax()]

        col1, col2, col3 = st.columns(3)
        with col1:
            _record_card(
                "Maior público",
                fmt_num(_max_att["attendance"]),
                _max_att,
                COLORS["success"],
                icon="🏟️",
            )
        with col2:
            _record_card(
                "Maior renda bruta",
                fmt_brl(_max_rev["gross_revenue"], 0),
                _max_rev,
                COLORS["primary"],
                icon="💰",
            )
        with col3:
            _record_card(
                "Mais sócios no jogo",
                fmt_num(_max_members["members"]),
                _max_members,
                COLORS["accent"],
                icon="🏅",
            )

        st.markdown("")

        col1, col2, col3 = st.columns(3)
        with col1:
            _record_card(
                "Menor público",
                fmt_num(_min_att["attendance"]),
                _min_att,
                COLORS["warning"],
                icon="📉",
            )
        with col2:
            _record_card(
                "Maior ticket médio",
                fmt_brl(_max_ticket_row["avg_ticket"]),
                _max_ticket_row,
                COLORS["primary"],
                icon="🎟️",
            )
        with col3:
            _record_card(
                "Mais ingressos vendidos",
                fmt_num(_max_ingressos["ingressos"]),
                _max_ingressos,
                COLORS["success"],
                icon="🎫",
            )

    st.divider()

    # ── 1. Gráficos de barra por ano ────────────────────────────────────
    _yr_agg_total = (
        df.groupby(["year", "monitored_club"])
        .agg(
            publico_total=("attendance", "sum"),
            renda_total=("gross_revenue", "sum"),
        )
        .reset_index()
    )
    if "year" not in df_avg.columns:
        df_avg["year"] = pd.to_datetime(df_avg["date"]).dt.year
    _yr_agg_avg = (
        df_avg.groupby(["year", "monitored_club"])
        .agg(
            publico_medio=("attendance", "mean"),
        )
        .reset_index()
    )

    col_c1, col_c2 = st.columns(2)

    with col_c1:
        st.markdown("**Público total por ano**")
        fig1 = px.bar(
            _yr_agg_total,
            x="year",
            y="publico_total",
            color="monitored_club",
            barmode="group",
            color_discrete_map=club_colors,
            labels={"year": "", "publico_total": "Público", "monitored_club": "Clube"},
        )
        fig1.update_layout(height=350, **chart_layout)
        st.plotly_chart(fig1, use_container_width=True)

    with col_c2:
        st.markdown("**Renda bruta por ano**")
        fig2 = px.bar(
            _yr_agg_total,
            x="year",
            y="renda_total",
            color="monitored_club",
            barmode="group",
            color_discrete_map=club_colors,
            labels={"year": "", "renda_total": "R$", "monitored_club": "Clube"},
        )
        fig2.update_layout(height=350, **chart_layout)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("**Média de público por ano**")
    fig_avg = px.bar(
        _yr_agg_avg,
        x="year",
        y="publico_medio",
        color="monitored_club",
        barmode="group",
        color_discrete_map=club_colors,
        labels={
            "year": "",
            "publico_medio": "Público médio",
            "monitored_club": "Clube",
        },
    )
    fig_avg.update_layout(height=350, **chart_layout)
    st.plotly_chart(fig_avg, use_container_width=True)

    st.divider()

    # ── 2. Top Públicos — visual cards ──────────────────────────────────
    st.markdown(
        '<div class="section-header">Top 10 — Maiores Públicos</div>',
        unsafe_allow_html=True,
    )

    _top = df.nlargest(10, "attendance").reset_index(drop=True)
    _top_max = _top["attendance"].max() if not _top.empty else 1

    _podium_colors = ["#FFD700", "#C0C0C0", "#CD7F32"]
    _cards_html = ""
    for _i, _row in _top.iterrows():
        _pos = _i + 1
        _date_str = pd.to_datetime(_row["date"]).strftime("%d/%m/%Y")
        _club_color = (
            COLORS["accent"] if _row["monitored_club"] == "FOR" else COLORS["primary"]
        )
        _bar_w = (_row["attendance"] / _top_max * 100) if _top_max > 0 else 0

        if _pos <= 3:
            _medal_color = _podium_colors[_pos - 1]
            _pos_html = (
                f'<div style="width:32px;height:32px;border-radius:50%;'
                f"background:{_medal_color};color:#fff;font-weight:800;"
                f"font-size:0.9rem;display:flex;align-items:center;justify-content:center;"
                f'box-shadow:0 2px 4px rgba(0,0,0,0.2);">{_pos}</div>'
            )
        else:
            _pos_html = (
                f'<div style="width:32px;height:32px;border-radius:50%;'
                f"background:{COLORS['bg']};color:{COLORS['text_secondary']};font-weight:700;"
                f"font-size:0.85rem;display:flex;align-items:center;justify-content:center;"
                f'border:1px solid {COLORS["border"]};">{_pos}</div>'
            )

        _cards_html += (
            f'<div style="display:flex;align-items:center;gap:12px;padding:10px 16px;'
            f"background:{'#f8f9fa' if _pos % 2 == 0 else '#fff'};"
            f'border-bottom:1px solid {COLORS["border"]};">'
            f"{_pos_html}"
            f'<div style="flex:1;min-width:0;">'
            f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:2px;">'
            f'<span style="background:{_club_color};color:#fff;padding:1px 8px;border-radius:4px;'
            f'font-size:0.72rem;font-weight:700;">{_row["monitored_club"]}</span>'
            f'<span style="font-weight:600;font-size:0.85rem;color:{COLORS["text"]};">'
            f"{_row['home']} vs {_row['away']}</span>"
            f"</div>"
            f'<div style="font-size:0.72rem;color:{COLORS["text_secondary"]};">'
            f"{_date_str} · {_row['competition']} · {_row['stadium']}</div>"
            f'<div style="height:4px;border-radius:2px;background:{COLORS["border"]};margin-top:4px;">'
            f'<div style="width:{_bar_w:.1f}%;height:100%;border-radius:2px;background:{_club_color};"></div>'
            f"</div>"
            f"</div>"
            f'<div style="text-align:right;min-width:90px;">'
            f'<div style="font-size:1.1rem;font-weight:800;color:{COLORS["text"]};">{fmt_num(_row["attendance"])}</div>'
            f'<div style="font-size:0.7rem;color:{COLORS["text_secondary"]};">{fmt_brl(_row["gross_revenue"], 0)}</div>'
            f"</div>"
            f"</div>"
        )

    st.markdown(
        f'<div style="border:1px solid {COLORS["border"]};border-radius:10px;overflow:hidden;">'
        f"{_cards_html}</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Top 10 rendas
    st.markdown("**Top 10 — Maiores Rendas**")
    top_rev = df.nlargest(10, "gross_revenue")[
        [
            "date",
            "monitored_club",
            "home",
            "away",
            "competition",
            "gross_revenue",
            "monitored_net_revenue",
        ]
    ].copy()
    top_rev["date"] = pd.to_datetime(top_rev["date"]).dt.strftime("%d/%m/%Y")
    top_rev.columns = [
        "Data",
        "Clube",
        "Mandante",
        "Visitante",
        "Competição",
        "Renda Bruta",
        "Renda Líquida",
    ]
    styled_rev = (
        top_rev.style.format(
            {"Renda Bruta": fmt_brl_cell, "Renda Líquida": fmt_brl_cell}
        )
        .map(style_clube, subset=["Clube"])
        .apply(gradient_blue, subset=["Renda Bruta"])
    )
    st.dataframe(
        styled_rev,
        use_container_width=True,
        hide_index=True,
        height=390,
        column_config={"Clube": st.column_config.TextColumn(width=55)},
    )

    st.divider()

    # ── 3. Evolução anual — média de público (linha) ────────────────────
    st.markdown("**Evolução anual — público médio**")
    yearly = (
        df_avg.groupby(["year", "monitored_club"])
        .agg(
            avg_att=("attendance", "mean"),
        )
        .reset_index()
    )
    fig3 = px.line(
        yearly,
        x="year",
        y="avg_att",
        color="monitored_club",
        color_discrete_map=club_colors,
        markers=True,
        labels={"year": "", "avg_att": "Público médio", "monitored_club": ""},
        text="avg_att",
    )
    fig3.update_traces(texttemplate="%{text:.2s}", textposition="top center", textfont_size=10)
    fig3.update_layout(height=300, **chart_layout)
    st.plotly_chart(fig3, use_container_width=True)

    # ── 4. Evolução anual — renda bruta total e média (linhas) ──────────
    col_ev1, col_ev2 = st.columns(2)
    with col_ev1:
        st.markdown("**Evolução anual — renda bruta total**")
        yearly_rev_total = (
            df.groupby(["year", "monitored_club"])["gross_revenue"].sum().reset_index()
        )
        fig_yrt = px.line(
            yearly_rev_total,
            x="year",
            y="gross_revenue",
            color="monitored_club",
            color_discrete_map=club_colors,
            markers=True,
            labels={"year": "", "gross_revenue": "R$ total", "monitored_club": ""},
            text="gross_revenue",
        )
        fig_yrt.update_traces(texttemplate="%{text:.2s}", textposition="top center", textfont_size=10)
        fig_yrt.update_layout(height=300, **chart_layout)
        st.plotly_chart(fig_yrt, use_container_width=True)

    with col_ev2:
        st.markdown("**Evolução anual — renda bruta média**")
        yearly_rev_avg = (
            df_avg.groupby(["year", "monitored_club"])["gross_revenue"]
            .mean()
            .reset_index()
        )
        fig_yra = px.line(
            yearly_rev_avg,
            x="year",
            y="gross_revenue",
            color="monitored_club",
            color_discrete_map=club_colors,
            markers=True,
            labels={"year": "", "gross_revenue": "R$ médio", "monitored_club": ""},
            text="gross_revenue",
        )
        fig_yra.update_traces(texttemplate="%{text:.2s}", textposition="top center", textfont_size=10)
        fig_yra.update_layout(height=300, **chart_layout)
        st.plotly_chart(fig_yra, use_container_width=True)

    st.divider()

    # ── 5. Top 10 estádios e competições (barras horizontais) ───────────
    col_b1, col_b2 = st.columns(2)

    with col_b1:
        st.markdown("**Top 10 estádios — jogos**")
        _stad = df["stadium"].value_counts().head(10).reset_index()
        _stad.columns = ["Estádio", "Jogos"]
        fig_st = px.bar(
            _stad,
            x="Jogos",
            y="Estádio",
            orientation="h",
            color_discrete_sequence=[COLORS["primary"]],
            text_auto=True,
        )
        fig_st.update_traces(textfont_size=10, textposition="outside", cliponaxis=False)
        fig_st.update_layout(
            height=350,
            yaxis=dict(autorange="reversed"),
            **chart_layout,
        )
        st.plotly_chart(fig_st, use_container_width=True)

    with col_b2:
        st.markdown("**Top 10 competições — jogos**")
        _comp = df["competition"].value_counts().head(10).reset_index()
        _comp.columns = ["Competição", "Jogos"]
        fig_cp = px.bar(
            _comp,
            x="Jogos",
            y="Competição",
            orientation="h",
            color_discrete_sequence=[COLORS["accent"]],
            text_auto=True,
        )
        fig_cp.update_traces(textfont_size=10, textposition="outside", cliponaxis=False)
        fig_cp.update_layout(
            height=350,
            yaxis=dict(autorange="reversed"),
            **chart_layout,
        )
        st.plotly_chart(fig_cp, use_container_width=True)

    st.divider()

    # ── 6. Tabelas: por competição e por estádio ────────────────────────
    col_r3, col_r4 = st.columns(2)

    with col_r3:
        st.markdown("**Por competição — média de público por clube**")
        comp_club = (
            df_avg.groupby(["competition", "monitored_club"])
            .agg(
                jogos=("id", "count"),
                publico_medio=("attendance", "mean"),
                renda_media=("gross_revenue", "mean"),
            )
            .reset_index()
        )
        top_comps = df_avg["competition"].value_counts().head(10).index.tolist()
        comp_club = comp_club[comp_club["competition"].isin(top_comps)]
        comp_club.columns = [
            "Competição",
            "Clube",
            "Jogos",
            "Público médio",
            "Renda média",
        ]
        styled_comp = (
            comp_club.style.format(
                {"Público médio": fmt_num_cell, "Renda média": fmt_brl_cell}
            )
            .map(style_clube, subset=["Clube"])
            .apply(gradient_red, subset=["Público médio"])
        )
        st.dataframe(styled_comp, use_container_width=True, hide_index=True, height=390)

    with col_r4:
        st.markdown("**Por estádio — média de público por clube**")
        stad_agg = (
            df_avg.groupby(["stadium", "monitored_club"])
            .agg(
                jogos=("id", "count"),
                publico_medio=("attendance", "mean"),
                publico_total=("attendance", "sum"),
                renda_media=("gross_revenue", "mean"),
            )
            .reset_index()
            .sort_values("publico_medio", ascending=False)
            .head(15)
        )
        stad_agg.columns = [
            "Estádio",
            "Clube",
            "Jogos",
            "Público médio",
            "Público total",
            "Renda média",
        ]
        styled_stad = (
            stad_agg.style.format(
                {
                    "Público médio": fmt_num_cell,
                    "Público total": fmt_num_cell,
                    "Renda média": fmt_brl_cell,
                }
            )
            .map(style_clube, subset=["Clube"])
            .apply(gradient_red, subset=["Público médio"])
        )
        st.dataframe(styled_stad, use_container_width=True, hide_index=True, height=390)

    st.divider()

    # ── 7. Top 10 adversários por público médio ─────────────────────────
    st.markdown("**Top 10 adversários — público médio**")
    _df_opp = df_avg.copy()
    _df_opp["adversario"] = _df_opp.apply(
        lambda r: r["away"] if r["monitored_as"] == "home" else r["home"], axis=1
    )
    _adv_agg = (
        _df_opp.groupby("adversario")
        .agg(jogos=("id", "count"), publico_medio=("attendance", "mean"))
        .reset_index()
        .query("jogos >= 2")
        .sort_values("publico_medio", ascending=False)
        .head(10)
    )
    if not _adv_agg.empty:
        fig_adv = px.bar(
            _adv_agg,
            x="publico_medio",
            y="adversario",
            orientation="h",
            color_discrete_sequence=[COLORS["accent"]],
            labels={"publico_medio": "Público médio", "adversario": ""},
            text="jogos",
        )
        fig_adv.update_traces(
            texttemplate="%{x:.2s} (%{text} j)",
            textposition="outside",
            textfont_size=10,
            cliponaxis=False,
        )
        fig_adv.update_layout(
            height=400,
            yaxis=dict(autorange="reversed"),
            **chart_layout,
        )
        st.plotly_chart(fig_adv, use_container_width=True)
