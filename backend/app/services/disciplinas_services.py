from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Disciplina
from app.schemas import DisciplinaIn, DisciplinaUpdateIn
from app.services.transacoes import confirmar_transacao


def listar_disciplinas(db: Session):
    return db.scalars(select(Disciplina).order_by(Disciplina.id)).all()


def buscar_disciplina(db: Session, id: int):
    dados = db.get(Disciplina, id)
    if dados is None:
        raise HTTPException(status_code=404, detail="Disciplina não encontrada")
    return dados


def cadastrar_disciplina(db: Session, disciplina: DisciplinaIn):
    dados = Disciplina(**disciplina.model_dump())
    db.add(dados)
    confirmar_transacao(db)
    db.refresh(dados)
    return dados


def atualizar_disciplina(db: Session, id: int, disciplina: DisciplinaUpdateIn):
    dados = buscar_disciplina(db, id)
    campos = disciplina.model_dump(exclude_unset=True)
    for campo, valor in campos.items():
        setattr(dados, campo, valor)
    confirmar_transacao(db)
    db.refresh(dados)
    return dados


def deletar_disciplina(db: Session, id: int):
    dados = buscar_disciplina(db, id)
    db.delete(dados)
    confirmar_transacao(db)
