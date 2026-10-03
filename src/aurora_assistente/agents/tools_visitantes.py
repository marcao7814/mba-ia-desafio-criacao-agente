from __future__ import annotations

from google.adk.tools import ToolContext

from aurora_assistente.storage import database
from aurora_assistente.storage.referencia import data_valida, erro_data_invalida
from aurora_assistente.storage.visitantes import listar_visitantes


async def autorizar_visitante(nome: str, data: str, tool_context: ToolContext) -> dict:
    """Autoriza a entrada de um visitante para o apartamento da sessao atual.

    Sempre exige confirmacao (Garantia 1, ela libera acesso ao predio),
    mesmo que o morador diga que ja confirmou na propria mensagem — a
    confirmacao real so acontece pela rota de confirmacoes.
    """
    apartamento = tool_context.state["apartamento"]
    if not data_valida(data):
        return erro_data_invalida(data)
    async with database.connect() as conn:
        await conn.execute(
            "INSERT INTO visitantes (apartamento, nome, data) VALUES (?, ?, ?)",
            (apartamento, nome, data),
        )
        await conn.commit()
    return {"nome": nome, "data": data}


async def listar_meus_visitantes(tool_context: ToolContext) -> dict:
    """Lista as autorizacoes de visita do apartamento da sessao atual."""
    apartamento = tool_context.state["apartamento"]
    return {"visitantes": await listar_visitantes(apartamento)}
