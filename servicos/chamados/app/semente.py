"""Cria chamados de exemplo quando o banco está vazio.

Diferente dos outros serviços, o Chamados não tem os dados de usuários nem de
equipamentos: ele precisa pedir os ids ao serviço de Usuários (login) e ao de
Inventário. Se eles ainda não estiverem no ar, tenta algumas vezes e desiste
sem impedir o serviço de subir.
"""
import logging
import os
import time

from sqlalchemy.orm import Session

from app import clientes, repositorio, servico
from app.esquemas import ChamadoCriar
from comum.erros import ServicoIndisponivel
from comum.tokens import Identidade

log = logging.getLogger("helpdesk.chamados.semente")

SENHA = os.getenv("SENHA_EXEMPLO", "Helpdesk2026")
TENTATIVAS = int(os.getenv("SEMENTE_TENTATIVAS", "15"))


def _com_tentativas(funcao):
    for tentativa in range(1, TENTATIVAS + 1):
        try:
            return funcao()
        except ServicoIndisponivel as erro:
            if tentativa == TENTATIVAS:
                raise
            log.info("Aguardando outro serviço para criar dados de exemplo (%s/%s): %s", tentativa, TENTATIVAS, erro)
            time.sleep(1)


def carregar(db: Session) -> None:
    if os.getenv("DADOS_EXEMPLO", "1") != "1":
        return
    if repositorio.listar(db):
        return

    try:
        ana = _com_tentativas(lambda: clientes.login("ana@empresa.com", SENHA))
        bruno = _com_tentativas(lambda: clientes.login("bruno@empresa.com", SENHA))
        carla = _com_tentativas(lambda: clientes.login("carla@empresa.com", SENHA))
        ativos = _com_tentativas(lambda: clientes.listar_ativos(ana["token"]))
    except ServicoIndisponivel as erro:
        log.warning("Sem dados de exemplo: %s", erro)
        return

    ativo_1 = ativos[0]["id"] if ativos else None
    ativo_2 = ativos[1]["id"] if len(ativos) > 1 else None

    c1 = servico.abrir(
        db,
        ChamadoCriar(titulo="Computador não liga", descricao="Apertei o botão e nada acontece.",
                     prioridade="alta", ativo_id=ativo_1),
        Identidade(ana["id"], "solicitante"), ana["token"],
    )
    servico.abrir(
        db,
        ChamadoCriar(titulo="Impressora atolando papel", descricao="Atola a cada 3 folhas.",
                     prioridade="media", ativo_id=ativo_2),
        Identidade(bruno["id"], "solicitante"), bruno["token"],
    )
    servico.abrir(
        db,
        ChamadoCriar(titulo="Acesso ao sistema de RH", descricao="Preciso de acesso para a nova estagiária.",
                     prioridade="baixa"),
        Identidade(bruno["id"], "solicitante"), bruno["token"],
    )
    servico.atribuir(db, c1.id, carla["id"], Identidade(carla["id"], "tecnico"), carla["token"])
