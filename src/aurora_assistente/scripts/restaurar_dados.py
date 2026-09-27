from __future__ import annotations

import asyncio
import json

from aurora_assistente.config import DADOS_DIR
from aurora_assistente.storage.database import connect, init_schema


async def _restaurar() -> None:
    await init_schema()

    reservas = json.loads((DADOS_DIR / "reservas.json").read_text(encoding="utf-8"))
    visitantes = json.loads((DADOS_DIR / "visitantes.json").read_text(encoding="utf-8"))

    # So reseta reservas/visitantes: sessoes do ADK ficam intactas para nao
    # violar a Garantia 3 (nada se perde no reinicio) quando a restauracao
    # e usada isoladamente, sem reiniciar a API.
    async with connect() as conn:
        await conn.execute("DELETE FROM reservas")
        await conn.execute("DELETE FROM visitantes")

        await conn.executemany(
            "INSERT INTO reservas (codigo, apartamento, area, data, cancelada) VALUES (?, ?, ?, ?, 0)",
            [(r["codigo"], r["apartamento"], r["area"], r["data"]) for r in reservas],
        )
        await conn.executemany(
            "INSERT INTO visitantes (apartamento, nome, data) VALUES (?, ?, ?)",
            [(v["apartamento"], v["nome"], v["data"]) for v in visitantes],
        )

        await conn.commit()

    print(f"Restaurado: {len(reservas)} reservas e {len(visitantes)} visitantes a partir de dados/.")


def main() -> None:
    asyncio.run(_restaurar())


if __name__ == "__main__":
    main()
