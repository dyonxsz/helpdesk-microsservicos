"""Chamadas HTTP aos serviços de Usuários e de Inventário.

Toda chamada repassa o token do usuário (cabeçalho Authorization) e usa um
tempo limite. Se o outro serviço estiver fora do ar, o Chamados responde 503
com uma mensagem clara em vez de travar.
"""
import logging
import os

import httpx

from comum.erros import NaoEncontrado, RegraDeNegocio, ServicoIndisponivel, SessaoInvalida

log = logging.getLogger("helpdesk.chamados.clientes")

USUARIOS_URL = os.getenv("USUARIOS_URL", "http://localhost:8001").rstrip("/")
INVENTARIO_URL = os.getenv("INVENTARIO_URL", "http://localhost:8002").rstrip("/")
TEMPO_LIMITE = float(os.getenv("HTTP_TIMEOUT", "3"))


def _obter(base: str, caminho: str, token: str, nome_servico: str, mensagem_404: str):
    try:
        resposta = httpx.get(f"{base}{caminho}", headers={"Authorization": token}, timeout=TEMPO_LIMITE)
    except httpx.TimeoutException as erro:
        raise ServicoIndisponivel(f"O serviço de {nome_servico} demorou demais para responder. Tente novamente.") from erro
    except httpx.HTTPError as erro:
        raise ServicoIndisponivel(f"O serviço de {nome_servico} está indisponível no momento.") from erro

    if resposta.status_code == 404:
        raise NaoEncontrado(mensagem_404)
    if resposta.status_code in (401, 403):
        raise SessaoInvalida("Sua sessão não é mais válida. Entre novamente.")
    if resposta.status_code != 200:
        raise ServicoIndisponivel(f"O serviço de {nome_servico} respondeu com erro ({resposta.status_code}).")

    try:
        return resposta.json()
    except ValueError as erro:
        raise ServicoIndisponivel(f"O serviço de {nome_servico} devolveu uma resposta inválida.") from erro


def obter_ativo(ativo_id: int, token: str) -> dict:
    """GET /ativos/{id} no serviço de Inventário."""
    dados = _obter(INVENTARIO_URL, f"/ativos/{ativo_id}", token, "Inventário", f"Ativo {ativo_id} não encontrado.")
    if dados.get("id") != ativo_id:
        raise ServicoIndisponivel("O serviço de Inventário devolveu um equipamento inesperado.")
    return dados


def obter_tecnico(tecnico_id: int, token: str) -> dict:
    """GET /usuarios/{id} no serviço de Usuários e confere o perfil."""
    dados = _obter(USUARIOS_URL, f"/usuarios/{tecnico_id}", token, "Usuários", f"Usuário {tecnico_id} não encontrado.")
    if dados.get("perfil") != "tecnico":
        raise RegraDeNegocio(f"Usuário {tecnico_id} não é técnico.")
    return dados


def listar_ativos(token: str) -> list[dict]:
    """GET /ativos no serviço de Inventário (usado só para os dados de exemplo)."""
    dados = _obter(INVENTARIO_URL, "/ativos", token, "Inventário", "Nenhum equipamento encontrado.")
    return dados if isinstance(dados, list) else []


def login(email: str, senha: str) -> dict:
    """POST /auth/login no serviço de Usuários (usado só para os dados de exemplo)."""
    try:
        resposta = httpx.post(
            f"{USUARIOS_URL}/auth/login", json={"email": email, "senha": senha}, timeout=TEMPO_LIMITE
        )
    except httpx.HTTPError as erro:
        raise ServicoIndisponivel("O serviço de Usuários está indisponível no momento.") from erro
    if resposta.status_code != 200:
        raise ServicoIndisponivel("Não foi possível entrar com a conta de exemplo.")
    dados = resposta.json()
    return {
        "id": dados["usuario"]["id"],
        "perfil": dados["usuario"]["perfil"],
        "token": f"Bearer {dados['access_token']}",
    }
