"""Shared HTML builders for borderô category tables and result cards."""

from decimal import Decimal

from ui.theme import COLORS, fmt_brl, fmt_num


def esc(text: str) -> str:
    """Escape text to prevent markdown interpretation inside st.markdown."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def val_opacity(val: float, max_val: float) -> str:
    """Return an opacity string (0.45–1.0) proportional to value magnitude."""
    if max_val <= 0:
        return "1.0"
    ratio = min(abs(val) / max_val, 1.0)
    return f"{0.45 + 0.55 * ratio:.2f}"


def build_category_table(
    lines: list[dict], categories: list[str], is_revenue: bool = False
) -> str:
    """Build an HTML div-based table for a category group (avoids markdown parsing issues)."""
    filtered = [l for l in lines if l["category"] in categories]
    if not filtered:
        return '<div style="padding:12px 18px;color:#6B7280;font-size:0.85rem;">Sem registros nesta categoria.</div>'

    subtotal_qty = 0
    subtotal_val = Decimal("0")
    vis_qty = 0
    vis_val = Decimal("0")
    man_qty = 0
    man_val = Decimal("0")
    val_color = COLORS["primary"] if is_revenue else COLORS["accent"]

    # Pre-compute max value for gradient
    all_vals = [abs(float(l["revenue"])) for l in filtered if l["revenue"]]
    max_val = max(all_vals) if all_vals else 1.0

    row_style = "display:flex;align-items:center;border-bottom:1px solid #f0f0f0;"

    rows_html = ""
    for l in filtered:
        qty = l["sold"] if l["sold"] else 0
        val = Decimal(str(l["revenue"])) if l["revenue"] else Decimal("0")
        subtotal_qty += qty
        subtotal_val += val
        is_vis = l.get("is_visitor_line", False)
        if is_vis:
            vis_qty += qty
            vis_val += val
        else:
            man_qty += qty
            man_val += val
        desc = esc(l["description"])

        # Visitor badge
        vis_badge = ""
        if is_vis and is_revenue:
            vis_badge = (
                '<span style="background:#fee2e2;color:#991b1b;padding:1px 7px;'
                "border-radius:10px;font-size:0.68rem;font-weight:600;margin-left:8px;"
                'letter-spacing:.02em;">VIS</span>'
            )

        opacity = val_opacity(float(val), max_val)

        rows_html += (
            f'<div style="{row_style}">'
            f'<div style="flex:1;padding:8px 14px;font-size:0.88rem;color:#374151;">{desc}{vis_badge}</div>'
            f'<div style="width:120px;padding:8px 14px;text-align:right;font-size:0.88rem;color:#374151;font-weight:500;opacity:{opacity};">{fmt_num(qty) if qty else "—"}</div>'
            f'<div style="width:160px;padding:8px 14px;text-align:right;font-size:0.88rem;color:{val_color};font-weight:600;opacity:{opacity};">{fmt_brl(val)}</div>'
            f"</div>"
        )

    subtotal_color = COLORS["primary"] if is_revenue else COLORS["accent"]
    subtotal_bg = "#EEF2F9" if is_revenue else "#fef2f2"

    header_html = (
        f'<div style="display:flex;align-items:center;border-bottom:2px solid {COLORS["border"]};">'
        f'<div style="flex:1;padding:10px 14px;font-size:0.78rem;text-transform:uppercase;letter-spacing:.04em;color:{COLORS["text_secondary"]};font-weight:600;">Descrição</div>'
        f'<div style="width:120px;padding:10px 14px;text-align:right;font-size:0.78rem;text-transform:uppercase;letter-spacing:.04em;color:{COLORS["text_secondary"]};font-weight:600;">Quantidade</div>'
        f'<div style="width:160px;padding:10px 14px;text-align:right;font-size:0.78rem;text-transform:uppercase;letter-spacing:.04em;color:{COLORS["text_secondary"]};font-weight:600;">Valor</div>'
        f"</div>"
    )

    # For INGRESSO: show Mandante / Visitante / Subtotal split
    subtotal_html = ""
    has_visitor = vis_val > 0 and is_revenue
    if has_visitor:
        sub_row = "display:flex;align-items:center;border-bottom:1px solid #e8e8e8;"
        subtotal_html += (
            f'<div style="{sub_row}background:#f0fdf4;">'
            f'<div style="flex:1;padding:8px 14px;font-size:0.85rem;font-weight:600;color:#166534;">Mandante</div>'
            f'<div style="width:120px;padding:8px 14px;text-align:right;font-size:0.85rem;font-weight:600;color:#166534;">{fmt_num(man_qty) if man_qty else "—"}</div>'
            f'<div style="width:160px;padding:8px 14px;text-align:right;font-size:0.85rem;font-weight:600;color:#166534;">{fmt_brl(man_val)}</div>'
            f"</div>"
            f'<div style="{sub_row}background:#fef2f2;">'
            f'<div style="flex:1;padding:8px 14px;font-size:0.85rem;font-weight:600;color:#991b1b;">Visitante</div>'
            f'<div style="width:120px;padding:8px 14px;text-align:right;font-size:0.85rem;font-weight:600;color:#991b1b;">{fmt_num(vis_qty) if vis_qty else "—"}</div>'
            f'<div style="width:160px;padding:8px 14px;text-align:right;font-size:0.85rem;font-weight:600;color:#991b1b;">{fmt_brl(vis_val)}</div>'
            f"</div>"
        )

    subtotal_html += (
        f'<div style="display:flex;align-items:center;background:{subtotal_bg};">'
        f'<div style="flex:1;padding:10px 14px;font-size:0.9rem;font-weight:700;color:{subtotal_color};">SUBTOTAL</div>'
        f'<div style="width:120px;padding:10px 14px;text-align:right;font-size:0.9rem;font-weight:700;color:{subtotal_color};">{fmt_num(subtotal_qty) if subtotal_qty else "—"}</div>'
        f'<div style="width:160px;padding:10px 14px;text-align:right;font-size:0.9rem;font-weight:700;color:{subtotal_color};">{fmt_brl(subtotal_val)}</div>'
        f"</div>"
    )

    return header_html + rows_html + subtotal_html


def build_section_header(label: str, tag_bg: str, tag_color: str, tipo: str) -> str:
    """Build a section header with colored category tag."""
    tipo_label = "RECEITA" if tipo == "receita" else "DESPESA"
    tipo_bg = "#dcfce7" if tipo == "receita" else "#fee2e2"
    tipo_color = "#166534" if tipo == "receita" else "#991b1b"

    return f"""
    <div style="
        display:flex;
        align-items:center;
        gap:12px;
        padding:12px 18px;
        border-radius:8px 8px 0 0;
        margin-top:20px;
        background:#f8f9fa;
        border:1px solid {COLORS["border"]};
        border-bottom:none;
    ">
        <span style="
            background:{tag_bg};color:{tag_color};
            padding:4px 12px;border-radius:6px;
            font-size:0.82rem;font-weight:700;
            letter-spacing:.02em;
        ">{label}</span>
        <span style="
            background:{tipo_bg};color:{tipo_color};
            padding:3px 10px;border-radius:12px;
            font-size:0.72rem;font-weight:600;
            text-transform:uppercase;letter-spacing:.04em;
        ">{tipo_label}</span>
    </div>
    """


def build_resultado_card(receita: Decimal, despesa: Decimal) -> str:
    """Build the final result card."""
    resultado = receita - despesa
    res_color = COLORS["success"] if resultado >= 0 else COLORS["error"]
    res_icon = "+" if resultado >= 0 else ""

    return f"""
    <div style="
        border:2px solid {COLORS["border"]};
        border-radius:12px;
        overflow:hidden;
        margin-top:24px;
        box-shadow:0 4px 12px rgba(0,0,0,0.08);
    ">
        <div style="
            display:flex;
            justify-content:space-between;
            padding:14px 24px;
            background:#f8f9fa;
            border-bottom:1px solid {COLORS["border"]};
        ">
            <span style="font-size:0.9rem;font-weight:600;color:{COLORS["primary"]};">
                Receita Total (Ingresso)
            </span>
            <span style="font-size:0.95rem;font-weight:700;color:{COLORS["primary"]};">
                {fmt_brl(receita)}
            </span>
        </div>
        <div style="
            display:flex;
            justify-content:space-between;
            padding:14px 24px;
            background:#fff;
            border-bottom:2px solid {COLORS["border"]};
        ">
            <span style="font-size:0.9rem;font-weight:600;color:{COLORS["accent"]};">
                Despesa Total (B1 a B5 + Descontos)
            </span>
            <span style="font-size:0.95rem;font-weight:700;color:{COLORS["accent"]};">
                {fmt_brl(despesa)}
            </span>
        </div>
        <div style="
            display:flex;
            justify-content:space-between;
            align-items:center;
            padding:18px 24px;
            background:linear-gradient(135deg, {res_color}08, {res_color}15);
        ">
            <span style="font-size:1rem;font-weight:800;color:{res_color};text-transform:uppercase;letter-spacing:.03em;">
                Resultado Líquido
            </span>
            <span style="font-size:1.3rem;font-weight:900;color:{res_color};">
                {res_icon}{fmt_brl(resultado)}
            </span>
        </div>
    </div>
    """
