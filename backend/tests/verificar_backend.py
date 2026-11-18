"""Teste HTTP real sem novas dependências. PostgreSQL isolado ou SQLite em memória.

Execute em backend: uv run --offline --no-sync python tests/verificar_backend.py --postgres
O schema PostgreSQL é criado dentro de uma transação e removido pelo rollback.
"""
import ast
from pathlib import Path
import socket
import sys
import threading
import time
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

# Execução direta do script também encontra app/.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
import uvicorn
import json

from app.database import Base, engine, get_db
from app.main import app

POSTGRES = '--postgres' in sys.argv
if POSTGRES:
    sys.argv.remove('--postgres')


class BackendTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = None
        cls.connection = None
        cls.server = None
        cls.thread = None
        cls.test_engine = engine if POSTGRES else create_engine(
            'sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool
        )
        if not POSTGRES:
            @event.listens_for(cls.test_engine, 'connect')
            def ativar_fk(dbapi_connection, _):
                dbapi_connection.execute('PRAGMA foreign_keys=ON')
        cls.addClassCleanup(cls.limpar)
        cls.connection = cls.test_engine.connect()
        cls.transaction = cls.connection.begin()
        if POSTGRES:
            cls.schema = 'prova_teste_' + uuid4().hex
            # Identificador gerado internamente, sem entrada do usuário.
            cls.connection.execute(text(f'CREATE SCHEMA "{cls.schema}"'))
            cls.connection.execute(text(f'SET LOCAL search_path TO "{cls.schema}"'))
            config = Config('alembic.ini')
            config.attributes['connection'] = cls.connection
            command.upgrade(config, 'head')
            print('Migrações: upgrade head em schema PostgreSQL temporário OK')
        else:
            Base.metadata.create_all(cls.connection)

        def sessao_teste():
            with Session(bind=cls.connection, join_transaction_mode='create_savepoint') as db:
                yield db

        app.dependency_overrides[get_db] = sessao_teste
        sock = socket.socket()
        sock.bind(('127.0.0.1', 0))
        cls.base_url = f'http://127.0.0.1:{sock.getsockname()[1]}'
        cls.server = uvicorn.Server(uvicorn.Config(app, log_level='critical', access_log=False))
        cls.thread = threading.Thread(target=cls.server.run, kwargs={'sockets': [sock]}, daemon=True)
        cls.thread.start()
        for _ in range(100):
            if cls.server.started:
                break
            time.sleep(.05)
        if not cls.server.started:
            raise RuntimeError('Servidor de teste não iniciou')
        print('Modo:', 'PostgreSQL isolado' if POSTGRES else 'SQLite em memória (não comprova PostgreSQL)')

    @classmethod
    def limpar(cls):
        if cls.server:
            cls.server.should_exit = True
        if cls.thread:
            cls.thread.join(timeout=10)
        app.dependency_overrides.clear()
        if cls.connection:
            if cls.connection.in_transaction():
                cls.connection.rollback()
            if cls.schema:
                restante = cls.connection.scalar(text('SELECT EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = :nome)'), {'nome': cls.schema})
                if restante:
                    raise AssertionError('O schema temporário ainda existe após rollback')
                print('Rollback confirmado: schema temporário ausente; dados existentes preservados.')
            cls.connection.close()
        cls.test_engine.dispose()

    def requisicao(self, method, path, body=None, status=200):
        request = Request(self.base_url + path, method=method,
                          data=json.dumps(body).encode() if body is not None else None,
                          headers={'Content-Type': 'application/json'})
        try:
            response = urlopen(request, timeout=10)
        except HTTPError as exc:
            response = exc
        with response:
            payload = response.read().decode()
            self.assertEqual(response.status, status, f'{method} {path}: {payload}')
            if 'application/json' in response.headers.get('Content-Type', ''):
                return json.loads(payload)
            return payload

    def endereco(self, cep=None):
        return self.requisicao('POST', '/enderecos/criar-endereco', {
            'cep': cep or uuid4().hex[:10], 'endereco': 'Rua Teste', 'bairro': 'Centro',
            'cidade': 'Rio de Janeiro', 'estado': 'RJ', 'regiao': 'Sudeste'})['id']

    def disciplina(self):
        return self.requisicao('POST', '/disciplinas/criar-disciplina', {
            'nome_disciplina': 'Projetos II', 'carga': '80', 'semestre': '2026.2'})['id']

    def aluno(self, endereco_id):
        return self.requisicao('POST', '/alunos/criar-aluno', {
            'matricula': 'TESTE', 'nome_aluno': 'Aluno Teste',
            'email': 'teste@example.invalid', 'endereco_id': endereco_id})['id']

    def test_01_documentacao(self):
        spec = self.requisicao('GET', '/openapi.json')
        self.assertEqual(len(spec['paths']), 24)
        self.assertIn('swagger-ui', self.requisicao('GET', '/docs'))
        offline = self.requisicao('GET', '/docs-offline')
        self.assertIn("fetch('/openapi.json')", offline)
        self.assertNotIn('https://', offline)

    def test_02_models_e_migracoes(self):
        inspector = inspect(self.connection)
        self.assertEqual(set(inspector.get_table_names()) - {'alembic_version'}, set(Base.metadata.tables))
        for table in Base.metadata.tables:
            self.assertEqual(inspector.get_pk_constraint(table)['constrained_columns'], ['id'])
        self.assertEqual(sum(len(inspector.get_foreign_keys(t)) for t in Base.metadata.tables), 3)
        self.assertEqual(compare_metadata(MigrationContext.configure(self.connection), Base.metadata), [])
        if POSTGRES:
            self.assertEqual(self.connection.scalar(text('SELECT version_num FROM alembic_version')), '0ad60a28ccaf')

    def test_03_crud_quatro_entidades(self):
        endereco = self.endereco()
        aluno = self.aluno(endereco)
        disciplina = self.disciplina()
        nota = self.requisicao('POST', '/notas/criar-nota', {'nome_id': aluno, 'disciplina_id': disciplina, 'nota': 7.5})['id']
        casos = [
            ('enderecos', 'endereco', 'endereco', endereco, {'bairro': 'Bairro atualizado'}),
            ('alunos', 'aluno', 'alunos', aluno, {'nome_aluno': 'Nome atualizado'}),
            ('disciplinas', 'disciplina', 'disciplina', disciplina, {'carga': '90'}),
            ('notas', 'nota', 'notas', nota, {'nota': 9.5}),
        ]
        for prefix, singular, leitura, id, mudanca in casos:
            with self.subTest(entidade=prefix):
                self.assertTrue(any(item['id'] == id for item in self.requisicao('GET', f'/{prefix}/pegar-dados-{leitura}')))
                url = f'/{prefix}/pegar-dados-{leitura}-por-id/{id}'
                antes = self.requisicao('GET', url)
                antes = antes[0] if isinstance(antes, list) else antes
                self.requisicao('PUT', f'/{prefix}/atualizar-{singular}/{id}', mudanca)
                depois = self.requisicao('GET', url)
                depois = depois[0] if isinstance(depois, list) else depois
                self.assertEqual(depois, {**antes, **mudanca})
                self.requisicao('PUT', f'/{prefix}/atualizar-{singular}/{id}', {})
        for prefix, singular, leitura, id, _ in reversed(casos):
            self.requisicao('DELETE', f'/{prefix}/deletar-{singular}/{id}')
            self.requisicao('GET', f'/{prefix}/pegar-dados-{leitura}-por-id/{id}', status=404)

    def test_04_nao_encontrado(self):
        for prefix, singular, leitura in [('alunos', 'aluno', 'alunos'), ('enderecos', 'endereco', 'endereco'), ('disciplinas', 'disciplina', 'disciplina'), ('notas', 'nota', 'notas')]:
            self.requisicao('GET', f'/{prefix}/pegar-dados-{leitura}-por-id/2147483647', status=404)
            self.requisicao('PUT', f'/{prefix}/atualizar-{singular}/2147483647', {}, status=404)
            self.requisicao('DELETE', f'/{prefix}/deletar-{singular}/2147483647', status=404)

    def test_05_validacao_422(self):
        for path in ['/alunos/criar-aluno', '/enderecos/criar-endereco', '/disciplinas/criar-disciplina', '/notas/criar-nota']:
            self.requisicao('POST', path, {}, status=422)
        self.requisicao('POST', '/notas/criar-nota', {'nome_id': 'abc', 'disciplina_id': 1, 'nota': 'abc'}, status=422)
        self.requisicao('GET', '/alunos/pegar-dados-alunos-por-id/abc', status=422)

    def test_06_integridade_e_rollback(self):
        endereco = self.endereco('TESTE-CEP')
        aluno = self.aluno(endereco)
        disciplina = self.disciplina()
        nota = self.requisicao('POST', '/notas/criar-nota', {'nome_id': aluno, 'disciplina_id': disciplina, 'nota': 8})['id']
        self.requisicao('POST', '/enderecos/criar-endereco', {'cep': 'TESTE-CEP', 'endereco': 'Rua', 'bairro': 'B', 'cidade': 'C', 'estado': 'RJ', 'regiao': 'R'}, status=409)
        for prefix, singular, id in [('enderecos', 'endereco', endereco), ('alunos', 'aluno', aluno), ('disciplinas', 'disciplina', disciplina)]:
            self.requisicao('DELETE', f'/{prefix}/deletar-{singular}/{id}', status=409)
        self.requisicao('PUT', f'/alunos/atualizar-aluno/{aluno}', {'endereco_id': 2147483647}, status=409)
        self.requisicao('PUT', f'/alunos/atualizar-aluno/{aluno}', {'nome_aluno': None}, status=409)
        for body in [{'nome_id': 2147483647, 'disciplina_id': disciplina, 'nota': 8}, {'nome_id': aluno, 'disciplina_id': 2147483647, 'nota': 8}]:
            self.requisicao('POST', '/notas/criar-nota', body, status=409)
        self.requisicao('POST', '/alunos/criar-aluno', {'matricula': 'X', 'nome_aluno': 'X', 'email': 'x@example.invalid', 'endereco_id': 2147483647}, status=409)
        # Confere que falhas não impedem uma operação válida posterior.
        self.requisicao('PUT', f'/notas/atualizar-nota/{nota}', {'nota': 10})
        for path, id in [('/notas/deletar-nota/', nota), ('/alunos/deletar-aluno/', aluno), ('/disciplinas/deletar-disciplina/', disciplina), ('/enderecos/deletar-endereco/', endereco)]:
            self.requisicao('DELETE', path + str(id))

    def test_07_routes_delegam(self):
        proibidos = {'get', 'add', 'commit', 'refresh', 'delete', 'scalars', 'execute', 'connect', 'to_sql', 'read_sql'}
        for path in Path('app/routes').glob('*.py'):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                    if node.func.value.id in {'db', 'engine', 'pd'}:
                        self.assertNotIn(node.func.attr, proibidos, str(path))


if __name__ == '__main__':
    unittest.main(verbosity=2)
