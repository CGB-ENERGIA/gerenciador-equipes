"""Validação do cadastro de colaborador feito pela tela (sem banco)."""

from datetime import date

import pytest

from app import validar_cadastro_colaborador


def corpo(**extra):
    base = {
        "chapa": "12345",
        "nome": "FULANO DE TAL",
        "tipo_funcao": "direto",
        "funcao": "ELETRICISTA",
        "admissao": "2024-01-31",
        "rateios": [{"rateio": "2.127.01", "grpccusto": "A"}],
    }
    base.update(extra)
    return base


def test_cadastro_valido_normaliza_campos():
    campos, rateios, erro = validar_cadastro_colaborador(corpo())

    assert erro is None
    assert rateios == [("2.127.01", "A")]
    assert campos["chapa"] == "12345"
    assert campos["TIPO_FUNÇÃO"] == "DIRETO"
    assert campos["ADMISSÃO"] == date(2024, 1, 31)
    assert campos["SEÇÃO"] is None


def test_admissao_aceita_dia_mes_ano():
    campos, _, erro = validar_cadastro_colaborador(corpo(admissao="31/01/2024"))

    assert erro is None
    assert campos["ADMISSÃO"] == date(2024, 1, 31)


def test_admissao_vazia_fica_sem_data():
    campos, _, erro = validar_cadastro_colaborador(corpo(admissao=""))

    assert erro is None
    assert campos["ADMISSÃO"] is None


@pytest.mark.parametrize(
    ("alteracao", "trecho"),
    [
        ({"chapa": "  "}, "CHAPA"),
        ({"nome": ""}, "NOME"),
        ({"tipo_funcao": ""}, "TIPO_FUNÇÃO"),
        ({"tipo_funcao": "OUTRO"}, "DIRETO ou INDIRETO"),
        ({"admissao": "31-31-2024"}, "ADMISSÃO"),
        ({"rateios": []}, "RATEIO"),
        ({"rateios": [{"rateio": "  ", "grpccusto": "A"}]}, "RATEIO"),
        ({"rateios": None}, "RATEIO"),
    ],
)
def test_cadastro_invalido_devolve_erro(alteracao, trecho):
    campos, rateios, erro = validar_cadastro_colaborador(corpo(**alteracao))

    assert campos is None and rateios is None
    assert trecho in erro


def test_rateios_ignoram_vazios_e_repetidos():
    _, rateios, erro = validar_cadastro_colaborador(corpo(rateios=[
        {"rateio": "2.127.01", "grpccusto": "A"},
        {"rateio": "2.127.01", "grpccusto": "A"},
        {"rateio": "", "grpccusto": "B"},
        {"rateio": "2.169.04", "grpccusto": ""},
    ]))

    assert erro is None
    assert rateios == [("2.127.01", "A"), ("2.169.04", None)]


# ============================================================
# EDIÇÃO EM MASSA
# ============================================================

from app import validar_edicao_massa  # noqa: E402


def test_edicao_em_massa_so_altera_o_que_foi_preenchido():
    alteracoes, rateios, erro = validar_edicao_massa({
        "funcao": " ELETRICISTA ",
        "secao": "",
        "tipo_funcao": "indireto",
        "admissao": "31/01/2024",
    })

    assert erro is None
    assert rateios is None
    assert alteracoes == {
        "FUNÇÃO": "ELETRICISTA",
        "TIPO_FUNÇÃO": "INDIRETO",
        "ADMISSÃO": date(2024, 1, 31),
    }


def test_edicao_em_massa_com_rateios_substitui_a_lista():
    alteracoes, rateios, erro = validar_edicao_massa({
        "rateios": [{"rateio": "2.127.01", "grpccusto": "A"}],
    })

    assert erro is None
    assert alteracoes == {}
    assert rateios == [("2.127.01", "A")]


@pytest.mark.parametrize(
    ("dados", "trecho"),
    [
        ({}, "ao menos um campo"),
        ({"funcao": "  "}, "ao menos um campo"),
        ({"tipo_funcao": "OUTRO"}, "DIRETO ou INDIRETO"),
        ({"admissao": "99/99/2024"}, "ADMISSÃO"),
        ({"rateios": []}, "RATEIO"),
        ({"rateios": [{"rateio": " "}]}, "RATEIO"),
    ],
)
def test_edicao_em_massa_invalida(dados, trecho):
    alteracoes, rateios, erro = validar_edicao_massa(dados)

    assert alteracoes is None and rateios is None
    assert trecho in erro


# ============================================================
# GRPCCUSTO: zero final perdido quando o Excel guarda como número
# ============================================================

from database.importacao.importar_colaboradores import (  # noqa: E402
    codigo_grupo_ccusto,
    normalizar_linha_colaborador,
)


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        (2.17, "2.170"),      # célula numérica 2.170 lida pelo pandas
        (2.127, "2.127"),
        (2.1, "2.100"),
        ("2.17", "2.170"),    # já gravado como texto sem o zero
        ("2.169", "2.169"),
        (" 2.170 ", "2.170"),
        ("A", "A"),           # texto livre passa como está
        ("", None),
        (None, None),
        (float("nan"), None),
    ],
)
def test_codigo_grupo_ccusto_mantem_tres_casas(valor, esperado):
    assert codigo_grupo_ccusto(valor) == esperado


def test_planilha_com_grpccusto_numerico_grava_2_170():
    dados, erro = normalizar_linha_colaborador({
        "CHAPA": 12345, "NOME": "FULANO", "TIPO_FUNÇÃO": "DIRETO",
        "RATEIO_FUNCIONARIO": "2.170.05", "GRPCCUSTO": 2.17,
    })

    assert erro is None
    assert dados["grpccusto"] == "2.170"


def test_tela_com_grpccusto_sem_zero_grava_2_170():
    _, rateios, erro = validar_cadastro_colaborador(corpo(rateios=[
        {"rateio": "2.170.05", "grpccusto": "2.17"},
    ]))

    assert erro is None
    assert rateios == [("2.170.05", "2.170")]
