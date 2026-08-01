"""Web version settings: just env vars (Render env vars in production, a
local .env for dev via python-dotenv-free manual loading in main.py)."""
import os
from typing import Optional


def get_api_key() -> Optional[str]:
    key = os.environ.get("GROQ_API_KEY")
    return key.strip() if key else None
