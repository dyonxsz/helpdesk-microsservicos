import os

# Precisa vir antes de importar o app.
os.environ.setdefault("JWT_SEGREDO", "segredo-de-teste-com-mais-de-32-caracteres-para-jwt")
os.environ.setdefault("DADOS_EXEMPLO", "0")
os.environ.setdefault("REDIS_URL", "")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from comum import tokens
from comum.banco import Base, get_db


@pytest.fixture
def sessao():
    """Banco novo, em memória, para cada teste."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Sessao = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def db_de_teste():
        db = Sessao()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = db_de_teste
    yield Sessao
    app.dependency_overrides.clear()


@pytest.fixture
def cliente(sessao):
    # Sem "with": não dispara o lifespan (nem o consumidor).
    return TestClient(app)


@pytest.fixture
def cabecalhos():
    return {
        apelido: {"Authorization": f"Bearer {tokens.criar(usuario_id, perfil)[0]}"}
        for apelido, usuario_id, perfil in [
            ("admin", 1, "admin"),
            ("ana", 2, "solicitante"),
            ("bia", 3, "solicitante"),
            ("carla", 4, "tecnico"),
        ]
    }
