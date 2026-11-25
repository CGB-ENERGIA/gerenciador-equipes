"""Servidor de TESTE da API: banco SQLite descartável com dados de exemplo.

Não toca no banco de verdade (Neon): ignora o DATABASE_URL do .env e recria o
arquivo de teste a cada início. Serve para validar telas e fluxos à mão.

    .venv/Scripts/python.exe scripts/servidor_teste.py

Entrar com  admin / teste123  (conta que só existe neste banco de teste).
O frontend (npm --prefix frontend run dev, porta 9000) já aponta para a porta 5000.
"""

import os
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

ARQUIVO = Path(tempfile.gettempdir()) / "gerenciador_equipes_teste.db"
if ARQUIVO.exists():
    ARQUIVO.unlink()
# antes de importar o app: database.database lê isto (e o load_dotenv não sobrescreve)
os.environ["DATABASE_URL"] = f"sqlite:///{ARQUIVO.as_posix()}"
os.environ["AUTO_CREATE_SCHEMA"] = "true"

from werkzeug.security import generate_password_hash  # noqa: E402

import app as modulo_app  # noqa: E402
from database.base import Base  # noqa: E402
from database.database import SessionLocal, engine  # noqa: E402
from database.models import (  # noqa: E402
    Colaborador,
    ComposicaoEquipe,
    Equipe,
    MembroEquipe,
    Usuario,
)


def semear():
    Base.metadata.create_all(engine)
    s = SessionLocal()

    s.add(Usuario(
        USUARIO="admin", NOME="ADMIN TESTE", NIVEL="ADMINISTRADOR", ATIVO=True,
        SENHA_HASH=generate_password_hash("teste123"),
    ))

    equipes = {}
    for base, prefixo in [
        ("BACABAL", "BCB-01"), ("BACABAL", "BCB-02"),
        ("PEDREIRAS", "PED-01"), ("PEDREIRAS", "PED-02"),
    ]:
        equipe = Equipe(BASE=base, PREFIXO=prefixo)
        s.add(equipe)
        equipes[prefixo] = equipe
    s.flush()

    vagas = {}
    for prefixo, equipe in equipes.items():
        for funcao in ("ELETRICISTA", "ELETRICISTA", "MOTORISTA"):
            vaga = ComposicaoEquipe(
                equipe_id=equipe.id, FUNÇÃO_ER=funcao, ESTRUTURA="CONSTRUÇÃO",
            )
            s.add(vaga)
            vagas.setdefault(prefixo, []).append(vaga)
    s.flush()

    nomes = [
        ("1001", "ANA ELETRICISTA", "ELETRICISTA"),
        ("1002", "BRUNO ELETRICISTA", "ELETRICISTA"),
        ("1003", "CARLOS MOTORISTA", "MOTORISTA"),
        ("1004", "DANIELA ELETRICISTA", "ELETRICISTA"),
        ("1005", "EDUARDO MOTORISTA", "MOTORISTA"),
        ("1006", "FABIO LIVRE", "ELETRICISTA"),
        ("1007", "GISELE LIVRE", "ELETRICISTA"),
        ("1008", "HUGO LIVRE", "MOTORISTA"),
    ]
    secoes = {"1004": "PEDREIRAS", "1005": "PEDREIRAS", "1008": "PEDREIRAS"}
    for chapa, nome, funcao in nomes:
        s.add(Colaborador(
            CHAPA=chapa, NOME=nome, FUNÇÃO=funcao, TIPO_FUNÇÃO="DIRETO", AFASTADO=False,
            SEÇÃO=secoes.get(chapa, "BACABAL"),
        ))
    s.add(Colaborador(
        CHAPA="1009", NOME="IRENE AFASTADA", FUNÇÃO="ELETRICISTA", TIPO_FUNÇÃO="DIRETO",
        SEÇÃO="BACABAL", AFASTADO=True, JUSTIFICATIVA_AFASTAMENTO="LICENÇA MÉDICA", AFASTADO_POR="admin",
    ))
    s.flush()

    s.add_all([
        MembroEquipe(composicao_id=vagas["BCB-01"][0].id, CHAPA="1001"),
        MembroEquipe(composicao_id=vagas["BCB-01"][1].id, CHAPA="1002"),
        MembroEquipe(composicao_id=vagas["BCB-01"][2].id, CHAPA="1003"),
        MembroEquipe(composicao_id=vagas["PED-01"][0].id, CHAPA="1004"),
        MembroEquipe(composicao_id=vagas["PED-01"][2].id, CHAPA="1005"),
    ])
    s.commit()
    s.close()


if __name__ == "__main__":
    semear()
    print("=" * 60)
    print("SERVIDOR DE TESTE (SQLite descartável, não é o banco de verdade)")
    print(f"Banco: {ARQUIVO}")
    print("Login: admin / teste123")
    print("=" * 60)
    modulo_app.app.run(host="127.0.0.1", port=5000, debug=False)
