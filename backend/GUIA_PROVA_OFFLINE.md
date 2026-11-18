# Guia offline — Projetos II / IBMEC

Preparação em **27/10/2026**, para a avaliação de **28/10/2026**.
Conteúdo: FastAPI, PostgreSQL, tabelas, PK/FK, SQLAlchemy ORM, Alembic,
Pydantic, routes, services e CRUD. Este guia e `/docs-offline` funcionam sem internet.
Os exemplos abaixo usam os nomes reais deste projeto.

## Índice rápido para a prova

- [Iniciar e conferir sem modificar o banco](#inicio-seguro)
- [Onde encontrar cada operação CRUD](#localizar-operacoes)
- [Adaptar nomes de tabelas e campos](#adaptar-nomes)
- [Levar o projeto para outro computador](#outro-computador)
- [Diagnosticar os 10 erros mais prováveis](#dez-erros)
- Consulta detalhada: seções numeradas **4** (models/PK/FK), **5** (schemas),
  **6** (Session/Depends), **7** (funções), **8** (CRUD), **9** (URLs),
  **10** (prática), **11** (Alembic), **12** (testes) e **13** (erros adicionais).

<a id="inicio-seguro"></a>
### Iniciar e conferir sem modificar o banco

No terminal, entre na pasta que contém `pyproject.toml`, `app/` e `alembic.ini`
(`backend` neste repositório). Não entre em `backend/backend` se já estiver nela.

```bash
uv sync --offline --locked --dry-run
uv run --offline --no-sync python tests/verificar_leitura_postgres.py
uv run --offline --no-sync alembic current
uv run --offline --no-sync alembic heads
uv run --offline --no-sync alembic check
uv run --offline --no-sync uvicorn app.main:app --reload
```

O `check` **ainda falha no banco auditado**, por revisão pendente; isso não impede
iniciar a API. O script de leitura confere imports, chamadas de services, metadata,
GETs e entrega dos HTMLs em uma transação PostgreSQL `READ ONLY`.
Não aplica migrações nem envia POST/PUT/DELETE.
Abra `http://127.0.0.1:8000/docs-offline` e use apenas GET para uma conferência
sem escrita. O usuário já relatou ter iniciado o servidor e consultado alunos
nessa página; isso é evidência manual relatada, não automação de navegador.

Para conferir os quatro CRUDs **sem tocar no PostgreSQL**:

```bash
uv run --offline --no-sync python tests/verificar_backend.py
```

Esse modo usa SQLite em memória. O modo `--postgres` da mesma suíte cria um
schema, aplica migrações e escreve nele, mesmo revertendo tudo ao final:
**não foi executado na auditoria final**, seguindo a restrição de não aplicar
migrações nem alterar dados sem autorização.

<a id="localizar-operacoes"></a>
### Onde encontrar cada operação CRUD

Cada linha abaixo tem todas as operações: GET lista → `listar_*`; GET ID →
`buscar_*`; POST → `cadastrar_*`; PUT → `atualizar_*`; DELETE → `deletar_*`.
A route chama essas funções. A implementação com `db` fica no service.

| Entidade | Route | Service | Funções do service |
| --- | --- | --- | --- |
| Aluno | [app/routes/alunos.py](app/routes/alunos.py) | [app/services/alunos_services.py](app/services/alunos_services.py) | `listar_alunos`, `buscar_aluno`, `cadastrar_aluno`, `atualizar_aluno`, `deletar_aluno` |
| Endereço | [app/routes/endereco.py](app/routes/endereco.py) | [app/services/endereco_services.py](app/services/endereco_services.py) | `listar_enderecos`, `buscar_endereco`, `cadastrar_endereco`, `atualizar_endereco`, `deletar_endereco` |
| Disciplina | [app/routes/disciplinas.py](app/routes/disciplinas.py) | [app/services/disciplinas_services.py](app/services/disciplinas_services.py) | `listar_disciplinas`, `buscar_disciplina`, `cadastrar_disciplina`, `atualizar_disciplina`, `deletar_disciplina` |
| Nota | [app/routes/notas.py](app/routes/notas.py) | [app/services/notas_services.py](app/services/notas_services.py) | `listar_notas`, `buscar_nota`, `cadastrar_nota`, `atualizar_nota`, `deletar_nota` |

- Tabelas/PK/FK: [app/models.py](app/models.py).
- Entrada/atualização/saída: [app/schemas.py](app/schemas.py), classes `*In`, `*UpdateIn`, `*Out`.
- Sessão e dependência: [app/database.py](app/database.py), `SessionLocal` e `get_db`.
- Commit e rollback: [app/services/transacoes.py](app/services/transacoes.py), `confirmar_transacao`.
- Registro dos routers: [app/main.py](app/main.py), `app.include_router(...)`.
- Criação das tabelas: [migração inicial](alembic/versions/38c9a6fba33e_tabelas.py).
- URLs exatas dos endpoints: tabela na seção **9** abaixo.

<a id="adaptar-nomes"></a>
### Como adaptar tabelas e campos para um exercício novo

Use um banco separado de estudo e preserve os arquivos das aulas. Exemplo de
raciocínio: adaptar `Aluno` para uma entidade `Professor` pedida pelo enunciado.
Isso é uma orientação; nenhuma nova entidade foi criada nesta auditoria.

1. **Model:** ajuste o nome da classe, `__tablename__`, atributos, tipos e limites.
   PK é `mapped_column(primary_key=True)`. Uma FK usa o **nome SQL da tabela**,
   por exemplo `ForeignKey('tb_enderecos.id')`, não `ForeignKey('Endereco.id')`.
2. **Schemas:** ajuste `ProfessorIn`, `ProfessorUpdateIn`, `ProfessorOut` e seus
   campos. Cadastro deve exigir o que o banco exige; update mantém campos opcionais;
   saída adiciona `id` e `ConfigDict(from_attributes=True)`.
3. **Service:** ajuste imports do model/schema, nomes das cinco funções,
   `select(Professor)`, `db.get(Professor, id)` e construção do objeto.
   Se o construtor enumera campos, como o de aluno, atualize cada atribuição.
   Em `Model(**schema.model_dump())`, nomes do schema e do model devem coincidir.
4. **Route:** ajuste import do service, `prefix`, URLs, schema de entrada e
   `response_model`. Toda chamada precisa corresponder ao nome real no service.
   Preserve `Depends(get_db)` e deixe as operações de banco no service.
5. **Main:** importe o novo módulo de route e registre `app.include_router(...)`.
6. **Alembic:** definir o model não muda o banco. Só quando o exercício autorizar,
   gere e revise a migração e aplique-a no banco escolhido. Não altere a revisão
   inicial já aplicada para simular uma mudança posterior. Renomeações podem virar
   DROP/CREATE na autogeração; revise antes de executar.
7. **Teste:** cadastre primeiro a entidade referenciada por FK; use o ID retornado
   em vez de supor `1`. Teste as quatro operações e confirme a alteração com GET.

Não substitua todas as ocorrências de uma palavra indiscriminadamente: `Aluno`
(classe), `tb_alunos` (tabela), `alunos` (prefixo), `alunos_services` (módulo) e
`nome_aluno` (campo) têm papéis diferentes. `Nota.nome_id` é uma FK de aluno,
apesar de não se chamar `aluno_id`; mudar esse nome exige atualizar todas as camadas.

<a id="outro-computador"></a>
### O que levar e o que preparar em outro computador

| Item | Portabilidade / preparação |
| --- | --- |
| `app/`, incluindo `static/docs-offline.html` | Código e página local portáveis; copiar mantendo a estrutura. |
| `alembic/` completo + `alembic.ini` | Revisões e configuração portáveis; não incluem o banco nem seus dados. |
| `pyproject.toml`, `uv.lock`, `.python-version` | Especificam dependências/Python; não contêm os pacotes instalados. |
| `tests/`, guias e README | Portáveis; incluir também os arquivos ainda não rastreados pelo Git. |
| `.venv/` | Ambiente local; não é uma instalação portável entre computadores/sistemas. Recrie no destino antes de ficar offline. |
| Cache do uv | Nesta máquina fica fora do projeto, em `~/.cache/uv`; copiar apenas o projeto não leva esse cache. Wheels também dependem de sistema/arquitetura/Python. |
| Pacotes offline | Não há `.whl` empacotado no backend. `uv.lock` sozinho não permite instalar sem rede/cache. Prepare o destino antes da prova. |
| `.env` | Ignorado pelo Git. Configure os valores privados localmente no destino; não cole credenciais no guia. |
| PostgreSQL | Serviço e banco separados da pasta. Criar/configurar banco de estudo no destino, com autorização. As tabelas dependem da aplicação das migrações. |
| Dados do PostgreSQL | Não acompanham o código; esta auditoria não fez exportação/restauração. |

No destino, instale/preconfigure Python 3.14 compatível com `.python-version`, uv,
pacotes e PostgreSQL **antes** de perder a internet. Quando houver autorização
para instalar, `uv sync --locked` prepara o ambiente; depois use os comandos
`--offline --no-sync` e o teste somente leitura para conferir.
Não houve instalação nesta auditoria nem teste em um segundo computador.
Se o servidor PostgreSQL depender de outra máquina ou de acesso externo,
`uv --offline` não o transforma em banco local.

Antes de fechar a preparação, confira que o destino abre `/docs-offline` com a
rede desconectada. Leve a pasta inteira dos fontes permitidos, incluindo os guias,
services, página HTML e revisão ainda não rastreados; um clone do commit atual
não contém automaticamente esses arquivos. Não é necessário fazer push para isso.

<a id="dez-erros"></a>
### Os 10 erros mais prováveis: diagnóstico rápido

| # | Sintoma | Diagnóstico e ação |
| --- | --- | --- |
| 1 | `No module named app` / `Could not import module` | Terminal na pasta errada ou venv errada. Entre na pasta com `app/` e execute `uv run --offline --no-sync python -c "from app.main import app; print(app.title)"`. |
| 2 | `alunos_service` não existe / `castrar_aluno` não encontrado | Confira `app/services/alunos_services.py` e `cadastrar_aluno`. Importe o módulo no plural e chame `alunos_services.cadastrar_aluno(db, aluno)`. |
| 3 | POST 500 / `'dados' is an invalid keyword argument for Aluno` | A route deve receber diretamente `dados = alunos_services.cadastrar_aluno(db, aluno)`. Não use `Aluno(dados=cadastrar_aluno(...))`: o service já constrói e grava o objeto. |
| 4 | uv/Python/pacote ausente ou tentativa de download | Confira `uv --version`, `python --version` via uv e `uv sync --offline --locked --dry-run`. Sem cache/venv pronta, prepare antes da prova; não há instalação garantida offline em outra máquina. |
| 5 | Conexão recusada, timeout ou falha de autenticação | Confira serviço PostgreSQL, banco e as cinco chaves do `.env` no editor local. Use o teste somente leitura. Não imprima a URL nem copie credenciais para relatórios. |
| 6 | `relation ... does not exist` | Banco/schema diferente ou tabelas não criadas. Confira `alembic current`, `.env` e revisão inicial. Só aplique migrations no banco autorizado. |
| 7 | `Target database is not up to date` | Compare `current` com `heads`. Aqui falta `0ad60a28ccaf`, revisão vazia. Não use `stamp` para esconder atraso. Sem autorização, apenas registre a pendência. |
| 8 | HTTP 422 | Leia `detail`: campo obrigatório ausente, JSON errado ou tipo incompatível. Use IDs inteiros, `nota` numérica e strings em `carga`/`semestre`. |
| 9 | HTTP 404 ou 409 | 404: ID inexistente. 409: FK inválida, CEP duplicado, `null` em NOT NULL ou pai ainda referenciado. Confira os IDs reais com GET e a ordem das dependências. |
| 10 | `/docs` vazio ou porta ocupada | Sem CDN/cache, use `/docs-offline`. Se houver `Address already in use`, encerre seu servidor com Ctrl+C ou use `--port 8001` e abra essa porta no navegador. |


## 1. Conferência rápida antes da prova

No terminal, entre na pasta `backend` do projeto. Os comandos deste guia partem dela.

```bash
uv --version
uv run --offline --no-sync python --version
uv sync --offline --locked --dry-run
uv run --offline --no-sync python -c "from app.main import app; print(app.title)"
uv run --offline --no-sync alembic heads
uv run --offline --no-sync alembic current
uv run --offline --no-sync python tests/verificar_leitura_postgres.py
uv run --offline --no-sync uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

O último comando mantém o servidor aberto. Acesse:

- `http://127.0.0.1:8000/docs-offline`: consulta e execução de requisições **sem CDN**.
- `http://127.0.0.1:8000/docs`: Swagger padrão; seus arquivos JS/CSS vêm de CDN.
  Sem internet e sem cache, a página pode ficar vazia. Use `/docs-offline` nesse caso.
- `http://127.0.0.1:8000/openapi.json`: descrição local dos caminhos e schemas.

`--offline` impede o uv de buscar pacotes pela rede; `--no-sync` usa o ambiente que
já existe, sem sincronizar dependências. Isso não desliga conexões da aplicação:
o PostgreSQL ainda precisa estar acessível no endereço configurado localmente.

Na máquina auditada, Python 3.14.8, uv e dependências já estavam disponíveis.
Se precisar preparar outra máquina **antes** da prova, execute `uv sync --locked`
com as dependências disponíveis. Depois confira tudo desconectado. Não dependa de
instalar ferramentas durante a avaliação. O `--dry-run` só confere e não instala.

## 2. Árvore dos arquivos e responsabilidades

```text
backend/
├── .env                         # configuração privada local; não copiar para o guia
├── .gitignore                   # ignora .env, .venv e arquivos gerados
├── .python-version              # Python 3.14
├── .venv/                       # interpretador e bibliotecas já instalados
├── pyproject.toml               # dependências e configuração do uv
├── uv.lock                      # versões resolvidas das dependências
├── README.md                    # primeiros passos originais e links deste material
├── GUIA_PROVA_OFFLINE.md         # esta consulta
├── RELATORIO_CHECKLIST.md        # evidências, testes e pendências
├── alembic.ini                  # configuração do Alembic
├── alembic/
│   ├── README
│   ├── env.py                   # usa Base.metadata e engine; online e geração SQL
│   ├── script.py.mako           # modelo para gerar uma revisão
│   └── versions/
│       ├── 38c9a6fba33e_tabelas.py   # cria as quatro tabelas, PK/FK e CEP único
│       └── 0ad60a28ccaf_tabelas.py   # revisão posterior vazia, preservada
├── app/
│   ├── main.py                  # FastAPI, include_router e /docs-offline
│   ├── database.py              # engine, Base, SessionLocal, get_db
│   ├── models.py                # tabelas mapeadas em classes SQLAlchemy
│   ├── schemas.py               # contratos Pydantic de entrada, atualização e saída
│   ├── routes/
│   │   ├── alunos.py            # HTTP /alunos → alunos_services
│   │   ├── disciplinas.py       # HTTP /disciplinas → disciplinas_services
│   │   ├── endereco.py          # HTTP /enderecos → endereco_services
│   │   └── notas.py             # HTTP /notas → notas_services
│   ├── services/
│   │   ├── alunos_services.py       # CRUD ORM de Aluno
│   │   ├── disciplinas_services.py  # CRUD ORM de Disciplina
│   │   ├── endereco_services.py     # CRUD ORM de Endereco
│   │   ├── notas_services.py        # CRUD ORM de Nota
│   │   └── transacoes.py            # commit, rollback e HTTP 409 de integridade
│   └── static/
│       └── docs-offline.html     # formulário local que lê /openapi.json
└── tests/
    ├── verificar_backend.py      # unittest + HTTP real, PostgreSQL isolado ou SQLite
    └── verificar_leitura_postgres.py # auditoria final: imports e GET, READ ONLY
```

Fluxo da requisição:

```text
JSON / URL → route → schema validado + Session → service → model ORM → PostgreSQL
resposta HTTP ← route ← resultado do service
```

O FastAPI valida os parâmetros e o corpo usando as anotações da route antes de
executar a função. `main.py` registra cada `router` com `app.include_router(...)`.
O nome da pasta é `services`; o arquivo de alunos é **`alunos_services.py`**,
no plural, e a função é **`cadastrar_aluno`**.

## 3. Configuração do banco sem credenciais no código de consulta

`database.py` carrega o `.env` localizado na pasta `backend` e lê estas chaves:
`user`, `senha`, `host`, `port`, `banco`. Os valores são privados.
Verifique-os apenas no seu editor local. Não imprima `DATABASE_URL` ou o `.env`.

A engine usa `postgresql+psycopg` e `URL.create(...)`, que recebe os componentes
separadamente e trata caracteres especiais da senha. A conexão tem timeout de
5 segundos. Não há criação automática de tabelas ao iniciar a API.

O banco PostgreSQL precisa existir antes das migrações. Pelo DBeaver, conectado
a um servidor local, você pode criar um **banco novo de estudo**. O SQL equivalente,
usado apenas se esse nome ainda não existir e seu usuário puder criar bancos, é:

```sql
CREATE DATABASE prova_estudo;
```

Depois ajuste a chave `banco` do `.env` para o banco de estudo. Não use dados
existentes para experimentar DELETE, downgrade ou alterações destrutivas.

## 4. Models, tabelas, PK e FK

Trecho real de `app/models.py`:

```python
class Aluno(Base):
    __tablename__ = 'tb_alunos'
    id: Mapped[int] = mapped_column(primary_key=True)
    matricula: Mapped[str] = mapped_column(String(20))
    nome_aluno: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255))
    endereco_id: Mapped[int] = mapped_column(ForeignKey('tb_enderecos.id'))
```

- `Base`: base declarativa compartilhada com Alembic.
- `__tablename__`: nome da tabela no banco.
- `Mapped[int]` e `Mapped[str]`: tipos Python dos atributos mapeados.
- `mapped_column(...)`: configuração da coluna SQL.
- `String(20)`: texto com até 20 caracteres no PostgreSQL.
- `primary_key=True`: PK; identifica cada registro. O `id` inteiro é gerado no cadastro.
- `ForeignKey('tb_enderecos.id')`: FK; o endereço referenciado precisa existir.
- Os campos mapeados sem `Optional` neste projeto são `NOT NULL`.

Relações reais:

| Tabela | PK | FK / outra restrição |
| --- | --- | --- |
| `tb_enderecos` | `id` | `cep` único |
| `tb_alunos` | `id` | `endereco_id` → `tb_enderecos.id` |
| `tb_disciplinas` | `id` | sem FK |
| `tb_notas` | `id` | `nome_id` → `tb_alunos.id`; `disciplina_id` → `tb_disciplinas.id` |

Apesar do nome, `Nota.nome_id` guarda o **ID do aluno**, não o nome.
`carga` e `semestre` são strings no código atual. `nota` é `Float` no banco.
Não há regra de faixa 0–10 nem validação de formato de email no projeto.

Uma FK não cria um atributo `relationship()` automaticamente. Aqui basta trabalhar
com os IDs. Nenhuma exclusão em cascata foi configurada: o PostgreSQL impede
excluir um pai referenciado. Cadastre endereço antes de aluno; aluno e disciplina
antes de nota. Exclua os registros de teste na ordem inversa das dependências.

Definir o model **não cria a tabela**. A migração real usa, por exemplo:

```python
op.create_table('tb_alunos',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('matricula', sa.String(length=20), nullable=False),
    sa.Column('nome_aluno', sa.String(length=255), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('endereco_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['endereco_id'], ['tb_enderecos.id'], ),
    sa.PrimaryKeyConstraint('id')
)
```

Esse trecho está em `alembic/versions/38c9a6fba33e_tabelas.py`.
É `alembic upgrade head` que aplica as revisões ao banco escolhido.

## 5. Schemas Pydantic

Trechos reais de `app/schemas.py`:

```python
class AlunoIn(BaseModel):
    matricula: str
    nome_aluno: str
    email: str
    endereco_id: int

class AlunoUpdateIn(BaseModel):
    matricula: Optional[str] = None
    nome_aluno: Optional[str] = None
    email: Optional[str] = None
    endereco_id: Optional[int] = None

class AlunoOut(AlunoIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
```

`In` recebe um cadastro: os quatro campos são obrigatórios, e o cliente não fornece
o `id`. `UpdateIn` permite enviar só os campos a alterar. `Out` descreve a leitura
e inclui o `id`; `from_attributes=True` permite validar a saída a partir de objetos
SQLAlchemy, lendo atributos em vez de exigir um dicionário.

**Model SQLAlchemy representa tabela; schema Pydantic representa dados da API.**
Um schema não cria tabelas nem substitui as restrições do banco.

Neste projeto os PUTs fazem atualização parcial, usando:

```python
campos = aluno.model_dump(exclude_unset=True)
```

Se chegar `{"nome_aluno": "Ana"}`, só esse campo será alterado. Um corpo `{}` é
aceito e mantém o registro. Campo omitido é diferente de `null`: o schema de update
aceita `None`, mas as colunas são `NOT NULL`; enviar `null` resulta em HTTP 409
quando o banco rejeita a alteração. Não use `exclude_none=True` para esconder essa
diferença. Os schemas atuais não validam os comprimentos máximos das strings;
respeite os tamanhos dos models, como `estado` com 2 caracteres e `cep` com até 10.

## 6. Session, get_db e Depends

Código real de `database.py`:

```python
SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    with SessionLocal() as db:
        yield db
```

- `engine`: administra as conexões com o banco.
- `sessionmaker`: fabrica sessões configuradas com essa engine.
- `Session`: unidade de trabalho do ORM; consulta objetos e acompanha alterações.
- `SessionLocal()`: cria uma sessão. Não é uma tabela nem um registro.
- `yield db`: entrega a sessão à requisição; ao terminar, o `with` fecha a sessão.
- `Depends(get_db)`: pede ao FastAPI para obter essa sessão e passá-la à route.
- `get_db` fecha a sessão, mas **não faz commit automático**. O service confirma.

Exemplo de route real:

```python
@router.post("/criar-aluno")
def criar_aluno(aluno: AlunoIn, db: Session = Depends(get_db)):
    dados = alunos_services.cadastrar_aluno(db, aluno)
    return {"mensagem": "Aluno cadastrado com sucesso!", "id": dados.id}
```

O prefixo `APIRouter(prefix="/alunos")` produz o caminho `/alunos/criar-aluno`.
A route recebe dados HTTP e chama o service. `db.get`, `db.add`, `db.commit`,
`db.refresh` e `db.delete` ficam na camada `services`, inclusive em `transacoes.py`.

## 7. Definir uma função e chamar uma função

```python
# Definição: registra o código; não cadastra um aluno agora.
def cadastrar_aluno(db: Session, aluno: AlunoIn):
    ...

# Chamada: executa a função com argumentos e guarda o retorno.
dados = alunos_services.cadastrar_aluno(db, aluno)
```

`return dados` devolve um valor a quem chamou. Escrever apenas
`alunos_services.cadastrar_aluno` obtém a função sem executá-la.
Em `Depends(get_db)`, passe a função **sem `()`**, porque o FastAPI precisa controlar
quando chamá-la e encerrar seu gerador. Já dentro da route,
`alunos_services.cadastrar_aluno(db, aluno)` tem `()` porque você quer executá-la.

`Aluno(...)` constrói um objeto do model. Não se deve envolver a chamada do service
em outro `Aluno(dados=...)`: `dados` não é coluna, e o service já constrói o objeto.

## 8. CRUD real no service de alunos

Os trechos abaixo vêm de `app/services/alunos_services.py`. Os outros três services
seguem a mesma estrutura. Imports usados:

```python
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Aluno
from app.schemas import AlunoIn, AlunoUpdateIn
from app.services.transacoes import confirmar_transacao
```

### GET — Read / consultar

```python
def listar_alunos(db: Session):
    return db.scalars(select(Aluno).order_by(Aluno.id)).all()


def buscar_aluno(db: Session, id: int):
    dados = db.get(Aluno, id)
    if dados is None:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
    return dados
```

`select(Aluno)` descreve a consulta; `db.scalars(...)` executa e devolve objetos
Aluno; `.all()` materializa a lista. `db.get(Aluno, id)` busca pela PK e retorna
um objeto ou `None`. Lista vazia é `[]`; busca de ID inexistente é HTTP 404.

Route real de leitura:

```python
@router.get("/pegar-dados-alunos", response_model=list[AlunoOut])
def pegar_dados_alunos(db: Session = Depends(get_db)):
    return alunos_services.listar_alunos(db)
```

### POST — Create / cadastrar

```python
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
```

`Aluno(...)` cria o objeto em memória. `db.add` coloca-o na sessão.
`confirmar_transacao` executa `db.commit()`, que grava a transação.
`db.refresh(dados)` relê os atributos do banco, incluindo o `id` gerado.
Nos outros services, `Model(**schema.model_dump())` distribui o dicionário como
argumentos nomeados do construtor; é uma forma curta de preencher os campos.

### PUT — Update / atualizar

```python
def atualizar_aluno(db: Session, id: int, aluno: AlunoUpdateIn):
    dados = buscar_aluno(db, id)
    campos = aluno.model_dump(exclude_unset=True)
    for campo, valor in campos.items():
        setattr(dados, campo, valor)
    confirmar_transacao(db)
    db.refresh(dados)
    return dados
```

O objeto buscado já é acompanhado pela sessão. `setattr` altera seu atributo;
o commit transforma a alteração em UPDATE. Não precisa montar SQL nem chamar
`db.add` novamente. A busca também atende o caso de registro inexistente.

```python
@router.put("/atualizar-aluno/{id}")
def atualizar_aluno(id: int, aluno: AlunoUpdateIn, db: Session = Depends(get_db)):
    alunos_services.atualizar_aluno(db, id, aluno)
    return {"mensagem": "Aluno atualizado com sucesso!"}
```

### DELETE — Delete / excluir

```python
def deletar_aluno(db: Session, id: int):
    dados = buscar_aluno(db, id)
    db.delete(dados)
    confirmar_transacao(db)
```

`db.delete` marca o objeto para exclusão. O commit efetiva o DELETE.

```python
@router.delete("/deletar-aluno/{id}")
def deletar_aluno(id: int, db: Session = Depends(get_db)):
    alunos_services.deletar_aluno(db, id)
    return {"mensagem": "Aluno deletado com sucesso!"}
```

### Confirmação e erro de integridade

Trecho completo de `app/services/transacoes.py`:

```python
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def confirmar_transacao(db: Session):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Operação viola uma restrição: confira FK, CEP único e campos obrigatórios."
        ) from None
```

Após uma falha no commit, o rollback é necessário para encerrar a transação que
falhou. O detalhe interno da exceção SQL não é devolvido pela API. Esse tratamento
cobre integridade (FK, UNIQUE, NOT NULL), não todo erro de conexão ou de tipo/tamanho.

## 9. Mapa dos endpoints

Todos os caminhos abaixo mantêm o padrão do projeto. O GET por ID de disciplina
foi acrescentado para completar a consulta. Os POSTs retornam mensagem e `id`.
PUT e DELETE retornam mensagem. O sucesso atual é HTTP **200**, inclusive POST.

| Entidade | GET lista | GET por ID | POST | PUT | DELETE |
| --- | --- | --- | --- | --- | --- |
| Aluno | `/alunos/pegar-dados-alunos` | `/alunos/pegar-dados-alunos-por-id/{id}` | `/alunos/criar-aluno` | `/alunos/atualizar-aluno/{id}` | `/alunos/deletar-aluno/{id}` |
| Endereço | `/enderecos/pegar-dados-endereco` | `/enderecos/pegar-dados-endereco-por-id/{id}` | `/enderecos/criar-endereco` | `/enderecos/atualizar-endereco/{id}` | `/enderecos/deletar-endereco/{id}` |
| Disciplina | `/disciplinas/pegar-dados-disciplina` | `/disciplinas/pegar-dados-disciplina-por-id/{id}` | `/disciplinas/criar-disciplina` | `/disciplinas/atualizar-disciplina/{id}` | `/disciplinas/deletar-disciplina/{id}` |
| Nota | `/notas/pegar-dados-notas` | `/notas/pegar-dados-notas-por-id/{id}` | `/notas/criar-nota` | `/notas/atualizar-nota/{id}` | `/notas/deletar-nota/{id}` |

GET por ID de aluno e disciplina retorna objeto. Endereço e nota mantêm lista
com um objeto, como no projeto anterior. Em todos eles, ID ausente retorna 404.
Também há as rotas de mensagem `/alunos/`, `/enderecos/pegar-mensagem`,
`/disciplinas/pegar-mensagem` e `/notas/pegar-mensagem`.

## 10. Passos para testar em /docs ou /docs-offline

1. Confira o `.env` local e use um banco de estudo. Inicie PostgreSQL e uvicorn.
2. Abra `/docs`. Expanda a operação, clique em **Try it out**, preencha e clique em
   **Execute**. Se o Swagger não carregar sem internet, abra `/docs-offline`:
   escolha a operação, preencha o ID quando necessário, edite o JSON e clique em
   **Executar requisição**. Essa alternativa não exige downloads.
3. Faça POST de um endereço de teste com CEP ainda não usado:

```json
{
  "cep": "00000-001",
  "endereco": "Rua de Teste",
  "bairro": "Centro",
  "cidade": "Rio de Janeiro",
  "estado": "RJ",
  "regiao": "Sudeste"
}
```

4. Anote o `id` retornado. Faça POST de um aluno. Substitua o `1` abaixo pelo ID
   real do endereço, sem supor que o banco começa em 1:

```json
{
  "matricula": "PROVA01",
  "nome_aluno": "Aluno de Teste",
  "email": "teste@example.invalid",
  "endereco_id": 1
}
```

5. Faça POST de uma disciplina e anote seu `id`:

```json
{"nome_disciplina": "Projetos II", "carga": "80", "semestre": "2026.2"}
```

6. Faça POST de uma nota usando os IDs reais de aluno e disciplina:

```json
{"nome_id": 1, "disciplina_id": 1, "nota": 8.5}
```

7. Faça GET das quatro listas e por ID. Confirme que os valores e as FKs coincidem.
8. Faça PUT, um por vez, com os IDs que você acabou de cadastrar:

```text
/enderecos/atualizar-endereco/{id}    {"bairro": "Bairro atualizado"}
/alunos/atualizar-aluno/{id}          {"nome_aluno": "Nome atualizado"}
/disciplinas/atualizar-disciplina/{id} {"carga": "90"}
/notas/atualizar-nota/{id}            {"nota": 9.5}
```

9. Repita GET e confirme que só os campos enviados mudaram.
10. Se quiser limpar **apenas seus registros de teste**, faça DELETE de nota,
    aluno, disciplina e endereço, nessa ordem. Confirme com GET por ID → 404.
    O teste automatizado faz isso somente no schema isolado e reverte tudo ao final.

Sem interface, `curl` também funciona localmente:

```bash
curl -i http://127.0.0.1:8000/alunos/pegar-dados-alunos
```

## 11. Alembic: comandos reais e o que significam

O projeto **já está inicializado**. Não execute `alembic init` de novo.
`alembic/env.py` importa os models para preencher `Base.metadata`.
A URL efetiva vem de `app.database.engine`, não do exemplo `driver://...` do `.ini`.

Consultas e geração de SQL sem aplicar mudanças:

```bash
uv run --offline --no-sync alembic heads
uv run --offline --no-sync alembic history
uv run --offline --no-sync alembic current
uv run --offline --no-sync alembic check
uv run --offline --no-sync alembic upgrade head --sql
```

- `heads`: revisão mais recente no código; aqui, `0ad60a28ccaf`.
- `history`: encadeamento `base → 38c9a6fba33e → 0ad60a28ccaf`.
- `current`: revisão registrada no banco selecionado; exige conexão.
- `check`: verifica se há operações de autogeração pendentes; exige banco na revisão
  atual. Na auditoria, falhou com `Target database is not up to date`.
- `upgrade head --sql`: imprime o SQL completo desde a base sem executá-lo nem
  consultar a revisão aplicada. Não copie esse SQL inteiro sobre um banco já populado.
  O modo `--sql` é geração offline do Alembic; ele é diferente de `uv --offline`.

Para aplicar as migrações **depois de conferir o banco selecionado e revisar as
revisões**, especialmente em um banco de estudo novo:

```bash
uv run --offline --no-sync alembic upgrade head
uv run --offline --no-sync alembic current
uv run --offline --no-sync alembic check
```

No banco existente auditado, as tabelas já coincidem com os models, mas a revisão
registrada é `38c9a6fba33e`. A revisão seguinte contém `pass` em `upgrade` e
`downgrade`: não altera tabelas, mas aplicá-la avança o controle de versão.
**Não foi aplicado upgrade nesse banco durante a preparação.**
A cadeia completa foi aplicada e testada somente no schema temporário.

Se a prova pedir uma nova coluna/tabela: altere o model, confira o banco de estudo,
gere a revisão, abra o arquivo para revisar as operações e só então aplique:

```bash
uv run --offline --no-sync alembic revision --autogenerate -m "descreva a alteracao"
uv run --offline --no-sync alembic upgrade head
```

`revision` cria o arquivo; `upgrade` executa. Autogeração exige conexão e não deve
ser aceita sem revisão: uma remoção/renomeação pode aparecer como DROP.
A revisão inicial possui `downgrade()` que apaga tabelas. Para reconhecer a sintaxe,
`uv run --offline --no-sync alembic downgrade -1` volta uma revisão; **não foi
executado** e não deve ser usado em dados que precisam ser preservados.
Também não use `stamp head` para mascarar uma migração faltante: stamp só altera
controle de versão, não cria as tabelas.

## 12. Testes disponíveis e seus limites

```bash
# Somente com autorização: aplica migrações e escreve em schema temporário.
# Usa PostgreSQL configurado; precisa de permissão CREATE SCHEMA.
uv run --offline --no-sync python tests/verificar_backend.py --postgres

# Alternativa independente de PostgreSQL: SQLite em memória.
uv run --offline --no-sync python tests/verificar_backend.py

# Sintaxe/importação compilável, sem executar CRUD.
uv run --offline --no-sync python -m compileall -q app alembic tests
```

A suíte usa `unittest`, `urllib` e uvicorn já disponíveis, sem exigir pytest/httpx.
Ela sobe uma API em porta local livre e faz requisições HTTP reais. No modo
PostgreSQL, cria um schema exclusivo dentro de uma transação, aplica Alembic nele,
substitui `get_db` apenas durante o teste e usa savepoints para que os commits dos
services não confirmem a transação externa. Ao final executa rollback e verifica
que o schema sumiu. Não cria tabelas nem apaga registros no schema existente.
Ela não executa `downgrade` nem `DROP TABLE` no banco existente.

Se PostgreSQL não estiver acessível ou faltar permissão para criar schema, esse
modo pode falhar: não considere o teste SQLite prova de funcionamento no PostgreSQL.
No SQLite, as tabelas são criadas com metadata, sem validar migrações PostgreSQL.
Um encerramento normal com `OK` e a mensagem de rollback confirma o teste isolado.
A suíte verifica 7 grupos de casos, incluindo todos os quatro CRUDs; não é apenas
um teste de importação.

Limites: o teste HTTP busca o HTML de `/docs` e `/docs-offline`, mas não automatiza
cliques nem executa o JavaScript no navegador. Confira a página offline manualmente
com a rede desconectada. O teste em PostgreSQL também depende de ele continuar
acessível no dia da avaliação; se o servidor estiver em outra máquina sem rede,
prepare uma instância local antes da prova.

## 13. Erros comuns

| Sintoma | Conferir / resolver |
| --- | --- |
| `No module named app` | Execute os comandos dentro de `backend`. O import é `app.main:app`. |
| `No module named app.services.alunos_service` | Nome correto: `alunos_services`, plural. Função: `cadastrar_aluno`. |
| `NameError: cadastrar_aluno` | Importe o módulo e use `alunos_services.cadastrar_aluno(db, aluno)`. |
| Argumento `dados` inválido em `Aluno` | Chame o service diretamente; não envolva seu retorno em outro `Aluno(...)`. |
| `uv: command not found` | uv precisa estar instalado e no PATH antes de ficar offline; use o Python da `.venv` já pronta se disponível. |
| Falha ao resolver/baixar dependência offline | Confira `uv.lock`, Python 3.14 e `.venv`; prepare antes da prova. Use `--offline --no-sync` para executar o ambiente pronto. |
| Falha de conexão PostgreSQL | Verifique o serviço, endereço/porta e banco no `.env` local. Não imprima valores privados. |
| `password authentication failed` | Confira usuário/senha localmente; não publique o erro completo ou sua URL. |
| `relation ... does not exist` | Banco errado ou tabelas não migradas. Confira `current` e migrações antes de aplicar `upgrade head` no banco de estudo. |
| `Target database is not up to date` | Compare `current` e `heads`; revise as migrações faltantes antes do upgrade. Não gere revisões em cima de banco atrasado. |
| HTTP 422 | Corpo/tipo inválido, campo obrigatório ausente ou ID da URL não inteiro. Leia `detail`. |
| HTTP 404 | ID não existe; copie o ID retornado pelo POST. |
| HTTP 409 | Confira CEP repetido, FK inexistente, `null` em campo obrigatório ou tentativa de apagar um pai referenciado. |
| Erro de transação após falha no commit | É necessário `db.rollback()`; o helper `confirmar_transacao` já o faz para `IntegrityError`. |
| HTTP 500 por texto comprido | Schemas atuais não têm `max_length`. Respeite os limites SQL: estado 2, CEP 10, matrícula 20, demais strings 255. |
| PUT apaga/zera campos não enviados | Use `model_dump(exclude_unset=True)`; não transforme todos os campos opcionais em alterações. |
| `/docs` em branco sem internet | Use `/docs-offline`; Swagger padrão depende de CDN. |
| `Address already in use` | Já há processo na porta 8000. Encerre o seu servidor com Ctrl+C ou escolha `--port 8001`. |
| Permissão negada no teste PostgreSQL | A suíte precisa criar schema isolado. Use banco local de estudo com permissão; SQLite só comprova a alternativa em memória. |

No macOS/Linux, alternativa sem uv após preparar `.venv`:

```bash
.venv/bin/python -m uvicorn app.main:app --reload
.venv/bin/python -m alembic current
```

No PowerShell/Windows, se a `.venv` foi criada nessa máquina:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
.\.venv\Scripts\python.exe -m alembic current
```

Ativar a venv é opcional quando usa `uv run` ou o caminho completo do Python.
Uma `.venv` copiada entre sistemas operacionais não substitui a instalação local.
