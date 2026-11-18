from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import DisciplinaIn, DisciplinaUpdateIn, DisciplinaOut
from app.services import disciplinas_services

router = APIRouter(prefix="/disciplinas")


@router.get("/pegar-mensagem")
def primeira_api():
    return {"message": "disciplinas"}


@router.get("/pegar-dados-disciplina", response_model=list[DisciplinaOut])
def pegar_dados_disciplinas(db: Session = Depends(get_db)):
    return disciplinas_services.listar_disciplinas(db)


@router.get("/pegar-dados-disciplina-por-id/{id}", response_model=DisciplinaOut)
def pegar_dados_disciplinas_por_id(id: int, db: Session = Depends(get_db)):
    return disciplinas_services.buscar_disciplina(db, id)


@router.post("/criar-disciplina")
def criar_disciplina(disciplina: DisciplinaIn, db: Session = Depends(get_db)):
    dados = disciplinas_services.cadastrar_disciplina(db, disciplina)
    return {"mensagem": "Disciplina cadastrada com sucesso!", "id": dados.id}


@router.put("/atualizar-disciplina/{id}")
def atualizar_disciplina(id: int, disciplina: DisciplinaUpdateIn, db: Session = Depends(get_db)):
    disciplinas_services.atualizar_disciplina(db, id, disciplina)
    return {"mensagem": "Disciplina atualizada com sucesso!"}


@router.delete("/deletar-disciplina/{id}")
def deletar_disciplina(id: int, db: Session = Depends(get_db)):
    disciplinas_services.deletar_disciplina(db, id)
    return {"mensagem": "Disciplina deletada com sucesso!"}
