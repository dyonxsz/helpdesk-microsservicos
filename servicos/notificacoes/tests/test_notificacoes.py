"""Testes da API de notificações."""
from app import servico


def test_exige_login(cliente):
    assert cliente.get("/notificacoes").status_code == 401


def test_saude_nao_exige_token(cliente):
    assert cliente.get("/saude").json() == {"status": "ok"}


def test_cada_usuario_ve_so_as_proprias(cliente, sessao, cabecalhos):
    with sessao() as db:
        servico.registrar(db, "ChamadoAberto", 2, "Seu chamado #1 foi aberto.")
        servico.registrar(db, "ChamadoAtribuido", 4, "O chamado #1 foi atribuído a você.")

    ana = cliente.get("/notificacoes", headers=cabecalhos["ana"]).json()
    carla = cliente.get("/notificacoes", headers=cabecalhos["carla"]).json()
    bia = cliente.get("/notificacoes", headers=cabecalhos["bia"]).json()
    assert [n["tipo"] for n in ana] == ["ChamadoAberto"]
    assert [n["tipo"] for n in carla] == ["ChamadoAtribuido"]
    assert bia == []


def test_nao_da_para_ver_notificacao_de_outro_pelo_id(cliente, sessao, cabecalhos):
    with sessao() as db:
        servico.registrar(db, "ChamadoResolvido", 3, "Seu chamado #2 foi resolvido.")
    # não existe rota por id; a lista sempre filtra pelo token
    assert cliente.get("/notificacoes", headers=cabecalhos["ana"]).json() == []


def test_ordem_das_notificacoes(cliente, sessao, cabecalhos):
    with sessao() as db:
        servico.registrar(db, "ChamadoAberto", 2, "primeiro")
        servico.registrar(db, "ChamadoResolvido", 2, "segundo")
    lista = cliente.get("/notificacoes", headers=cabecalhos["ana"]).json()
    assert [n["mensagem"] for n in lista] == ["primeiro", "segundo"]
