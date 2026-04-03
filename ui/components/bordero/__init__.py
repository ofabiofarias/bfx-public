"""Borderô UI components."""

from ui.components.bordero.helpers import (
    build_category_table,
    build_resultado_card,
    build_section_header,
    esc,
    val_opacity,
)
from ui.components.bordero.tab_rubrica import render as render_rubrica

__all__ = [
    "build_category_table",
    "build_resultado_card",
    "build_section_header",
    "esc",
    "render_rubrica",
    "val_opacity",
]
