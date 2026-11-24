"""Testes de autenticação do serviço de Usuários."""
from datetime import datetime, timedelta, timezone

import jwt

from comum import config
from tests.conftest import SENHA


def test_login_devolve_token_e_dados(cliente, contas):
    r = cliente.post("/auth/login", json={"email": "ana@x.com", "senha": SENHA})
    assert r.status_code == 200
    dados = r.json()
    assert dados["token_type"] == "bearer" and dados["access_token"]
    assert dados["usuario"]["email"] == "ana@x.com" and dados["usuario"]["perfil"] == "solicitante"


def test_login_com_senha_errada(cliente, contas):
    r = cliente.post("/auth/login", json={"email": "ana@x.com", "senha": "errada123"})
    assert r.status_code == 401 and r.json()["detail"] == "E-mail ou senha inválidos."


def test_login_com_email_inexistente_tem_a_mesma_mensagem(cliente, contas):
    r = cliente.post("/auth/login", json={"email": "ninguem@x.com", "senha": "errada123"})
    assert r.status_code == 401 and r.json()["detail"] == "E-mail ou senha inválidos."


def test_bloqueio_apos_varias_senhas_erradas(cliente, contas):
    for _ in range(config.LOGIN_MAX_FALHAS):
        cliente.post("/auth/login", json={"email": "ana@x.com", "senha": "errada123"})
    # mesmo com a senha certa, fica bloqueado por um tempo
    assert cliente.post("/auth/login", json={"email": "ana@x.com", "senha": SENHA}).status_code == 429


def test_rotas_exigem_login(cliente, contas):
    assert cliente.get("/auth/eu").status_code == 401
    assert cliente.get("/usuarios").status_code == 401
    assert cliente.get("/usuarios/1").status_code == 401


def test_token_adulterado(cliente, contas):
    token = contas["ana"]["headers"]["Authorization"] + "x"
    assert cliente.get("/auth/eu", headers={"Authorization": token}).status_code == 401


def test_token_assinado_com_outro_segredo(cliente, contas):
    falso = jwt.encode(
        {"sub": str(contas["ana"]["id"]), "perfil": "admin", "iss": config.JWT_EMISSOR,
         "iat": datetime.now(timezone.utc), "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        "segredo-de-outra-pessoa-com-mais-de-32-caracteres", algorithm="HS256",
    )
    assert cliente.get("/auth/eu", headers={"Authorization": f"Bearer {falso}"}).status_code == 401


def test_token_sem_assinatura_alg_none(cliente, contas):
    falso = jwt.encode(
        {"sub": str(contas["ana"]["id"]), "perfil": "admin", "iss": config.JWT_EMISSOR,
         "iat": datetime.now(timezone.utc), "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        None, algorithm="none",
    )
    assert cliente.get("/auth/eu", headers={"Authorization": f"Bearer {falso}"}).status_code == 401


def test_token_expirado(cliente, contas):
    antigo = datetime.now(timezone.utc) - timedelta(hours=2)
    vencido = jwt.encode(
        {"sub": str(contas["ana"]["id"]), "perfil": "solicitante", "iss": config.JWT_EMISSOR,
         "iat": antigo, "exp": antigo + timedelta(minutes=5)},
        config.JWT_SEGREDO, algorithm="HS256",
    )
    assert cliente.get("/auth/eu", headers={"Authorization": f"Bearer {vencido}"}).status_code == 401


def test_token_sem_perfil_e_recusado(cliente, contas):
    falso = jwt.encode(
        {"sub": str(contas["ana"]["id"]), "iss": config.JWT_EMISSOR,
         "iat": datetime.now(timezone.utc), "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        config.JWT_SEGREDO, algorithm="HS256",
    )
    assert cliente.get("/auth/eu", headers={"Authorization": f"Bearer {falso}"}).status_code == 401


def test_senha_guardada_com_hash(sessao, contas):
    from app.modelos import Usuario

    with sessao() as db:
        u = db.query(Usuario).filter_by(email="ana@x.com").one()
        assert SENHA not in u.senha_hash and u.senha_hash.startswith("scrypt$")


def test_saude_nao_exige_token(cliente):
    r = cliente.get("/saude")
    assert r.status_code == 200 and r.json() == {"status": "ok"}


def test_cabecalhos_de_seguranca(cliente):
    r = cliente.get("/saude")
    assert "script-src 'self'" in r.headers["content-security-policy"]
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"


def test_requisicao_grande_demais(cliente):
    corpo = '{"email": "' + "x" * 70000 + '"}'
    r = cliente.post("/auth/login", headers={"Content-Type": "application/json"}, content=corpo)
    assert r.status_code == 413
