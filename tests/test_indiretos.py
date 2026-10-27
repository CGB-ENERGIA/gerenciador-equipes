"""Regras da alocação de indiretos (planilha e normalização), num SQLite em
memória — não toca no banco de verdade."""

import io

import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import indiretos
from database.base import Base
from database.models import AlocacaoIndireto, Colaborador


@pytest.fixture
def sessao():
    motor = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(motor)
    s = sessionmaker(bind=motor)()
    s.add_all([
        Colaborador(CHAPA="100", NOME="ANA INDIRETA", TIPO_FUNÇÃO="INDIRETO"),
        Colaborador(CHAPA="101", NOME="BRUNO INDIRETO", TIPO_FUNÇÃO="INDIRETO"),
        Colaborador(CHAPA="200", NOME="CARLA DIRETA", TIPO_FUNÇÃO="DIRETO"),
        Colaborador(CHAPA="900", NOME="CHEFE UM", TIPO_FUNÇÃO="INDIRETO"),
        Colaborador(CHAPA="901", NOME="CHEFE DOIS", TIPO_FUNÇÃO="DIRETO"),
    ])
    s.commit()
    yield s
    s.close()


def planilha(linhas, aba="Alocação"):
    colunas = ["SETOR", "BASE", "CHAPA RESPONSÁVEL", "NOME RESPONSÁVEL",
               "CHAPA INDIRETO", "NOME INDIRETO", "FUNÇÃO INDIRETO", "OBSERVAÇÃO"]
    arquivo = io.BytesIO()
    with pd.ExcelWriter(arquivo, engine="openpyxl") as writer:
        pd.DataFrame([{"X": 1}]).to_excel(writer, index=False, sheet_name="Instruções")
        pd.DataFrame(linhas, columns=colunas).to_excel(writer, index=False, sheet_name=aba)
    arquivo.seek(0)
    return arquivo


def linha(setor="Almoxarifado", base="bcb", resp=900, chapa=100, obs=None):
    return {"SETOR": setor, "BASE": base, "CHAPA RESPONSÁVEL": resp,
            "CHAPA INDIRETO": chapa, "OBSERVAÇÃO": obs}


def test_le_aba_pelo_nome_e_padroniza_setor_e_base(sessao):
    plano = indiretos.analisar_planilha_indiretos(
        planilha([linha(setor="  almoxarifado   central ", chapa=100)]), sessao
    )
    assert not plano["erros"]
    item = plano["alocar"][0]
    assert (item["setor"], item["base"], item["chapa"]) == ("ALMOXARIFADO CENTRAL", "BCB", "100")


def test_responsaveis_diferentes_no_mesmo_setor_e_base_sao_aceitos(sessao):
    plano = indiretos.analisar_planilha_indiretos(planilha([
        linha(resp=900, chapa=100),
        linha(resp=901, chapa=101),
    ]), sessao)
    assert not plano["erros"]
    assert {i["responsavel_chapa"] for i in plano["alocar"]} == {"900", "901"}


@pytest.mark.parametrize(
    ("alteracao", "trecho"),
    [
        ({"chapa": 999}, "CHAPA INDIRETO não encontrada"),
        ({"chapa": 200}, "não INDIRETO"),
        ({"resp": 777}, "CHAPA RESPONSÁVEL não encontrada"),
        ({"setor": None}, "Falta preencher: SETOR"),
    ],
)
def test_linhas_invalidas_viram_erro(sessao, alteracao, trecho):
    plano = indiretos.analisar_planilha_indiretos(planilha([linha(**alteracao)]), sessao)
    assert trecho in plano["erros"][0]["erro"]


def test_indireto_repetido_e_linhas_vazias(sessao):
    vazia = {"SETOR": None, "BASE": None, "CHAPA RESPONSÁVEL": None,
             "CHAPA INDIRETO": None, "OBSERVAÇÃO": None}
    plano = indiretos.analisar_planilha_indiretos(
        planilha([linha(chapa=100), vazia, linha(chapa=100, base="PDT")]), sessao
    )
    assert len(plano["alocar"]) == 1
    assert "repetido" in plano["erros"][0]["erro"]


def test_mover_atualizar_e_sem_mudanca(sessao):
    sessao.add_all([
        AlocacaoIndireto(CHAPA="100", SETOR="FROTA", BASE="BCB", RESPONSAVEL_CHAPA="900"),
        AlocacaoIndireto(CHAPA="101", SETOR="ALMOXARIFADO", BASE="BCB", RESPONSAVEL_CHAPA="900"),
        AlocacaoIndireto(CHAPA="900", SETOR="ALMOXARIFADO", BASE="BCB", RESPONSAVEL_CHAPA="901"),
    ])
    sessao.commit()
    plano = indiretos.analisar_planilha_indiretos(planilha([
        linha(chapa=100),                 # FROTA -> ALMOXARIFADO: mover
        linha(chapa=101, resp=901),       # só o responsável: atualizar
        linha(chapa=900, resp=901),       # igual: sem mudança
    ]), sessao)
    assert [i["chapa"] for i in plano["mover"]] == ["100"]
    assert plano["mover"][0]["de"] == "FROTA · BCB"
    assert [i["chapa"] for i in plano["atualizar"]] == ["101"]
    assert plano["sem_mudanca"] == 1


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [(12345, "12345"), (12345.0, "12345"), ("12345.0", "12345"), (" 0123 ", "0123"), (None, "")],
)
def test_chapa_da_celula(valor, esperado):
    assert indiretos.chapa_da_celula(valor) == esperado
