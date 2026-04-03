"""Page: Borderô — Análise financeira individual de cada jogo (read-only)."""

from datetime import date
from decimal import Decimal

import streamlit as st
from sqlmodel import select

from ui.theme import (
    CATEGORY_COLORS,
    CATEGORY_LABELS,
    CATEGORY_ORDER,
    COLORS,
    build_metric_card,
    fmt_brl,
    fmt_num,
    verification_badge_html,
)
from core.database import (
    get_session,
    get_all_clubs_dict,
    get_distinct_competitions,
    get_distinct_stadiums,
    get_distinct_visitors,
)
from core.match_service import (
    load_filtered_matches as _load_filtered_matches,
    load_match_lines as _load_match_lines,
    aggregate_totals as _aggregate_totals,
    aggregate_lines_totals as _aggregate_lines_totals,
)
from models.models import Club, Match, MonitoredAs
from ui.components.bordero import (
    build_category_table,
    build_resultado_card,
    build_section_header,
    render_rubrica,
)


# ── Page ─────────────────────────────────────────────────────────────────────

st.markdown("# :material/receipt_long: Borderô")
st.caption("Análise financeira detalhada do borderô de cada jogo.")

st.divider()

# ── Filters ──────────────────────────────────────────────────────────────────

clubs_map = get_all_clubs_dict()
monitored = {cid: c for cid, c in clubs_map.items() if c.monitored}

col1, col2, col3 = st.columns(3)
with col1:
    filter_club = st.selectbox(
        "Clube",
        options=[None] + list(monitored.keys()),
        format_func=lambda x: (
            "Todos" if x is None else f"{monitored[x].name} ({monitored[x].short_name})"
        ),
        key="brd_club",
    )
with col2:
    visitors = get_distinct_visitors()
    filter_adversario = st.selectbox(
        "Adversário",
        options=[None] + visitors,
        format_func=lambda x: "Todos" if x is None else x,
        key="brd_adv",
    )
with col3:
    competitions = get_distinct_competitions()
    filter_comp = st.selectbox(
        "Competição",
        options=[None] + competitions,
        format_func=lambda x: "Todas" if x is None else x,
        key="brd_comp",
    )

col4, col5, col6 = st.columns(3)
with col4:
    filter_from = st.date_input(
        "De",
        value=date.today().replace(month=1, day=1),
        format="DD/MM/YYYY",
        min_value=date(2012, 1, 1),
        max_value=date.today(),
        key="brd_from",
    )
with col5:
    filter_to = st.date_input(
        "Até",
        value=date.today(),
        format="DD/MM/YYYY",
        min_value=date(2012, 1, 1),
        max_value=date.today(),
        key="brd_to",
    )
with col6:
    stadiums = get_distinct_stadiums()
    filter_stadium = st.selectbox(
        "Estádio",
        options=[None] + stadiums,
        format_func=lambda x: "Todos" if x is None else x,
        key="brd_stadium",
    )

# ── Load filtered matches ────────────────────────────────────────────────────

matches = _load_filtered_matches(
    filter_club, filter_comp, filter_adversario, filter_from, filter_to,
    stadium=filter_stadium,
)

if not matches:
    st.info("Nenhum jogo com borderô encontrado para os filtros selecionados.")
    st.stop()

brd_tab1, brd_tab2 = st.tabs(
    [":material/receipt_long: Jogo Individual", ":material/analytics: Análise por Rubrica"]
)

