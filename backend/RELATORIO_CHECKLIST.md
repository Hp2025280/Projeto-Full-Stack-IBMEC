# Auditoria final — 27/10/2026

Este quadro é o resultado **mais recente** e prevalece sobre o histórico da
preparação anterior, mantido ao final. Avaliação: **28/10/2026**.
Não foram instalados pacotes, consultada internet, aplicadas migrações, alterados
dados do PostgreSQL nem arquivos do frontend nesta rodada. Não houve push.
Escritas de teste ocorreram apenas no SQLite em memória.

## Resultado por verificação

| Verificação | Status | Evidência e limite |
| --- | --- | --- |
| Imports de todos os módulos Python em `app/` | **APROVADO** | Importação executada por `tests/verificar_leitura_postgres.py`; compilação também aprovada. |
| Nomes e chamadas dos services | **APROVADO** | 20 chamadas verificadas com AST/importação e `getattr`/`callable`; 24 operações OpenAPI com `operationId` único. Não há referência ao módulo singular nem a `castrar_aluno` no código Python de `app/`. |
| Separação routes/services nas quatro entidades | **APROVADO** | Teste 07 passou após corrigir somente a route/service de alunos. Chamadas `db.*` de CRUD ficam nos services. |
| GET/POST/PUT/DELETE das quatro entidades em SQLite | **APROVADO** | 7 testes passaram; incluem HTTP real, leitura lista/ID, cadastro, atualização parcial/vazia, exclusão, 404, 422, FK/UNIQUE/NOT NULL e rollback após conflito. |
| GET lista das quatro entidades no PostgreSQL | **APROVADO** | HTTP 200 nas quatro, em transação confirmada como `READ ONLY`; IDs ausentes retornaram 404. |
| GET ID existente de aluno/endereço no PostgreSQL | **APROVADO** | HTTP 200 usando ID encontrado na respectiva lista, sem imprimir dados pessoais. |
| GET ID existente de disciplina/nota no PostgreSQL | **NÃO TESTADO** | As duas tabelas estavam vazias; nenhum dado foi criado para completar o caso. Esse caso passou no SQLite. |
| POST/PUT/DELETE em PostgreSQL nesta auditoria final | **NÃO TESTADO** | Restrição atual de não alterar dados nem aplicar migrations sem autorização. Resultados PostgreSQL da preparação anterior são históricos, não nova aprovação do código corrigido. |
| Models/PK/FK versus tabelas PostgreSQL | **APROVADO** | `compare_metadata` retornou `[]` dentro de transação somente leitura; teste SQLite também conferiu PKs e 3 FKs. |
| Python/dependências offline nesta máquina | **APROVADO** | `uv sync --offline --locked --dry-run`: `Would make no changes`; todos os testes usaram `uv run --offline --no-sync`. Nenhuma instalação. |
| Entrega da documentação local e OpenAPI | **APROVADO** | HTTP 200 em `/openapi.json`, `/docs`, `/docs-offline`; JavaScript com sintaxe válida e ausência de scripts/styles externos na página offline. |
| Navegador realmente desconectado nesta rodada | **NÃO TESTADO** | Não houve automação de cliques ou desconexão de rede. Usuário relatou Uvicorn e consulta de alunos na página offline; não se presume que a rede estivesse desligada nesse teste. `/docs` padrão continua dependente de CDN/cache. |
| Diagnóstico do Alembic | **APROVADO** | Executados `current`, `heads`, `history`, `check`; examinadas as duas revisões. Motivo do erro detalhado abaixo. |
| Banco na revisão head / `alembic check` aprovado | **PENDENTE** | Banco em `38c9a6fba33e`, head `0ad60a28ccaf`; check falha com código 255. Não aplicada migração, nem usado stamp. |
| Guia: índice CRUD, adaptação, início e 10 erros | **APROVADO** | `GUIA_PROVA_OFFLINE.md` atualizado com links dos quatro services/routes, passos de adaptação e seções rápidas com âncoras locais. |
| Portabilidade dos arquivos-fonte/documentação | **APROVADO** | Estrutura e dependências auditadas; `.env` e `.venv` ignorados no Git, cache externo, 0 wheels empacotados. Guia distingue cada componente. |
| Preparação de outro computador | **PENDENTE** | Precisa de Python/dependências instalados para o sistema de destino, PostgreSQL e configuração privada local. Código/lock não empacotam instalação nem banco. |
| Execução em outro computador | **NÃO TESTADO** | Nenhuma segunda máquina foi usada. Não há aprovação de instalação/restauração offline no destino. |
| Frontend e fontes preservados | **APROVADO** | Hashes dos 11 arquivos do frontend iguais antes/depois. Cópia dos dois fontes de alunos e documentos anteriores salva fora do repositório, sem `.env`. |

