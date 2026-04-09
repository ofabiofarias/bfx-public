"""Público e Renda — Main entrypoint"""

from datetime import datetime

import streamlit as st

from ui.theme import inject_shared_css, COLORS
from core.database import init_db
from core.sync import pull_from_cloud, get_sync_status

# Page config MUST be the first Streamlit command
st.set_page_config(
    page_title="Público e Renda",
    page_icon=":material/stadium:",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

# Sync on startup — process-wide cache avoids per-session re-pulls.
# The pull itself is gated by a persistent TTL in .sync_meta, so even across
# process restarts the cloud is only contacted when stale.


@st.cache_resource
def _sync_once_per_process() -> dict:
    return pull_from_cloud()


pull_result = _sync_once_per_process()
_status = pull_result.get("status")
if _status == "ok":
    _mode = pull_result.get("mode")
    if _mode and _mode != "noop":
        stats = pull_result.get("stats", {})
        st.toast(
            f"Dados atualizados — {stats.get('matches', 0)} jogos",
            icon=":material/cloud_done:",
        )
elif _status == "error":
    st.toast("Falha ao atualizar dados", icon=":material/cloud_alert:")

# Pages

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

pg = st.navigation([home, relatorios, jogos, bordero])

# Shared CSS

inject_shared_css()

# Sidebar

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

    # Last update indicator
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

    if st.button(
        ":material/refresh: Atualizar agora",
        key="btn_force_pull",
        use_container_width=True,
        help="Força um pull da nuvem, ignorando o TTL",
    ):
        with st.spinner("Atualizando dados..."):
            _forced = pull_from_cloud(force=True)
        _sync_once_per_process.clear()
        if _forced.get("status") == "ok":
            _mode = _forced.get("mode")
            if _mode == "noop":
                st.toast("Nada novo", icon=":material/cloud_done:")
            else:
                stats = _forced.get("stats", {})
                st.toast(
                    f"Atualizado — {stats.get('matches', 0)} jogos",
                    icon=":material/cloud_done:",
                )
        else:
            st.toast(
                _forced.get("message", "Falha ao atualizar"),
                icon=":material/cloud_alert:",
            )
        st.rerun()

    # Footer
    st.markdown(
        f"""<div style="position:fixed;bottom:12px;padding:4px 0;z-index:10;">
            <small><a href="https://farias.cc" target="_blank"
            style="color:{COLORS["text_secondary"]};text-decoration:none;">
            [r.lab] &bull; fabio farias &copy; {datetime.now().year}</a></small>
        </div>""",
        unsafe_allow_html=True,
    )

# Run

pg.run()
