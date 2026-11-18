from app.database import Base, engine
import app.models
from alembic import context

config = context.config
target_metadata = Base.metadata


def executar_migracoes(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    # Permite testar migrações com uma conexão/transação isolada.
    connection = config.attributes.get("connection")
    if connection is not None:
        executar_migracoes(connection)
    else:
        with engine.connect() as connection:
            executar_migracoes(connection)


def run_migrations_offline():
    context.configure(
        url=engine.url, target_metadata=target_metadata,
        literal_binds=True, dialect_opts={"paramstyle": "named"}
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
