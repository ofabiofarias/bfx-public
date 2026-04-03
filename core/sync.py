"""Sync engine: pull-only from Supabase cloud (read-only public version).

Only pulls data from cloud to local SQLite. No push operations.
"""

import json
import logging
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from sqlmodel import Session, create_engine, select, text

from core.config import BASE_DIR, CLOUD_DATABASE_URL
from models.models import Club, LineTag, Match, MatchLine

logger = logging.getLogger(__name__)

_DATA_DIR = BASE_DIR / "data"
_SYNC_META = _DATA_DIR / ".sync_meta"
_SYNC_LOG = _DATA_DIR / ".sync_log"
_LOCAL_DB = _DATA_DIR / "bfx.db"
_MAX_PRE_SYNC_BACKUPS = 3


# Sync metadata


def _read_meta() -> dict:
    if _SYNC_META.exists():
        try:
            return json.loads(_SYNC_META.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _write_meta(meta: dict):
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    _SYNC_META.write_text(json.dumps(meta, indent=2, default=str))


def _append_log(message: str):
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(_SYNC_LOG, "a", encoding="utf-8") as f:
        f.write(f"{ts}  {message}\n")


# Cloud engine


def _get_cloud_engine():
    if not CLOUD_DATABASE_URL:
        return None
    return create_engine(
        CLOUD_DATABASE_URL,
        echo=False,
        pool_size=2,
        max_overflow=1,
        pool_pre_ping=True,
        pool_recycle=300,
    )


# Pre-sync backup


def _backup_before_sync() -> Path | None:
    if not _LOCAL_DB.exists():
        return None
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    backup_path = _DATA_DIR / f"pre_sync_{ts}.db"
    shutil.copy2(str(_LOCAL_DB), str(backup_path))
    _rotate_pre_sync_backups()
    return backup_path


def _rotate_pre_sync_backups():
    backups = sorted(_DATA_DIR.glob("pre_sync_*.db"), reverse=True)
    for old in backups[_MAX_PRE_SYNC_BACKUPS:]:
        old.unlink(missing_ok=True)


# PULL: cloud -> local


def pull_from_cloud() -> dict:
    """Pull all data from Supabase into local SQLite."""
    if not CLOUD_DATABASE_URL:
        _append_log("PULL SKIP  no cloud URL configured")
        return {"status": "no_cloud", "message": "Cloud URL não configurada"}

    cloud_engine = _get_cloud_engine()
    if cloud_engine is None:
        return {"status": "no_cloud", "message": "Cloud URL não configurada"}

    backup_path = _backup_before_sync()

    try:
        with Session(cloud_engine) as cloud:
            cloud_clubs = cloud.exec(select(Club)).all()
            cloud_tags = cloud.exec(select(LineTag)).all()
            cloud_matches = cloud.exec(select(Match)).all()
            cloud_lines = cloud.exec(select(MatchLine)).all()

        local_count = _count_local_matches()
        cloud_count = len(cloud_matches)
        if local_count > 0 and cloud_count == 0:
            msg = (
                f"PULL ABORT  cloud has 0 matches but local has {local_count}. "
                "Possible cloud corruption — aborting for safety."
            )
            _append_log(msg)
            return {"status": "abort", "message": msg}

        if local_count > 0 and cloud_count < local_count * 0.5:
            msg = (
                f"PULL ABORT  cloud has {cloud_count} matches vs local {local_count} "
                "(>50% drop). Aborting for safety."
            )
            _append_log(msg)
            return {"status": "abort", "message": msg}

        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(_LOCAL_DB))
        cur = conn.cursor()

        _ensure_local_schema(cur)

        try:
            cloud_club_ids = {c.id for c in cloud_clubs}
            for c in cloud_clubs:
                cur.execute(
                    "INSERT OR REPLACE INTO clubs VALUES (?,?,?,?)",
                    (c.id, c.name, c.short_name, int(c.monitored)),
                )
            cur.execute(
                f"DELETE FROM clubs WHERE id NOT IN ({','.join('?' * len(cloud_club_ids))})",
                list(cloud_club_ids),
            ) if cloud_club_ids else None

            cloud_tag_ids = {t.id for t in cloud_tags}
            for t in cloud_tags:
                cur.execute(
                    'INSERT OR REPLACE INTO line_tags VALUES (?,?,?)',
                    (t.id, t.name, t.group),
                )
            if cloud_tag_ids:
                cur.execute(
                    f"DELETE FROM line_tags WHERE id NOT IN ({','.join('?' * len(cloud_tag_ids))})",
                    list(cloud_tag_ids),
                )

            cloud_match_ids = {m.id for m in cloud_matches}
            for m in cloud_matches:
                cur.execute(
                    "INSERT OR REPLACE INTO matches VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        m.id, m.external_ref, m.competition, str(m.date), m.stadium,
                        m.home_club_id, m.away_club_id, m.monitored_club_id,
                        m.monitored_as.value if hasattr(m.monitored_as, "value") else str(m.monitored_as),
                        m.attendance, m.members, m.complimentary, m.free, m.ingressos,
                        str(m.gross_revenue), str(m.net_revenue), str(m.monitored_net_revenue),
                        str(m.avg_ticket), m.gates, m.match_type,
                        m.bordero_url, m.sumula_url, m.pdf_filename,
                        str(m.created_at) if m.created_at else None,
                        str(m.updated_at) if m.updated_at else None,
                        int(m.is_info_verified), int(m.is_details_verified),
                    ),
                )
            if cloud_match_ids:
                cur.execute(
                    f"DELETE FROM matches WHERE id NOT IN ({','.join('?' * len(cloud_match_ids))})",
                    list(cloud_match_ids),
                )
            else:
                cur.execute("DELETE FROM matches")

            cloud_line_ids = {ln.id for ln in cloud_lines}
            for ln in cloud_lines:
                cur.execute(
                    "INSERT OR REPLACE INTO match_lines VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        ln.id, ln.match_id, ln.stadium, ln.club,
                        ln.category, ln.description,
                        ln.available, ln.returned, ln.sold,
                        str(ln.price) if ln.price is not None else None,
                        str(ln.revenue) if ln.revenue is not None else None,
                        int(ln.is_visitor_line), ln.tag_id,
                    ),
                )
            if cloud_line_ids:
                cur.execute(
                    f"DELETE FROM match_lines WHERE id NOT IN ({','.join('?' * len(cloud_line_ids))})",
                    list(cloud_line_ids),
                )
            else:
                cur.execute("DELETE FROM match_lines")

            conn.commit()

        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

        stats = {
            "clubs": len(cloud_clubs),
            "line_tags": len(cloud_tags),
            "matches": len(cloud_matches),
            "match_lines": len(cloud_lines),
        }
        meta = _read_meta()
        meta["last_pull_at"] = datetime.now().isoformat()
        meta["last_error"] = None
        meta["stats"] = stats
        _write_meta(meta)

        _append_log(
            f"PULL OK  clubs={stats['clubs']} tags={stats['line_tags']} "
            f"matches={stats['matches']} lines={stats['match_lines']}"
        )

        cloud_engine.dispose()
        return {"status": "ok", "stats": stats}

    except Exception as e:
        _append_log(f"PULL FAIL  {type(e).__name__}: {e}")
        meta = _read_meta()
        meta["last_error"] = f"Pull failed: {e}"
        _write_meta(meta)
        return {"status": "error", "message": str(e)}