## Regressão encontrada e correção limitada

O estado atual já tinha o import `alunos_services.cadastrar_aluno` escrito
corretamente, mas a route de cadastro ainda fazia:

```python
dados = Aluno(dados=cadastrar_aluno(db, aluno))
```

A chamada do service ocorre antes da construção externa inválida. Assim, no banco
real o cadastro poderia ser confirmado e a requisição ainda responder 500.
Esse risco foi identificado pelo código; o erro 500 foi reproduzido **somente
no SQLite em memória**, sem gravar um aluno de diagnóstico no PostgreSQL.

GET/PUT/DELETE também estavam diretamente na route, e o service tinha só cadastro.
A suíte inicial terminou com **4 falhas em 7 testes**: grupos 03, 04, 06 e 07.
O GET de aluno inexistente retornava 200/null, em vez de 404.

Antes da edição, o problema e a correção foram explicados ao usuário.
Foram corrigidos somente:

- `app/routes/alunos.py`: chamada direta ao service em todas as operações,
  schema de saída e remoção de imports sem uso na route.
- `app/services/alunos_services.py`: completadas as funções `listar_alunos`,
  `buscar_aluno`, `atualizar_aluno`, `deletar_aluno`; cadastro explícito preservado;
  commit passa pelo helper `confirmar_transacao`, como nos demais services.

Os caminhos HTTP existentes foram mantidos. Nenhum outro código de aplicação,
model, schema, configuração, revisão ou lock foi modificado nesta rodada.
Foi acrescentado `tests/verificar_leitura_postgres.py` para repetir a auditoria
sem migrações ou CRUD de escrita. Os guias foram atualizados.

## Alembic: causa real do erro

Resultados atuais:

```text
current: 38c9a6fba33e
heads:   0ad60a28ccaf (head)
history: <base> → 38c9a6fba33e → 0ad60a28ccaf
check:   FAILED: Target database is not up to date. (código 255)
comparação direta models/tabelas (READ ONLY): []
```

A revisão `0ad60a28ccaf_tabelas.py` referencia `38c9a6fba33e` e tem `pass` nos dois
sentidos. Portanto, **o erro observado é o atraso do marcador de versão**, não
uma diferença de tabelas demonstrada pelo check. O comando check para ao detectar
que o banco ainda não chegou ao head. A comparação direta foi feita separadamente
e não encontrou diferenças nos models atuais. A revisão vazia ainda precisa ser
aplicada para o controle ficar alinhado, mas isso não foi autorizado nesta rodada.

Nenhum `upgrade`, `downgrade`, `revision`, `stamp` ou teste `--postgres` foi
executado nesta auditoria final. Não foram criados schemas no PostgreSQL.
A suíte antiga com `--postgres` aplica migrações temporárias; por isso foi evitada.

## Testes/comandos desta auditoria final

Executados na pasta `backend` (ou por `uv --directory backend`):

| Comando / execução | Resultado |
| --- | --- |
| `uv sync --offline --locked --dry-run` | Código 0, 57 pacotes resolvidos/51 conferidos, nenhuma mudança necessária. |
| `uv run --offline --no-sync python -m compileall -q app alembic tests` | Código 0. |
| `uv run --offline --no-sync python tests/verificar_backend.py` antes da correção | Código 1; 7 grupos executados, 4 falhas. Somente SQLite em memória. |
| Mesmo comando após correção | Código 0; **7 testes OK**, incluindo todos os CRUDs das quatro entidades. Somente SQLite em memória. |
| `uv run --offline --no-sync python tests/verificar_leitura_postgres.py` | Código 0; imports, chamadas de services, GETs, metadata e documentação aprovados; transação PostgreSQL READ ONLY. |
| `uv run --offline --no-sync alembic current` | Código 0; `38c9a6fba33e`. |
| `uv run --offline --no-sync alembic heads` | Código 0; `0ad60a28ccaf (head)`. |
| `uv run --offline --no-sync alembic history` | Código 0; duas revisões encadeadas. |
| `uv run --offline --no-sync alembic check` | Código 255; banco não está no head. |
| JavaScript de `docs-offline.html` analisado por `node:vm.Script` | Sintaxe OK; não executa o navegador. |
| `git diff --check -- backend` | Código 0. |

