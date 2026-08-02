"""Web version settings -- env vars only (Render env vars in production, a
local web/.env for dev, loaded via python-dotenv in main.py)."""
import os
from typing import Optional


def get_api_key() -> Optional[str]:
    key = os.environ.get("GROQ_API_KEY")
    return key.strip() if key else None


def get_database_url() -> str:
    """A Neon (or any Postgres) connection string. Required -- unlike the
    Groq key, there's no offline fallback for "no database"."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Copy web/.env.example to web/.env and paste your "
            "Neon connection string, or set it as an env var (Render: Settings -> Environment)."
        )
    return url.strip()
