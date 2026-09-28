from __future__ import annotations

from aurora_assistente.storage.regulamento import buscar_capitulo


async def buscar_regulamento(assunto: str) -> dict:
    """Busca no regulamento interno o capitulo mais relevante para o assunto.

    Devolve so o capitulo encontrado, nunca o regulamento inteiro, para que
    a sessao nao acumule trechos de assuntos que ninguem perguntou
    (Garantia 4).
    """
    capitulo = buscar_capitulo(assunto)
    if capitulo is None:
        return {"encontrado": False}
    return {"encontrado": True, "titulo": capitulo.titulo, "texto": capitulo.texto}
