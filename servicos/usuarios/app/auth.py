from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy.orm import Session

from app import limite, senhas, servico
from app.esquemas import UsuarioSaida
from app.modelos import Usuario
from comum import tokens
from comum.banco import get_db
from comum.dependencias import NAO_AUTENTICADO, identidade_atual

router = APIRouter(prefix="/auth", tags=["Autenticação"])


def usuario_atual(
    identidade: tokens.Identidade = Depends(identidade_atual),
    db: Session = Depends(get_db),
) -> Usuario:
    """Confirma que a conta do token ainda existe e está ativa.

    Só o serviço de Usuários tem o banco de usuários, então é o único que
    consegue fazer esta checagem. Os outros serviços confiam na assinatura.
    """
    usuario = db.get(Usuario, identidade.id)
    if usuario is None or not usuario.ativo:
        raise NAO_AUTENTICADO
    return usuario


def exigir_usuario_perfil(*perfis: str):
    def verificar(usuario: Usuario = Depends(usuario_atual)) -> Usuario:
        if usuario.perfil not in perfis:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não tem permissão para esta ação.",
            )
        return usuario

    return verificar


class Login(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr
    senha: str = Field(min_length=1, max_length=128)


class TokenSaida(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expira_em: datetime
    usuario: UsuarioSaida


@router.post("/login", response_model=TokenSaida)
def login(dados: Login, request: Request, db: Session = Depends(get_db)):
    email = dados.email.lower()
    chave = f"{email}|{request.client.host if request.client else '-'}"
    if limite.bloqueado(chave):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Muitas tentativas. Tente de novo em alguns minutos.")

    usuario = servico.buscar_por_email(db, email)
    # Confere a senha mesmo sem usuário, para o tempo de resposta não revelar se o e-mail existe
    senha_ok = senhas.conferir(dados.senha, usuario.senha_hash if usuario else senhas.HASH_FALSO)
    if not usuario or not senha_ok or not usuario.ativo:
        limite.registrar_falha(chave)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "E-mail ou senha inválidos.")

    limite.limpar(chave)
    token, expira = tokens.criar(usuario.id, usuario.perfil)
    return TokenSaida(access_token=token, expira_em=expira, usuario=UsuarioSaida.model_validate(usuario))


@router.get("/eu", response_model=UsuarioSaida)
def quem_sou_eu(usuario: Usuario = Depends(usuario_atual)):
    return usuario
