"""Tab FOR vs CEA — comparativo entre Fortaleza e Ceará."""

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlmodel import select

from ui.theme import (
    COLORS,
    fmt_brl,
    fmt_num,
    style_clube,
    fmt_brl_cell,
    fmt_num_cell,
    fmt_pct_cell,
    gradient_blue,
    gradient_red,
    build_metric_card,
)
from core.database import get_session
from models.models import Club, MatchLine


def render(
    df: pd.DataFrame,
    df_avg: pd.DataFrame,
    chart_layout: dict,
    club_colors: dict,
) -> None:
    df_for = df[df["monitored_club"] == "FOR"]
    df_cea = df[df["monitored_club"] == "CEA"]
    df_for_avg = df_avg[df_avg["monitored_club"] == "FOR"]
    df_cea_avg = df_avg[df_avg["monitored_club"] == "CEA"]

    if df_for.empty and df_cea.empty:
        st.info("Nenhum jogo do Fortaleza ou Ceará nos filtros selecionados.")
        return
    if df_for.empty or df_cea.empty:
        _only_club = "Fortaleza" if not df_for.empty else "Ceará"
        st.info(
            f"Apenas **{_only_club}** tem jogos nos filtros selecionados. "
            "Ajuste os filtros para ver a comparação."
        )
        return

    def _s(s):
        return s.sum() if len(s) > 0 else 0

    def _m(s):
        return s.mean() if len(s) > 0 else 0

    def _mx(s):
        return s.max() if len(s) > 0 else 0

    def _pct(n, d):
        return (n / d * 100) if d > 0 else 0

    for_att = _s(df_for["attendance"])
    cea_att = _s(df_cea["attendance"])

    # Gates counts per club
    _for_ab = len(df_for[df_for["gates"] == "ABERTO"])
    _for_fe = len(df_for[df_for["gates"] == "FECHADO"])
    _cea_ab = len(df_cea[df_cea["gates"] == "ABERTO"])
    _cea_fe = len(df_cea[df_cea["gates"] == "FECHADO"])
    _for_gates = f"✔ {_for_ab} aberto" + (
        f" · 🔒 {_for_fe} fechado" if _for_fe > 0 else ""
    )
    _cea_gates = f"✔ {_cea_ab} aberto" + (
        f" · 🔒 {_cea_fe} fechado" if _cea_fe > 0 else ""
    )

    # Header cards
    _col1, _col2 = st.columns(2)
    with _col1:
        st.markdown(
            build_metric_card(
                title="CLUBE",
                value="Fortaleza EC",
                subtitle=f"{len(df_for)} jogos · {_for_gates}",
                sub2=f"Público total: {fmt_num(for_att)}",
                icon="🇫🇷",
                color=COLORS["primary"],
            ),
            unsafe_allow_html=True,
        )
    with _col2:
        st.markdown(
            build_metric_card(
                title="CLUBE",
                value="Ceará SC",
                subtitle=f"{len(df_cea)} jogos · {_cea_gates}",
                sub2=f"Público total: {fmt_num(cea_att)}",
                icon="💩",
                color=COLORS["accent"],
            ),
            unsafe_allow_html=True,
        )

    st.markdown("")

    # Comparison metrics table
    _metrics = [
        ("Jogos", len(df_for), len(df_cea), "num"),
        ("Público total", for_att, cea_att, "num"),
        (
            "Média de público",
            _m(df_for_avg["attendance"]),
            _m(df_cea_avg["attendance"]),
            "num",
        ),
        (
            "Maior público",
            _mx(df_for["attendance"]),
            _mx(df_cea["attendance"]),
            "num",
        ),
        ("Sócios (total)", _s(df_for["members"]), _s(df_cea["members"]), "num"),
        (
            "% Sócios",
            _pct(_s(df_for["members"]), for_att),
            _pct(_s(df_cea["members"]), cea_att),
            "pct",
        ),
        (
            "Cortesias",
            _s(df_for["complimentary"]),
            _s(df_cea["complimentary"]),
            "num",
        ),
        ("Gratuidades", _s(df_for["free"]), _s(df_cea["free"]), "num"),
        (
            "Ingressos vendidos",
            _s(df_for["ingressos"]),
            _s(df_cea["ingressos"]),
            "num",
        ),
        (
            "Renda bruta total",
            _s(df_for["gross_revenue"]),
            _s(df_cea["gross_revenue"]),
            "brl0",
        ),
        (
            "Renda líq. monitorado",
            _s(df_for["monitored_net_revenue"]),
            _s(df_cea["monitored_net_revenue"]),
            "brl0",
        ),
        (
            "Ticket médio",
            _m(df_for_avg["avg_ticket"]),
            _m(df_cea_avg["avg_ticket"]),
            "brl2",
        ),
    ]

    def _fv(v, k):
        if k == "num":
            return fmt_num(v)
        if k == "pct":
            return f"{v:.1f}%"
        if k == "brl0":
            return fmt_brl(v, 0)
        if k == "brl2":
            return fmt_brl(v)
        return str(v)

    def _bar_row(label, vf, vc, kind):
        fv_str = _fv(vf, kind)
        cv_str = _fv(vc, kind)

        if kind == "raw":
            bar_html = ""
            delta_html = ""
        else:
            nf = float(vf) if not isinstance(vf, str) else 0
            nc = float(vc) if not isinstance(vc, str) else 0
            total = nf + nc
            pct_f = (nf / total * 100) if total > 0 else 50
            pct_c = 100 - pct_f

            if nc > 0 and nf > 0:
                diff = ((nf - nc) / nc) * 100
                if abs(diff) < 0.5:
                    delta_html = '<span style="color:#adb5bd;font-size:0.7rem;font-weight:600;">≈</span>'
                elif diff > 0:
                    delta_html = f'<span style="color:{COLORS["primary"]};font-size:0.7rem;font-weight:700;">+{diff:.0f}%</span>'
                else:
                    delta_html = f'<span style="color:{COLORS["accent"]};font-size:0.7rem;font-weight:700;">{diff:.0f}%</span>'
            else:
                delta_html = ""

            bar_html = (
                f'<div style="display:flex;height:8px;border-radius:4px;overflow:hidden;margin:4px 0 0 0;">'
                f'<div style="width:{pct_f:.1f}%;background:{COLORS["primary"]};"></div>'
                f'<div style="width:{pct_c:.1f}%;background:{COLORS["accent"]};"></div>'
                f"</div>"
            )

        return (
            f'<div style="display:flex;align-items:center;gap:8px;">'
            f'<div style="flex:1;text-align:right;">'
            f'<span style="font-size:0.92rem;font-weight:600;color:{COLORS["primary"]};">{fv_str}</span>'
            f"</div>"
            f'<div style="flex:2;">'
            f'<div style="text-align:center;font-size:0.78rem;font-weight:600;color:{COLORS["text_secondary"]};margin-bottom:2px;">{label}</div>'
            f"{bar_html}"
            f"</div>"
            f'<div style="flex:1;text-align:left;">'
            f'<span style="font-size:0.92rem;font-weight:600;color:{COLORS["accent"]};">{cv_str}</span>'
            f"</div>"
            f'<div style="width:45px;text-align:center;">{delta_html}</div>'
            f"</div>"
        )

    # Stadium row
    _for_stad = (
        df_for["stadium"].mode().iloc[0]
        if len(df_for["stadium"].mode()) > 0
        else "—"
    )
    _cea_stad = (
        df_cea["stadium"].mode().iloc[0]
        if len(df_cea["stadium"].mode()) > 0
        else "—"
    )

    # Build all rows
    _all_rows = ""
    for _i, (_label, _vf, _vc, _kind) in enumerate(_metrics):
        _bg = "#f8f9fa" if _i % 2 == 0 else "#fff"
        _all_rows += (
            f'<div style="background:{_bg};padding:8px 16px;">'
            f"{_bar_row(_label, _vf, _vc, _kind)}"
            f"</div>"
        )
    _bg_last = "#f8f9fa" if len(_metrics) % 2 == 0 else "#fff"
    _all_rows += (
        f'<div style="background:{_bg_last};padding:8px 16px;">'
        f'<div style="display:flex;align-items:center;gap:8px;">'
        f'<div style="flex:1;text-align:right;">'
        f'<span style="font-size:0.85rem;font-weight:600;color:{COLORS["primary"]};">{_for_stad}</span>'
        f"</div>"
        f'<div style="flex:2;">'
        f'<div style="text-align:center;font-size:0.78rem;font-weight:600;color:{COLORS["text_secondary"]};">Estádio principal</div>'
        f"</div>"
        f'<div style="flex:1;text-align:left;">'
        f'<span style="font-size:0.85rem;font-weight:600;color:{COLORS["accent"]};">{_cea_stad}</span>'
        f"</div>"
        f'<div style="width:45px;"></div>'
        f"</div></div>"
    )

    st.markdown(
        f'<div style="border:1px solid {COLORS["border"]};border-radius:10px;overflow:hidden;margin:10px 0;">'
        f'<div style="background:{COLORS["primary"]};display:flex;padding:12px 16px;align-items:center;">'
        f'<div style="flex:1;text-align:right;color:#fff;font-size:0.78rem;text-transform:uppercase;letter-spacing:.03em;font-weight:600;">Fortaleza</div>'
        f'<div style="flex:2;text-align:center;color:rgba(255,255,255,0.5);font-size:0.7rem;text-transform:uppercase;letter-spacing:.05em;">Comparativo</div>'
        f'<div style="flex:1;text-align:left;color:#fff;font-size:0.78rem;text-transform:uppercase;letter-spacing:.03em;font-weight:600;">Ceará</div>'
        f'<div style="width:45px;text-align:center;color:rgba(255,255,255,0.5);font-size:0.65rem;">Δ</div>'
        f"</div>"
        f"{_all_rows}"
        f"</div>",
        unsafe_allow_html=True,
    )

    st.divider()

    # Charts
    if "year" not in df.columns:
        df["year"] = pd.to_datetime(df["date"]).dt.year

    _df_fc = df[df["monitored_club"].isin(["FOR", "CEA"])]
    _df_fc_avg = df_avg[df_avg["monitored_club"].isin(["FOR", "CEA"])]

    _col1, _col2 = st.columns(2)
    with _col1:
        st.markdown("**Público médio por ano**")
        _yc_att = (
            _df_fc_avg.groupby(["year", "monitored_club"])["attendance"]
            .mean()
            .reset_index()
        )
        _fig = px.bar(
            _yc_att,
            x="year",
            y="attendance",
            color="monitored_club",
            barmode="group",
            color_discrete_map=club_colors,
            labels={
                "year": "",
                "attendance": "Público médio",
                "monitored_club": "",
            },
            text_auto=".2s",
        )
        _fig.update_traces(textfont_size=10, textangle=0, textposition="outside", cliponaxis=False)
        _fig.update_layout(height=350, **chart_layout)
        st.plotly_chart(_fig, use_container_width=True)

    with _col2:
        st.markdown("**Renda bruta média por ano**")
        _yc_rev = (
            _df_fc_avg.groupby(["year", "monitored_club"])["gross_revenue"]
            .mean()
            .reset_index()
        )
        _fig = px.bar(
            _yc_rev,
            x="year",
            y="gross_revenue",
            color="monitored_club",
            barmode="group",
            color_discrete_map=club_colors,
            labels={"year": "", "gross_revenue": "R$ médio", "monitored_club": ""},
            text_auto=".2s",
        )
        _fig.update_traces(textfont_size=10, textangle=0, textposition="outside", cliponaxis=False)
        _fig.update_layout(height=350, **chart_layout)
        st.plotly_chart(_fig, use_container_width=True)

    st.markdown("**Ticket médio por ano**")
    _yc_tk = (
        _df_fc_avg.groupby(["year", "monitored_club"])["avg_ticket"]
        .mean()
        .reset_index()
    )
    _fig = px.line(
        _yc_tk,
        x="year",
        y="avg_ticket",
        color="monitored_club",
        markers=True,
        color_discrete_map=club_colors,
        labels={
            "year": "",
            "avg_ticket": "Ticket médio (R$)",
            "monitored_club": "",
        },
        text="avg_ticket",
    )
    _fig.update_traces(texttemplate="R$ %{text:.2f}", textposition="top center", textfont_size=10)
    _fig.update_layout(height=300, **chart_layout)
    st.plotly_chart(_fig, use_container_width=True)

    # Público total por ano
    st.markdown("**Público total por ano**")
    _yc_total = (
        _df_fc.groupby(["year", "monitored_club"])["attendance"].sum().reset_index()
    )
    _fig = px.bar(
        _yc_total,
        x="year",
        y="attendance",
        color="monitored_club",
        barmode="group",
        color_discrete_map=club_colors,
        labels={"year": "", "attendance": "Público total", "monitored_club": ""},
        text_auto=".2s",
    )
    _fig.update_traces(textfont_size=10, textangle=0, textposition="outside", cliponaxis=False)
    _fig.update_layout(height=350, **chart_layout)
    st.plotly_chart(_fig, use_container_width=True)

    # Ranking média de público por ano
    st.divider()
    st.markdown(
        '<div class="section-header">Ranking — Média de Público por Ano</div>',
        unsafe_allow_html=True,
    )
    _rank_yr = (
        _df_fc_avg.groupby(["year", "monitored_club"])["attendance"]
        .mean()
        .reset_index()
    )
    _rank_yr.columns = ["Ano", "Clube", "Público médio"]
    _rank_pivot = _rank_yr.pivot(
        index="Ano", columns="Clube", values="Público médio"
    ).reset_index()

    _rank_rows = ""
    for _, _rr in _rank_pivot.iterrows():
        _yr = int(_rr["Ano"])
        _vf = _rr.get("FOR", 0) or 0
        _vc = _rr.get("CEA", 0) or 0
        _winner_color = COLORS["primary"] if _vf >= _vc else COLORS["accent"]
        _winner = "FOR" if _vf >= _vc else "CEA"
        _total = _vf + _vc
        _pf = (_vf / _total * 100) if _total > 0 else 50
        _pc = 100 - _pf

        _rank_rows += (
            f'<div style="display:flex;align-items:center;gap:8px;padding:10px 16px;'
            f"background:{'#f8f9fa' if _yr % 2 == 0 else '#fff'};"
            f'border-bottom:1px solid {COLORS["border"]};">'
            f'<div style="width:50px;font-weight:700;color:{COLORS["text"]};">{_yr}</div>'
            f'<div style="flex:1;text-align:right;font-weight:600;color:{COLORS["primary"]};">{fmt_num(_vf)}</div>'
            f'<div style="flex:2;">'
            f'<div style="display:flex;height:8px;border-radius:4px;overflow:hidden;">'
            f'<div style="width:{_pf:.1f}%;background:{COLORS["primary"]};"></div>'
            f'<div style="width:{_pc:.1f}%;background:{COLORS["accent"]};"></div>'
            f"</div></div>"
            f'<div style="flex:1;text-align:left;font-weight:600;color:{COLORS["accent"]};">{fmt_num(_vc)}</div>'
            f'<div style="width:45px;text-align:center;">'
            f'<span style="background:{_winner_color};color:#fff;padding:1px 6px;border-radius:4px;'
            f'font-size:0.7rem;font-weight:700;">{_winner}</span>'
            f"</div>"
            f"</div>"
        )

    st.markdown(
        f'<div style="border:1px solid {COLORS["border"]};border-radius:10px;overflow:hidden;">'
        f'<div style="background:{COLORS["primary"]};display:flex;padding:10px 16px;align-items:center;">'
        f'<div style="width:50px;color:#fff;font-size:0.75rem;font-weight:600;">ANO</div>'
        f'<div style="flex:1;text-align:right;color:#fff;font-size:0.75rem;font-weight:600;">FORTALEZA</div>'
        f'<div style="flex:2;"></div>'
        f'<div style="flex:1;text-align:left;color:#fff;font-size:0.75rem;font-weight:600;">CEARÁ</div>'
        f'<div style="width:45px;"></div>'
        f"</div>"
        f"{_rank_rows}</div>",
        unsafe_allow_html=True,
    )

    # Top 10 clássicos por público
    st.divider()
    st.markdown(
        '<div class="section-header">Top 10 Clássicos — FOR vs CEA</div>',
        unsafe_allow_html=True,
    )

    with get_session() as session:
        for_names = {
            c.name
            for c in session.exec(
                select(Club).where(Club.short_name == "FOR")
            ).all()
        }
        cea_names = {
            c.name
            for c in session.exec(
                select(Club).where(Club.short_name == "CEA")
            ).all()
        }

    if for_names and cea_names:
        classicos = df[
            ((df["home"].isin(for_names)) & (df["away"].isin(cea_names)))
            | ((df["home"].isin(cea_names)) & (df["away"].isin(for_names)))
        ]

        if not classicos.empty:
            top_classicos = classicos.nlargest(10, "attendance")[
                [
                    "date",
                    "monitored_club",
                    "home",
                    "away",
                    "competition",
                    "stadium",
                    "attendance",
                    "gross_revenue",
                ]
            ].copy()
            top_classicos["date"] = pd.to_datetime(
                top_classicos["date"]
            ).dt.strftime("%d/%m/%Y")
            top_classicos.columns = [
                "Data",
                "Clube",
                "Mandante",
                "Visitante",
                "Competição",
                "Estádio",
                "Público",
                "Renda Bruta",
            ]
            styled_cls = (
                top_classicos.style.format(
                    {"Público": fmt_num_cell, "Renda Bruta": fmt_brl_cell}
                )
                .map(style_clube, subset=["Clube"])
                .apply(gradient_red, subset=["Público"])
                .apply(gradient_blue, subset=["Renda Bruta"])
            )
            st.dataframe(
                styled_cls,
                use_container_width=True,
                hide_index=True,
                height=390,
                column_config={"Clube": st.column_config.TextColumn(width=55)},
            )
        else:
            st.info("Nenhum clássico FOR vs CEA encontrado no período.")
    else:
        st.info("Clubes FOR e/ou CEA não encontrados.")

    # Top 10 maior público visitante
    st.divider()
    st.markdown(
        '<div class="section-header">Top 10 — Maior Público Visitante</div>',
        unsafe_allow_html=True,
    )

    with get_session() as session:
        vis_agg = {}
        all_lines = session.exec(
            select(MatchLine).where(
                MatchLine.is_visitor_line == True,  # noqa: E712
                MatchLine.category == "INGRESSO",
            )
        ).all()
        for ml in all_lines:
            vis_agg.setdefault(ml.match_id, {"pub": 0, "rec": 0.0})
            vis_agg[ml.match_id]["pub"] += ml.sold or 0
            vis_agg[ml.match_id]["rec"] += float(ml.revenue or 0)

    if vis_agg:
        df_vis = df[df["id"].isin(vis_agg.keys())].copy()
        if not df_vis.empty:
            df_vis["pub_visitante"] = df_vis["id"].map(
                lambda x: vis_agg.get(x, {}).get("pub", 0)
            )
            df_vis["rec_visitante"] = df_vis["id"].map(
                lambda x: vis_agg.get(x, {}).get("rec", 0.0)
            )
            df_vis["pct_visitante"] = (
                df_vis["pub_visitante"] / df_vis["attendance"] * 100
            ).where(df_vis["attendance"] > 0, 0)

            top_vis = df_vis.nlargest(10, "pub_visitante")[
                [
                    "date",
                    "monitored_club",
                    "home",
                    "away",
                    "competition",
                    "attendance",
                    "pub_visitante",
                    "rec_visitante",
                    "pct_visitante",
                ]
            ].copy()
            top_vis["date"] = pd.to_datetime(top_vis["date"]).dt.strftime(
                "%d/%m/%Y"
            )
            top_vis.columns = [
                "Data",
                "Clube",
                "Mandante",
                "Visitante",
                "Competição",
                "Público",
                "Púb. Visitante",
                "Rec. Visitante",
                "% Vis.",
            ]
            styled_vis = (
                top_vis.style.format(
                    {
                        "Público": fmt_num_cell,
                        "Púb. Visitante": fmt_num_cell,
                        "Rec. Visitante": fmt_brl_cell,
                        "% Vis.": fmt_pct_cell,
                    }
                )
                .map(style_clube, subset=["Clube"])
                .apply(gradient_red, subset=["Púb. Visitante"])
            )
            st.dataframe(
                styled_vis,
                use_container_width=True,
                hide_index=True,
                height=390,
                column_config={"Clube": st.column_config.TextColumn(width=55)},
            )
        else:
            st.info("Nenhum jogo com dados de visitante nos filtros selecionados.")
    else:
        st.info(
            "Nenhum dado de público visitante encontrado. Use 'Corrigir Flag Visitante' em Importar/Exportar."
        )
