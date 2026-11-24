"""Testes de cadastro e consulta de usuários."""


def test_admin_cria_usuario(cliente, contas):
    r = cliente.post(
        "/usuarios",
        headers=contas["admin"]["headers"],
        json={"nome": "Davi", "email": "davi@x.com", "perfil": "tecnico", "senha": "Forte1234"},
    )
    assert r.status_code == 201
    assert "senha" not in r.json() and "senha_hash" not in r.json()


def test_solicitante_nao_cria_usuario(cliente, contas):
    r = cliente.post(
        "/usuarios",
        headers=contas["ana"]["headers"],
        json={"nome": "Eva", "email": "eva@x.com", "perfil": "admin", "senha": "Forte1234"},
    )
    assert r.status_code == 403


def test_senha_fraca_e_recusada(cliente, contas):
    r = cliente.post(
        "/usuarios",
        headers=contas["admin"]["headers"],
        json={"nome": "Eva", "email": "eva@x.com", "perfil": "solicitante", "senha": "abcdefgh"},
    )
    assert r.status_code == 422


def test_email_repetido_e_recusado(cliente, contas):
    dados = {"nome": "Ana 2", "email": "ANA@x.com", "perfil": "solicitante", "senha": "Forte1234"}
    assert cliente.post("/usuarios", headers=contas["admin"]["headers"], json=dados).status_code == 422


def test_usuario_inexistente(cliente, contas):
    assert cliente.get("/usuarios/99", headers=contas["ana"]["headers"]).status_code == 404


def test_lista_publica_nao_mostra_email(cliente, contas):
    lista = cliente.get("/usuarios", headers=contas["ana"]["headers"]).json()
    assert lista and all("email" not in u for u in lista)


def test_lista_filtra_por_perfil(cliente, contas):
    lista = cliente.get("/usuarios", params={"perfil": "tecnico"}, headers=contas["ana"]["headers"]).json()
    assert [u["nome"] for u in lista] == ["Carla"]


def test_obter_usuario_devolve_perfil(cliente, contas):
    """O serviço de Chamados usa esta rota para saber se o id é mesmo técnico."""
    r = cliente.get(f"/usuarios/{contas['carla']['id']}", headers=contas["ana"]["headers"])
    assert r.status_code == 200 and r.json()["perfil"] == "tecnico"


def test_eu_devolve_dados_completos(cliente, contas):
    r = cliente.get("/auth/eu", headers=contas["ana"]["headers"])
    assert r.status_code == 200 and r.json()["email"] == "ana@x.com"
