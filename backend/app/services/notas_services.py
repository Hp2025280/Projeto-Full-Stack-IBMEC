from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Nota
from app.schemas import NotaIn, NotaUpdateIn
from app.services.transacoes import confirmar_transacao


def listar_notas(db: Session):
    return db.scalars(select(Nota).order_by(Nota.id)).all()


def buscar_nota(db: Session, id: int):
    dados = db.get(Nota, id)
    if dados is None:
        raise HTTPException(status_code=404, detail="Nota não encontrada")
    return dados


def cadastrar_nota(db: Session, nota: NotaIn):
    dados = Nota(**nota.model_dump())
    db.add(dados)
    confirmar_transacao(db)
    db.refresh(dados)
    return dados


def atualizar_nota(db: Session, id: int, nota: NotaUpdateIn):
    dados = buscar_nota(db, id)
    campos = nota.model_dump(exclude_unset=True)
    for campo, valor in campos.items():
        setattr(dados, campo, valor)
    confirmar_transacao(db)
    db.refresh(dados)
    return dados


def deletar_nota(db: Session, id: int):
    dados = buscar_nota(db, id)
    db.delete(dados)
    confirmar_transacao(db)
