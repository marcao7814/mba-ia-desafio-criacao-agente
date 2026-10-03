from __future__ import annotations

import random
import string

import aiosqlite
from google.adk.tools import ToolContext

from aurora_assistente.storage import database
from aurora_assistente.storage.reservas import listar_reservas_ativas
from aurora_assistente.storage.referencia import (
    area_existe,
    data_valida,
    erro_data_invalida,
    taxa_da_area,
)


def _gerar_codigo() -> str:
    sufixo = "".join(random.choices(string.digits, k=4))
    return f"RSV-{sufixo}"


async def consultar_disponibilidade(area: str, data: str) -> dict:
    """Verifica se uma area comum esta livre numa data.

    Devolve so 'livre' ou 'ocupada': nunca revela de qual apartamento e a
    reserva existente, mesmo quando a area esta ocupada (Garantia 2).
    """
    if not area_existe(area):
        return {"erro": f"Area '{area}' nao existe."}
    if not data_valida(data):
        return erro_data_invalida(data)
    async with database.connect() as conn:
        cursor = await conn.execute(
            "SELECT 1 FROM reservas WHERE area = ? AND data = ? AND cancelada = 0",
            (area, data),
        )
        ocupada = await cursor.fetchone() is not None
    return {"status": "ocupada" if ocupada else "livre"}


def area_tem_taxa(area: str, **_kwargs: object) -> bool:
    return area_existe(area) and taxa_da_area(area) > 0


async def criar_reserva(area: str, data: str, tool_context: ToolContext) -> dict:
    """Cria uma reserva de uma area comum para o apartamento da sessao atual.

    O apartamento nunca e um parametro do modelo: vem sempre do state da
    sessao (Garantia 2). Se a area tiver taxa, esta tool exige confirmacao
    antes de gravar (ver require_confirmation em agents/especialistas.py).
    """
    apartamento = tool_context.state["apartamento"]
    if not area_existe(area):
        return {"erro": f"Area '{area}' nao existe."}
    if not data_valida(data):
        return erro_data_invalida(data)

    for _ in range(5):
        codigo = _gerar_codigo()
        try:
            async with database.connect() as conn:
                await conn.execute(
                    "INSERT INTO reservas (codigo, apartamento, area, data, cancelada)"
                    " VALUES (?, ?, ?, ?, 0)",
                    (codigo, apartamento, area, data),
                )
                await conn.commit()
            return {"codigo": codigo, "area": area, "data": data}
        except aiosqlite.IntegrityError as erro:
            if "reservas.codigo" in str(erro):
                continue
            return {"erro": "Ja existe uma reserva ativa para essa area nessa data."}
    return {"erro": "Nao foi possivel gerar um codigo de reserva unico. Tente novamente."}


async def cancelar_reserva(area: str, data: str, tool_context: ToolContext) -> dict:
    """Cancela uma reserva do apartamento da sessao atual, identificada por area e data.

    So cancela reservas do proprio apartamento (regra de negocio 4): a
    clausula WHERE usa o apartamento da sessao, nunca um valor vindo do
    modelo.
    """
    apartamento = tool_context.state["apartamento"]
    if not data_valida(data):
        return erro_data_invalida(data)
    async with database.connect() as conn:
        cursor = await conn.execute(
            "UPDATE reservas SET cancelada = 1"
            " WHERE apartamento = ? AND area = ? AND data = ? AND cancelada = 0",
            (apartamento, area, data),
        )
        await conn.commit()
        if cursor.rowcount == 0:
            return {"erro": "Nenhuma reserva sua encontrada para essa area e data."}
    return {"cancelada": True, "area": area, "data": data}


async def listar_minhas_reservas(tool_context: ToolContext) -> dict:
    """Lista as reservas ativas do apartamento da sessao atual."""
    apartamento = tool_context.state["apartamento"]
    return {"reservas": await listar_reservas_ativas(apartamento)}
