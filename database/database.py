import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.base import Base
from database import models


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "A variável DATABASE_URL não foi encontrada no arquivo .env"
    )


# pool_size baixo de propósito: no Vercel cada requisição pode cair numa
# instância de função nova (serverless), então cada uma abre o próprio pool
# — não faz sentido manter 5 conexões ociosas por instância como no projeto
# original (Render, processo único de longa duração). A DATABASE_URL já usa
# o endpoint "-pooler" da Neon (pgbouncer do lado deles), que é quem
# realmente absorve picos de muitas instâncias abrindo conexão ao mesmo
# tempo — isto aqui só evita desperdiçar esse pool com conexões ociosas.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=1,
    max_overflow=2,
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


if os.getenv("AUTO_CREATE_SCHEMA", "false").lower() == "true":
    Base.metadata.create_all(bind=engine)

print("Banco de dados conectado com sucesso!")