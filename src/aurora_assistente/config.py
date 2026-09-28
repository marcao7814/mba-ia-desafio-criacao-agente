from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DADOS_DIR = PROJECT_ROOT / "dados"

_SQLITE_PREFIX = "sqlite:///"
_database_url = os.getenv("DATABASE_URL", "sqlite:///./data/aurora.db")
if not _database_url.startswith(_SQLITE_PREFIX):
    raise ValueError(f"DATABASE_URL precisa comecar com '{_SQLITE_PREFIX}': {_database_url}")

DATABASE_PATH = (PROJECT_ROOT / _database_url[len(_SQLITE_PREFIX) :]).resolve()

PORT = int(os.getenv("PORT", "8000"))

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
