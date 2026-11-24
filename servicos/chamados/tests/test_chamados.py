"""Testes das regras do serviço de Chamados.

As chamadas HTTP aos outros serviços são substituídas por funções de mentira
(fixture `servicos`), então os testes rodam sozinhos, sem Docker.
"""
from datetime import datetime

from comum.erros import ServicoIndisponivel, SessaoInvalida


def abrir(cliente, contas, quem="ana", prioridade="alta", **extra):
    dados = {"titulo": "PC não liga", "descricao": "Nada acontece", "prioridade": prioridade, "ativo_id": 1, **extra}
    return cliente.post("/chamados", headers=contas[quem]["headers"], json=dados)


# ---------- abertura ----------

def test_abrir_calcula_sla_e_publica_evento(cliente, contas, servicos, eventos):
    r = abrir(cliente, contas, prioridade="critica")
    assert r.status_code == 201
    c = r.json()
    assert c["solicitante_id"] == contas["ana"]["id"] and c["status"] == "aberto"
    horas = (datetime.fromisoformat(c["prazo_sla"]) - datetime.fromisoformat(c["criado_em"])).total_seconds() / 3600
    assert round(horas) == 4
    assert eventos[0]["tipo"] == "ChamadoAberto" and eventos[0]["destinatario_id"] == contas["ana"]["id"]


def test_abrir_repassa_o_token_para_o_inventario(cliente, contas, servicos, eventos):
    abrir(cliente, contas)
    assert servicos["ativos"] == [{"ativo_id": 1, "token": contas["ana"]["headers"]["Authorization"]}]


def test_abrir_sem_ativo_nao_chama_o_inventario(cliente, contas, servicos, eventos):
    r = cliente.post("/chamados", headers=contas["ana"]["headers"],
                     json={"titulo": "Sem equipamento", "descricao": "Acesso", "prioridade": "baixa"})
    assert r.status_code == 201 and servicos["ativos"] == []


def test_abrir_com_ativo_inexistente(cliente, contas, servicos, eventos):
    assert abrir(cliente, contas, ativo_id=999).status_code == 404


def test_inventario_fora_do_ar_responde_503(cliente, contas, servicos, eventos, monkeypatch):
    def fora_do_ar(ativo_id, token):
        raise ServicoIndisponivel("O serviço de Inventário está indisponível no momento.")

    monkeypatch.setattr("app.servico.clientes.obter_ativo", fora_do_ar)
    r = abrir(cliente, contas)
    assert r.status_code == 503 and "Inventário" in r.json()["detail"]
    # nada foi gravado: a lista continua vazia
    assert cliente.get("/chamados", headers=contas["ana"]["headers"]).json() == []


def test_token_recusado_pelo_outro_servico_responde_401(cliente, contas, servicos, eventos, monkeypatch):
    def sessao_invalida(ativo_id, token):
        raise SessaoInvalida("Sua sessão não é mais válida. Entre novamente.")

    monkeypatch.setattr("app.servico.clientes.obter_ativo", sessao_invalida)
    assert abrir(cliente, contas).status_code == 401


def test_nao_da_para_abrir_chamado_em_nome_de_outro(cliente, contas, servicos):
    r = abrir(cliente, contas, solicitante_id=contas["bia"]["id"])
    assert r.status_code == 422


# ---------- atribuição ----------

def test_atribuir_muda_status_e_publica_evento(cliente, contas, servicos, eventos):
    cid = abrir(cliente, contas).json()["id"]
    r = cliente.patch(f"/chamados/{cid}/atribuir", headers=contas["carla"]["headers"],
                      json={"tecnico_id": contas["carla"]["id"]})
    assert r.status_code == 200
    assert r.json()["status"] == "em_atendimento" and r.json()["tecnico_id"] == contas["carla"]["id"]
    assert eventos[-1]["tipo"] == "ChamadoAtribuido" and eventos[-1]["destinatario_id"] == contas["carla"]["id"]


def test_atribuir_repassa_o_token_para_usuarios(cliente, contas, servicos, eventos):
    cid = abrir(cliente, contas).json()["id"]
    cliente.patch(f"/chamados/{cid}/atribuir", headers=contas["carla"]["headers"],
                  json={"tecnico_id": contas["carla"]["id"]})
    assert servicos["tecnicos"][0]["token"] == contas["carla"]["headers"]["Authorization"]


def test_so_tecnico_pode_ser_atribuido(cliente, contas, servicos, eventos):
    cid = abrir(cliente, contas).json()["id"]
    r = cliente.patch(f"/chamados/{cid}/atribuir", headers=contas["carla"]["headers"],
                      json={"tecnico_id": contas["ana"]["id"]})
    assert r.status_code == 422


def test_atribuir_para_usuario_inexistente(cliente, contas, servicos, eventos):
    cid = abrir(cliente, contas).json()["id"]
    r = cliente.patch(f"/chamados/{cid}/atribuir", headers=contas["carla"]["headers"], json={"tecnico_id": 99})
    assert r.status_code == 404


def test_usuarios_fora_do_ar_responde_503(cliente, contas, servicos, eventos, monkeypatch):
    def fora_do_ar(tecnico_id, token):
        raise ServicoIndisponivel("O serviço de Usuários está indisponível no momento.")

    monkeypatch.setattr("app.servico.clientes.obter_tecnico", fora_do_ar)
    cid = abrir(cliente, contas).json()["id"]
    r = cliente.patch(f"/chamados/{cid}/atribuir", headers=contas["carla"]["headers"],
                      json={"tecnico_id": contas["carla"]["id"]})
    assert r.status_code == 503 and "Usuários" in r.json()["detail"]


