"""Shared HTML builders for the match header card (used by Jogos and Borderô)."""

from datetime import date, datetime

# ── Style constants ─────────────────────────────────────────────────────────

_MI = "font-family:'Material Symbols Rounded';font-size:13px;vertical-align:middle;margin-right:1px;"
_DOC = "display:inline-flex;align-items:center;gap:4px;padding:4px 12px;border-radius:6px;font-size:0.75rem;font-weight:600;"
_ICO = "font-family:'Material Symbols Rounded';font-size:14px;vertical-align:middle;"


# ── Badge builders ──────────────────────────────────────────────────────────


def badge_tipo(value: str) -> str:
    """Badge for match type (Mandante/Visitante). Accepts enum value or string."""
    v = str(value).upper() if value else ""
    if v in ("HOME", "MANDANTE"):
        return f'<span style="color:#1e40af;font-size:0.75rem;font-weight:600;"><span style="{_MI}">home</span> Mandante</span>'
    if v in ("AWAY", "VISITANTE"):
        return f'<span style="color:#991b1b;font-size:0.75rem;font-weight:600;"><span style="{_MI}">flight</span> Visitante</span>'
    return f'<span style="color:#9ca3af;font-size:0.75rem;">{value or "—"}</span>'


def badge_gates(value: str) -> str:
    """Badge for gates status (ABERTO/FECHADO)."""
    v = str(value).upper() if value else ""
    if v == "ABERTO":
        return f'<span style="color:#166534;font-size:0.75rem;font-weight:600;"><span style="{_MI}">lock_open</span> Aberto</span>'
    if v == "FECHADO":
        return f'<span style="color:#6c757d;font-size:0.75rem;font-weight:600;"><span style="{_MI}">lock</span> Fechado</span>'
    return f'<span style="color:#9ca3af;font-size:0.75rem;">{value or "—"}</span>'


def badge_doc_link(url: str | None, icon: str, label: str) -> str:
    """Badge for document link (Borderô, Súmula). Active link or disabled."""
    if url:
        return (
            f'<a href="{url}" target="_blank" style="{_DOC}border:1px solid #1B2A4A;'
            f'color:#1B2A4A;text-decoration:none;"><span style="{_ICO}">{icon}</span> {label}</a>'
        )
    return (
        f'<span style="{_DOC}border:1px solid #dee2e6;color:#adb5bd;cursor:not-allowed;">'
        f'<span style="{_ICO}">{icon}</span> {label}</span>'
    )


def fmt_date_br(value) -> str:
    """Format date as dd/mm/yyyy."""
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return str(value)


# ── Main card builder ───────────────────────────────────────────────────────


def build_match_card_html(
    *,
    mon_name: str,
    date_str: str,
    stadium: str,
    home_name: str,
    away_name: str,
    competition: str,
    match_id: int,
    verified_badge: str = "",
    external_ref: str | None = None,
    bord_html: str = "",
    sum_html: str = "",
    gates_badge: str = "",
    tipo_badge: str = "",
) -> str:
    """Build the full match header card HTML (L1 + L2 + L3)."""

    # External ref pill (only shown if provided)
    ref_pill = ""
    if external_ref is not None:
        ref_pill = (
            '<span style="background:#e9ecef;color:#495057;padding:2px 8px;border-radius:8px;font-size:0.75rem;">'
            f'<span style="font-family:\'Material Symbols Rounded\';font-size:13px;vertical-align:middle;color:#6c757d;">link</span>'
            f' Ref: <strong>{external_ref or "—"}</strong></span>'
        )

    id_pill = (
        '<span style="background:#e9ecef;color:#495057;padding:2px 8px;border-radius:8px;font-size:0.75rem;">'
        f'<span style="font-family:\'Material Symbols Rounded\';font-size:13px;vertical-align:middle;color:#6c757d;">tag</span>'
        f' ID: <strong>{match_id}</strong></span>'
    )

    # Doc badges for L3
    docs_left = ""
    if bord_html or sum_html:
        parts = [x for x in (bord_html, sum_html) if x]
        docs_left = f'<div style="display:flex;gap:8px;align-items:center;">{"".join(parts)}</div>'

    return f"""
    <div style="
        border:1px solid #dee2e6;
        border-radius:12px;
        overflow:hidden;
        font-family:'Segoe UI', sans-serif;
    ">
      <!-- L1: Contexto principal -->
      <div style="
          background:#f8f9fa;
          padding:10px 18px;
          display:flex;
          gap:20px;
          flex-wrap:wrap;
          align-items:center;
          border-bottom:1px solid #e9ecef;
          font-size:0.82rem;
          color:#6c757d;
      ">
          <span><span style="font-family:'Material Symbols Rounded';font-size:15px;vertical-align:middle;color:#1B2A4A;">star</span> Monitorado: <strong style="color:#1B2A4A;">{mon_name}</strong></span>
          <span style="color:#dee2e6;">|</span>
          <span><span style="font-family:'Material Symbols Rounded';font-size:15px;vertical-align:middle;color:#6c757d;">calendar_today</span> <strong style="color:#343a40;">{date_str}</strong></span>
          <span style="color:#dee2e6;">|</span>
          <span><span style="font-family:'Material Symbols Rounded';font-size:15px;vertical-align:middle;color:#6c757d;">stadium</span> <strong style="color:#343a40;">{stadium or "—"}</strong></span>
          <span style="flex:1;"></span>{ref_pill}{id_pill}{verified_badge}
      </div>

      <!-- L2: Confronto -->
      <div style="
          background:linear-gradient(135deg, #1B2A4A 0%, #2d4278 50%, #C41E3A 100%);
          padding:20px 24px;
          display:flex;
          align-items:center;
          justify-content:space-between;
          gap:12px;
      ">
          <div style="flex:1;text-align:center;">
              <div style="font-size:0.72rem;color:rgba(255,255,255,0.6);text-transform:uppercase;letter-spacing:.08em;margin-bottom:4px;">Mandante</div>
              <div style="font-size:1.15rem;font-weight:700;color:#ffffff;line-height:1.2;">{home_name}</div>
          </div>
          <div style="text-align:center;flex-shrink:0;">
              <div style="font-size:0.68rem;color:rgba(255,255,255,0.7);text-transform:uppercase;letter-spacing:.1em;margin-bottom:6px;">{competition}</div>
              <div style="font-size:1.6rem;font-weight:900;color:#ffffff;letter-spacing:.05em;opacity:.9;">\u00d7</div>
          </div>
          <div style="flex:1;text-align:center;">
              <div style="font-size:0.72rem;color:rgba(255,255,255,0.6);text-transform:uppercase;letter-spacing:.08em;margin-bottom:4px;">Visitante</div>
              <div style="font-size:1.15rem;font-weight:700;color:#ffffff;line-height:1.2;">{away_name}</div>
          </div>
      </div>

      <!-- L3: Documentos + Operacional -->
      <div style="
          padding:8px 18px;
          display:flex;
          flex-wrap:wrap;
          align-items:center;
          background:#fdfdfd;
          font-size:0.78rem;
          color:#495057;
      ">
          {docs_left}
          <span style="flex:1;"></span>
          <div style="display:flex;gap:14px;align-items:center;">
              {gates_badge}
              <span style="color:#dee2e6;">|</span>
              {tipo_badge}
          </div>
      </div>
    </div>
    """
