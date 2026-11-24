"""Publicação dos eventos de chamado em uma fila (Redis Streams).

Se o Redis estiver fora do ar, o chamado continua funcionando: o erro só é
registrado no log. A notificação é um efeito colateral, não um requisito para
abrir ou alterar um chamado.
"""
import logging
import os
from datetime import datetime, timezone

import redis

log = logging.getLogger("helpdesk.chamados.eventos")

REDIS_URL = os.getenv("REDIS_URL", "")
STREAM = os.getenv("EVENTOS_STREAM", "helpdesk:eventos")


def publicar(tipo: str, destinatario_id: int, mensagem: str, chamado_id: int) -> bool:
    """Publica um evento. Devolve False quando não há fila configurada ou ela falha."""
    if not REDIS_URL:
        return False
    try:
        cliente = redis.from_url(REDIS_URL, decode_responses=True, socket_timeout=1, socket_connect_timeout=1)
        cliente.xadd(
            STREAM,
            {
                "tipo": tipo,
                "destinatario_id": str(destinatario_id),
                "mensagem": mensagem,
                "chamado_id": str(chamado_id),
                "criado_em": datetime.now(timezone.utc).isoformat(),
            },
            maxlen=1000,
            approximate=True,
        )
        return True
    except Exception as erro:  # a fila nunca pode derrubar o fluxo do chamado
        log.warning("Não foi possível publicar %s: %s", tipo, erro)
        return False