Ambiente observado: Python 3.14.8, uv 0.13.0, FastAPI 0.141.1, SQLAlchemy 2.0.54,
Pydantic 2.13.5, Alembic 1.20.0, psycopg 3.3.6, uvicorn 0.53.0,
python-dotenv 1.2.3. Não foi consultado nem impresso o conteúdo do `.env`.

## Conferência segura antes da prova

```bash
# Na pasta backend:
uv sync --offline --locked --dry-run
uv run --offline --no-sync python tests/verificar_backend.py
uv run --offline --no-sync python tests/verificar_leitura_postgres.py
uv run --offline --no-sync alembic current
uv run --offline --no-sync alembic heads
uv run --offline --no-sync uvicorn app.main:app --reload
```

Abra `/docs-offline`; para não escrever, use apenas GET. A aplicação de migrações,
o CRUD PostgreSQL de escrita e a preparação de outro banco dependem de autorização
específica. A execução em outra máquina e o navegador desconectado continuam sem
teste nesta auditoria. Os detalhes estão no índice rápido do guia.

---

## Histórico da preparação anterior

**Os resultados abaixo pertencem à rodada anterior.** Em particular, os testes
PostgreSQL com migrações temporárias não foram repetidos nesta auditoria final.

### Relatório original — backend / Projetos II

Auditoria local em **27/10/2026** para a avaliação de **28/10/2026**.
Nenhuma consulta à internet, instalação de pacote, push, remoção de tabelas existentes
ou exclusão de registros existentes foi realizada.

Legenda: **verificado** = há evidência local indicada; **pendente** = há uma ação
concreta ainda necessária; **não testado** = o cenário indicado não foi executado.
As marcações representam os testes desta máquina nesta data.

## Os 7 pontos

- [x] **1. Backend executável — verificado.** Importação da aplicação, compilação e
  inicialização real de uvicorn em porta local livre, com requisições HTTP.
  Evidências: `app/main.py`, `app/database.py`, `pyproject.toml`, `uv.lock`,
  `.python-version`, `tests/verificar_backend.py`.
  Python **3.14.8**, FastAPI **0.141.1**, SQLAlchemy **2.0.54**, Pydantic **2.13.5**,
  Alembic **1.20.0**, psycopg **3.3.6**, uvicorn **0.53.0** e python-dotenv **1.2.3**.
  `uv sync --offline --locked --dry-run`: `Would make no changes`.

- [x] **2. Models, tabelas e PK/FK — verificado em PostgreSQL.** Quatro tabelas,
  PK `id` em todas, três FKs e CEP único. Migração inicial aplicada em schema
  temporário. Introspecção e comparação com metadata: nenhuma diferença.
  Também houve comparação somente de leitura com as tabelas existentes: `[]`.
  Evidências: `app/models.py`, `alembic/versions/38c9a6fba33e_tabelas.py`,
  testes `test_02_models_e_migracoes` e `test_06_integridade_e_rollback`.

- [x] **3. Schemas Pydantic — verificado.** Entrada, atualização e saída nas quatro
  entidades. Respostas GET validadas por `response_model`; saída ORM com
  `from_attributes=True`. Corpos obrigatórios ausentes, tipos inválidos e ID de
  caminho inválido retornaram 422. Atualização parcial preservou campos omitidos.
  Evidências: `app/schemas.py`, `app/routes/*.py`, testes 03 e 05.
  Limites mantidos: sem `max_length`, validação de formato de email ou faixa de nota;
  update aceita `None` no schema, mas o banco rejeita `null` em NOT NULL com 409.

- [x] **4. Routes chamando services — verificado.** Cada operação de dados recebe
  `Session` por `Depends(get_db)` e chama seu service. Nenhuma route executa
  `db.get/add/commit/refresh/delete`, pandas ou SQL direto.
  Evidências: `app/routes/alunos.py`, `disciplinas.py`, `endereco.py`, `notas.py`;
  respectivos arquivos em `app/services/`; teste 07 de estrutura e requisições HTTP.
  As rotas de mensagem e documentação apenas retornam mensagem/arquivo.

- [x] **5. CRUD GET/POST/PUT/DELETE via ORM — verificado em PostgreSQL.** Para cada
  entidade: POST, GET lista e ID, PUT parcial, PUT vazio, nova leitura, DELETE e
  GET posterior 404. Também foram testados 404 em PUT/DELETE, FK inválida,
  CEP duplicado, NOT NULL e bloqueio de exclusão de pai referenciado (409).
  Uma operação válida após os conflitos comprovou recuperação com rollback.
  Evidências: `app/services/*_services.py`, `app/services/transacoes.py`, testes
  03, 04, 05 e 06. Sucessos mantêm HTTP 200; POST também retorna o ID gerado.

