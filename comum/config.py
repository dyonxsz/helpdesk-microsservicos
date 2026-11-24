"""Configurações compartilhadas, lidas das variáveis de ambiente."""
import logging
import os
import secrets

log = logging.getLogger("helpdesk")

# Os serviços logam no logger "helpdesk" (e filhos). Sem um handler próprio, o
# nível padrão do Python (WARNING) esconderia os eventos consumidos, que são
# registrados em INFO.
if not log.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(levelname)s: %(name)s - %(message)s"))
    log.addHandler(_handler)
log.setLevel(os.getenv("LOG_LEVEL", "INFO"))
log.propagate = False


def _segredo_jwt() -> str:
    """Lê JWT_SEGREDO do ambiente; se faltar, gera um segredo temporário."""
    segredo = os.getenv("JWT_SEGREDO") or ""
    if len(segredo) < 32:
        if segredo:
            log.warning("JWT_SEGREDO tem menos de 32 caracteres; usando um segredo aleatório.")
        segredo = secrets.token_urlsafe(48)
    return segredo


# Todos os serviços precisam do MESMO segredo para conferir o token uns dos outros.
JWT_SEGREDO = _segredo_jwt()
JWT_ALGORITMO = "HS256"
JWT_EMISSOR = "helpdesk-ti"
TOKEN_MINUTOS = int(os.getenv("TOKEN_MINUTOS", "60"))

# Proteção contra tentativas de adivinhar senhas (usada no serviço de Usuários)
LOGIN_MAX_FALHAS = int(os.getenv("LOGIN_MAX_FALHAS", "5"))
LOGIN_JANELA_SEGUNDOS = int(os.getenv("LOGIN_JANELA_SEGUNDOS", "300"))

# Tamanho máximo do corpo de uma requisição (em bytes)
TAMANHO_MAXIMO_REQUISICAO = 64 * 1024

DOCS_ATIVA = os.getenv("DOCS", "1") == "1"

# Cada serviço recebe a sua própria URL de banco pelo ambiente.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./helpdesk.db")
