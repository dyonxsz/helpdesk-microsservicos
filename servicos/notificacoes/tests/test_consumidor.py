"""Testes do consumidor de eventos (sem Redis de verdade)."""
import asyncio

import pytest
import redis

from app import consumidor, servico

EVENTO = {
    "tipo": "ChamadoAberto",
    "destinatario_id": "2",
    "mensagem": "Seu chamado #1 foi aberto.",
    "chamado_id": "1",
    "criado_em": "2026-01-01T10:00:00+00:00",
}


def test_registrar_evento_valido(sessao):
    with sessao() as db:
        consumidor.registrar_evento(db, EVENTO)
        lista = servico.listar(db, 2)
    assert len(lista) == 1 and lista[0].tipo == "ChamadoAberto"


@pytest.mark.parametrize("campos", [
    {},
    {"tipo": "ChamadoAberto"},
    {"tipo": "", "destinatario_id": "2", "mensagem": "oi"},
    {"tipo": "ChamadoAberto", "destinatario_id": "0", "mensagem": "oi"},
    {"tipo": "ChamadoAberto", "destinatario_id": "abc", "mensagem": "oi"},
])
def test_evento_invalido_e_recusado(sessao, campos):
    with sessao() as db:
        with pytest.raises((ValueError, TypeError)):
            consumidor.registrar_evento(db, campos)


class ClienteFalso:
    def __init__(self, resposta):
        self.resposta = resposta
        self.acks = []

    def xreadgroup(self, *args, **kwargs):
        return self.resposta

    def xack(self, stream, grupo, msg_id):
        self.acks.append(msg_id)


def test_consome_lote_grava_e_confirma(sessao):
    invalido = {"tipo": "ChamadoAberto"}
    cliente = ClienteFalso([[consumidor.STREAM, [("1-0", EVENTO), ("2-0", invalido)]]])
    total = consumidor.consumir_uma_vez(cliente, sessao)
    assert total == 1
    assert cliente.acks == ["1-0", "2-0"]  # o inválido também é confirmado, para não travar a fila
    with sessao() as db:
        assert len(servico.listar(db, 2)) == 1


def test_consumir_sem_mensagens_nao_falha(sessao):
    assert consumidor.consumir_uma_vez(ClienteFalso([]), sessao) == 0
    assert consumidor.consumir_uma_vez(ClienteFalso(None), sessao) == 0


def test_criar_grupo_ignora_busygroup():
    class Cliente:
        def xgroup_create(self, *args, **kwargs):
            raise redis.ResponseError("BUSYGROUP Consumer Group name already exists")

    consumidor.criar_grupo(Cliente())  # não deve levantar


def test_criar_grupo_propaga_outros_erros():
    class Cliente:
        def xgroup_create(self, *args, **kwargs):
            raise redis.ResponseError("ERR something else")

    with pytest.raises(redis.ResponseError):
        consumidor.criar_grupo(Cliente())


def test_consumidor_desligado_sem_redis(monkeypatch):
    monkeypatch.setattr(consumidor, "REDIS_URL", "")
    asyncio.run(consumidor.consumir_para_sempre())  # retorna na hora, sem erro
