from __future__ import annotations

from aurora_assistente.storage.database import connect


async def listar_reservas_ativas(apartamento: str) -> list[dict]:
    async with connect() as conn:
        cursor = await conn.execute(
            "SELECT codigo, area, data FROM reservas"
            " WHERE apartamento = ? AND cancelada = 0"
            " ORDER BY data",
            (apartamento,),
        )
        rows = await cursor.fetchall()
        return [{"codigo": codigo, "area": area, "data": data} for codigo, area, data in rows]
