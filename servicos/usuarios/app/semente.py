"""Cria os usuários de exemplo quando o banco está vazio.

Uso apenas em aula: todos os usuários de exemplo têm a mesma senha
(variável SENHA_EXEMPLO). Em produção, rode com DADOS_EXEMPLO=0.
"""
import os

from sqlalchemy.orm import Session

from app import servico
from app.esquemas import UsuarioCriar

SENHA = os.getenv("SENHA_EXEMPLO", "Helpdesk2026")

CONTAS = [
    ("Admin TI", "admin@empresa.com", "admin"),
    ("Ana Souza", "ana@empresa.com", "solicitante"),
    ("Bruno Lima", "bruno@empresa.com", "solicitante"),
    ("Carla Dias", "carla@empresa.com", "tecnico"),
    ("Diego Rocha", "diego@empresa.com", "tecnico"),
]


def carregar(db: Session) -> None:
    if servico.listar(db):
        return
    for nome, email, perfil in CONTAS:
        servico.criar(db, UsuarioCriar(nome=nome, email=email, perfil=perfil, senha=SENHA))
