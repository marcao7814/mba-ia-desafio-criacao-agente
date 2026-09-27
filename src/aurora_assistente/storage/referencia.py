from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache

from aurora_assistente.config import DADOS_DIR


@dataclass(frozen=True)
class Apartamento:
    numero: str
    morador: str


@dataclass(frozen=True)
class Area:
    id: str
    nome: str
    taxa: float


@lru_cache(maxsize=1)
def carregar_apartamentos() -> dict[str, Apartamento]:
    dados = json.loads((DADOS_DIR / "apartamentos.json").read_text(encoding="utf-8"))
    return {item["numero"]: Apartamento(**item) for item in dados}


@lru_cache(maxsize=1)
def carregar_areas() -> dict[str, Area]:
    dados = json.loads((DADOS_DIR / "areas.json").read_text(encoding="utf-8"))
    return {item["id"]: Area(**item) for item in dados}


def apartamento_existe(numero: str) -> bool:
    return numero in carregar_apartamentos()


def area_existe(area_id: str) -> bool:
    return area_id in carregar_areas()


def taxa_da_area(area_id: str) -> float:
    return carregar_areas()[area_id].taxa
