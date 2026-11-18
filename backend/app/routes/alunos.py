from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import AlunoIn, AlunoUpdateIn, AlunoOut
from app.services import alunos_services

router = APIRouter(prefix="/alunos")


@router.get("/")
def primeira_api():
    return {"message": "rotas alunos"}


@router.get("/pegar-dados-alunos", response_model=list[AlunoOut])
def pegar_dados_alunos(db: Session = Depends(get_db)):
    return alunos_services.listar_alunos(db)


@router.get("/pegar-dados-alunos-por-id/{id}", response_model=AlunoOut)
def pegar_dados_alunos_por_id(id: int, db: Session = Depends(get_db)):
    return alunos_services.buscar_aluno(db, id)


@router.post("/criar-aluno")
def criar_aluno(aluno: AlunoIn, db: Session = Depends(get_db)):
    dados = alunos_services.cadastrar_aluno(db, aluno)
    return {"mensagem": "Aluno cadastrado com sucesso!", "id": dados.id}


@router.put("/atualizar-aluno/{id}")
def atualizar_aluno(id: int, aluno: AlunoUpdateIn, db: Session = Depends(get_db)):
    alunos_services.atualizar_aluno(db, id, aluno)
    return {"mensagem": "Aluno atualizado com sucesso!"}


@router.delete("/deletar-aluno/{id}")
def deletar_aluno(id: int, db: Session = Depends(get_db)):
    alunos_services.deletar_aluno(db, id)
    return {"mensagem": "Aluno deletado com sucesso!"}
