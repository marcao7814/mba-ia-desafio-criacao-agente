from __future__ import annotations

from fastapi import APIRouter

from aurora_assistente.api.schemas import ReservaVerificacao, VisitanteVerificacao
from aurora_assistente.storage.reservas import listar_reservas_ativas
from aurora_assistente.storage.visitantes import listar_visitantes

router = APIRouter(prefix="/apartamentos", tags=["verificacao"])


@router.get("/{numero}/reservas", response_model=list[ReservaVerificacao])
async def reservas_do_apartamento(numero: str) -> list[dict]:
    return await listar_reservas_ativas(numero)


@router.get("/{numero}/visitantes", response_model=list[VisitanteVerificacao])
async def visitantes_do_apartamento(numero: str) -> list[dict]:
    return await listar_visitantes(numero)
