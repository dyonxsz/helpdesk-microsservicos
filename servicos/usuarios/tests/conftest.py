import os

# Precisa vir antes de importar o app: o segredo e o banco são lidos no import.
os.environ.setdefault("JWT_SEGREDO", "segredo-de-teste-com-mais-de-32-caracteres-para-jwt")
os.environ.setdefault("DADOS_EXEMPLO", "0")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import limite
from app.esquemas import UsuarioCriar
from app.main import app
from app.servico import criar
from comum.banco import Base, get_db

SENHA = "Senha123"


@pytest.fixture
def sessao():
    """Banco novo, em memória, para cada teste."""
    limite.limpar_tudo()
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
    # Sem "with": não dispara o lifespan, então o banco de teste é o único usado.
    return TestClient(app)


@pytest.fixture
def contas(sessao, cliente):
    """Cria um admin, dois solicitantes e um técnico e devolve o login de cada um."""
    with sessao() as db:
        for nome, email, perfil in [
            ("Admin", "admin@x.com", "admin"),
            ("Ana", "ana@x.com", "solicitante"),
            ("Bia", "bia@x.com", "solicitante"),
            ("Carla", "carla@x.com", "tecnico"),
        ]:
            criar(db, UsuarioCriar(nome=nome, email=email, perfil=perfil, senha=SENHA))
    resultado = {}
    for apelido in ("admin", "ana", "bia", "carla"):
        r = cliente.post("/auth/login", json={"email": f"{apelido}@x.com", "senha": SENHA}).json()
        resultado[apelido] = {"headers": {"Authorization": f"Bearer {r['access_token']}"}, "id": r["usuario"]["id"]}
    return resultado
