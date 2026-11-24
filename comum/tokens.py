"""Criação e validação dos tokens JWT.

O token carrega o id e o perfil do usuário. Assim cada serviço confere a
assinatura sozinho, sem consultar o banco dos outros serviços.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt

from comum.config import JWT_ALGORITMO, JWT_EMISSOR, JWT_SEGREDO, TOKEN_MINUTOS

PERFIS = ("solicitante", "tecnico", "admin")


class TokenInvalido(Exception):
    """O token não é válido para este sistema."""


@dataclass(frozen=True)
class Identidade:
    """Quem está chamando a API, segundo o token (já verificado)."""

    id: int
    perfil: str


def criar(usuario_id: int, perfil: str) -> tuple[str, datetime]:
    agora = datetime.now(timezone.utc)
    expira = agora + timedelta(minutes=TOKEN_MINUTOS)
    dados = {
        "sub": str(usuario_id),
        "perfil": perfil,
        "iat": agora,
        "exp": expira,
        "iss": JWT_EMISSOR,
    }
    return jwt.encode(dados, JWT_SEGREDO, algorithm=JWT_ALGORITMO), expira


def ler(token: str) -> Identidade:
    """Devolve a identidade do token ou lança TokenInvalido."""
    try:
        dados = jwt.decode(
            token,
            JWT_SEGREDO,
            algorithms=[JWT_ALGORITMO],
            issuer=JWT_EMISSOR,
            options={"require": ["exp", "iat", "sub", "iss", "perfil"]},
        )
        perfil = dados["perfil"]
        if perfil not in PERFIS:
            raise TokenInvalido()
        return Identidade(int(dados["sub"]), perfil)
    except (jwt.PyJWTError, ValueError, KeyError, TypeError) as erro:
        raise TokenInvalido() from erro
