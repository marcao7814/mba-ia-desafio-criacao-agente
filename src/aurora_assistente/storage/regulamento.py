from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache

from aurora_assistente.config import DADOS_DIR

_CAPITULO_PATTERN = re.compile(r"^## (.+)$", re.MULTILINE)


@dataclass(frozen=True)
class Capitulo:
    titulo: str
    texto: str


def _normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return sem_acento.lower()


@lru_cache(maxsize=1)
def carregar_capitulos() -> list[Capitulo]:
    conteudo = (DADOS_DIR / "regulamento.md").read_text(encoding="utf-8")
    matches = list(_CAPITULO_PATTERN.finditer(conteudo))
    capitulos = []
    for indice, match in enumerate(matches):
        inicio = match.start()
        fim = matches[indice + 1].start() if indice + 1 < len(matches) else len(conteudo)
        capitulos.append(Capitulo(titulo=match.group(1).strip(), texto=conteudo[inicio:fim].strip()))
    return capitulos


def buscar_capitulo(consulta: str) -> Capitulo | None:
    """Devolve o capitulo com maior sobreposicao de palavras com a consulta.

    So um capitulo inteiro e devolvido (nunca o regulamento completo), para
    que a sessao nunca acumule trechos de assuntos que ninguem perguntou
    (Garantia 4).
    """
    termos = [t for t in _normalizar(consulta).split() if len(t) > 2]
    if not termos:
        return None

    melhor_capitulo: Capitulo | None = None
    melhor_pontuacao = 0
    for capitulo in carregar_capitulos():
        corpo_normalizado = _normalizar(capitulo.texto)
        pontuacao = sum(corpo_normalizado.count(termo) for termo in termos)
        if pontuacao > melhor_pontuacao:
            melhor_pontuacao = pontuacao
            melhor_capitulo = capitulo
    return melhor_capitulo