- [ ] **6. Alembic e comandos — verificado no teste isolado; pendente no banco
  existente.** `heads`, `history`, `current` e geração de SQL offline funcionaram.
  `upgrade head` foi executado no schema temporário, chegando a `0ad60a28ccaf`,
  com tabelas iguais aos models e rollback final confirmado.
  **O banco existente permanece em `38c9a6fba33e`**; a revisão posterior é vazia.
  `alembic check` nesse banco retornou `Target database is not up to date`
  (código 255). Nenhum upgrade foi aplicado ao schema existente.
  Evidências: `alembic/env.py`, `alembic/versions/*.py`, teste 02 e comandos abaixo.
  Para alinhar o banco escolhido, revise a revisão vazia e execute manualmente
  `alembic upgrade head`, seguido de `current` e `check`, usando o prefixo uv abaixo.
  Downgrade destrutivo: **não testado**, pois não era necessário à conferência segura.

- [x] **7. Documentação local de consulta — verificado quanto aos arquivos e HTTP.**
  Guia em português com árvore, responsabilidades, trechos reais, PK/FK, Pydantic,
  funções, Session/Depends, CRUD, uv/uvicorn/Alembic, roteiro de teste e erros comuns.
  `/docs-offline` serve HTML local e lê `/openapi.json`, sem bibliotecas externas.
  Evidências: `GUIA_PROVA_OFFLINE.md`, `README.md`, `app/static/docs-offline.html`,
  `app/main.py`, teste 01. O Swagger `/docs` continua disponível, mas usa CDN.
  Clique/execução JavaScript em navegador desconectado: **não testado** pela suíte;
  deve ser conferido manualmente no ambiente da prova.

## Diagnóstico antes dos ajustes

- O import de `app.main` falhava com
  `ModuleNotFoundError: No module named 'app.services.alunos_service'`.
- `alunos.py` importava `castrar_aluno`, mas chamava `cadastrar_aluno`; o POST ainda
  envolvia essa chamada em `Aluno(dados=...)`, argumento que não existe no model.
- Havia um service com o cadastro de aluno em andamento. O restante da lógica
  permanecia nas routes. Endereços, disciplinas e notas usavam pandas/SQL direto.
- Models e migração inicial já continham as quatro tabelas, PK/FK e CEP único.
- Os schemas de cadastro e atualização já existiam. Não havia schemas de saída.
- A conexão PostgreSQL funcionou. Tabelas existentes: `alembic_version`,
  `tb_enderecos`, `tb_alunos`, `tb_disciplinas`, `tb_notas`.
- O banco registrava `38c9a6fba33e`; `heads` apontava `0ad60a28ccaf`, revisão vazia.
- README era introdutório e dependia de orientações de instalação pela internet;
  não havia suíte de testes nem guia de consulta offline.

## Mudanças realizadas e motivo

1. Corrigido import/chamada de aluno, preservando o cadastro explícito do service.
2. CRUD transferido para os quatro services, com `select`, `db.get`, `db.add`,
   `db.refresh`, `db.delete` e confirmação de transação. `transacoes.py` centraliza
   `db.commit()`/`db.rollback()` e resposta 409, evitando repetição desse tratamento.
3. Routes simplificadas, preservando os caminhos existentes. Acrescentado GET por
   ID de disciplina. GET por ID de endereço/nota mantém lista com um objeto;
   aluno/disciplina retorna objeto. ID ausente agora retorna 404 de forma consistente.
4. Schemas `Out` adicionados sem substituir os schemas de entrada existentes.
5. `database.py` usa `URL.create` para caracteres especiais e carrega `.env` por
   caminho explícito. Timeout de conexão de 5 segundos.
6. Alembic ganhou geração SQL offline e suporte a conexão fornecida pelo teste;
   os arquivos de revisão existentes foram preservados.
7. Adicionados teste local reproduzível, formulário `/docs-offline` e guias.
   Dependências e lock do backend não foram alterados.

## Comandos e resultados observados

Executados a partir de `backend` (ou com `uv --directory backend`, equivalente):

