"""Sync engine: pull-only from Supabase cloud (read-only public version).

Egress-aware design:
  1. TTL gate — skip entirely if last pull is recent (default 6h)
  2. Cheap probe — COUNT/MAX before any full transfer
  3. Incremental pull — only rows beyond local watermarks
  4. Full pull only when local DB is empty or probe mismatch is large

Never writes to cloud.
"""

import json
import logging
import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from sqlmodel import Session, create_engine, func, select

from core.config import BASE_DIR, CLOUD_DATABASE_URL
from models.models import Club, LineTag, Match, MatchLine

logger = logging.getLogger(__name__)

_DATA_DIR = BASE_DIR / "data"
_SYNC_META = _DATA_DIR / ".sync_meta"
_SYNC_LOG = _DATA_DIR / ".sync_log"
_LOCAL_DB = _DATA_DIR / "bfx.db"
_MAX_PRE_SYNC_BACKUPS = 3

# TTL in seconds. Read-only consumer can be aggressive — user can force via button.
PULL_TTL_SECONDS = int(os.getenv("PULL_TTL_SECONDS", str(6 * 3600)))


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


# TTL gate


def _parse_ts(value) -> datetime | None:
    """Parse a timestamp from either datetime, ISO string, or 'YYYY-MM-DD HH:MM:SS.ffffff'."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace(" ", "T"))
    except (ValueError, TypeError):
        return None


def _age_seconds(iso_ts: str | None) -> float | None:
    ts = _parse_ts(iso_ts)
    if ts is None:
        return None
    try:
        return (datetime.now() - ts).total_seconds()
    except (ValueError, TypeError):
        return None


def _should_skip_by_ttl() -> bool:
    """Return True if the last successful pull is recent enough to skip."""
    if PULL_TTL_SECONDS <= 0:
        return False
    age = _age_seconds(_read_meta().get("last_pull_at"))
    return age is not None and age < PULL_TTL_SECONDS


# Local state (cheap watermark read)


def _local_state() -> dict:
    """Read local counts and watermarks directly via sqlite3 (no ORM)."""
    state = {
        "match_count": 0,
        "line_count": 0,
        "club_count": 0,
        "tag_count": 0,
        "max_match_updated_at": None,
        "max_match_id": 0,
        "max_line_id": 0,
    }
    if not _LOCAL_DB.exists():
        return state
    try:
        conn = sqlite3.connect(str(_LOCAL_DB))
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*), MAX(updated_at), MAX(id) FROM matches")
        row = cur.fetchone() or (0, None, 0)
        state["match_count"] = row[0] or 0
        state["max_match_updated_at"] = row[1]
        state["max_match_id"] = row[2] or 0
        cur.execute("SELECT COUNT(*), MAX(id) FROM match_lines")
        row = cur.fetchone() or (0, 0)
        state["line_count"] = row[0] or 0
        state["max_line_id"] = row[1] or 0
        cur.execute("SELECT COUNT(*) FROM clubs")
        state["club_count"] = (cur.fetchone() or (0,))[0] or 0
        cur.execute("SELECT COUNT(*) FROM line_tags")
        state["tag_count"] = (cur.fetchone() or (0,))[0] or 0
        conn.close()
    except Exception:
        pass
    return state


# Cloud probe (cheap — COUNT and MAX only)


def _probe_cloud(cloud: Session) -> dict:
    """Run cheap aggregate queries against cloud. Egress ≈ a few hundred bytes."""
    match_count = cloud.exec(select(func.count(Match.id))).one() or 0
    line_count = cloud.exec(select(func.count(MatchLine.id))).one() or 0
    club_count = cloud.exec(select(func.count(Club.id))).one() or 0
    tag_count = cloud.exec(select(func.count(LineTag.id))).one() or 0
    max_match_updated = cloud.exec(select(func.max(Match.updated_at))).one()
    max_match_id = cloud.exec(select(func.max(Match.id))).one() or 0
    max_line_id = cloud.exec(select(func.max(MatchLine.id))).one() or 0
    return {
        "match_count": match_count,
        "line_count": line_count,
        "club_count": club_count,
        "tag_count": tag_count,
        # Keep as datetime (or None) — _nothing_changed normalizes before compare.
        "max_match_updated_at": max_match_updated,
        "max_match_id": max_match_id,
        "max_line_id": max_line_id,
    }


def _nothing_changed(local: dict, cloud: dict) -> bool:
    """Decide if local already mirrors cloud based on probe result."""
    if local["match_count"] == 0:
        return False  # local empty → always pull
    # Counts must match exactly
    if (
        local["match_count"] != cloud["match_count"]
        or local["line_count"] != cloud["line_count"]
        or local["club_count"] != cloud["club_count"]
        or local["tag_count"] != cloud["tag_count"]
    ):
        return False
    # Watermarks must match
    if local["max_line_id"] != cloud["max_line_id"]:
        return False
    # Normalize timestamps (local from sqlite is 'YYYY-MM-DD HH:MM:SS.ffffff',
    # cloud from PG comes as datetime) before comparing.
    local_ts = _parse_ts(local.get("max_match_updated_at"))
    cloud_ts = _parse_ts(cloud.get("max_match_updated_at"))
    if local_ts != cloud_ts:
        return False
    return True


# Pre-sync backup (only for full pull)


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


# Row fetchers — column-explicit, return tuples (no ORM objects)


# Column lists used for both cloud SELECT and local INSERT
_CLUB_COLS = (Club.id, Club.name, Club.short_name, Club.monitored)
_TAG_COLS = (LineTag.id, LineTag.name, LineTag.group)
_MATCH_COLS = (
    Match.id, Match.external_ref, Match.competition, Match.date, Match.stadium,
    Match.home_club_id, Match.away_club_id, Match.monitored_club_id, Match.monitored_as,
    Match.attendance, Match.members, Match.complimentary, Match.free, Match.ingressos,
    Match.gross_revenue, Match.net_revenue, Match.monitored_net_revenue, Match.avg_ticket,
    Match.gates, Match.match_type,
    Match.bordero_url, Match.sumula_url, Match.pdf_filename,
    Match.created_at, Match.updated_at,
    Match.is_info_verified, Match.is_details_verified,
)
_LINE_COLS = (
    MatchLine.id, MatchLine.match_id, MatchLine.stadium, MatchLine.club,
    MatchLine.category, MatchLine.description,
    MatchLine.available, MatchLine.returned, MatchLine.sold,
    MatchLine.price, MatchLine.revenue,
    MatchLine.is_visitor_line, MatchLine.tag_id,
)


def _club_tuple(r) -> tuple:
    return (r[0], r[1], r[2], int(bool(r[3])))


def _tag_tuple(r) -> tuple:
    return (r[0], r[1], r[2])


def _match_tuple(r) -> tuple:
    monitored_as = r[8]
    monitored_as_val = (
        monitored_as.value if hasattr(monitored_as, "value") else str(monitored_as)
    )
    return (
        r[0], r[1], r[2], str(r[3]), r[4],
        r[5], r[6], r[7], monitored_as_val,
        r[9] or 0, r[10] or 0, r[11] or 0, r[12] or 0, r[13] or 0,
        str(r[14]) if r[14] is not None else "0",
        str(r[15]) if r[15] is not None else "0",
        str(r[16]) if r[16] is not None else "0",
        str(r[17]) if r[17] is not None else "0",
        r[18], r[19],
        r[20], r[21], r[22],
        str(r[23]) if r[23] else None,
        str(r[24]) if r[24] else None,
        int(bool(r[25])), int(bool(r[26])),
    )


def _line_tuple(r) -> tuple:
    return (
        r[0], r[1], r[2], r[3],
        r[4], r[5],
        r[6], r[7], r[8],
        str(r[9]) if r[9] is not None else None,
        str(r[10]) if r[10] is not None else None,
        int(bool(r[11])), r[12],
    )


# Writers — apply fetched rows into local SQLite


def _apply_rows(cur: sqlite3.Cursor, table: str, rows: list[tuple]):
    if not rows:
        return
    if table == "clubs":
        cur.executemany(
            "INSERT OR REPLACE INTO clubs VALUES (?,?,?,?)",
            [_club_tuple(r) for r in rows],
        )
    elif table == "line_tags":
        cur.executemany(
            'INSERT OR REPLACE INTO line_tags VALUES (?,?,?)',
            [_tag_tuple(r) for r in rows],
        )
    elif table == "matches":
        cur.executemany(
            "INSERT OR REPLACE INTO matches VALUES "
            "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            [_match_tuple(r) for r in rows],
        )
    elif table == "match_lines":
        cur.executemany(
            "INSERT OR REPLACE INTO match_lines VALUES "
            "(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            [_line_tuple(r) for r in rows],
        )


# Full pull (first time, or when drift is large)


def _full_pull(cloud: Session) -> dict:
    """Fetch all rows from cloud and rewrite local SQLite. Egress-heavy."""
    clubs = cloud.exec(select(*_CLUB_COLS)).all()
    tags = cloud.exec(select(*_TAG_COLS)).all()
    matches = cloud.exec(select(*_MATCH_COLS)).all()
    lines = cloud.exec(select(*_LINE_COLS)).all()

    local_count = _local_state()["match_count"]
    cloud_count = len(matches)

    # Safety: abort on suspicious cloud emptiness
    if local_count > 0 and cloud_count == 0:
        raise RuntimeError(
            f"cloud has 0 matches but local has {local_count} — aborting for safety"
        )
    if local_count > 0 and cloud_count < local_count * 0.5:
        raise RuntimeError(
            f"cloud has {cloud_count} matches vs local {local_count} (>50% drop) — "
            "aborting for safety"
        )

    _backup_before_sync()
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_LOCAL_DB))
    try:
        cur = conn.cursor()
        _ensure_local_schema(cur)

        _apply_rows(cur, "clubs", clubs)
        if clubs:
            ids = [c[0] for c in clubs]
            cur.execute(
                f"DELETE FROM clubs WHERE id NOT IN ({','.join('?' * len(ids))})",
                ids,
            )

        _apply_rows(cur, "line_tags", tags)
        if tags:
            ids = [t[0] for t in tags]
            cur.execute(
                f"DELETE FROM line_tags WHERE id NOT IN ({','.join('?' * len(ids))})",
                ids,
            )

        _apply_rows(cur, "matches", matches)
        if matches:
            ids = [m[0] for m in matches]
            # Chunk to avoid SQLite variable limit on very large sets
            chunk = 500
            cur.execute(
                "CREATE TEMP TABLE IF NOT EXISTS _keep_match_ids (id INTEGER PRIMARY KEY)"
            )
            cur.execute("DELETE FROM _keep_match_ids")
            for i in range(0, len(ids), chunk):
                batch = ids[i:i + chunk]
                cur.executemany(
                    "INSERT INTO _keep_match_ids VALUES (?)",
                    [(x,) for x in batch],
                )
            cur.execute(
                "DELETE FROM matches WHERE id NOT IN (SELECT id FROM _keep_match_ids)"
            )
            cur.execute("DROP TABLE _keep_match_ids")
        else:
            cur.execute("DELETE FROM matches")

        _apply_rows(cur, "match_lines", lines)
        if lines:
            ids = [ln[0] for ln in lines]
            chunk = 500
            cur.execute(
                "CREATE TEMP TABLE IF NOT EXISTS _keep_line_ids (id INTEGER PRIMARY KEY)"
            )
            cur.execute("DELETE FROM _keep_line_ids")
            for i in range(0, len(ids), chunk):
                batch = ids[i:i + chunk]
                cur.executemany(
                    "INSERT INTO _keep_line_ids VALUES (?)",
                    [(x,) for x in batch],
                )
            cur.execute(
                "DELETE FROM match_lines WHERE id NOT IN (SELECT id FROM _keep_line_ids)"
            )
            cur.execute("DROP TABLE _keep_line_ids")
        else:
            cur.execute("DELETE FROM match_lines")

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return {
        "clubs": len(clubs),
        "line_tags": len(tags),
        "matches": len(matches),
        "match_lines": len(lines),
        "mode": "full",
    }


# Incremental pull (cheap — only rows beyond local watermarks)


def _incremental_pull(cloud: Session, local: dict) -> dict:
    """Fetch only rows newer than local watermarks.

    - matches: WHERE updated_at > local max (catches inserts + updates)
    - match_lines: WHERE id > local max (append-only in practice)
    - clubs / line_tags: small dimension tables, re-fetch fully (few KB)
    """
    # Small dimension tables — cheap to refresh fully (a few bytes)
    clubs = cloud.exec(select(*_CLUB_COLS)).all()
    tags = cloud.exec(select(*_TAG_COLS)).all()

    # Matches — delta by updated_at
    max_updated_ts = _parse_ts(local.get("max_match_updated_at"))
    match_q = select(*_MATCH_COLS)
    if max_updated_ts is not None:
        match_q = match_q.where(Match.updated_at > max_updated_ts)
    matches = cloud.exec(match_q).all()

    # MatchLines — delta by id (append-only). We also re-fetch lines for any
    # match whose updated_at changed, to capture edits to existing lines.
    max_line_id = local.get("max_line_id", 0)
    new_lines = cloud.exec(
        select(*_LINE_COLS).where(MatchLine.id > max_line_id)
    ).all()

    updated_match_ids = [m[0] for m in matches]
    edited_lines: list = []
    if updated_match_ids:
        # Chunk to avoid hitting parameter limits on very large deltas
        chunk = 200
        for i in range(0, len(updated_match_ids), chunk):
            batch = updated_match_ids[i:i + chunk]
            edited_lines.extend(
                cloud.exec(
                    select(*_LINE_COLS).where(MatchLine.match_id.in_(batch))
                ).all()
            )

    # Merge line sets by id (edited takes precedence)
    line_map: dict = {}
    for r in new_lines:
        line_map[r[0]] = r
    for r in edited_lines:
        line_map[r[0]] = r
    lines = list(line_map.values())

    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_LOCAL_DB))
    try:
        cur = conn.cursor()
        _ensure_local_schema(cur)

        # Dimension tables: upsert + prune removed
        _apply_rows(cur, "clubs", clubs)
        if clubs:
            ids = [c[0] for c in clubs]
            cur.execute(
                f"DELETE FROM clubs WHERE id NOT IN ({','.join('?' * len(ids))})",
                ids,
            )
        _apply_rows(cur, "line_tags", tags)
        if tags:
            ids = [t[0] for t in tags]
            cur.execute(
                f"DELETE FROM line_tags WHERE id NOT IN ({','.join('?' * len(ids))})",
                ids,
            )

        # Matches/lines: only upsert the delta (no prune — safety-preserving)
        _apply_rows(cur, "matches", matches)
        _apply_rows(cur, "match_lines", lines)

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return {
        "clubs": len(clubs),
        "line_tags": len(tags),
        "matches": len(matches),
        "match_lines": len(lines),
        "mode": "incremental",
    }


# Public entry point


def pull_from_cloud(*, force: bool = False) -> dict:
    """Pull data from Supabase into local SQLite.

    Egress stages:
      1. TTL gate — zero bytes if recent
      2. Probe — a few hundred bytes
      3. Incremental or full pull — only when delta exists

    Args:
        force: bypass the TTL gate (but still uses probe to avoid useless pulls).
    """
    if not CLOUD_DATABASE_URL:
        _append_log("PULL SKIP  no cloud URL configured")
        return {"status": "no_cloud", "message": "Cloud URL não configurada"}

    # Stage 1 — TTL gate
    if not force and _should_skip_by_ttl():
        age = _age_seconds(_read_meta().get("last_pull_at")) or 0
        _append_log(f"PULL SKIP  ttl ({int(age)}s < {PULL_TTL_SECONDS}s)")
        return {
            "status": "skipped",
            "reason": "ttl",
            "message": f"Pull recente ({int(age/60)}min atrás) — TTL não expirou",
        }

    cloud_engine = _get_cloud_engine()
    if cloud_engine is None:
        return {"status": "no_cloud", "message": "Cloud URL não configurada"}

    try:
        with Session(cloud_engine) as cloud:
            # Stage 2 — probe
            cloud_state = _probe_cloud(cloud)
            local = _local_state()

            if _nothing_changed(local, cloud_state):
                meta = _read_meta()
                meta["last_pull_at"] = datetime.now().isoformat()
                meta["last_error"] = None
                meta["stats"] = {
                    "clubs": cloud_state["club_count"],
                    "line_tags": cloud_state["tag_count"],
                    "matches": cloud_state["match_count"],
                    "match_lines": cloud_state["line_count"],
                }
                _write_meta(meta)
                _append_log("PULL OK  probe match (no transfer)")
                cloud_engine.dispose()
                return {
                    "status": "ok",
                    "mode": "noop",
                    "stats": meta["stats"],
                }

            # Stage 3 — full or incremental
            local_empty = local["match_count"] == 0
            if local_empty:
                stats = _full_pull(cloud)
            else:
                # Drift too large → safer to do a full pull
                match_drift = abs(
                    cloud_state["match_count"] - local["match_count"]
                )
                line_drift = abs(
                    cloud_state["line_count"] - local["line_count"]
                )
                if match_drift > max(50, local["match_count"] * 0.2):
                    stats = _full_pull(cloud)
                elif line_drift > max(500, local["line_count"] * 0.2):
                    stats = _full_pull(cloud)
                else:
                    stats = _incremental_pull(cloud, local)

        meta = _read_meta()
        meta["last_pull_at"] = datetime.now().isoformat()
        meta["last_error"] = None
        meta["stats"] = {
            "clubs": cloud_state["club_count"],
            "line_tags": cloud_state["tag_count"],
            "matches": cloud_state["match_count"],
            "match_lines": cloud_state["line_count"],
        }
        _write_meta(meta)
        _append_log(
            f"PULL OK  mode={stats.get('mode')}  "
            f"matches={stats.get('matches')} lines={stats.get('match_lines')}"
        )
        cloud_engine.dispose()
        return {"status": "ok", "mode": stats.get("mode"), "stats": meta["stats"]}

    except Exception as e:
        _append_log(f"PULL FAIL  {type(e).__name__}: {e}")
        meta = _read_meta()
        meta["last_error"] = f"Pull failed: {e}"
        _write_meta(meta)
        try:
            cloud_engine.dispose()
        except Exception:
            pass
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
