"""Page: Início — Página pública com visão geral e últimos jogos."""

import datetime

import streamlit as st
from sqlmodel import select

from core.services import get_dashboard_stats
from core.database import get_session
from models.models import Club, Match, MatchLine
from ui.theme import fmt_brl, fmt_num, build_metric_card, COLORS

# Header

st.markdown("# :material/stadium: Público e Renda")
st.caption(
    "Dados de público e renda dos jogos de Fortaleza EC e Ceará SC, "
    "extraídos dos boletins financeiros oficiais."
)

st.divider()

# Quick Stats

stats = get_dashboard_stats()

total_matches = stats["total_matches"]
matches_with_lines = stats["matches_with_lines"]
total_clubs = stats["total_clubs"]

for_stats = stats["for_stats"]
total_gross = for_stats["total_gross"]
avg_net = for_stats["avg_net"]
total_attendance = for_stats["total_attendance"]
avg_attendance = for_stats["avg_attendance"]
total_members = for_stats["total_members"]
avg_members = for_stats["avg_members"]
avg_ticket = for_stats["avg_ticket"]

current_year = datetime.date.today().year

st.markdown(
    '<div class="section-header">Visão Geral</div>',
    unsafe_allow_html=True,
)

st.markdown(
    f'<div style="display:flex;gap:12px;margin-bottom:16px;flex-wrap:wrap;">'
    f'<span style="background:#e9ecef;color:#495057;padding:4px 12px;border-radius:20px;font-size:0.75rem;font-weight:600;"><span style="font-family:\'Material Symbols Rounded\';font-size:13px;vertical-align:-2px;opacity:0.7;margin-right:2px;">database</span> jogos: {fmt_num(total_matches)}</span>'
    f'<span style="background:#e9ecef;color:#495057;padding:4px 12px;border-radius:20px;font-size:0.75rem;font-weight:600;"><span style="font-family:\'Material Symbols Rounded\';font-size:13px;vertical-align:-2px;opacity:0.7;margin-right:2px;">check_circle</span> detalhado: {fmt_num(matches_with_lines)}</span>'
    f'<span style="background:#e9ecef;color:#495057;padding:4px 12px;border-radius:20px;font-size:0.75rem;font-weight:600;"><span style="font-family:\'Material Symbols Rounded\';font-size:13px;vertical-align:-2px;opacity:0.7;margin-right:2px;">shield</span> clubes: {fmt_num(total_clubs)}</span>'
    f"</div>",
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(
        build_metric_card(
            title="Público Total",
            value=fmt_num(total_attendance),
            color=COLORS["primary"],
            icon="groups",
            bg_color="#FFFFFF",
            subtitle=f"Média: {fmt_num(avg_attendance)}",
        ),
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        build_metric_card(
            title="Renda Bruta",
            value=fmt_brl(total_gross, 0),
            color="#6B7280",
            icon="payments",
            bg_color="#F8F9FA",
            subtitle=f"Líq. méd: {fmt_brl(avg_net, 0)}",
        ),
        unsafe_allow_html=True,
    )
with col3:
    st.markdown(
        build_metric_card(
            title="Total de Sócios",
            value=fmt_num(total_members),
            color=COLORS["accent"],
            icon="workspace_premium",
            bg_color="#FFFFFF",
            subtitle=f"Média: {fmt_num(avg_members)} | Ticket: {fmt_brl(avg_ticket)}",
        ),
        unsafe_allow_html=True,
    )

st.markdown(
    f'<div style="text-align:right;font-size:0.65rem;font-weight:700;color:#ADB5BD;letter-spacing:0.05em;margin-top:6px;padding-right:4px;">FORTALEZA EC | {current_year}</div>',
    unsafe_allow_html=True,
)

st.divider()

# Últimos Jogos Registrados

st.markdown(
    '<div class="section-header">Últimos Jogos Registrados</div>',
    unsafe_allow_html=True,
)


@st.cache_data(ttl=60)
def _get_recent_matches(limit: int = 5) -> list[dict]:
    with get_session() as session:
        last_matches = session.exec(
            select(Match).order_by(Match.created_at.desc()).limit(limit)
        ).all()
        if not last_matches:
            return []
        clubs = {c.id: c for c in session.exec(select(Club)).all()}
        ids_with_lines_set = set(
            session.exec(select(MatchLine.match_id).distinct()).all()
        )
        results = []
        for match in last_matches:
            home_club = clubs.get(match.home_club_id)
            away_club = clubs.get(match.away_club_id)
            mon_club = clubs.get(match.monitored_club_id)
            has_lines = match.id in ids_with_lines_set
            results.append({
                "match": match,
                "home_name": home_club.name if home_club else "?",
                "away_name": away_club.name if away_club else "?",
                "mon_short": mon_club.short_name if mon_club else "?",
                "has_lines": has_lines,
            })
        return results


results = _get_recent_matches(limit=5)

if not results:
    st.info("Nenhum jogo registrado ainda.")
else:
    rows_html = []
    for r in results:
        match = r["match"]
        home_name = r["home_name"]
        away_name = r["away_name"]
        mon_short = r["mon_short"]
        has_lines = r["has_lines"]

        match_date = (
            match.date.strftime("%d/%m/%Y")
            if hasattr(match.date, "strftime")
            else str(match.date)
        )

        publico = fmt_num(match.attendance)
        bruta = fmt_brl(match.gross_revenue, 0)

        if mon_short == "FOR":
            club_color = "#C41E3A"
        elif mon_short == "CEA":
            club_color = "#1B2A4A"
        else:
            club_color = "#dee2e6"

        status_dot = (
            '<span style="color:#198754;" title="Com detalhamento">&#9679;</span>'
            if has_lines
            else '<span style="color:#C41E3A;" title="Sem detalhamento">&#9679;</span>'
        )

        rows_html.append(
            f'<div style="display:flex;align-items:center;justify-content:space-between;'
            f"padding:9px 14px;border-bottom:1px solid #f0f0f0;font-size:0.83rem;"
            f'color:#1B2A4A;border-left:3px solid {club_color};">'
            f'  <span style="color:#adb5bd;min-width:82px;font-size:0.77rem;">{match_date}</span>'
            f'  <span style="color:#6c757d;min-width:110px;font-size:0.77rem;">{match.competition}</span>'
            f'  <span style="flex:1;"><strong>{home_name}</strong> '
            f'<span style="color:#adb5bd;">&times;</span> <strong>{away_name}</strong></span>'
            f'  <span style="color:#6c757d;font-size:0.77rem;min-width:60px;text-align:right;">{mon_short}</span>'
            f'  <span style="min-width:70px;text-align:right;color:#6c757d;font-size:0.77rem;">{publico}</span>'
            f'  <span style="min-width:80px;text-align:right;color:#1B2A4A;font-weight:600;">{bruta}</span>'
            f'  <span style="margin-left:12px;">{status_dot}</span>'
            f"</div>"
        )

    st.markdown(
        '<div style="border:1px solid #e9ecef;border-radius:8px;overflow:hidden;margin-top:8px;">'
        + "".join(rows_html)
        + "</div>",
        unsafe_allow_html=True,
    )

st.divider()

# Sobre

st.markdown(
    '<div class="section-header">Sobre</div>',
    unsafe_allow_html=True,
)

st.markdown(
    f"""<div style="font-size:0.88rem;color:{COLORS['primary']};line-height:1.6;">
Este dashboard disponibiliza publicamente os dados de <strong>público e renda</strong> extraídos
dos boletins financeiros (borderôs) dos jogos de <strong>Fortaleza EC</strong> e <strong>Ceará SC</strong>.
<br><br>
<strong>O que você encontra aqui:</strong><br>
&bull; <strong>Jogos</strong> — Lista completa com público, renda bruta e líquida<br>
&bull; <strong>Relatórios</strong> — Painéis analíticos com filtros por clube, competição e período<br>
&bull; <strong>Borderô</strong> — Detalhamento financeiro individual de cada jogo
<br><br>
Os dados são atualizados periodicamente a partir dos boletins financeiros oficiais
publicados pela CBF e FCF.
<br><br>
<span style="font-size:0.78rem;color:{COLORS['text_secondary']};">Criado e atualizado por fabio farias.</span>
</div>""",
    unsafe_allow_html=True,
)

if total_matches == 0:
    st.divider()
    st.info(
        "Os dados ainda estão sendo carregados. "
        "Volte em breve para visualizar as informações."
    )
