"""Serviço de Chamados: abertura, atribuição, status, comentários e painel."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import semente
from app.rotas import router as chamados_router
from comum.api import criar_app
from comum.banco import Base, SessionLocal, engine


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    """Cria a tabela e, se pedido, os chamados de exemplo ao iniciar."""
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        semente.carregar(db)
    yield


app = criar_app("HelpDesk TI — Serviço de Chamados", "1.0.0", ciclo_de_vida)
app.include_router(chamados_router)
