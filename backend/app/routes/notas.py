from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import NotaIn, NotaUpdateIn, NotaOut
from app.services import notas_services

router = APIRouter(prefix="/notas")


@router.get("/pegar-mensagem")
def primeira_api():
    return {"message": "rotas notas"}


@router.get("/pegar-dados-notas", response_model=list[NotaOut])
def pegar_dados_notas(db: Session = Depends(get_db)):
    return notas_services.listar_notas(db)


@router.get("/pegar-dados-notas-por-id/{id}", response_model=list[NotaOut])
def pegar_dados_notas_por_id(id: int, db: Session = Depends(get_db)):
    return [notas_services.buscar_nota(db, id)]


@router.post("/criar-nota")
def criar_nota(nota: NotaIn, db: Session = Depends(get_db)):
    dados = notas_services.cadastrar_nota(db, nota)
    return {"mensagem": "Nota cadastrada com sucesso!", "id": dados.id}


@router.put("/atualizar-nota/{id}")
def atualizar_nota(id: int, nota: NotaUpdateIn, db: Session = Depends(get_db)):
    notas_services.atualizar_nota(db, id, nota)
    return {"mensagem": "Nota atualizada com sucesso!"}


@router.delete("/deletar-nota/{id}")
def deletar_nota(id: int, db: Session = Depends(get_db)):
    notas_services.deletar_nota(db, id)
    return {"mensagem": "Nota deletada com sucesso!"}
