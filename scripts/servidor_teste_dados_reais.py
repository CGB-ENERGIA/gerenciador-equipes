"""Servidor de TESTE com uma CÓPIA dos dados reais do Neon.

Lê o Neon (só SELECT, nada é gravado lá), copia as tabelas para um SQLite
descartável e sobe a API em cima da cópia. Tudo o que for feito na tela vale só
para a cópia, que é recriada a cada início. Colunas que ainda não existem no
Neon (migration não aplicada) ficam com o valor padrão na cópia.

    .venv/Scripts/python.exe scripts/servidor_teste_dados_reais.py

Entrar com  teste / teste123  (conta de Administrador que só existe na cópia).
As contas t_* (senha abc123) e dois colaboradores fora de operação são recriados a
cada início, para o roteiro de testes (ROTEIRO_TESTES_PERFIS.md).
As contas reais vêm com as senhas reais; para entrar como uma delas, edite a
conta em Usuários (na cópia) e defina uma senha nova.
"""

import os
import sys
import tempfile
from pathlib import Path

from dotenv import dotenv_values

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

URL_NEON = dotenv_values(RAIZ / ".env").get("DATABASE_URL")
if not URL_NEON:
    raise SystemExit("DATABASE_URL não encontrada no .env")

ARQUIVO = Path(tempfile.gettempdir()) / "gerenciador_equipes_copia_real.db"
if ARQUIVO.exists():
    ARQUIVO.unlink()
# antes de importar o app: database.database lê isto
os.environ["DATABASE_URL"] = f"sqlite:///{ARQUIVO.as_posix()}"
os.environ["AUTO_CREATE_SCHEMA"] = "true"

from sqlalchemy import create_engine, inspect, select  # noqa: E402
from werkzeug.security import generate_password_hash  # noqa: E402

import app as modulo_app  # noqa: E402
from database.base import Base  # noqa: E402
from database.database import SessionLocal, engine  # noqa: E402
from datetime import date, datetime, timezone  # noqa: E402

from database.models import Colaborador, MembroEquipe, Usuario, VinculoUsuario  # noqa: E402


def copiar_do_neon():
    Base.metadata.create_all(engine)
    neon = create_engine(URL_NEON, pool_pre_ping=True)
    existentes = set(inspect(neon).get_table_names())

    with neon.connect() as origem, engine.begin() as destino:
        for tabela in Base.metadata.sorted_tables:
            if tabela.name not in existentes:
                print(f"[copia] {tabela.name}: não existe no Neon, ficou vazia")
                continue
            colunas_neon = {c["name"] for c in inspect(neon).get_columns(tabela.name)}
            colunas = [c for c in tabela.columns if c.name in colunas_neon]
            linhas = [dict(l._mapping) for l in origem.execute(select(*colunas))]
            if linhas:
                destino.execute(tabela.insert(), linhas)
            print(f"[copia] {tabela.name}: {len(linhas)} linha(s)")
    neon.dispose()


def conta_de_teste():
    s = SessionLocal()
    try:
        if not s.query(Usuario).filter(Usuario.USUARIO == "teste").first():
            s.add(Usuario(
                USUARIO="teste", NOME="ADMIN TESTE", NIVEL="ADMINISTRADOR", ATIVO=True,
                SENHA_HASH=generate_password_hash("teste123"),
            ))
            s.commit()
    finally:
        s.close()


# login, nome, nível, perfil, vínculos
CONTAS_DO_ROTEIRO = (
    ("t_dir_sup", "T DIRETO SUPERVISOR", "SUPERVISOR", "DIRETO", {"BASE": ["BACABAL"], "TIPO_EQUIPE": ["TODOS"]}),
    ("t_dir_coord", "T DIRETO COORDENADOR", "COORDENADOR", "DIRETO", {"BASE": ["TODOS"], "TIPO_EQUIPE": ["TODOS"]}),
    ("t_dir_ger", "T DIRETO GERENTE", "GERENTE", "DIRETO", {"BASE": ["TODOS"], "TIPO_EQUIPE": ["TODOS"]}),
    ("t_dir_gstc", "T DIRETO SO GSTC", "SUPERVISOR", "DIRETO", {"SETOR": ["GSTC"]}),
    ("t_dir_vazio", "T DIRETO SEM VINCULO", "SUPERVISOR", "DIRETO", {}),
    # como o Kleyton (Coordenador Direto da GOMAN de Itapecuru), que tambem aloca nos
    # Indiretos da GOMAN
    ("t_dir_goman", "T DIRETO GOMAN ITAPECURU", "COORDENADOR", "DIRETO",
     {"BASE": ["ITAPECURU"], "SETOR": ["GOMAN"], "SETOR_INDIRETO": ["GOMAN"]}),
    ("t_ind_adm", "T INDIRETO ADMINISTRATIVO", "SUPERVISOR", "INDIRETO", {"SETOR_INDIRETO": ["ADMINISTRATIVO"]}),
    ("t_ind_todos", "T INDIRETO TODOS", "SUPERVISOR", "INDIRETO", {"SETOR_INDIRETO": ["TODOS"]}),
    ("t_ind_vazio", "T INDIRETO SEM VINCULO", "SUPERVISOR", "INDIRETO", {}),
)


def contas_do_roteiro():
    s = SessionLocal()
    try:
        senha = generate_password_hash("abc123")
        for login, nome, nivel, perfil, vinculos in CONTAS_DO_ROTEIRO:
            conta = Usuario(
                USUARIO=login, NOME=nome, NIVEL=nivel, PERFIL=perfil, ATIVO=True, SENHA_HASH=senha,
            )
            for tipo, valores in vinculos.items():
                for valor in valores:
                    conta.vinculos.append(VinculoUsuario(TIPO=tipo, VALOR=valor))
            s.add(conta)

        # um afastado (com justificativa) e um desligado (com data), da base BCB,
        # para conferir quem vê o motivo
        diretos = (
            s.query(Colaborador)
            .filter(Colaborador.TIPO_FUNÇÃO == "DIRETO", Colaborador.AFASTADO.is_(False))
            .order_by(Colaborador.CHAPA)
            .all()
        )
        escolhidos = [c for c in diretos if c.CHAPA in ("23288", "23455")] or diretos[:2]
        agora = datetime.now(timezone.utc)
        for pessoa, desligado in zip(escolhidos, (False, True)):
            s.query(MembroEquipe).filter(MembroEquipe.CHAPA == pessoa.CHAPA).delete()
            pessoa.AFASTADO = True
            pessoa.AFASTADO_POR = "teste"
            pessoa.AFASTADO_EM = agora
            if desligado:
                pessoa.DATA_DESLIGAMENTO = date(2026, 12, 1)
            else:
                pessoa.JUSTIFICATIVA_AFASTAMENTO = "TESTE - LICENCA MEDICA"
        s.commit()
        print("[roteiro] contas t_* e 2 colaboradores fora de operação:",
              [f"{c.CHAPA} {c.NOME}" for c in escolhidos])
    finally:
        s.close()


if __name__ == "__main__":
    copiar_do_neon()
    conta_de_teste()
    contas_do_roteiro()
    print("Copia pronta. Entre com teste / teste123.")
    modulo_app.app.run(host="127.0.0.1", port=5000, debug=False)
