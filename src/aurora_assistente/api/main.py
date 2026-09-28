from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from aurora_assistente.api.routes_sessoes import router as sessoes_router
from aurora_assistente.api.routes_verificacao import router as verificacao_router
from aurora_assistente.config import PORT
from aurora_assistente.storage.database import init_schema


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_schema()
    yield


app = FastAPI(title="Assistente Residencial Aurora", lifespan=lifespan)
app.include_router(sessoes_router)
app.include_router(verificacao_router)


def executar() -> None:
    import uvicorn

    uvicorn.run("aurora_assistente.api.main:app", host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    executar()
