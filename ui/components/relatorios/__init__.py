"""Componentes de abas do módulo Relatórios."""

from ui.components.relatorios.tab_painel_geral import render as render_painel_geral
from ui.components.relatorios.tab_for_vs_cea import render as render_for_vs_cea
from ui.components.relatorios.tab_competicao import render as render_competicao
from ui.components.relatorios.tab_composicao import render as render_composicao
from ui.components.relatorios.tab_financeiro import render as render_financeiro
from ui.components.relatorios.tab_sazonalidade import render as render_sazonalidade
from ui.components.relatorios.tab_alertas import render as render_alertas

__all__ = [
    "render_painel_geral",
    "render_for_vs_cea",
    "render_competicao",
    "render_composicao",
    "render_financeiro",
    "render_sazonalidade",
    "render_alertas",
]
