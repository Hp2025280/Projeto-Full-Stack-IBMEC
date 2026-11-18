# fast_api_orm_alembic

## 1. Primeiros Passos
Instalar tudo que precisa para preparar antes

install do uv:
abrir powershell e rodar: powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
install do postman e do dbeaver pelo site oficial deles

## 2. Clonar o repositório e ambiente virtual

clonar este repositório e usar o uv sync para instalar as bibliotecas, após o download ative o venv com esse comando:
.venv\Scripts\activate

## 3. Criar o DB (ajustar .env)

no dbeaver faça a conexão com o postgre e crie um novo db para receber as tabelas
crie um novo file para o .env com as informações do db (coloque no .gitignore)

## 4. Alembic

rode alembic upgrade head no terminal para adicionar as tabelas no db criado

## 5. API

rode o uvicorn para testar a API com o postman
com o ambiente virtual ja ativado rode uvicorn app.main:app --reload

## 6. Postman

popule o db com o postman e teste todas as rotas da API

## Consulta para a avaliação sem internet

- [GUIA_PROVA_OFFLINE.md](GUIA_PROVA_OFFLINE.md): conceitos, código real, comandos e roteiro de prática.
- [RELATORIO_CHECKLIST.md](RELATORIO_CHECKLIST.md): auditoria, testes executados e pendências.
- Com o servidor iniciado, abra `http://127.0.0.1:8000/docs-offline` para testar sem CDN.

Dentro de `backend`, usando o ambiente já preparado:

```bash
uv run --offline --no-sync python tests/verificar_backend.py --postgres
uv run --offline --no-sync uvicorn app.main:app --reload
```

O teste PostgreSQL usa schema isolado em transação e reverte tudo ao final;
precisa de permissão para criar schema. Sem PostgreSQL, omita `--postgres` para
usar SQLite em memória, que não comprova migrações nem funcionamento em PostgreSQL.
