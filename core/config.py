"""Configuracoes globais do bfx-public (read-only)."""

import os
from pathlib import Path
from urllib.parse import urlparse, urlunparse, quote_plus

from dotenv import load_dotenv

load_dotenv()

# --- Database ---
_raw_url = os.getenv("DATABASE_URL", "")
_db_password = os.getenv("DB_PASSWORD", "")

# --- Cloud URL (Supabase) ---
if _raw_url and _db_password:
    try:
        parsed = urlparse(_raw_url)
        username = parsed.username or ""
        host = parsed.hostname or ""
        port = f":{parsed.port}" if parsed.port else ""
        netloc = f"{username}:{quote_plus(_db_password)}@{host}{port}"
        CLOUD_DATABASE_URL = urlunparse(parsed._replace(netloc=netloc))
    except Exception:
        CLOUD_DATABASE_URL = _raw_url
elif _raw_url:
    CLOUD_DATABASE_URL = _raw_url
else:
    CLOUD_DATABASE_URL = ""

# --- Local-first: app sempre usa SQLite, cloud é sync ---
BASE_DIR = Path(__file__).parent.parent
LOCAL_DB_PATH = str(BASE_DIR / "data" / "bfx.db")


def get_database_url() -> str:
    """Retorna a URL do banco local (SQLite). Sempre local-first."""
    return f"sqlite:///{LOCAL_DB_PATH}"


DATABASE_URL = get_database_url()

# Clubes monitorados iniciais
MONITORED_CLUBS = [
    {"name": "Fortaleza EC", "short_name": "FOR", "monitored": True},
    {"name": "Ceará SC", "short_name": "CEA", "monitored": True},
]