# ---------- status ----------

def test_fluxo_completo_de_status(cliente, contas, servicos, eventos):
    cid = abrir(cliente, contas).json()["id"]
    tec = contas["carla"]["headers"]
    cliente.patch(f"/chamados/{cid}/atribuir", headers=tec, json={"tecnico_id": contas["carla"]["id"]})
    assert cliente.patch(f"/chamados/{cid}/status", headers=tec, json={"status": "resolvido"}).status_code == 200
    assert eventos[-1]["tipo"] == "ChamadoResolvido" and eventos[-1]["destinatario_id"] == contas["ana"]["id"]
    # o próprio solicitante confirma e fecha
    r = cliente.patch(f"/chamados/{cid}/status", headers=contas["ana"]["headers"], json={"status": "fechado"})
    assert r.json()["status"] == "fechado"


def test_transicao_invalida(cliente, contas, servicos):
    cid = abrir(cliente, contas).json()["id"]
    r = cliente.patch(f"/chamados/{cid}/status", headers=contas["carla"]["headers"], json={"status": "fechado"})
    assert r.status_code == 422


def test_iniciar_atendimento_sem_tecnico(cliente, contas, servicos):
    cid = abrir(cliente, contas).json()["id"]
    r = cliente.patch(f"/chamados/{cid}/status", headers=contas["carla"]["headers"],
                      json={"status": "em_atendimento"})
    assert r.status_code == 422


def test_solicitante_nao_atribui_nem_resolve(cliente, contas, servicos):
    cid = abrir(cliente, contas).json()["id"]
    h = contas["ana"]["headers"]
    assert cliente.patch(f"/chamados/{cid}/atribuir", headers=h,
                         json={"tecnico_id": contas["carla"]["id"]}).status_code == 403
    assert cliente.patch(f"/chamados/{cid}/status", headers=h,
                         json={"status": "em_atendimento"}).status_code == 403


# ---------- comentários e painel ----------

def test_comentar_usa_o_usuario_logado(cliente, contas, servicos):
    cid = abrir(cliente, contas).json()["id"]
    r = cliente.post(f"/chamados/{cid}/comentarios", headers=contas["carla"]["headers"],
                     json={"texto": "Verificando a fonte."})
    assert r.status_code == 201 and r.json()["autor_id"] == contas["carla"]["id"]
    assert len(cliente.get(f"/chamados/{cid}", headers=contas["ana"]["headers"]).json()["comentarios"]) == 1


def test_nao_da_para_comentar_em_nome_de_outro(cliente, contas, servicos):
    cid = abrir(cliente, contas).json()["id"]
    r = cliente.post(f"/chamados/{cid}/comentarios", headers=contas["ana"]["headers"],
                     json={"texto": "oi", "autor_id": contas["carla"]["id"]})
    assert r.status_code == 422


def test_chamado_fechado_nao_recebe_comentario(cliente, contas, servicos):
    cid = abrir(cliente, contas).json()["id"]
    tec = contas["carla"]["headers"]
    cliente.patch(f"/chamados/{cid}/atribuir", headers=tec, json={"tecnico_id": contas["carla"]["id"]})
    cliente.patch(f"/chamados/{cid}/status", headers=tec, json={"status": "resolvido"})
    cliente.patch(f"/chamados/{cid}/status", headers=tec, json={"status": "fechado"})
    r = cliente.post(f"/chamados/{cid}/comentarios", headers=tec, json={"texto": "depois"})
    assert r.status_code == 422


def test_painel(cliente, contas, servicos):
    abrir(cliente, contas)
    abrir(cliente, contas, prioridade="baixa")
    p = cliente.get("/chamados/painel", headers=contas["carla"]["headers"]).json()
    assert p["total"] == 2 and p["por_status"] == {"aberto": 2}


# ---------- permissões de leitura ----------

def test_solicitante_nao_ve_chamado_de_outra_pessoa(cliente, contas, servicos):
    cid = abrir(cliente, contas).json()["id"]
    assert cliente.get(f"/chamados/{cid}", headers=contas["bia"]["headers"]).status_code == 404
    assert cliente.get("/chamados", headers=contas["bia"]["headers"]).json() == []


def test_tecnico_ve_todos_os_chamados(cliente, contas, servicos):
    abrir(cliente, contas)
    assert len(cliente.get("/chamados", headers=contas["carla"]["headers"]).json()) == 1


def test_filtra_por_status(cliente, contas, servicos):
    abrir(cliente, contas)
    assert len(cliente.get("/chamados", params={"status": "aberto"},
                           headers=contas["carla"]["headers"]).json()) == 1
    assert cliente.get("/chamados", params={"status": "fechado"},
                       headers=contas["carla"]["headers"]).json() == []


# ---------- entrada, autenticação e saúde ----------

def test_rotas_exigem_login(cliente):
    assert cliente.get("/chamados").status_code == 401
    assert cliente.get("/chamados/painel").status_code == 401
    assert cliente.post("/chamados", json={}).status_code == 401


def test_saude_nao_exige_token(cliente):
    assert cliente.get("/saude").json() == {"status": "ok"}


def test_titulo_grande_demais(cliente, contas, servicos):
    assert abrir(cliente, contas, titulo="x" * 500).status_code == 422
