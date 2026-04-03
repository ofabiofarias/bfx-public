"""Público e Renda — Visualização pública de dados de borderô. Main Streamlit entrypoint."""

from datetime import datetime

import streamlit as st

from ui.theme import inject_shared_css, COLORS
from core.database import init_db
from core.sync import pull_from_cloud, get_sync_status

init_db()

# ── Sync on startup (once per session) ──────────────────────────────────────

if "sync_done" not in st.session_state:
    with st.spinner("Atualizando dados..."):
        pull_result = pull_from_cloud()
    st.session_state.sync_done = True
    st.session_state.sync_result = pull_result
    if pull_result.get("status") == "ok":
        stats = pull_result.get("stats", {})
        st.toast(f"Dados atualizados — {stats.get('matches', 0)} jogos", icon=":material/cloud_done:")
    elif pull_result.get("status") != "no_cloud":
        st.toast("Falha ao atualizar dados", icon=":material/cloud_alert:")

st.set_page_config(
    page_title="Público e Renda",
    page_icon=":material/stadium:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Pages ────────────────────────────────────────────────────────────────────

home = st.Page(
    "pages/00_inicio.py", title="Início", icon=":material/home:", default=True
)
jogos = st.Page("pages/01_jogos.py", title="Jogos", icon=":material/sports_soccer:")
relatorios = st.Page(
    "pages/02_relatorios.py", title="Relatórios", icon=":material/bar_chart:"
)
bordero = st.Page(
    "pages/03_bordero.py", title="Borderô", icon=":material/receipt_long:"
)

pg = st.navigation(
    {
        "INÍCIO": [home],
        "DADOS": [jogos, relatorios, bordero],
    }
)

# ── Shared CSS ───────────────────────────────────────────────────────────────

inject_shared_css()

# ── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(
        f"""<div style="padding:12px 0 8px 0;">
            <span style="font-size:1.4rem;font-weight:700;color:{COLORS["primary"]};">Público e Renda</span><br>
            <span style="font-size:0.78rem;color:{COLORS["text_secondary"]};letter-spacing:0.03em;">
                dados de borderô
            </span>
        </div>""",
        unsafe_allow_html=True,
    )
    st.divider()

    # ── Last update indicator ──────────────────────────────────────────────
    _sync = get_sync_status()
    _last = _sync.get("last_pull")

    _ts_str = "Nunca atualizado"
    if _last:
        try:
            _ts = datetime.fromisoformat(_last)
            _ts_str = f"Atualizado em {_ts:%d/%m/%Y %H:%M}"
        except (ValueError, TypeError):
            pass

    _color = COLORS["text_secondary"]
    if _sync["state"] == "synced":
        _color = COLORS["success"]
    elif _sync["state"] == "error":
        _color = COLORS["error"]

    st.markdown(
        f'<div style="display:flex;align-items:center;gap:5px;padding:2px 0 8px 0;cursor:default;">'
        f'<span style="font-family:\'Material Symbols Rounded\';font-size:0.75rem;color:{_color};">cloud_done</span>'
        f'<span style="color:{COLORS["text_secondary"]};font-size:0.68rem;letter-spacing:0.02em;">{_ts_str}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Footer
    st.markdown(
        f"""<div style="position:fixed;bottom:12px;padding:4px 0;z-index:10;">
            <small><a href="https://farias.cc" target="_blank"
            style="color:{COLORS["text_secondary"]};text-decoration:none;">
            [r.lab] &bull; fabio farias &copy; {datetime.now().year}</a></small>
        </div>""",
        unsafe_allow_html=True,
    )

# ── Run ──────────────────────────────────────────────────────────────────────

pg.run()