with brd_tab1:

    # ── Aggregate Cards ─────────────────────────────────────────────────────

    agg = _aggregate_totals(matches)
    agg_lines = _aggregate_lines_totals(matches)

    st.markdown(
        f'<div class="section-header">Visão Geral — {agg["count"]} jogos com borderô</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            build_metric_card(
                "Jogos com Borderô",
                str(agg["count"]),
                COLORS["primary"],
                icon="stadium",
                subtitle=f"Média bruta: {fmt_brl(agg['avg_gross'])}",
            ),
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            build_metric_card(
                "Receita Total",
                fmt_brl(agg_lines["ingresso"]),
                COLORS["primary"],
                icon="payments",
                subtitle=f"Bruta acumulada",
            ),
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            build_metric_card(
                "Despesas Total",
                fmt_brl(agg_lines["despesa"]),
                COLORS["accent"],
                icon="money_off",
                subtitle=f"B1 a B5 + Descontos",
            ),
            unsafe_allow_html=True,
        )
    with c4:
        res_color = COLORS["success"] if agg_lines["resultado"] >= 0 else COLORS["error"]
        st.markdown(
            build_metric_card(
                "Resultado Acumulado",
                fmt_brl(agg_lines["resultado"]),
                res_color,
                icon="account_balance",
                subtitle=f"Média líquida: {fmt_brl(agg['avg_net'])}",
            ),
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Game Selector ────────────────────────────────────────────────────────

    game_labels = {}
    year_counters = {}
    for m in matches:
        year = m["date"].year
        key = (year, m["mon_short"])
        year_counters[key] = year_counters.get(key, 0) + 1
        game_num = year_counters[key]

        d = m["date"].strftime("%d/%m")
        label = f"#{game_num} | {d} | {m['mon_short']} | {m['home_name']} x {m['away_name']} | {m['competition']}"
        game_labels[m["id"]] = label

    matches_display = list(reversed(matches))

    st.markdown(
        f'<div class="section-header">Selecionar Jogo</div>',
        unsafe_allow_html=True,
    )

    search_text = st.text_input(
        "Buscar jogo",
        placeholder="Digite para filtrar... (ex: Atlético, Brasileirão, 15/03)",
        key="brd_search",
        label_visibility="collapsed",
    )

    filtered_ids = []
    for m in matches_display:
        mid = m["id"]
        label = game_labels[mid]
        if not search_text or search_text.lower() in label.lower():
            filtered_ids.append(mid)

    _show_detail = True

    if not filtered_ids:
        st.warning("Nenhum jogo encontrado com o texto digitado.")
        _show_detail = False

    if _show_detail:
        PLACEHOLDER = "__none__"
        select_options = [PLACEHOLDER] + filtered_ids
        selected_raw = st.selectbox(
            "Jogo",
            options=select_options,
            format_func=lambda x: (
                "Selecione um jogo..." if x == PLACEHOLDER else game_labels[x]
            ),
            key="brd_game",
            label_visibility="collapsed",
        )

        if selected_raw == PLACEHOLDER:
            _show_detail = False
        else:
            selected_id = selected_raw
            sel_match = next((m for m in matches if m["id"] == selected_id), None)
            if not sel_match:
                _show_detail = False

    if _show_detail:
        st.markdown("<br>", unsafe_allow_html=True)

        # ── Match Header ─────────────────────────────────────────────────────

        from ui.match_card import (
            badge_doc_link,
            badge_gates,
            badge_tipo,
            build_match_card_html,
            fmt_date_br,
        )

        card_html = build_match_card_html(
            mon_name=sel_match["mon_name"],
            date_str=fmt_date_br(sel_match["date"]),
            stadium=sel_match["stadium"],
            home_name=sel_match["home_name"],
            away_name=sel_match["away_name"],
            competition=sel_match["competition"],
            match_id=sel_match["id"],
            verified_badge=verification_badge_html(
                sel_match["is_info_verified"], sel_match["is_details_verified"]
            ),
            bord_html=badge_doc_link(sel_match.get("bordero_url"), "description", "Borderô"),
            gates_badge=badge_gates(sel_match.get("gates", "")),
            tipo_badge=badge_tipo(sel_match.get("match_type", "")),
        )
        st.markdown(card_html, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Load lines ───────────────────────────────────────────────────────

        lines = _load_match_lines(selected_id)

        if not lines:
            st.warning("Este jogo não possui detalhamento de borderô (linhas).")

        if lines:
            receita_bruta = Decimal("0")
            despesa_total = Decimal("0")
            count_receita = 0
            count_despesa = 0

            for l in lines:
                rev = Decimal(str(l["revenue"]))
                if l["category"] == "INGRESSO":
                    receita_bruta += rev
                    count_receita += 1
                elif l["category"] != "DESCONTOS":
                    despesa_total += rev
                    count_despesa += 1

            receita_liquida = receita_bruta - despesa_total
            res_color = COLORS["success"] if receita_liquida >= 0 else COLORS["error"]

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(
                    build_metric_card(
                        "Receita Bruta",
                        fmt_brl(receita_bruta),
                        COLORS["primary"],
                        icon="payments",
                        subtitle=f"{count_receita} linhas de ingresso",
                    ),
                    unsafe_allow_html=True,
                )
            with c2:
                st.markdown(
                    build_metric_card(
                        "Despesas",
                        fmt_brl(despesa_total),
                        COLORS["accent"],
                        icon="money_off",
                        subtitle=f"{count_despesa} linhas de despesa",
                    ),
                    unsafe_allow_html=True,
                )
            with c3:
                st.markdown(
                    build_metric_card(
                        "Receita Líquida",
                        fmt_brl(receita_liquida),
                        res_color,
                        icon="account_balance",
                        subtitle="Receita - Despesas",
                    ),
                    unsafe_allow_html=True,
                )

            st.markdown("<br>", unsafe_allow_html=True)

            # ── Detail by Category ───────────────────────────────────────────

            st.markdown(
                f'<div class="section-header">Detalhamento por Categoria</div>',
                unsafe_allow_html=True,
            )

            tag_bg, tag_color = CATEGORY_COLORS["INGRESSO"]
            st.markdown(
                build_section_header("Ingresso", tag_bg, tag_color, "receita"),
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div style="border:1px solid {COLORS["border"]};border-top:none;border-radius:0 0 8px 8px;overflow:hidden;">'
                + build_category_table(lines, ["INGRESSO"], is_revenue=True)
                + "</div>",
                unsafe_allow_html=True,
            )

            tag_bg, tag_color = CATEGORY_COLORS["B1 - ALUGUEIS E SEGUROS"]
            st.markdown(
                build_section_header("B1 - Aluguéis e Seguros", tag_bg, tag_color, "despesa"),
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div style="border:1px solid {COLORS["border"]};border-top:none;border-radius:0 0 8px 8px;overflow:hidden;">'
                + build_category_table(lines, ["B1 - ALUGUEIS E SEGUROS"])
                + "</div>",
                unsafe_allow_html=True,
            )

            tag_bg, tag_color = CATEGORY_COLORS["B2 - TAXAS E IMPOSTOS"]
            st.markdown(
                build_section_header("B2 - Taxas e Impostos", tag_bg, tag_color, "despesa"),
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div style="border:1px solid {COLORS["border"]};border-top:none;border-radius:0 0 8px 8px;overflow:hidden;">'
                + build_category_table(lines, ["B2 - TAXAS E IMPOSTOS"])
                + "</div>",
                unsafe_allow_html=True,
            )

            tag_bg, tag_color = CATEGORY_COLORS["B3 - DESPESAS OPERACIONAIS"]
            st.markdown(
                build_section_header("B3 - Despesas Operacionais", tag_bg, tag_color, "despesa"),
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div style="border:1px solid {COLORS["border"]};border-top:none;border-radius:0 0 8px 8px;overflow:hidden;">'
                + build_category_table(lines, ["B3 - DESPESAS OPERACIONAIS"])
                + "</div>",
                unsafe_allow_html=True,
            )

            tag_bg, tag_color = CATEGORY_COLORS["B4 - DESPESAS EVENTUAIS / DEDUÇÕES"]
            st.markdown(
                build_section_header("B4 e B5 - Eventuais / Ajuste", tag_bg, tag_color, "despesa"),
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div style="border:1px solid {COLORS["border"]};border-top:none;border-radius:0 0 8px 8px;overflow:hidden;">'
                + build_category_table(
                    lines, ["B4 - DESPESAS EVENTUAIS / DEDUÇÕES", "B5 - AJUSTE BORDERÔ"]
                )
                + "</div>",
                unsafe_allow_html=True,
            )

            descontos_lines = [l for l in lines if l["category"] == "DESCONTOS"]
            if descontos_lines:
                tag_bg, tag_color = CATEGORY_COLORS["DESCONTOS"]
                st.markdown(
                    build_section_header("Descontos", tag_bg, tag_color, "despesa"),
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div style="border:1px solid {COLORS["border"]};border-top:none;border-radius:0 0 8px 8px;overflow:hidden;">'
                    + build_category_table(lines, ["DESCONTOS"])
                    + "</div>",
                    unsafe_allow_html=True,
                )

            st.markdown(build_resultado_card(receita_bruta, despesa_total), unsafe_allow_html=True)

            st.markdown("<br><br>", unsafe_allow_html=True)

# ── Tab 2: Análise por Rubrica ─────────────────────────────────────────────

with brd_tab2:
    render_rubrica(matches)
