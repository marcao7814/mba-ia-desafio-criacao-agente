from __future__ import annotations

from aurora_assistente.storage.database import connect


async def listar_visitantes(apartamento: str) -> list[dict]:
    async with connect() as conn:
        cursor = await conn.execute(
            "SELECT nome, data FROM visitantes WHERE apartamento = ? ORDER BY data",
            (apartamento,),
        )
        rows = await cursor.fetchall()
        return [{"nome": nome, "data": data} for nome, data in rows]
