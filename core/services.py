"""Core service layer for database operations (read-only)."""

import datetime
import streamlit as st
from sqlmodel import select, func

from core.database import get_session
from models.models import Club, Match, MatchLine


@st.cache_data(ttl=120)
def get_dashboard_stats() -> dict:
    with get_session() as session:
        total_matches = session.exec(select(func.count(Match.id))).one()
        total_lines = session.exec(select(func.count(MatchLine.id))).one()
        total_clubs = session.exec(select(func.count(Club.id))).one()
        matches_with_lines = session.exec(
            select(func.count(func.distinct(MatchLine.match_id)))
        ).one()

        current_year = datetime.date.today().year
        year_start = datetime.date(current_year, 1, 1)
        year_end = datetime.date(current_year, 12, 31)

        for_club = session.exec(select(Club).where(Club.short_name == "FOR")).first()
        for_club_id = for_club.id if for_club else None

        if for_club_id:
            _year_filter = [
                Match.monitored_club_id == for_club_id,
                Match.date >= year_start,
                Match.date <= year_end,
            ]
            total_gross = (
                session.exec(
                    select(func.sum(Match.gross_revenue)).where(*_year_filter)
                ).one()
                or 0
            )
            avg_net = (
                session.exec(
                    select(func.avg(Match.monitored_net_revenue)).where(*_year_filter)
                ).one()
                or 0
            )
            total_attendance = (
                session.exec(
                    select(func.sum(Match.attendance)).where(*_year_filter)
                ).one()
                or 0
            )
            avg_attendance = (
                session.exec(
                    select(func.avg(Match.attendance)).where(*_year_filter)
                ).one()
                or 0
            )
            total_members = (
                session.exec(
                    select(func.sum(Match.members)).where(*_year_filter)
                ).one()
                or 0
            )
            avg_members = (
                session.exec(
                    select(func.avg(Match.members)).where(*_year_filter)
                ).one()
                or 0
            )
            avg_ticket = (
                session.exec(
                    select(func.avg(Match.avg_ticket)).where(*_year_filter)
                ).one()
                or 0
            )
        else:
            (
                total_gross,
                avg_net,
                total_attendance,
                avg_attendance,
                total_members,
                avg_members,
                avg_ticket,
            ) = (0, 0, 0, 0, 0, 0, 0)

        verified_count = 0
        matches_with_lines_count = matches_with_lines

        return {
            "total_matches": total_matches,
            "total_lines": total_lines,
            "total_clubs": total_clubs,
            "matches_with_lines": matches_with_lines,
            "verified_count": verified_count,
            "for_stats": {
                "total_gross": total_gross,
                "avg_net": avg_net,
                "total_attendance": total_attendance,
                "avg_attendance": avg_attendance,
                "total_members": total_members,
                "avg_members": avg_members,
                "avg_ticket": avg_ticket,
            },
        }
