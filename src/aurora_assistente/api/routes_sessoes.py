from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from google.genai import types

from aurora_assistente.api.conversa import (
    REQUEST_CONFIRMATION_FUNCTION_CALL_NAME,
    confirmacoes_pendentes,
    executar_turno,
)
from aurora_assistente.api.deps import APP_NAME, get_session_service
from aurora_assistente.api.schemas import (
    CriarSessaoRequest,
    CriarSessaoResponse,
    EnviarMensagemRequest,
    ResponderConfirmacaoRequest,
    RespostaConversa,
)
from aurora_assistente.storage.sessoes import apartamento_da_sessao, registrar_sessao

router = APIRouter(prefix="/sessoes", tags=["sessoes"])


async def _responder_turno(
    session_id: str, apartamento: str, nova_mensagem: types.Content
) -> RespostaConversa:
    resposta = await executar_turno(
        session_id=session_id, apartamento=apartamento, new_message=nova_mensagem
    )
    pendentes = await confirmacoes_pendentes(session_id, apartamento)
    return RespostaConversa(resposta=resposta, confirmacoes_pendentes=pendentes)


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


@router.post("/{session_id}/mensagens", response_model=RespostaConversa)
async def enviar_mensagem(session_id: str, body: EnviarMensagemRequest) -> RespostaConversa:
    apartamento = await apartamento_da_sessao(session_id)
    if apartamento is None:
        raise HTTPException(status_code=404, detail="Sessao nao encontrada")

    nova_mensagem = types.Content(role="user", parts=[types.Part(text=body.texto)])
    return await _responder_turno(session_id, apartamento, nova_mensagem)


@router.post("/{session_id}/confirmacoes", response_model=RespostaConversa)
async def responder_confirmacao(
    session_id: str, body: ResponderConfirmacaoRequest
) -> RespostaConversa:
    apartamento = await apartamento_da_sessao(session_id)
    if apartamento is None:
        raise HTTPException(status_code=404, detail="Sessao nao encontrada")

    pendentes_antes = await confirmacoes_pendentes(session_id, apartamento)
    if body.id not in {pendente["id"] for pendente in pendentes_antes}:
        raise HTTPException(
            status_code=409, detail="Nao existe confirmacao pendente com esse id nesta sessao"
        )

    nova_mensagem = types.Content(
        role="user",
        parts=[
            types.Part(
                function_response=types.FunctionResponse(
                    id=body.id,
                    name=REQUEST_CONFIRMATION_FUNCTION_CALL_NAME,
                    response={"confirmed": body.confirmado},
                )
            )
        ],
    )
    return await _responder_turno(session_id, apartamento, nova_mensagem)
