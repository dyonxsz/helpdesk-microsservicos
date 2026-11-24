"""Regras do serviço de Notificações. É a porta pública do serviço."""
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modelos import Notificacao


def registrar(db: Session, tipo: str, destinatario_id: int, mensagem: str) -> Notificacao:
    """Grava um aviso. No mundo real, aqui também sairia um e-mail ou SMS."""
    aviso = Notificacao(
        tipo=tipo[:40],
        destinatario_id=destinatario_id,
        mensagem=mensagem[:300],
        criada_em=datetime.now(),
    )
    db.add(aviso)
    db.commit()
    db.refresh(aviso)
    return aviso


def listar(db: Session, destinatario_id: int) -> list[Notificacao]:
    consulta = select(Notificacao).where(Notificacao.destinatario_id == destinatario_id).order_by(Notificacao.id)
    return list(db.scalars(consulta))
