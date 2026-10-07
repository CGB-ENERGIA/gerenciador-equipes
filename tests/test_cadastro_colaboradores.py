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
    }
    base.update(extra)
    return base


def test_cadastro_valido_normaliza_campos():
    campos, rateios, erro = validar_cadastro_colaborador(corpo())

    assert erro is None
    assert rateios == []
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
