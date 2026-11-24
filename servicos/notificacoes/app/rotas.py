from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import servico
from app.esquemas import NotificacaoSaida
from comum.banco import get_db
from comum.dependencias import identidade_atual
from comum.tokens import Identidade

router = APIRouter(prefix="/notificacoes", tags=["Notificações"])


@router.get("", response_model=list[NotificacaoSaida])
def minhas_notificacoes(
    identidade: Identidade = Depends(identidade_atual),
    db: Session = Depends(get_db),
):
    """Cada usuário vê só as próprias notificações."""
    return servico.listar(db, identidade.id)
