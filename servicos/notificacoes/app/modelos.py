from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from comum.banco import Base


class Notificacao(Base):
    __tablename__ = "notificacoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo: Mapped[str] = mapped_column(String(40))
    # Destinatário vive no banco de usuários; aqui guardamos só o id.
    destinatario_id: Mapped[int] = mapped_column()
    mensagem: Mapped[str] = mapped_column(String(300))
    criada_em: Mapped[datetime] = mapped_column(DateTime)
