"""Service layer for match queries (read-only public version)."""

from decimal import Decimal

from sqlmodel import select, func

from core.database import get_session, get_all_clubs_dict
from models.models import Club, Match, MatchLine


# ── Club helpers ─────────────────────────────────────────────────────────────


def load_monitored_clubs() -> dict[str, Club]:
    """Return monitored clubs keyed by short_name."""
    with get_session() as session:
        clubs = session.exec(select(Club).where(Club.monitored == True)).all()  # noqa: E712
        return {c.short_name: c for c in clubs}


# ── Match queries ────────────────────────────────────────────────────────────


def load_match_detail(match_id: int):
    """Return (Match, list[MatchLine]) for a given match ID."""
    with get_session() as session:
        match = session.get(Match, match_id)
        if not match:
            return None, []
        lines = list(
            session.exec(select(MatchLine).where(MatchLine.match_id == match_id)).all()
        )
        return match, lines


def load_match_lines(match_id: int) -> list[dict]:
    """Load all MatchLine records for a match as dicts."""
    with get_session() as session:
        lines = session.exec(
            select(MatchLine).where(MatchLine.match_id == match_id)
        ).all()
        return [
            {
                "category": l.category,
                "description": l.description,
                "sold": l.sold,
                "revenue": float(l.revenue) if l.revenue else 0.0,
                "price": float(l.price) if l.price else 0.0,
                "is_visitor_line": l.is_visitor_line,
            }
            for l in lines
        ]


# ── Filtered queries ────────────────────────────────────────────────────────


def load_filtered_matches(
    club_id, competition, adversario, date_from, date_to, stadium=None
) -> list[dict]:
    """Load matches that have borderô lines, with filters applied."""
    with get_session() as session:
        has_lines = select(MatchLine.match_id).distinct().subquery()
        query = select(Match).where(Match.id.in_(select(has_lines.c.match_id)))
        if club_id:
            query = query.where(Match.monitored_club_id == club_id)
        if competition:
            query = query.where(Match.competition == competition)
        if stadium:
            query = query.where(Match.stadium == stadium)
        if adversario:
            adv_club = session.exec(select(Club).where(Club.name == adversario)).first()
            if adv_club:
                query = query.where(
                    (Match.away_club_id == adv_club.id)
                    | (Match.home_club_id == adv_club.id)
                )
        query = query.where(
            Match.date >= str(date_from),
            Match.date <= str(date_to),
        )
        query = query.order_by(Match.date.asc())
        matches = session.exec(query).all()

        clubs = get_all_clubs_dict()
        results = []
        for m in matches:
            mon = clubs.get(m.monitored_club_id)
            home = clubs.get(m.home_club_id)
            away = clubs.get(m.away_club_id)
            results.append(
                {
                    "id": m.id,
                    "date": m.date,
                    "competition": m.competition,
                    "stadium": m.stadium,
                    "home_name": home.name if home else "?",
                    "away_name": away.name if away else "?",
                    "mon_short": mon.short_name if mon else "?",
                    "mon_name": mon.name if mon else "?",
                    "attendance": m.attendance,
                    "gross_revenue": m.gross_revenue,
                    "net_revenue": m.net_revenue,
                    "bordero_url": m.bordero_url,
                    "is_info_verified": m.is_info_verified,
                    "is_details_verified": m.is_details_verified,
                    "monitored_as": m.monitored_as,
                    "gates": m.gates,
                    "match_type": m.match_type,
                }
            )
        return results


# ── Aggregations ─────────────────────────────────────────────────────────────


def aggregate_totals(matches: list[dict]) -> dict:
    """Aggregate financial totals from a list of match dicts."""
    total_receita = Decimal("0")
    total_liquida = Decimal("0")
    count = len(matches)

    for m in matches:
        total_receita += Decimal(str(m["gross_revenue"]))
        total_liquida += Decimal(str(m["net_revenue"]))

    return {
        "count": count,
        "gross_revenue": total_receita,
        "net_revenue": total_liquida,
        "avg_gross": total_receita / count if count else Decimal("0"),
        "avg_net": total_liquida / count if count else Decimal("0"),
    }


def aggregate_lines_totals(matches: list[dict]) -> dict:
    """Aggregate line-level totals (ingresso/despesa) across matches."""
    total_ingresso = Decimal("0")
    total_despesa = Decimal("0")

    with get_session() as session:
        match_ids = [m["id"] for m in matches]
        if not match_ids:
            return {
                "ingresso": Decimal("0"),
                "despesa": Decimal("0"),
                "resultado": Decimal("0"),
            }

        lines = session.exec(
            select(MatchLine).where(MatchLine.match_id.in_(match_ids))
        ).all()

        for l in lines:
            rev = Decimal(str(l.revenue)) if l.revenue else Decimal("0")
            if l.category == "INGRESSO":
                total_ingresso += rev
            elif l.category != "DESCONTOS":
                total_despesa += rev

    return {
        "ingresso": total_ingresso,
        "despesa": total_despesa,
        "resultado": total_ingresso - total_despesa,
    }
