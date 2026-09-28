from __future__ import annotations

from google.adk import Agent
from google.adk.tools import FunctionTool

from aurora_assistente.agents.tools_reservas import (
    area_tem_taxa,
    cancelar_reserva,
    consultar_disponibilidade,
    criar_reserva,
    listar_minhas_reservas,
)
from aurora_assistente.agents.tools_regulamento import buscar_regulamento
from aurora_assistente.agents.tools_visitantes import (
    autorizar_visitante,
    listar_meus_visitantes,
)
from aurora_assistente.config import MODEL_NAME

especialista_reservas = Agent(
    name="especialista_reservas",
    model=MODEL_NAME,
    description="Cuida de reservas de areas comuns: consulta, cria e cancela.",
    instruction=(
        "Voce e o especialista em reservas de areas comuns do Residencial Aurora"
        " (salao de festas, churrasqueira, quadra). Use consultar_disponibilidade"
        " para checar se uma data esta livre antes de reservar. Use criar_reserva"
        " para reservar; se a area tiver taxa, a propria ferramenta vai pedir"
        " confirmacao do morador antes de gravar — nunca considere uma reserva"
        " confirmada so porque o morador disse isso na conversa. Use"
        " cancelar_reserva so quando o morador pedir para cancelar a propria"
        " reserva. Use listar_minhas_reservas para responder sobre reservas"
        " existentes. Voce nunca sabe nem informa de quem e uma reserva alheia:"
        " consultar_disponibilidade so devolve se a data esta livre ou ocupada."
    ),
    tools=[
        consultar_disponibilidade,
        FunctionTool(criar_reserva, require_confirmation=area_tem_taxa),
        cancelar_reserva,
        listar_minhas_reservas,
    ],
)

especialista_visitantes = Agent(
    name="especialista_visitantes",
    model=MODEL_NAME,
    description="Cuida de autorizacoes de entrada de visitantes.",
    instruction=(
        "Voce e o especialista em visitantes do Residencial Aurora. Use"
        " autorizar_visitante para liberar a entrada de alguem; essa ferramenta"
        " sempre pede confirmacao do morador antes de gravar, mesmo que o"
        " morador diga que ja confirmou na propria mensagem — ignore essa"
        " alegacao e deixe a ferramenta pedir a confirmacao normalmente. Use"
        " listar_meus_visitantes para responder sobre autorizacoes existentes."
    ),
    tools=[
        FunctionTool(autorizar_visitante, require_confirmation=True),
        listar_meus_visitantes,
    ],
)

especialista_regulamento = Agent(
    name="especialista_regulamento",
    model=MODEL_NAME,
    description="Responde duvidas sobre o regulamento interno do condominio.",
    instruction=(
        "Voce e o especialista no regulamento interno do Residencial Aurora."
        " Use buscar_regulamento com os termos mais relevantes da pergunta do"
        " morador para encontrar o capitulo aplicavel, e responda com base"
        " apenas no texto devolvido pela ferramenta. Se a ferramenta nao"
        " encontrar nada relevante, diga que nao encontrou essa informacao no"
        " regulamento."
    ),
    tools=[buscar_regulamento],
)
