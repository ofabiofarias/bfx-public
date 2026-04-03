"""Page: Jogos — Lista e visualização de jogos (read-only)."""

from datetime import date
from decimal import Decimal

import pandas as pd
import streamlit as st
from sqlmodel import select

from core.calculator import calc_avg_ticket, calc_ingressos, calc_publico
from ui.theme import (
    TABLE_COL_CONFIG,
    fmt_brl,
    fmt_num,
    style_clube,
    style_tipo,
    style_negative,
    fmt_brl_cell,
    fmt_num_cell,
    gradient_blue,
    gradient_red,
    style_verificado,
    verification_cell,
    verification_badge_html,
    COLORS,
)
from core.database import (
    get_session,
    get_distinct_stadiums,
    get_distinct_visitors,
    get_distinct_competitions,
    get_all_clubs_dict,
)
from core.match_service import load_match_detail as _load_match_detail
from models.models import Club, Match, MatchLine, MonitoredAs


# ── Helpers ──────────────────────────────────────────────────────────────────


def _load_matches(
    club_id,
    competition,
    date_from,
    date_to,
    stadium=None,
    tipo=None,
    adversario=None,
) -> list[dict]:
    with get_session() as session:
        query = select(Match)
        if club_id:
            query = query.where(Match.monitored_club_id == club_id)
        if competition:
            query = query.where(Match.competition == competition)
        if stadium:
            query = query.where(Match.stadium == stadium)
        if tipo:
            monitored_as_val = (
                MonitoredAs.home if tipo == "MAN" else MonitoredAs.away
            )
            query = query.where(Match.monitored_as == monitored_as_val)
        if adversario:
            adv_club = session.exec(
                select(Club).where(Club.name == adversario)
            ).first()
            if adv_club:
                query = query.where(
                    (Match.away_club_id == adv_club.id)
                    | (Match.home_club_id == adv_club.id)
                )
        query = query.where(
            Match.date >= str(date_from),
            Match.date <= str(date_to),
        )
        query = query.order_by(Match.date.desc())
        matches = session.exec(query).all()

        match_ids = [m.id for m in matches]
        line_counts = {}
        if match_ids:
            from sqlmodel import func

            stmt = (
                select(MatchLine.match_id, func.count(MatchLine.id))
                .where(MatchLine.match_id.in_(match_ids))
                .group_by(MatchLine.match_id)
            )
            for m_id, count in session.exec(stmt).all():
                line_counts[m_id] = count

        clubs = get_all_clubs_dict()
        _classic_shorts = {"FOR", "CEA"}
        rows = []
        for m in matches:
            line_count = line_counts.get(m.id, 0)
            mon = clubs.get(m.monitored_club_id)
            home_c = clubs.get(m.home_club_id)
            away_c = clubs.get(m.away_club_id)
            is_classico = (
                {(home_c.short_name if home_c else ""), (away_c.short_name if away_c else "")}
                == _classic_shorts
            )

            rows.append(
                {
                    "Verificado": verification_cell(
                        m.is_info_verified, m.is_details_verified
                    ),
                    "ID": m.id,
                    "Clube": mon.short_name if mon else "?",
                    "Data": pd.Timestamp(m.date),
                    "Competição": m.competition,
                    "Visitante": away_c.name if away_c else "?",
                    "Público": m.attendance,
                    "Bruta": float(m.gross_revenue),
                    "Liquida": float(m.net_revenue),
                    "Tipo": "MAN" if m.monitored_as == MonitoredAs.home else "VIS",
                    "_classico": is_classico,
                }
            )
        return rows


# ── Header ───────────────────────────────────────────────────────────────────

st.markdown("# :material/sports_soccer: Jogos")
st.caption("Lista de jogos com dados de público e renda.")

st.divider()

# ── Filters ──────────────────────────────────────────────────────────────────

clubs_map = get_all_clubs_dict()
monitored = {cid: c for cid, c in clubs_map.items() if c.monitored}

col1, col2, col3, col4 = st.columns(4)
with col1:
    filter_club = st.selectbox(
        "Clube",
        options=[None] + list(monitored.keys()),
        format_func=lambda x: (
            "Todos" if x is None else f"{monitored[x].name} ({monitored[x].short_name})"
        ),
    )
