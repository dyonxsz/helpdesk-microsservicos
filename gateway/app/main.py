"""API Gateway: único ponto de entrada (porta 8000).

- serve a tela do HelpDesk;
- encaminha cada rota para o serviço certo (HTTP);
- responde 503 com mensagem clara se o serviço de destino estiver fora;
- mostra em /saude quais serviços estão no ar.

O gateway não confere o token: cada serviço faz isso. Ele apenas repassa o
cabeçalho Authorization, como o desafio pede.
"""
import asyncio
import os
from pathlib import Path

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, Response

from comum.seguranca_http import CabecalhosDeSeguranca

WEB = Path(__file__).parent.parent / "web"

USUARIOS_URL = os.getenv("USUARIOS_URL", "http://localhost:8001").rstrip("/")
INVENTARIO_URL = os.getenv("INVENTARIO_URL", "http://localhost:8002").rstrip("/")
CHAMADOS_URL = os.getenv("CHAMADOS_URL", "http://localhost:8003").rstrip("/")
NOTIFICACOES_URL = os.getenv("NOTIFICACOES_URL", "http://localhost:8004").rstrip("/")
TEMPO_LIMITE = float(os.getenv("PROXY_TIMEOUT", "10"))

# prefixo de rota -> (URL do serviço, nome para a mensagem de erro)
DESTINOS = [
    ("/auth", USUARIOS_URL, "Usuários"),
    ("/usuarios", USUARIOS_URL, "Usuários"),
    ("/ativos", INVENTARIO_URL, "Inventário"),
    ("/chamados", CHAMADOS_URL, "Chamados"),
    ("/notificacoes", NOTIFICACOES_URL, "Notificações"),
]

# Cabeçalhos que valem só para uma conexão e não devem ser repassados
CABECALHOS_DA_REQUISICAO = {
    "host", "content-length", "connection", "keep-alive", "transfer-encoding",
    "upgrade", "proxy-authorization", "proxy-authenticate", "te", "trailer",
}
CABECALHOS_DA_RESPOSTA = {
    "content-length", "content-encoding", "transfer-encoding", "connection", "keep-alive",
}

app = FastAPI(
    title="HelpDesk TI — API Gateway",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
app.add_middleware(CabecalhosDeSeguranca)

cliente_http = httpx.AsyncClient(timeout=httpx.Timeout(TEMPO_LIMITE, connect=3.0))


def destino(caminho: str) -> tuple[str, str] | tuple[None, None]:
    """Descobre qual serviço atende a rota (prefixo com limite de barra)."""
    for prefixo, url, nome in DESTINOS:
        if caminho == prefixo or caminho.startswith(prefixo + "/"):
            return url, nome
    return None, None


async def repassar(url: str, metodo: str, cabecalhos: dict, corpo: bytes, parametros):
    """Faz a chamada HTTP ao serviço de destino.

    Fica em uma função separada para os testes trocarem por uma versão falsa.
    """
    return await cliente_http.request(metodo, url, headers=cabecalhos, content=corpo, params=parametros)


async def verificar(url: str) -> str:
    """Confere a rota /saude de um serviço."""
    try:
        resposta = await cliente_http.get(f"{url}/saude", timeout=2)
    except httpx.HTTPError:
        return "fora do ar"
    return "ok" if resposta.status_code == 200 else f"erro {resposta.status_code}"


@app.get("/saude", tags=["Saúde"])
async def saude():
    """Mostra quais serviços estão no ar, sem derrubar o gateway."""
    nomes = [("usuarios", USUARIOS_URL), ("inventario", INVENTARIO_URL),
             ("chamados", CHAMADOS_URL), ("notificacoes", NOTIFICACOES_URL)]
    estados = await asyncio.gather(*(verificar(url) for _, url in nomes))
    servicos = {nome: estado for (nome, _), estado in zip(nomes, estados)}
    return {
        "status": "ok" if all(estado == "ok" for estado in servicos.values()) else "degradado",
        "servicos": servicos,
    }


@app.get("/", include_in_schema=False)
def tela_inicial():
    return FileResponse(WEB / "index.html")


@app.get("/app.js", include_in_schema=False)
def script():
    return FileResponse(WEB / "app.js", media_type="text/javascript")


@app.get("/estilo.css", include_in_schema=False)
def estilo():
    return FileResponse(WEB / "estilo.css", media_type="text/css")


@app.api_route(
    "/{caminho:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
    include_in_schema=False,
)
async def encaminhar(caminho: str, request: Request):
    url, nome = destino(f"/{caminho}")
    if url is None:
        return JSONResponse(status_code=404, content={"detail": "Rota não encontrada."})

    cabecalhos = {
        chave: valor for chave, valor in request.headers.items()
        if chave.lower() not in CABECALHOS_DA_REQUISICAO
    }
    try:
        resposta = await repassar(
            f"{url}/{caminho}", request.method, cabecalhos, await request.body(), request.query_params
        )
    except httpx.TimeoutException:
        return JSONResponse(
            status_code=503,
            content={"detail": f"O serviço de {nome} demorou demais para responder. Tente novamente."},
        )
    except httpx.HTTPError:
        return JSONResponse(
            status_code=503,
            content={"detail": f"O serviço de {nome} está indisponível no momento."},
        )

    return Response(
        content=resposta.content,
        status_code=resposta.status_code,
        headers={chave: valor for chave, valor in resposta.headers.items()
                 if chave.lower() not in CABECALHOS_DA_RESPOSTA},
    )
