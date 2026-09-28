from __future__ import annotations

from functools import lru_cache

from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService

from aurora_assistente.agents.principal import agente_principal
from aurora_assistente.config import DATABASE_PATH

APP_NAME = "residencial-aurora"


@lru_cache(maxsize=1)
def get_session_service() -> DatabaseSessionService:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    return DatabaseSessionService(db_url=f"sqlite+aiosqlite:///{DATABASE_PATH}")


@lru_cache(maxsize=1)
def get_runner() -> Runner:
    return Runner(
        app_name=APP_NAME,
        agent=agente_principal,
        session_service=get_session_service(),
    )