with col2:
    visitors = get_distinct_visitors()
    filter_adversario = st.selectbox(
        "Adversário",
        options=[None] + visitors,
        format_func=lambda x: "Todos" if x is None else x,
    )
with col3:
    competitions = get_distinct_competitions()
    filter_comp = st.selectbox(
        "Competição",
        options=[None] + competitions,
        format_func=lambda x: "Todas" if x is None else x,
    )
with col4:
    stadiums = get_distinct_stadiums()
    filter_stadium = st.selectbox(
        "Estádio",
        options=[None] + stadiums,
        format_func=lambda x: "Todos" if x is None else x,
    )

col5, col6, col7, col8 = st.columns(4)
with col5:
    filter_from = st.date_input(
        "De",
        value=date.today().replace(month=1, day=1),
        format="DD/MM/YYYY",
        min_value=date(2012, 1, 1),
        max_value=date.today(),
    )
with col6:
    filter_to = st.date_input(
        "Até",
        value=date.today(),
        format="DD/MM/YYYY",
        min_value=date(2012, 1, 1),
        max_value=date.today(),
    )
with col7:
    filter_tipo = st.selectbox(
        "Tipo",
        options=[None, "MAN", "VIS"],
        format_func=lambda x: "Todos" if x is None else ("Mandante" if x == "MAN" else "Visitante"),
    )
with col8:
    filter_classico = st.selectbox(
        "Clássico",
        options=[None, "Sim", "Não"],
        format_func=lambda x: "Todos" if x is None else x,
    )

# ── Match List ───────────────────────────────────────────────────────────────

matches = _load_matches(
    filter_club,
    filter_comp,
    filter_from,
    filter_to,
    filter_stadium,
    filter_tipo,
    filter_adversario,
)

# Filtro Clássico (client-side)
if filter_classico is not None:
    _want = filter_classico == "Sim"
    matches = [m for m in matches if m["_classico"] == _want]

if not matches:
    st.info("Nenhum jogo encontrado com os filtros selecionados.")
    st.stop()

st.markdown(f"**{len(matches)} jogos encontrados**")

df = pd.DataFrame(matches)

styled_df = (
    df.style.format(
        {"Bruta": fmt_brl_cell, "Liquida": fmt_brl_cell, "Público": fmt_num_cell}
    )
    .map(style_clube, subset=["Clube"])
    .map(style_tipo, subset=["Tipo"])
    .map(style_verificado, subset=["Verificado"])
    .map(style_negative, subset=["Liquida"])
    .apply(gradient_blue, subset=["Bruta"])
    .apply(gradient_red, subset=["Público"])
)

event = st.dataframe(
    styled_df,
    use_container_width=True,
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row",
    height=450,
    column_config={**TABLE_COL_CONFIG, "_classico": None},
)

# ── Selected Match (view-only) ──────────────────────────────────────────────

selected_rows = event.selection.rows if event.selection else []

if not selected_rows:
    st.caption("Selecione um jogo na tabela acima para visualizar.")
    st.stop()

match_id = matches[selected_rows[0]]["ID"]
match, lines = _load_match_detail(match_id)

if not match:
    st.error("Jogo não encontrado.")
    st.stop()

home_club = clubs_map.get(match.home_club_id)
away_club = clubs_map.get(match.away_club_id)
mon_club = clubs_map.get(match.monitored_club_id)

st.divider()

# ── Match Header Card ───────────────────────────────────────────────────────

st.markdown(
    f'<div class="section-header">Jogo <span style="background:#1B2A4A;color:#fff;padding:2px 10px;border-radius:12px;font-size:0.78rem;font-weight:700;margin-left:6px;">ID {match.id}</span></div>',
    unsafe_allow_html=True,
)

from ui.match_card import (
    badge_doc_link,
    badge_gates,
    badge_tipo,
    build_match_card_html,
    fmt_date_br,
)

card_html = build_match_card_html(
    mon_name=mon_club.name if mon_club else "?",
    date_str=fmt_date_br(match.date),
    stadium=match.stadium,
    home_name=home_club.name if home_club else "?",
    away_name=away_club.name if away_club else "?",
    competition=match.competition,
    match_id=match.id,
    verified_badge=verification_badge_html(
        match.is_info_verified, match.is_details_verified
    ),
    external_ref=match.external_ref,
    bord_html=badge_doc_link(match.bordero_url, "description", "Borderô"),
    sum_html=badge_doc_link(match.sumula_url, "summarize", "Súmula"),
    gates_badge=badge_gates(match.gates),
    tipo_badge=badge_tipo(
        match.monitored_as.value if match.monitored_as else None
    ),
)
st.markdown(card_html, unsafe_allow_html=True)

