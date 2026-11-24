"""Cria os equipamentos de exemplo quando o banco está vazio."""
import os

from sqlalchemy.orm import Session

from app import servico
from app.esquemas import AtivoCriar

ATIVOS = [
    ("PAT-0001", "computador", "Desktop Dell OptiPlex", "Financeiro"),
    ("PAT-0002", "impressora", "Impressora HP LaserJet", "RH"),
    ("PAT-0003", "notebook", "Notebook Lenovo ThinkPad", "TI"),
]


def carregar(db: Session) -> None:
    if os.getenv("DADOS_EXEMPLO", "1") != "1":
        return
    if servico.listar(db):
        return
    for patrimonio, tipo, descricao, setor in ATIVOS:
        servico.criar(db, AtivoCriar(patrimonio=patrimonio, tipo=tipo, descricao=descricao, setor=setor))
