"""Testes do serviço de Inventário."""

ATIVO = {"patrimonio": "PAT-1", "tipo": "computador", "descricao": "Desktop", "setor": "TI"}


def test_saude_nao_exige_token(cliente):
    r = cliente.get("/saude")
    assert r.status_code == 200 and r.json() == {"status": "ok"}


def test_rotas_exigem_login(cliente):
    assert cliente.get("/ativos").status_code == 401
    assert cliente.get("/ativos/1").status_code == 401
    assert cliente.post("/ativos", json=ATIVO).status_code == 401


def test_token_adulterado_e_recusado(cliente, cabecalhos):
    h = {"Authorization": cabecalhos["tecnico"]["Authorization"] + "x"}
    assert cliente.get("/ativos", headers=h).status_code == 401


def test_tecnico_cadastra_ativo(cliente, cabecalhos):
    r = cliente.post("/ativos", headers=cabecalhos["tecnico"], json=ATIVO)
    assert r.status_code == 201 and r.json()["patrimonio"] == "PAT-1"


def test_admin_cadastra_ativo(cliente, cabecalhos):
    assert cliente.post("/ativos", headers=cabecalhos["admin"], json=ATIVO).status_code == 201


def test_solicitante_nao_cadastra_ativo(cliente, cabecalhos):
    r = cliente.post("/ativos", headers=cabecalhos["solicitante"], json=ATIVO)
    assert r.status_code == 403


def test_solicitante_pode_listar(cliente, cabecalhos):
    assert cliente.get("/ativos", headers=cabecalhos["solicitante"]).status_code == 200


def test_filtra_por_setor(cliente, cabecalhos):
    h = cabecalhos["tecnico"]
    cliente.post("/ativos", headers=h, json={**ATIVO, "patrimonio": "PAT-1", "setor": "RH"})
    cliente.post("/ativos", headers=h, json={**ATIVO, "patrimonio": "PAT-2", "setor": "TI"})
    lista = cliente.get("/ativos", params={"setor": "RH"}, headers=h).json()
    assert len(lista) == 1 and lista[0]["patrimonio"] == "PAT-1"


def test_ativo_inexistente(cliente, cabecalhos):
    assert cliente.get("/ativos/99", headers=cabecalhos["solicitante"]).status_code == 404


def test_patrimonio_repetido_e_recusado(cliente, cabecalhos):
    h = cabecalhos["tecnico"]
    cliente.post("/ativos", headers=h, json=ATIVO)
    assert cliente.post("/ativos", headers=h, json=ATIVO).status_code == 422


def test_tipo_invalido_e_recusado(cliente, cabecalhos):
    r = cliente.post("/ativos", headers=cabecalhos["tecnico"], json={**ATIVO, "tipo": "geladeira"})
    assert r.status_code == 422


def test_patrimonio_com_caractere_invalido_e_recusado(cliente, cabecalhos):
    r = cliente.post("/ativos", headers=cabecalhos["tecnico"], json={**ATIVO, "patrimonio": "PAT 1!"})
    assert r.status_code == 422


def test_campo_extra_e_recusado(cliente, cabecalhos):
    r = cliente.post("/ativos", headers=cabecalhos["tecnico"], json={**ATIVO, "fornecedor": "X"})
    assert r.status_code == 422
