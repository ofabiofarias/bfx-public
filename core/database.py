"""Database engine, session management (read-only public version)."""

import streamlit as st
from sqlmodel import Session, SQLModel, create_engine, select

from core.config import get_database_url, MONITORED_CLUBS
from models.models import Club, LineTag, Match, MatchLine


@st.cache_resource
def _get_engine(db_url: str):
    """Create and cache engine based on URL."""
    return create_engine(db_url, echo=False)


def get_engine():
    """Return the active engine for the current DB mode."""
    return _get_engine(get_database_url())


def create_db_and_tables():
    """Create all tables if they don't exist yet."""
    import os
    from core.config import LOCAL_DB_PATH
    os.makedirs(os.path.dirname(LOCAL_DB_PATH), exist_ok=True)
    SQLModel.metadata.create_all(get_engine())


def get_session() -> Session:
    """Return a new database session."""
    return Session(get_engine())


def seed_clubs():
    """Insert monitored clubs if they don't exist yet."""
    with get_session() as session:
        for club_data in MONITORED_CLUBS:
            existing = session.exec(
                select(Club).where(Club.short_name == club_data["short_name"])
            ).first()
            if not existing:
                session.add(Club(**club_data))
        session.commit()


@st.cache_data(ttl=300)
def get_distinct_stadiums() -> list[str]:
    """Return sorted list of distinct stadium names from matches."""
    with get_session() as session:
        results = session.exec(
            select(Match.stadium)
            .distinct()
            .where(Match.stadium != None, Match.stadium != "")
        ).all()
        return sorted([s for s in results if s])


@st.cache_data(ttl=300)
def get_all_clubs() -> list[Club]:
    """Return all clubs ordered by name."""
    with get_session() as session:
        return list(session.exec(select(Club).order_by(Club.name)).all())


@st.cache_data(ttl=300)
def get_all_clubs_dict() -> dict[int, Club]:
    """Return a dictionary mapping Club ID to Club object."""
    with get_session() as session:
        return {c.id: c for c in session.exec(select(Club)).all()}


@st.cache_data(ttl=300)
def get_distinct_competitions() -> list[str]:
    """Return sorted list of distinct competition names from matches."""
    with get_session() as session:
        results = session.exec(
            select(Match.competition)
            .distinct()
            .where(Match.competition != None, Match.competition != "")
        ).all()
        return sorted([c for c in results if c])


@st.cache_data(ttl=300)
def get_distinct_visitors() -> list[str]:
    """Return sorted list of distinct visitor (away) club names from matches."""
    with get_session() as session:
        away_ids = session.exec(select(Match.away_club_id).distinct()).all()
        if not away_ids:
            return []
        clubs = {c.id: c for c in session.exec(select(Club)).all()}
        names = set()
        for aid in away_ids:
            c = clubs.get(aid)
            if c and c.name:
                names.add(c.name)
        return sorted(names)


def init_db():
    """Create tables and seed initial data."""
    create_db_and_tables()
    seed_clubs()
