from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Aluno
from app.schemas import AlunoIn, AlunoUpdateIn
from app.services.transacoes import confirmar_transacao


def listar_alunos(db: Session):
    return db.scalars(select(Aluno).order_by(Aluno.id)).all()


def buscar_aluno(db: Session, id: int):
    dados = db.get(Aluno, id)
    if dados is None:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
    return dados


def cadastrar_aluno(db: Session, aluno: AlunoIn):
    dados = Aluno(
        matricula=aluno.matricula,
        nome_aluno=aluno.nome_aluno,
        email=aluno.email,
        endereco_id=aluno.endereco_id
    )
    db.add(dados)
    confirmar_transacao(db)
    db.refresh(dados)
    return dados


def atualizar_aluno(db: Session, id: int, aluno: AlunoUpdateIn):
    dados = buscar_aluno(db, id)
    campos = aluno.model_dump(exclude_unset=True)
    for campo, valor in campos.items():
        setattr(dados, campo, valor)
    confirmar_transacao(db)
    db.refresh(dados)
    return dados


def deletar_aluno(db: Session, id: int):
    dados = buscar_aluno(db, id)
    db.delete(dados)
    confirmar_transacao(db)
