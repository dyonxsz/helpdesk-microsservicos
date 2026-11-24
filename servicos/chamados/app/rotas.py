from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app import servico
from app.esquemas import (
    Atribuicao, ChamadoCriar, ChamadoSaida, ComentarioCriar, ComentarioSaida, MudancaStatus, Painel, Status,
)
from comum.banco import get_db
from comum.dependencias import identidade_atual
from comum.tokens import Identidade

router = APIRouter(prefix="/chamados", tags=["Chamados"])


@router.post("", response_model=ChamadoSaida, status_code=201)
def abrir_chamado(
    dados: ChamadoCriar,
    request: Request,
    usuario: Identidade = Depends(identidade_atual),
    db: Session = Depends(get_db),
):
    # Repassa o token do usuário na chamada ao Inventário
    return servico.abrir(db, dados, usuario, request.headers.get("authorization", ""))


@router.get("", response_model=list[ChamadoSaida])
def listar_chamados(
    status: Status | None = None,
    tecnico_id: int | None = None,
    usuario: Identidade = Depends(identidade_atual),
    db: Session = Depends(get_db),
):
    return servico.listar(db, usuario, status, tecnico_id)


@router.get("/painel", response_model=Painel)
def painel(usuario: Identidade = Depends(identidade_atual), db: Session = Depends(get_db)):
    return servico.painel(db, usuario)


@router.get("/{chamado_id}", response_model=ChamadoSaida)
def obter_chamado(
    chamado_id: int,
    usuario: Identidade = Depends(identidade_atual),
    db: Session = Depends(get_db),
):
    return servico.obter(db, chamado_id, usuario)


@router.patch("/{chamado_id}/atribuir", response_model=ChamadoSaida)
def atribuir_chamado(
    chamado_id: int,
    dados: Atribuicao,
    request: Request,
    usuario: Identidade = Depends(identidade_atual),
    db: Session = Depends(get_db),
):
    # Repassa o token do usuário na chamada ao serviço de Usuários
    return servico.atribuir(db, chamado_id, dados.tecnico_id, usuario, request.headers.get("authorization", ""))


@router.patch("/{chamado_id}/status", response_model=ChamadoSaida)
def mudar_status(
    chamado_id: int,
    dados: MudancaStatus,
    usuario: Identidade = Depends(identidade_atual),
    db: Session = Depends(get_db),
):
    return servico.mudar_status(db, chamado_id, dados.status, usuario)


@router.post("/{chamado_id}/comentarios", response_model=ComentarioSaida, status_code=201)
def comentar(
    chamado_id: int,
    dados: ComentarioCriar,
    usuario: Identidade = Depends(identidade_atual),
    db: Session = Depends(get_db),
):
    return servico.comentar(db, chamado_id, dados, usuario)
