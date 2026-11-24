"""Dependências do FastAPI para exigir login e perfil.

A confiança vem da assinatura do token: nenhum serviço consulta o banco de
outro para saber quem é o usuário. Quem precisa confirmar que a conta ainda
existe (o serviço de Usuários) faz essa checagem no próprio banco.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from comum import tokens

esquema = HTTPBearer(auto_error=False)

NAO_AUTENTICADO = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Faça login para continuar.",
    headers={"WWW-Authenticate": "Bearer"},
)


def identidade_atual(
    credenciais: HTTPAuthorizationCredentials | None = Depends(esquema),
) -> tokens.Identidade:
    if credenciais is None or credenciais.scheme.lower() != "bearer":
        raise NAO_AUTENTICADO
    try:
        return tokens.ler(credenciais.credentials)
    except tokens.TokenInvalido:
        raise NAO_AUTENTICADO


def exigir_perfil(*perfis: str):
    """Libera a rota só para os perfis informados."""

    def verificar(identidade: tokens.Identidade = Depends(identidade_atual)) -> tokens.Identidade:
        if identidade.perfil not in perfis:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não tem permissão para esta ação.",
            )
        return identidade

    return verificar
