"""Serviço de Inventário: cadastro e consulta dos equipamentos de TI."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import semente
from app.rotas import router as ativos_router
from comum.api import criar_app
from comum.banco import Base, SessionLocal, engine


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    """Cria a tabela e, se pedido, os equipamentos de exemplo ao iniciar."""
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        semente.carregar(db)
    yield


app = criar_app("HelpDesk TI — Serviço de Inventário", "1.0.0", ciclo_de_vida)
app.include_router(ativos_router)
