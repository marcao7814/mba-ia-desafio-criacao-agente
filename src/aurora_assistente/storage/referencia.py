from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from functools import lru_cache

from aurora_assistente.config import DADOS_DIR

_DATA_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


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


def data_valida(data: str) -> bool:
    """Confere se a data esta exatamente no formato AAAA-MM-DD do contrato.

    As tools nunca devem gravar nem consultar uma data em outro formato: se
    o modelo normalizasse "2030-04-20" para "20/04/2030" ou qualquer outra
    variante, a mesma data real passaria a ser tratada como duas datas
    diferentes pelo banco, furando a exclusividade de reserva (Garantia 5).
    """
    if not _DATA_PATTERN.match(data):
        return False
    try:
        date.fromisoformat(data)
    except ValueError:
        return False
    return True


def erro_data_invalida(data: str) -> dict:
    """Mensagem de erro padrao devolvida por toda tool quando data_valida(data) e False."""
    return {"erro": f"Data '{data}' invalida. Use o formato AAAA-MM-DD (ex.: 2030-04-20)."}
