"""Testes do API Gateway: tela, roteamento, falhas e /saude."""
import httpx
import pytest

from app import main as gateway


# ---------- tela ----------

def test_serve_a_tela(cliente):
    r = cliente.get("/")
    assert r.status_code == 200 and "text/html" in r.headers["content-type"]
    assert "HelpDesk" in r.text
    assert "script-src 'self'" in r.headers["content-security-policy"]


def test_serve_os_arquivos_da_tela(cliente):
    assert cliente.get("/app.js").status_code == 200
    assert "text/css" in cliente.get("/estilo.css").headers["content-type"]


# ---------- roteamento ----------

@pytest.mark.parametrize(("caminho", "destino"), [
    ("/auth/login", "http://usuarios-teste:8000/auth/login"),
    ("/auth/eu", "http://usuarios-teste:8000/auth/eu"),
    ("/usuarios", "http://usuarios-teste:8000/usuarios"),
    ("/usuarios/4", "http://usuarios-teste:8000/usuarios/4"),
    ("/ativos/1", "http://inventario-teste:8000/ativos/1"),
    ("/chamados/painel", "http://chamados-teste:8000/chamados/painel"),
    ("/chamados/2/comentarios", "http://chamados-teste:8000/chamados/2/comentarios"),
    ("/notificacoes", "http://notificacoes-teste:8000/notificacoes"),
])
def test_encaminha_para_o_servico_certo(cliente, chamadas, caminho, destino):
    assert cliente.get(caminho).status_code == 200
    assert chamadas[0]["url"] == destino


def test_repassa_o_token(cliente, chamadas):
    cliente.get("/chamados", headers={"Authorization": "Bearer token-da-ana"})
    assert chamadas[0]["cabecalhos"]["authorization"] == "Bearer token-da-ana"


def test_repassa_o_corpo_e_o_metodo(cliente, chamadas):
    cliente.post("/chamados", json={"titulo": "PC", "descricao": "Nao liga", "prioridade": "alta"})
    assert chamadas[0]["metodo"] == "POST"
    assert b'"titulo"' in chamadas[0]["corpo"]


def test_repassa_a_query_string(cliente, chamadas):
    cliente.get("/chamados?status=aberto&tecnico_id=4")
    assert chamadas[0]["parametros"]["status"] == "aberto"
    assert chamadas[0]["parametros"]["tecnico_id"] == "4"


def test_resposta_do_servico_e_repassada(cliente, chamadas, monkeypatch):
    async def resposta_422(url, metodo, cabecalhos, corpo, parametros):
        return httpx.Response(422, json={"detail": "Não é possível ir de 'aberto' para 'fechado'."})

    monkeypatch.setattr(gateway, "repassar", resposta_422)
    r = cliente.patch("/chamados/1/status", json={"status": "fechado"})
    assert r.status_code == 422 and "aberto" in r.json()["detail"]


def test_401_do_servico_mantem_o_cabecalho(cliente, chamadas, monkeypatch):
    async def resposta_401(url, metodo, cabecalhos, corpo, parametros):
        return httpx.Response(401, json={"detail": "Faça login para continuar."},
                              headers={"WWW-Authenticate": "Bearer"})

    monkeypatch.setattr(gateway, "repassar", resposta_401)
    r = cliente.get("/chamados")
    assert r.status_code == 401 and r.headers["www-authenticate"] == "Bearer"


# ---------- falhas ----------

def test_servico_fora_do_ar_responde_503(cliente, chamadas, monkeypatch):
    async def fora_do_ar(url, metodo, cabecalhos, corpo, parametros):
        raise httpx.ConnectError("sem conexão")

    monkeypatch.setattr(gateway, "repassar", fora_do_ar)
    r = cliente.get("/chamados")
    assert r.status_code == 503 and "Chamados" in r.json()["detail"]


def test_timeout_responde_503(cliente, chamadas, monkeypatch):
    async def demorou(url, metodo, cabecalhos, corpo, parametros):
        raise httpx.TimeoutException("demorou")

    monkeypatch.setattr(gateway, "repassar", demorou)
    r = cliente.get("/ativos")
    assert r.status_code == 503 and "Inventário" in r.json()["detail"]


def test_rota_desconhecida_responde_404(cliente, chamadas):
    r = cliente.get("/nao-existe")
    assert r.status_code == 404 and chamadas == []


def test_requisicao_grande_demais(cliente):
    corpo = '{"titulo": "' + "x" * 70000 + '"}'
    r = cliente.post("/chamados", headers={"Content-Type": "application/json"}, content=corpo)
    assert r.status_code == 413


# ---------- saúde ----------

def test_saude_mostra_quais_servicos_estao_no_ar(cliente, monkeypatch):
    async def verificar_falso(url):
        return "fora do ar" if "inventario" in url else "ok"

    monkeypatch.setattr(gateway, "verificar", verificar_falso)
    r = cliente.get("/saude")
    assert r.status_code == 200
    assert r.json()["status"] == "degradado"
    assert r.json()["servicos"] == {
        "usuarios": "ok", "inventario": "fora do ar", "chamados": "ok", "notificacoes": "ok",
    }


def test_saude_com_todos_no_ar(cliente, monkeypatch):
    async def verificar_falso(url):
        return "ok"

    monkeypatch.setattr(gateway, "verificar", verificar_falso)
    assert cliente.get("/saude").json()["status"] == "ok"
