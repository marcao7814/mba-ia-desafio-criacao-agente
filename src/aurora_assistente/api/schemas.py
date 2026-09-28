from __future__ import annotations

from pydantic import BaseModel


class CriarSessaoRequest(BaseModel):
    apartamento: str


class CriarSessaoResponse(BaseModel):
    session_id: str


class ReservaVerificacao(BaseModel):
    codigo: str
    area: str
    data: str


class VisitanteVerificacao(BaseModel):
    nome: str
    data: str
