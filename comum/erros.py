"""Erros de negócio compartilhados pelos serviços."""


class NaoEncontrado(Exception):
    """O recurso pedido não existe (ou o usuário não pode vê-lo)."""


class RegraDeNegocio(Exception):
    """A operação viola uma regra do sistema."""


class SemPermissao(Exception):
    """O usuário está logado, mas não pode fazer esta operação."""


class SessaoInvalida(Exception):
    """O outro serviço recusou o token repassado (conta removida ou inativa)."""


class ServicoIndisponivel(Exception):
    """Outro serviço não respondeu dentro do tempo limite."""
