
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from app.routes import alunos, disciplinas, notas, endereco


app = FastAPI()

app.include_router(alunos.router)
app.include_router(endereco.router)
app.include_router(disciplinas.router)
app.include_router(notas.router)

# Alternativa local ao Swagger, sem dependências de CDN/internet.
@app.get('/docs-offline', include_in_schema=False)
def documentacao_offline():
    return FileResponse(Path(__file__).parent / 'static' / 'docs-offline.html')
