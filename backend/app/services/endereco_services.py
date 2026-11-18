from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Endereco
from app.schemas import EnderecoIn, EnderecoUpdateIn
from app.services.transacoes import confirmar_transacao


def listar_enderecos(db: Session):
    return db.scalars(select(Endereco).order_by(Endereco.id)).all()


def buscar_endereco(db: Session, id: int):
    dados = db.get(Endereco, id)
    if dados is None:
        raise HTTPException(status_code=404, detail="Endereço não encontrado")
    return dados


def cadastrar_endereco(db: Session, endereco: EnderecoIn):
    dados = Endereco(**endereco.model_dump())
    db.add(dados)
    confirmar_transacao(db)
    db.refresh(dados)
    return dados


def atualizar_endereco(db: Session, id: int, endereco: EnderecoUpdateIn):
    dados = buscar_endereco(db, id)
    campos = endereco.model_dump(exclude_unset=True)
    for campo, valor in campos.items():
        setattr(dados, campo, valor)
    confirmar_transacao(db)
    db.refresh(dados)
    return dados


def deletar_endereco(db: Session, id: int):
    dados = buscar_endereco(db, id)
    db.delete(dados)
    confirmar_transacao(db)
