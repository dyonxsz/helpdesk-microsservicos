from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import servico
from app.auth import exigir_usuario_perfil, usuario_atual
from app.esquemas import Perfil, UsuarioCriar, UsuarioPublico, UsuarioSaida
from app.modelos import Usuario
from comum.banco import get_db

router = APIRouter(prefix="/usuarios", tags=["Usuários"])


@router.post("", response_model=UsuarioSaida, status_code=201)
def criar_usuario(
    dados: UsuarioCriar,
    usuario: Usuario = Depends(exigir_usuario_perfil("admin")),
    db: Session = Depends(get_db),
):
    return servico.criar(db, dados)


@router.get("", response_model=list[UsuarioPublico])
def listar_usuarios(
    perfil: Perfil | None = None,
    usuario: Usuario = Depends(usuario_atual),
    db: Session = Depends(get_db),
):
    return servico.listar(db, perfil)


@router.get("/{usuario_id}", response_model=UsuarioPublico)
def obter_usuario(
    usuario_id: int,
    usuario: Usuario = Depends(usuario_atual),
    db: Session = Depends(get_db),
):
    """Usado pelo serviço de Chamados para conferir se o técnico existe."""
    return servico.obter(db, usuario_id)
