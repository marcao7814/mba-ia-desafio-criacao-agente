from __future__ import annotations

from aurora_assistente.storage.database import connect


async def registrar_sessao(session_id: str, apartamento: str) -> None:
    async with connect() as conn:
        await conn.execute(
            "INSERT INTO sessoes (session_id, apartamento) VALUES (?, ?)",
            (session_id, apartamento),
        )
        await conn.commit()


async def apartamento_da_sessao(session_id: str) -> str | None:
    async with connect() as conn:
        cursor = await conn.execute(
            "SELECT apartamento FROM sessoes WHERE session_id = ?", (session_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else None