| Comando / verificação | Resultado observado |
| --- | --- |
| `git status --short` antes das mudanças | Alterações prévias registradas abaixo; preservadas |
| `uv run --offline --no-sync python -c 'import sys; print(sys.version)'` | Python 3.14.8 |
| `uv sync --offline --locked --dry-run` | 57 pacotes resolvidos, 51 conferidos; `Would make no changes` |
| `uv run --offline --no-sync python -m compileall -q app alembic tests` | Sem erros; código 0 |
| `uv run --offline --no-sync python tests/verificar_backend.py --postgres` | **7 testes OK**, HTTP real + migrações PostgreSQL no schema isolado |
| `uv run --offline --no-sync python tests/verificar_backend.py` | **7 testes OK**, SQLite em memória com FKs ativadas; não substitui PostgreSQL |
| `uv run --offline --no-sync alembic heads` | `0ad60a28ccaf (head)` |
| `uv run --offline --no-sync alembic history` | `<base> → 38c9a6fba33e → 0ad60a28ccaf` |
| `uv run --offline --no-sync alembic current` | `38c9a6fba33e` no banco existente |
| `uv run --offline --no-sync alembic check` | **Pendente**: código 255, `Target database is not up to date` |
| `uv run --offline --no-sync alembic upgrade head --sql` | SQL de criação das tabelas e avanço das duas revisões gerado; código 0; não executado no banco existente |
| Comparação programática `compare_metadata(...)` em transação `READ ONLY` no banco existente | `[]`, sem diferenças entre tabelas e models |
| Consulta após testes | Revisão existente continua `38c9a6fba33e`; 0 schemas `prova_teste_%` restantes |
| Sintaxe do JavaScript local (`node --check`, lendo o script do HTML pela entrada padrão) | Código 0; não executa cliques nem substitui teste no navegador |
| `git diff --check -- backend` | Sem erros no backend |
| `git diff --check` no repositório inteiro | Apontou espaço em branco prévio em `frontend/connection/base_api.py:15`; frontend não foi alterado nesta tarefa |

Os sete testes executados são:

```text
test_01_documentacao                 OK
test_02_models_e_migracoes           OK
test_03_crud_quatro_entidades        OK
test_04_nao_encontrado               OK
test_05_validacao_422                OK
test_06_integridade_e_rollback       OK
test_07_routes_delegam               OK
```

O teste sobe uvicorn em uma thread e usa `urllib` para executar HTTP local. Não
foi instalado httpx, que não estava disponível, nem outra dependência.
No modo PostgreSQL o teste cria um schema aleatório em transação, aplica as duas
revisões ali e injeta sessões com `join_transaction_mode='create_savepoint'`.
Assim, os commits dos services fecham savepoints e a transação externa continua
aberta. Ao terminar, o rollback elimina todo o schema de teste. A ausência do
schema foi confirmada. Não houve teste em registros existentes.

## Preservação do trabalho existente

Estado inicial do Git:

```text
 M backend/app/routes/alunos.py
 M frontend/connection/base_api.py
 M frontend/menus/pagina_aluno.py
 M frontend/menus/pagina_endereco.py
 M frontend/uv.lock
?? backend/alembic/versions/0ad60a28ccaf_tabelas.py
?? backend/app/services/
```

Não foram executados reset, checkout de arquivos, limpeza do Git, commit ou push.
Nenhum arquivo do frontend foi editado nesta tarefa. A revisão não rastreada
`0ad60a28ccaf_tabelas.py` foi mantida como estava. O service de aluno em andamento
foi completado. Uma cópia dos fontes originais de `app/` e `alembic/`, sem `.env`,
foi salva em pasta temporária local `ibmec-backend-antes-*`; não dependa dela para
consulta na prova. Valores do `.env` não foram exibidos nem copiados para os guias.

## Pendências e checagem manual antes da avaliação

1. Confira na máquina que será usada na prova se Python, uv, dependências e
   PostgreSQL estão disponíveis sem internet. Se o banco configurado exigir rede,
   prepare um PostgreSQL local antes da avaliação.
2. Se quiser alinhar **o banco selecionado**, confira o `.env` no editor, revise
   `0ad60a28ccaf_tabelas.py` e execute `uv run --offline --no-sync alembic upgrade head`.
   Depois execute `current` e `check`. Essa aplicação não foi feita no banco existente.
3. Execute os testes PostgreSQL novamente e confirme `OK` e a mensagem de rollback.
4. Inicie o servidor e teste o formulário `/docs-offline` com a rede desconectada.
   A suíte comprovou a entrega do HTML, não os cliques do navegador.
5. Use os IDs dos seus próprios cadastros para prática manual. Downgrade, deleção
   de dados existentes, fluxo frontend e testes de concorrência/carga não foram executados.

Comandos mínimos de conferência (pasta `backend`):

```bash
uv sync --offline --locked --dry-run
uv run --offline --no-sync alembic current
uv run --offline --no-sync alembic heads
uv run --offline --no-sync python tests/verificar_backend.py --postgres
uv run --offline --no-sync uvicorn app.main:app --reload
```