# Sync status for sidebar


def get_sync_status() -> dict:
    """Return sync status for sidebar display."""
    meta = _read_meta()

    if not CLOUD_DATABASE_URL:
        return {
            "state": "offline",
            "last_pull": None,
            "message": "Sem cloud configurada",
        }

    if meta.get("last_error"):
        return {
            "state": "error",
            "last_pull": meta.get("last_pull_at"),
            "message": meta["last_error"],
        }

    if meta.get("last_pull_at"):
        return {
            "state": "synced",
            "last_pull": meta.get("last_pull_at"),
            "message": "Sincronizado",
        }

    return {
        "state": "unknown",
        "last_pull": None,
        "message": "Nunca sincronizado",
    }


# Helpers


def _count_local_matches() -> int:
    if not _LOCAL_DB.exists():
        return 0
    try:
        conn = sqlite3.connect(str(_LOCAL_DB))
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM matches")
        count = cur.fetchone()[0]
        conn.close()
        return count
    except Exception:
        return 0


def _ensure_local_schema(cur: sqlite3.Cursor):
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS clubs (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            short_name TEXT NOT NULL UNIQUE,
            monitored INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS line_tags (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            "group" TEXT
        );

        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY,
            external_ref TEXT,
            competition TEXT NOT NULL,
            date TEXT NOT NULL,
            stadium TEXT NOT NULL,
            home_club_id INTEGER NOT NULL,
            away_club_id INTEGER NOT NULL,
            monitored_club_id INTEGER NOT NULL,
            monitored_as TEXT NOT NULL,
            attendance INTEGER NOT NULL DEFAULT 0,
            members INTEGER NOT NULL DEFAULT 0,
            complimentary INTEGER NOT NULL DEFAULT 0,
            free INTEGER NOT NULL DEFAULT 0,
            ingressos INTEGER NOT NULL DEFAULT 0,
            gross_revenue TEXT NOT NULL DEFAULT '0',
            net_revenue TEXT NOT NULL DEFAULT '0',
            monitored_net_revenue TEXT NOT NULL DEFAULT '0',
            avg_ticket TEXT NOT NULL DEFAULT '0',
            gates TEXT,
            match_type TEXT,
            bordero_url TEXT,
            sumula_url TEXT,
            pdf_filename TEXT,
            created_at TEXT,
            updated_at TEXT,
            is_info_verified INTEGER NOT NULL DEFAULT 0,
            is_details_verified INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS match_lines (
            id INTEGER PRIMARY KEY,
            match_id INTEGER NOT NULL,
            stadium TEXT,
            club TEXT,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            available INTEGER,
            returned INTEGER,
            sold INTEGER,
            price TEXT,
            revenue TEXT,
            is_visitor_line INTEGER NOT NULL DEFAULT 0,
            tag_id INTEGER
        );
    """)
