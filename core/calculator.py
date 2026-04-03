"""Calculated fields for match data.

Regras de cálculo:
    Público  = Público Total (do PDF) - Gratuidades
    Ingressos = Público - Sócios - Cortesias
    Ticket Médio = Renda Bruta / Ingressos
"""

from decimal import Decimal, ROUND_HALF_UP


def calc_publico(attendance: int, free: int) -> int:
    """Calculate adjusted público: total attendance minus gratuidades."""
    return max(0, attendance - free)


def calc_ingressos(publico: int, members: int, complimentary: int) -> int:
    """Calculate ingressos: público (já ajustado) minus sócios and cortesias."""
    return max(0, publico - members - complimentary)


def calc_avg_ticket(gross_revenue: Decimal, ingressos: int) -> Decimal:
    """Calculate average ticket price: gross_revenue / ingressos."""
    if ingressos <= 0:
        return Decimal("0")
    return (gross_revenue / Decimal(ingressos)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