# ── Público e Renda ─────────────────────────────────────────────────────────

st.markdown('<div class="section-header">Público e Renda</div>', unsafe_allow_html=True)

_ing_lines = [line for line in lines if line.category == "INGRESSO"]
_vis_lines = [line for line in _ing_lines if line.is_visitor_line]
_man_lines = [line for line in _ing_lines if not line.is_visitor_line]
pub_visitante = sum((line.sold or 0) for line in _vis_lines)
pub_mandante = sum((line.sold or 0) for line in _man_lines)
rec_visitante = sum(float(line.revenue or 0) for line in _vis_lines)
rec_mandante = sum(float(line.revenue or 0) for line in _man_lines)

with st.container(border=True):
    publico = calc_publico(match.attendance, match.free)
    ingressos = calc_ingressos(publico, match.members, match.complimentary)
    avg = calc_avg_ticket(match.gross_revenue, ingressos)
    net_val = float(match.net_revenue)
    net_color = "#16A34A" if net_val >= 0 else "#DC2626"

    _card = "background:#EEF2F9;border:1px solid #E2E4EA;border-radius:10px;padding:16px 20px;flex:1;"
    _lbl = "font-size:0.78rem;text-transform:uppercase;letter-spacing:.04em;color:#1B2A4A;opacity:.65;margin-bottom:4px;"
    _val = "font-size:1.45rem;font-weight:700;line-height:1.3;"
    _navy = f"{_val}color:#1B2A4A;"
    _row = "display:flex;gap:12px;margin-bottom:12px;"

    pct_mem = (match.members / match.attendance * 100) if match.attendance > 0 else 0
    pct_cmp = (match.complimentary / match.attendance * 100) if match.attendance > 0 else 0
    pct_fre = (match.free / match.attendance * 100) if match.attendance > 0 else 0

    st.markdown(
        f'<div style="{_row}">'
        f'<div style="{_card}border-top:3px solid #C41E3A;">'
        f'  <div style="{_lbl}">Público Total</div>'
        f'  <div style="font-size:1.85rem;font-weight:800;color:#1B2A4A;line-height:1.2;">{fmt_num(match.attendance)}</div>'
        f'  <div style="font-size:0.8rem;color:#6B7280;margin-top:2px;">Pagantes: <strong style="color:#1B2A4A;">{fmt_num(publico)}</strong></div>'
        f"</div>"
        f'<div style="{_card}border-top:3px solid #C41E3A;">'
        f'  <div style="{_lbl}">Sócios</div>'
        f'  <div style="{_navy}">{fmt_num(match.members)}</div>'
        f'  <div style="font-size:0.8rem;color:#6B7280;margin-top:2px;">{pct_mem:.1f}% do total</div>'
        f"</div>"
        f'<div style="{_card}border-top:3px solid #C41E3A;">'
        f'  <div style="{_lbl}">Cortesias</div>'
        f'  <div style="{_navy}">{fmt_num(match.complimentary)}</div>'
        f'  <div style="font-size:0.8rem;color:#6B7280;margin-top:2px;">{pct_cmp:.1f}% do total</div>'
        f"</div>"
        f'<div style="{_card}border-top:3px solid #C41E3A;">'
        f'  <div style="{_lbl}">Gratuidades</div>'
        f'  <div style="{_navy}">{fmt_num(match.free)}</div>'
        f'  <div style="font-size:0.8rem;color:#6B7280;margin-top:2px;">{pct_fre:.1f}% do total</div>'
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div style="{_row}">'
        f'<div style="{_card}border-top:3px solid {net_color};">'
        f'  <div style="{_lbl}">Renda Líquida</div>'
        f'  <div style="{_val}color:{net_color};">{fmt_brl(net_val, 0)}</div>'
        f"</div>"
        f'<div style="{_card}border-top:3px solid #1B2A4A;">'
        f'  <div style="{_lbl}">Renda Bruta</div>'
        f'  <div style="{_navy}">{fmt_brl(match.gross_revenue, 0)}</div>'
        f"</div>"
        f'<div style="{_card}border-top:3px solid #1B2A4A;">'
        f'  <div style="{_lbl}">Ingressos</div>'
        f'  <div style="{_navy}">{fmt_num(ingressos)}</div>'
        f"</div>"
        f'<div style="{_card}border-top:3px solid #1B2A4A;">'
        f'  <div style="{_lbl}">Ticket Médio</div>'
        f'  <div style="{_navy}">{fmt_brl(avg)}</div>'
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    if _ing_lines:
        pct_vis = (pub_visitante / match.attendance * 100) if match.attendance > 0 else 0
        pct_man = (pub_mandante / match.attendance * 100) if match.attendance > 0 else 0
        gross_val = float(match.gross_revenue)
        pct_rec_vis = (rec_visitante / gross_val * 100) if gross_val > 0 else 0
        pct_rec_man = (rec_mandante / gross_val * 100) if gross_val > 0 else 0

        st.markdown(
            f'<div style="{_row}">'
            f'<div style="{_card}border-top:3px solid #CED4DA;">'
            f'  <div style="{_lbl}">Púb. Mandante</div>'
            f'  <div style="{_navy}">{fmt_num(pub_mandante)}</div>'
            f'  <div style="font-size:0.8rem;color:#6B7280;margin-top:4px;">{pct_man:.1f}% do total</div>'
            f'  <div style="margin-top:4px;height:5px;border-radius:3px;background:#E2E4EA;overflow:hidden;">'
            f'    <div style="width:{min(pct_man, 100):.1f}%;height:100%;background:#1B2A4A;border-radius:3px;"></div>'
            f"  </div>"
            f"</div>"
            f'<div style="{_card}border-top:3px solid #CED4DA;">'
            f'  <div style="{_lbl}">Rec. Mandante</div>'
            f'  <div style="{_navy}">{fmt_brl(rec_mandante, 0)}</div>'
            f'  <div style="font-size:0.8rem;color:#6B7280;margin-top:4px;">{pct_rec_man:.1f}% da bruta</div>'
            f"  </div>"
            f'<div style="{_card}border-top:3px solid #CED4DA;">'
            f'  <div style="{_lbl}">Púb. Visitante</div>'
            f'  <div style="{_navy}">{fmt_num(pub_visitante)}</div>'
            f'  <div style="font-size:0.8rem;color:#6B7280;margin-top:4px;">{pct_vis:.1f}% do total</div>'
            f"  </div>"
            f'<div style="{_card}border-top:3px solid #CED4DA;">'
            f'  <div style="{_lbl}">Rec. Visitante</div>'
            f'  <div style="{_navy}">{fmt_brl(rec_visitante, 0)}</div>'
            f'  <div style="font-size:0.8rem;color:#6B7280;margin-top:4px;">{pct_rec_vis:.1f}% da bruta</div>'
            f"  </div>"
            f"</div>",
            unsafe_allow_html=True,
        )

# ── Detalhamento (read-only) ────────────────────────────────────────────────

st.markdown(
    '<div class="section-header">Detalhamento</div>',
    unsafe_allow_html=True,
)

with st.container(border=True):
    if lines:
        from ui.theme import style_categoria

        st.caption(f"{len(lines)} linhas")
        lines_ro = pd.DataFrame(
            [
                {
                    "Categoria": line.category,
                    "Descrição": line.description,
                    "Disponível": line.available,
                    "Devolvidos": line.returned,
                    "Vendidos": line.sold,
                    "Preço": float(line.price) if line.price else None,
                    "Arrecadação": float(line.revenue) if line.revenue else None,
                    "Visitante?": line.is_visitor_line,
                }
                for line in lines
            ]
        )

        styled_lines_ro = lines_ro.style.map(
            style_categoria, subset=["Categoria"]
        ).format(
            {
                "Preço": fmt_brl_cell,
                "Arrecadação": fmt_brl_cell,
                "Disponível": fmt_num_cell,
                "Devolvidos": fmt_num_cell,
                "Vendidos": fmt_num_cell,
            }
        )

        st.dataframe(
            styled_lines_ro, use_container_width=True, hide_index=True, height=300
        )
    else:
        st.caption("Este jogo não possui detalhamento de borderô.")
