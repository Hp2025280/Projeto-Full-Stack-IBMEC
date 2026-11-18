from dotenv import load_dotenv
import os
from pathlib import Path
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# Parametros da configuracao da conexao
user = os.getenv('user')
senha = os.getenv('senha')
host = os.getenv('host')
port = os.getenv('port')
banco = os.getenv('banco')

# Conexao
DATABASE_URL = URL.create(
    "postgresql+psycopg", username=user, password=senha,
    host=host, port=int(port) if port else None, database=banco
)

# engine de conexao com o db
engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 5})

# configuracao de sessao
SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    with SessionLocal() as db:
        yield db
