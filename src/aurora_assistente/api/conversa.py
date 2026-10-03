from __future__ import annotations

from fastapi import HTTPException
from google.genai import types
from google.genai.errors import APIError

from aurora_assistente.api.deps import APP_NAME, get_runner, get_session_service

REQUEST_CONFIRMATION_FUNCTION_CALL_NAME = "adk_request_confirmation"


async def executar_turno(*, session_id: str, apartamento: str, new_message: types.Content) -> str:
    """Roda um turno do Runner e devolve o texto final da resposta.

    Devolve string vazia quando a execucao para esperando confirmacao (o
    proprio contrato da API preve isso em `resposta`).
    """
    runner = get_runner()
    resposta = ""
    try:
        async for evento in runner.run_async(
            user_id=apartamento, session_id=session_id, new_message=new_message
        ):
            if evento.is_final_response() and evento.content and evento.content.parts:
                texto = "".join(parte.text or "" for parte in evento.content.parts)
                if texto:
                    resposta = texto
    except APIError as erro:
        raise HTTPException(
            status_code=503, detail="Servico de IA temporariamente indisponivel. Tente novamente."
        ) from erro
    return resposta


async def confirmacoes_pendentes(session_id: str, apartamento: str) -> list[dict]:
    """Varre todo o historico da sessao e lista confirmacoes ainda em aberto.

    Uma confirmacao (chamada sintetica `adk_request_confirmation`, gerada
    pelo ADK quando uma tool pede confirmacao) esta pendente se nenhum
    evento do morador ("user") trouxe uma function_response com o mesmo id.
    """
    session_service = get_session_service()
    sessao = await session_service.get_session(
        app_name=APP_NAME, user_id=apartamento, session_id=session_id
    )
    if sessao is None:
        return []

    pendentes: dict[str, dict] = {}
    respondidas: set[str] = set()

    for evento in sessao.events:
        for chamada in evento.get_function_calls():
            if chamada.name != REQUEST_CONFIRMATION_FUNCTION_CALL_NAME or not chamada.id:
                continue
            original = (chamada.args or {}).get("originalFunctionCall") or {}
            pendentes[chamada.id] = {
                "id": chamada.id,
                "acao": original.get("name"),
                "detalhes": original.get("args") or {},
            }

        if evento.author == "user":
            for resposta_fn in evento.get_function_responses():
                if (
                    resposta_fn.name == REQUEST_CONFIRMATION_FUNCTION_CALL_NAME
                    and resposta_fn.id
                ):
                    respondidas.add(resposta_fn.id)

    return [dado for id_, dado in pendentes.items() if id_ not in respondidas]
