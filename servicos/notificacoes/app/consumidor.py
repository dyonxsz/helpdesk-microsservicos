"""Consumidor dos eventos de chamado (Redis Streams).

O serviço de Chamados publica e continua a vida dele; se este consumidor
estiver fora do ar, os eventos ficam guardados no stream e são entregues
quando ele voltar (consumer group). Se o Redis cair, este serviço continua
respondendo /notificacoes com o que já tem gravado.
"""
import asyncio
import logging
import os
import socket

import redis
from sqlalchemy.orm import Session, sessionmaker

from app import servico
from comum.banco import SessionLocal

log = logging.getLogger("helpdesk.notificacoes.consumidor")

REDIS_URL = os.getenv("REDIS_URL", "")
STREAM = os.getenv("EVENTOS_STREAM", "helpdesk:eventos")
GRUPO = os.getenv("EVENTOS_GRUPO", "notificacoes")
CONSUMIDOR = f"{socket.gethostname()}-{os.getpid()}"


def criar_grupo(cliente) -> None:
    """Cria o consumer group se ainda não existir."""
    try:
        cliente.xgroup_create(STREAM, GRUPO, id="0", mkstream=True)
    except redis.ResponseError as erro:
        if "BUSYGROUP" not in str(erro):
            raise


def registrar_evento(db: Session, campos: dict) -> None:
    """Valida um evento do stream e grava a notificação."""
    tipo = str(campos.get("tipo") or "").strip()
    mensagem = str(campos.get("mensagem") or "").strip()
    if not tipo or not mensagem:
        raise ValueError("evento sem tipo ou mensagem")
    destinatario_id = int(campos.get("destinatario_id", ""))
    if destinatario_id <= 0:
        raise ValueError("destinatário inválido")
    servico.registrar(db, tipo, destinatario_id, mensagem)


def consumir_uma_vez(cliente, sessao_factory: sessionmaker = SessionLocal) -> int:
    """Lê um lote do stream, grava e confirma (XACK) cada mensagem."""
    resposta = cliente.xreadgroup(GRUPO, CONSUMIDOR, {STREAM: ">"}, count=10, block=1000)
    total = 0
    for _, mensagens in resposta or []:
        for msg_id, campos in mensagens:
            with sessao_factory() as db:
                try:
                    registrar_evento(db, campos)
                    total += 1
                    log.info("Evento %s gravado para o usuário %s", campos.get("tipo"), campos.get("destinatario_id"))
                except (ValueError, TypeError) as erro:
                    log.warning("Evento inválido %s ignorado: %s", msg_id, erro)
            cliente.xack(STREAM, GRUPO, msg_id)
    return total


async def consumir_para_sempre() -> None:
    """Fica lendo eventos; reconecta sozinho se o Redis cair."""
    if not REDIS_URL:
        log.info("REDIS_URL não configurado; consumidor de notificações desligado.")
        return

    while True:
        try:
            cliente = redis.from_url(
                REDIS_URL, decode_responses=True, socket_timeout=5, socket_connect_timeout=2
            )
            criar_grupo(cliente)
            log.info("Consumindo eventos do stream %s", STREAM)
            while True:
                await asyncio.to_thread(consumir_uma_vez, cliente)
        except asyncio.CancelledError:
            raise
        except Exception as erro:  # Redis fora do ar: tenta de novo em instantes
            log.warning("Consumidor de notificações aguardando o Redis: %s", erro)
            await asyncio.sleep(2)
