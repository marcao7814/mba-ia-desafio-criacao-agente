from __future__ import annotations

import aiosqlite

from aurora_assistente.config import DATABASE_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS reservas (
    codigo TEXT PRIMARY KEY,
    apartamento TEXT NOT NULL,
    area TEXT NOT NULL,
    data TEXT NOT NULL,
    cancelada INTEGER NOT NULL DEFAULT 0
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_reserva_ativa_area_data
    ON reservas (area, data)
    WHERE cancelada = 0;

CREATE TABLE IF NOT EXISTS visitantes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    apartamento TEXT NOT NULL,
    nome TEXT NOT NULL,
    data TEXT NOT NULL
);
"""


def connect() -> aiosqlite.Connection:
    """Abre uma conexao SQLite para uso com `async with`.

    A constraint UNIQUE em `idx_reserva_ativa_area_data` e quem garante a
    Garantia 5 (exclusividade de reserva por area+data) no instante do
    INSERT, nao uma checagem previa feita pela aplicacao.
    """
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    return aiosqlite.connect(DATABASE_PATH)


async def init_schema() -> None:
    async with connect() as conn:
        await conn.executescript(SCHEMA)
        await conn.commit()
