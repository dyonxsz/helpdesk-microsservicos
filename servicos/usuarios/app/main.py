"""Serviço de Usuários: login, dados de quem está logado e cadastro de usuários."""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import semente
from app.auth import router as auth_router
from app.usuarios import router as usuarios_router
from comum.api import criar_app
from comum.banco import Base, SessionLocal, engine


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    """Cria a tabela e, se pedido, os usuários de exemplo ao iniciar."""
    Base.metadata.create_all(engine)
    if os.getenv("DADOS_EXEMPLO", "1") == "1":
        with SessionLocal() as db:
            semente.carregar(db)
    yield


app = criar_app("HelpDesk TI — Serviço de Usuários", "1.0.0", ciclo_de_vida)
app.include_router(auth_router)
app.include_router(usuarios_router)
