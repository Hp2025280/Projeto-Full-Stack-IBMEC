"""Auditoria HTTP/ORM somente leitura. Não aplica migrações nem executa CRUD de escrita.
Execute em backend: uv run --offline --no-sync python tests/verificar_leitura_postgres.py
"""
import ast
import importlib
import json
from pathlib import Path
import socket
import sys
import threading
import time
from urllib.error import HTTPError
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import text
from sqlalchemy.orm import Session
import uvicorn
from app.database import Base, engine, get_db
from app.main import app


def auditar():
    for path in Path('app').rglob('*.py'):
        importlib.import_module('.'.join(path.with_suffix('').parts))
    chamadas = 0
    for path in Path('app/routes').glob('*.py'):
        module = importlib.import_module('app.routes.' + path.stem)
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                owner = node.func.value
                if isinstance(owner, ast.Name) and owner.id.endswith('_services'):
                    assert callable(getattr(getattr(module, owner.id), node.func.attr)), str(path)
                    chamadas += 1
    spec = app.openapi()
    operation_ids = [operation['operationId'] for paths in spec['paths'].values() for method, operation in paths.items() if method in {'get', 'post', 'put', 'delete'}]
    assert len(operation_ids) == len(set(operation_ids)), 'operationId repetido'
    print(f'Imports e chamadas de services: OK ({chamadas} chamadas; {len(operation_ids)} operações únicas)')

    with engine.connect() as conn:
        conn.execute(text('SET TRANSACTION READ ONLY'))
        assert conn.scalar(text('SHOW transaction_read_only')) == 'on'
        assert compare_metadata(MigrationContext.configure(conn), Base.metadata) == [], 'Tabelas diferem dos models'
        print('PostgreSQL READ ONLY: models/tabelas sem diferenças')
        print('Revisão atual:', conn.scalar(text('SELECT version_num FROM alembic_version')))

        def sessao_leitura():
            with Session(bind=conn, join_transaction_mode='create_savepoint') as db:
                yield db

        app.dependency_overrides[get_db] = sessao_leitura
        sock = socket.socket()
        sock.bind(('127.0.0.1', 0))
        base_url = f'http://127.0.0.1:{sock.getsockname()[1]}'
        server = uvicorn.Server(uvicorn.Config(app, log_level='critical', access_log=False))
        thread = threading.Thread(target=server.run, kwargs={'sockets': [sock]}, daemon=True)

        def get(path, esperado=200):
            try:
                response = urlopen(base_url + path, timeout=10)
            except HTTPError as exc:
                response = exc
            with response:
                assert response.status == esperado, f'GET {path}: HTTP {response.status}'
                payload = response.read().decode()
                return json.loads(payload) if 'application/json' in response.headers.get('Content-Type', '') else payload

        try:
            thread.start()
            for _ in range(100):
                if server.started:
                    break
                time.sleep(.05)
            assert server.started, 'Servidor não iniciou'
            for prefix, leitura in [('alunos', 'alunos'), ('enderecos', 'endereco'), ('disciplinas', 'disciplina'), ('notas', 'notas')]:
                path = f'/{prefix}/pegar-dados-{leitura}'
                dados = get(path)
                assert isinstance(dados, list)
                if dados:
                    get(path + '-por-id/' + str(dados[0]['id']))
                    detalhe = 'lista e ID existente HTTP 200'
                else:
                    detalhe = 'lista HTTP 200; ID existente NÃO TESTADO (tabela vazia)'
                get(path + '-por-id/2147483647', 404)
                print(f'GET {prefix}: {detalhe}; ID ausente HTTP 404')
            assert len(get('/openapi.json')['paths']) == 24
            assert 'swagger-ui' in get('/docs')
            offline = get('/docs-offline')
            assert "fetch('/openapi.json')" in offline and 'https://' not in offline
            print('OpenAPI, /docs e HTML /docs-offline: HTTP 200; offline sem URL externa')
        finally:
            server.should_exit = True
            thread.join(timeout=10)
            sock.close()
            app.dependency_overrides.clear()
            conn.rollback()
    engine.dispose()
    print('APROVADO: auditoria PostgreSQL somente leitura; nenhuma migração ou escrita executada.')


if __name__ == '__main__':
    auditar()
