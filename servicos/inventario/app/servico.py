"""Regras do serviço de Inventário. É a porta pública do serviço."""
from sqlalchemy.orm import Session

from app import repositorio
from app.esquemas import AtivoCriar
from app.modelos import Ativo
from comum.erros import NaoEncontrado, RegraDeNegocio


def criar(db: Session, dados: AtivoCriar) -> Ativo:
    if repositorio.buscar_por_patrimonio(db, dados.patrimonio):
        raise RegraDeNegocio("Já existe um ativo com este patrimônio.")
    return repositorio.salvar(db, Ativo(**dados.model_dump()))


def obter(db: Session, ativo_id: int) -> Ativo:
    ativo = repositorio.buscar_por_id(db, ativo_id)
    if ativo is None:
        raise NaoEncontrado(f"Ativo {ativo_id} não encontrado.")
    return ativo


def listar(db: Session, setor: str | None = None) -> list[Ativo]:
    return repositorio.listar(db, setor)
