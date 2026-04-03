"""SQLModel models for BFX."""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class MonitoredAs(str, Enum):
    home = "home"
    away = "away"


class Club(SQLModel, table=True):
    __tablename__ = "clubs"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    short_name: str = Field(max_length=10, unique=True)
    monitored: bool = Field(default=False)

    home_matches: list["Match"] = Relationship(
        back_populates="home_club",
        sa_relationship_kwargs={"foreign_keys": "Match.home_club_id"},
    )
    away_matches: list["Match"] = Relationship(
        back_populates="away_club",
        sa_relationship_kwargs={"foreign_keys": "Match.away_club_id"},
    )
    monitored_matches: list["Match"] = Relationship(
        back_populates="monitored_club",
        sa_relationship_kwargs={"foreign_keys": "Match.monitored_club_id"},
    )


class Match(SQLModel, table=True):
    __tablename__ = "matches"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    external_ref: Optional[str] = Field(default=None, index=True)
    competition: str
    date: date
    stadium: str

    home_club_id: int = Field(foreign_key="clubs.id")
    away_club_id: int = Field(foreign_key="clubs.id")
    monitored_club_id: int = Field(foreign_key="clubs.id")
    monitored_as: MonitoredAs

    attendance: int = Field(default=0)
    members: int = Field(default=0)
    complimentary: int = Field(default=0)
    free: int = Field(default=0)
    ingressos: int = Field(default=0)

    gross_revenue: Decimal = Field(
        default=Decimal("0"), max_digits=12, decimal_places=2
    )
    net_revenue: Decimal = Field(default=Decimal("0"), max_digits=12, decimal_places=2)
    monitored_net_revenue: Decimal = Field(
        default=Decimal("0"), max_digits=12, decimal_places=2
    )
    avg_ticket: Decimal = Field(default=Decimal("0"), max_digits=10, decimal_places=2)

    gates: Optional[str] = Field(default=None)
    match_type: Optional[str] = Field(default=None)
    bordero_url: Optional[str] = Field(default=None)
    sumula_url: Optional[str] = Field(default=None)
    pdf_filename: Optional[str] = Field(default=None)

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Verification Flags
    is_info_verified: bool = Field(default=False)
    is_details_verified: bool = Field(default=False)

    # Relationships
    home_club: Optional[Club] = Relationship(
        back_populates="home_matches",
        sa_relationship_kwargs={"foreign_keys": "[Match.home_club_id]"},
    )
    away_club: Optional[Club] = Relationship(
        back_populates="away_matches",
        sa_relationship_kwargs={"foreign_keys": "[Match.away_club_id]"},
    )
    monitored_club: Optional[Club] = Relationship(
        back_populates="monitored_matches",
        sa_relationship_kwargs={"foreign_keys": "[Match.monitored_club_id]"},
    )
    lines: list["MatchLine"] = Relationship(back_populates="match")


class LineTag(SQLModel, table=True):
    """Rubrica: normalized tag for grouping MatchLine descriptions."""

    __tablename__ = "line_tags"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    group: Optional[str] = Field(default=None)

    lines: list["MatchLine"] = Relationship(back_populates="tag")


class MatchLine(SQLModel, table=True):
    __tablename__ = "match_lines"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    match_id: int = Field(foreign_key="matches.id", index=True)
    stadium: Optional[str] = Field(default=None)
    club: Optional[str] = Field(default=None)
    category: str
    description: str
    available: Optional[int] = Field(default=None)
    returned: Optional[int] = Field(default=None)
    sold: Optional[int] = Field(default=None)
    price: Optional[Decimal] = Field(default=None, max_digits=10, decimal_places=2)
    revenue: Optional[Decimal] = Field(default=None, max_digits=12, decimal_places=2)
    is_visitor_line: bool = Field(default=False)
    tag_id: Optional[int] = Field(default=None, foreign_key="line_tags.id", index=True)

    match: Optional[Match] = Relationship(back_populates="lines")
    tag: Optional[LineTag] = Relationship(back_populates="lines")
