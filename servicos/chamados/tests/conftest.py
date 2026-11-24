import os

# Precisa vir antes de importar o app: segredo, banco e fila são lidos no import.
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
from comum.erros import NaoEncontrado, RegraDeNegocio


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
    # Sem "with": não dispara o lifespan, então o banco de teste é o único usado.
    return TestClient(app)


@pytest.fixture
def contas():
    """Tokens válidos para cada perfil, criados sem depender de outro serviço."""
    return {
        apelido: {
            "headers": {"Authorization": f"Bearer {tokens.criar(usuario_id, perfil)[0]}"},
            "id": usuario_id,
        }
        for apelido, usuario_id, perfil in [
            ("admin", 1, "admin"),
            ("ana", 2, "solicitante"),
            ("bia", 3, "solicitante"),
            ("carla", 4, "tecnico"),
        ]
    }


@pytest.fixture
def servicos(monkeypatch):
    """Troca as chamadas HTTP por funções de mentira e registra o que foi chamado."""
    chamadas = {"ativos": [], "tecnicos": []}

    def obter_ativo(ativo_id, token):
        chamadas["ativos"].append({"ativo_id": ativo_id, "token": token})
        if ativo_id != 1:
            raise NaoEncontrado(f"Ativo {ativo_id} não encontrado.")
        return {"id": 1, "patrimonio": "PAT-1", "tipo": "computador", "descricao": "Desktop", "setor": "TI"}

    def obter_tecnico(tecnico_id, token):
        chamadas["tecnicos"].append({"tecnico_id": tecnico_id, "token": token})
        if tecnico_id == 99:
            raise NaoEncontrado("Usuário 99 não encontrado.")
        if tecnico_id != 4:
            raise RegraDeNegocio(f"Usuário {tecnico_id} não é técnico.")
        return {"id": 4, "nome": "Carla", "perfil": "tecnico"}

    monkeypatch.setattr("app.servico.clientes.obter_ativo", obter_ativo)
    monkeypatch.setattr("app.servico.clientes.obter_tecnico", obter_tecnico)
    return chamadas


@pytest.fixture
def eventos(monkeypatch):
    """Captura os eventos publicados, sem precisar de Redis."""
    publicados = []

    def publicar(tipo, destinatario_id, mensagem, chamado_id):
        publicados.append({
            "tipo": tipo, "destinatario_id": destinatario_id, "mensagem": mensagem, "chamado_id": chamado_id,
        })
        return True

    monkeypatch.setattr("app.servico.eventos.publicar", publicar)
    return publicados
