"""Serviço de Notificações: consome os eventos de chamado e expõe os avisos."""
import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI

from app import consumidor
from app.rotas import router as notificacoes_router
from comum.api import criar_app
from comum.banco import Base, engine


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    """Cria a tabela e começa a consumir eventos em segundo plano."""
    Base.metadata.create_all(engine)
    tarefa = asyncio.create_task(consumidor.consumir_para_sempre())
    try:
        yield
    finally:
        tarefa.cancel()
        with suppress(asyncio.CancelledError):
            await tarefa


app = criar_app("HelpDesk TI — Serviço de Notificações", "1.0.0", ciclo_de_vida)
app.include_router(notificacoes_router)
