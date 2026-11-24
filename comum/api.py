"""Fábrica de aplicação FastAPI usada por todos os serviços.

Deixa igual em todos: documentação, cabeçalhos de segurança, erros de negócio
e a rota de saúde.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from comum.config import DOCS_ATIVA
from comum.erros import NaoEncontrado, RegraDeNegocio, SemPermissao, ServicoIndisponivel, SessaoInvalida
from comum.seguranca_http import CabecalhosDeSeguranca


def criar_app(titulo: str, versao: str, ciclo_de_vida=None) -> FastAPI:
    app = FastAPI(
        title=titulo,
        version=versao,
        lifespan=ciclo_de_vida,
        docs_url="/docs" if DOCS_ATIVA else None,
        redoc_url=None,
        openapi_url="/openapi.json" if DOCS_ATIVA else None,
    )
    app.add_middleware(CabecalhosDeSeguranca)

    @app.exception_handler(NaoEncontrado)
    def tratar_nao_encontrado(request: Request, erro: NaoEncontrado):
        return JSONResponse(status_code=404, content={"detail": str(erro)})

    @app.exception_handler(RegraDeNegocio)
    def tratar_regra(request: Request, erro: RegraDeNegocio):
        return JSONResponse(status_code=422, content={"detail": str(erro)})

    @app.exception_handler(SemPermissao)
    def tratar_sem_permissao(request: Request, erro: SemPermissao):
        return JSONResponse(status_code=403, content={"detail": str(erro)})

    @app.exception_handler(SessaoInvalida)
    def tratar_sessao_invalida(request: Request, erro: SessaoInvalida):
        return JSONResponse(
            status_code=401,
            content={"detail": str(erro)},
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(ServicoIndisponivel)
    def tratar_servico_indisponivel(request: Request, erro: ServicoIndisponivel):
        return JSONResponse(status_code=503, content={"detail": str(erro)})

    @app.exception_handler(IntegrityError)
    def tratar_conflito(request: Request, erro: IntegrityError):
        # Não expõe detalhes do banco na resposta
        return JSONResponse(status_code=409, content={"detail": "O registro conflita com outro já existente."})

    @app.get("/saude", tags=["Saúde"])
    def saude():
        return {"status": "ok"}

    return app
