from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from aurora_assistente.api.deps import APP_NAME, get_session_service
from aurora_assistente.api.schemas import CriarSessaoRequest, CriarSessaoResponse
from aurora_assistente.storage.sessoes import apartamento_da_sessao, registrar_sessao

router = APIRouter(prefix="/sessoes", tags=["sessoes"])


@router.post("", status_code=201, response_model=CriarSessaoResponse)
async def criar_sessao(body: CriarSessaoRequest) -> CriarSessaoResponse:
    session_service = get_session_service()
    sessao = await session_service.create_session(
        app_name=APP_NAME,
        user_id=body.apartamento,
        state={"apartamento": body.apartamento},
    )
    await registrar_sessao(sessao.id, body.apartamento)
    return CriarSessaoResponse(session_id=sessao.id)


@router.get("/{session_id}/eventos")
async def listar_eventos(session_id: str) -> list[dict[str, Any]]:
    apartamento = await apartamento_da_sessao(session_id)
    if apartamento is None:
        raise HTTPException(status_code=404, detail="Sessao nao encontrada")

    session_service = get_session_service()
    sessao = await session_service.get_session(
        app_name=APP_NAME, user_id=apartamento, session_id=session_id
    )
    if sessao is None:
        raise HTTPException(status_code=404, detail="Sessao nao encontrada")

    return [evento.model_dump(mode="json") for evento in sessao.events]
