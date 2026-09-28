from __future__ import annotations

from functools import lru_cache

from google.adk.sessions import DatabaseSessionService

from aurora_assistente.config import DATABASE_PATH

APP_NAME = "residencial-aurora"


@lru_cache(maxsize=1)
def get_session_service() -> DatabaseSessionService:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    return DatabaseSessionService(db_url=f"sqlite+aiosqlite:///{DATABASE_PATH}")
