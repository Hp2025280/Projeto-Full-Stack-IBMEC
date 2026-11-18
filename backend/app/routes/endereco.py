from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import EnderecoIn, EnderecoUpdateIn, EnderecoOut
from app.services import endereco_services

router = APIRouter(prefix="/enderecos")


@router.get("/pegar-mensagem")
def primeira_api():
    return {"message": "Hello World"}


@router.get("/pegar-dados-endereco", response_model=list[EnderecoOut])
def pegar_dados_enderecos(db: Session = Depends(get_db)):
    return endereco_services.listar_enderecos(db)


@router.get("/pegar-dados-endereco-por-id/{id}", response_model=list[EnderecoOut])
def pegar_dados_enderecos_por_id(id: int, db: Session = Depends(get_db)):
    return [endereco_services.buscar_endereco(db, id)]


@router.post("/criar-endereco")
def criar_endereco(endereco: EnderecoIn, db: Session = Depends(get_db)):
    dados = endereco_services.cadastrar_endereco(db, endereco)
    return {"mensagem": "Endereço cadastrado com sucesso!", "id": dados.id}


@router.put("/atualizar-endereco/{id}")
def atualizar_endereco(id: int, endereco: EnderecoUpdateIn, db: Session = Depends(get_db)):
    endereco_services.atualizar_endereco(db, id, endereco)
    return {"mensagem": "Endereço atualizado com sucesso!"}


@router.delete("/deletar-endereco/{id}")
def deletar_endereco(id: int, db: Session = Depends(get_db)):
    endereco_services.deletar_endereco(db, id)
    return {"mensagem": "Endereço deletado com sucesso!"}
