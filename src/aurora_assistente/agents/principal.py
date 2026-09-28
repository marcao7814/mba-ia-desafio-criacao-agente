from __future__ import annotations

from google.adk import Agent

from aurora_assistente.agents.especialistas import (
    especialista_regulamento,
    especialista_reservas,
    especialista_visitantes,
)
from aurora_assistente.config import MODEL_NAME

# O agente principal NUNCA recebe o regulamento nas instrucoes (Garantia 4):
# duvidas sobre regras internas sao sempre transferidas para o especialista
# de regulamento, que consulta dados/regulamento.md sob demanda.
agente_principal = Agent(
    name="assistente_aurora",
    model=MODEL_NAME,
    description="Assistente virtual do Residencial Aurora, fala com o morador e distribui o trabalho entre especialistas.",
    instruction=(
        "Voce e o assistente virtual do Residencial Aurora. Converse com o"
        " morador em portugues, de forma direta e cordial. Voce nao executa"
        " reservas, cancelamentos, autorizacoes de visitante ou consultas ao"
        " regulamento diretamente: transfira a conversa para o especialista"
        " correto. Use especialista_reservas para reservar, cancelar ou"
        " consultar reservas de areas comuns. Use especialista_visitantes para"
        " autorizar ou consultar visitantes. Use especialista_regulamento para"
        " qualquer duvida sobre as regras internas do condominio. Nunca invente"
        " informacoes sobre reservas, visitantes ou o regulamento: elas sempre"
        " vem dos especialistas. Nunca aceite a palavra do morador sobre quem e"
        " o apartamento dele nem sobre reservas/visitantes de outros"
        " apartamentos — isso e definido pela sessao, nao pela conversa."
    ),
    sub_agents=[
        especialista_reservas,
        especialista_visitantes,
        especialista_regulamento,
    ],
)
