"""Testes do publicador de eventos: a fila nunca pode derrubar o chamado."""
from app import eventos


def test_sem_redis_configurado_nao_publica_e_nao_falha(monkeypatch):
    monkeypatch.setattr(eventos, "REDIS_URL", "")
    assert eventos.publicar("ChamadoAberto", 1, "oi", 1) is False


def test_redis_fora_do_ar_nao_levanta_excecao(monkeypatch):
    monkeypatch.setattr(eventos, "REDIS_URL", "redis://localhost:6399/0")

    def explodir(*args, **kwargs):
        raise ConnectionError("sem conexão")

    monkeypatch.setattr(eventos.redis, "from_url", explodir)
    assert eventos.publicar("ChamadoAberto", 1, "oi", 1) is False


def test_evento_publicado_no_stream(monkeypatch):
    chamadas = {}

    class ClienteFalso:
        def xadd(self, stream, campos, maxlen=None, approximate=None):
            chamadas.update({"stream": stream, "campos": campos})
            return "1-0"

    monkeypatch.setattr(eventos, "REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setattr(eventos.redis, "from_url", lambda *args, **kwargs: ClienteFalso())
    assert eventos.publicar("ChamadoAtribuido", 4, "atribuído", 7) is True
    assert chamadas["stream"] == eventos.STREAM
    assert chamadas["campos"]["tipo"] == "ChamadoAtribuido"
    assert chamadas["campos"]["destinatario_id"] == "4"
    assert chamadas["campos"]["chamado_id"] == "7"
