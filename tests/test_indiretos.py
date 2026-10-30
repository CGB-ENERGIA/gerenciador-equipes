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


def test_funcao_para_gravar(sessao):
    sessao.add(Colaborador(CHAPA="300", NOME="OUTRO", FUNÇÃO="ENCARREGADO DE FROTA I"))
    sessao.commit()
    pessoa = sessao.query(Colaborador).filter(Colaborador.CHAPA == "100").first()
    pessoa.FUNÇÃO = "AUXILIAR"

    # existe no cadastro: grava
    assert indiretos.funcao_para_gravar(sessao, pessoa, " ENCARREGADO DE FROTA I ") == (
        "ENCARREGADO DE FROTA I"
    )
    # vazia ou igual à do cadastro: volta a usar a do cadastro
    assert indiretos.funcao_para_gravar(sessao, pessoa, "") is None
    assert indiretos.funcao_para_gravar(sessao, pessoa, "AUXILIAR") is None
    # inventada: recusa
    with pytest.raises(indiretos.FuncaoInvalida):
        indiretos.funcao_para_gravar(sessao, pessoa, "FUNÇÃO INVENTADA")


def test_validar_cadeia_recusa_ciclo_e_responder_a_si_mesmo():
    # Camila (1) <- Rikelme (2) <- Luis (3) <- Danilo (4); Camila responde a si mesma
    hoje = {"1": "1", "2": "1", "3": "2", "4": "3"}
    indiretos.validar_cadeia(hoje, {"4": "2"})  # Danilo direto ao Rikelme: ok
    with pytest.raises(indiretos.OrganogramaInvalido):
        indiretos.validar_cadeia(hoje, {"3": "3"})
    # Rikelme abaixo do Danilo fecharia Rikelme -> Danilo -> Luis -> Rikelme
    with pytest.raises(indiretos.OrganogramaInvalido):
        indiretos.validar_cadeia(hoje, {"2": "4"})
    # "acima": Luis assume o chefe do Rikelme e o Rikelme passa a responder ao Luis
    indiretos.validar_cadeia(hoje, {"3": "1", "2": "3"})


def test_planilha_le_subsetor_e_sem_a_coluna_mantem_o_atual(sessao):
    sessao.add(AlocacaoIndireto(CHAPA="100", SETOR="ALMOXARIFADO", BASE="BCB",
                                RESPONSAVEL_CHAPA="900", SUBSETOR="OBRAS"))
    sessao.commit()
    # com a coluna: troca
    linhas = [dict(linha(chapa=100), **{"SUBSETOR": " epi/epc "})]
    colunas = ["SETOR", "BASE", "CHAPA RESPONSÁVEL", "CHAPA INDIRETO", "OBSERVAÇÃO", "SUBSETOR"]
    arquivo = io.BytesIO()
    with pd.ExcelWriter(arquivo, engine="openpyxl") as writer:
        pd.DataFrame(linhas, columns=colunas).to_excel(writer, index=False, sheet_name="Alocação")
    arquivo.seek(0)
    plano = indiretos.analisar_planilha_indiretos(arquivo, sessao)
    assert plano["atualizar"][0]["subsetor"] == "EPI/EPC"
    # sem a coluna (planilha antiga): mantém OBRAS, nada a mudar
    plano = indiretos.analisar_planilha_indiretos(planilha([linha(chapa=100)]), sessao)
    assert plano["sem_mudanca"] == 1 and not plano["atualizar"]


def test_plano_bases_responsavel():
    def a(chapa, base, resp, bases=None):
        return AlocacaoIndireto(CHAPA=chapa, SETOR="ALMOX", BASE=base,
                                RESPONSAVEL_CHAPA=resp, BASES_RESPONSAVEL=bases)
    # Camila (C) chefe de todos; Rikelme (R) em BCB; equipe em BCB e BDC
    alocacoes = {x.CHAPA: x for x in [
        a("R", "BCB", "C"), a("B1", "BCB", "C"), a("B2", "BCB", "C"),
        a("D1", "BDC", "C"), a("L", "BCB", "B1"),
    ]}
    resp, bases = indiretos.plano_bases_responsavel(alocacoes, "R", ["BCB"])
    # quem da BCB respondia à Camila passa ao Rikelme; L (abaixo de B1) fica
    assert resp == {"B1": "R", "B2": "R"}
    assert bases == {"R": ["BCB"]}

    alocacoes["R"].BASES_RESPONSAVEL = "BCB"
    alocacoes["B1"].RESPONSAVEL_CHAPA = alocacoes["B2"].RESPONSAVEL_CHAPA = "R"
    # desmarca BCB e marca BDC: BCB volta à Camila, BDC vem para ele
    resp, bases = indiretos.plano_bases_responsavel(alocacoes, "R", ["BDC"])
    assert resp == {"B1": "C", "B2": "C", "D1": "R"}
    assert bases == {"R": ["BDC"]}


def test_subsetor_efetivo_herda_pela_cadeia():
    def a(chapa, resp, sub=None, setor="ALMOX"):
        return AlocacaoIndireto(CHAPA=chapa, SETOR=setor, BASE="BCB",
                                RESPONSAVEL_CHAPA=resp, SUBSETOR=sub)
    # Luis (OBRAS) <- Danilo <- Ana ; Bia (EPI) abaixo de Luis ; Caio em outro setor
    alocacoes = {x.CHAPA: x for x in [
        a("C", "C"), a("L", "C", "OBRAS"), a("D", "L"), a("A", "D"),
        a("B", "L", "EPI"), a("E", "B"), a("X", "L", setor="FROTA"),
    ]}
    assert indiretos.subsetor_efetivo(alocacoes, "A") == "OBRAS"
    assert indiretos.subsetor_efetivo(alocacoes, "E") == "EPI"
    assert indiretos.subsetor_efetivo(alocacoes, "C") == ""
    assert indiretos.subsetor_efetivo(alocacoes, "X") == ""  # chefe de outro setor


def test_subsetor_efetivo_herda_do_bloco_pendurado():
    def a(chapa, resp, sub=None, abaixo=None):
        return AlocacaoIndireto(CHAPA=chapa, SETOR="ALMOX", BASE="BCB", RESPONSAVEL_CHAPA=resp,
                                SUBSETOR=sub, ABAIXO_DE_FUNCAO=abaixo)
    # R (sem subsetor) chefia o bloco ALMOXARIFE de MEDIDORES; Ana fica abaixo
    # dele e Bia responde a Ana; Caio está abaixo de um bloco sem subsetor
    alocacoes = {x.CHAPA: x for x in [
        a("R", "R"), a("F", "R", "MEDIDORES"), a("A", "R", abaixo="ALMOXARIFE|MEDIDORES"),
        a("B", "A"), a("C", "R", abaixo="ALMOXARIFE"),
    ]}
    assert indiretos.subsetor_efetivo(alocacoes, "A") == "MEDIDORES"
    assert indiretos.subsetor_efetivo(alocacoes, "B") == "MEDIDORES"
    assert indiretos.subsetor_efetivo(alocacoes, "C") == ""


def test_plano_bases_gerencia_nao_move_ninguem():
    def a(chapa, resp, base="BCB", bases=None):
        return AlocacaoIndireto(CHAPA=chapa, SETOR=indiretos.SETOR_GERENCIA, BASE=base,
                                RESPONSAVEL_CHAPA=resp, BASES_RESPONSAVEL=bases)
    # G (geral) <- A e B, todos na mesma base "física"
    alocacoes = {x.CHAPA: x for x in [a("G", "G"), a("A", "G"), a("B", "G", bases="ITM")]}
    resp, bases = indiretos.plano_bases_responsavel(alocacoes, "A", ["BCB", "ITM"])
    assert resp == {}
    assert bases == {"A": ["BCB", "ITM"], "B": []}  # a base sai de quem cuidava dela
    resp, bases = indiretos.plano_bases_responsavel(alocacoes, "B", [])
    assert resp == {}
    assert bases == {"B": []}


def test_gerente_sem_base_e_responsavel_fica_acima_de_todos(sessao, monkeypatch):
    from flask import Flask

    import auth
    sessao.add(Colaborador(CHAPA="G", NOME="GERENTE", FUNÇÃO="GERENTE", TIPO_FUNÇÃO="INDIRETO"))
    sessao.commit()
    monkeypatch.setattr(indiretos, "SessionLocal", lambda: sessao)
    monkeypatch.setattr(sessao, "close", lambda: None)
    monkeypatch.setattr(auth, "usuario_logado", lambda: {"ignora_vinculos": True, "nome": "T"})
    monkeypatch.setattr(indiretos, "quem_esta_logado", lambda: "T")
    app = Flask(__name__)
    app.register_blueprint(indiretos.bp)
    cliente = app.test_client()

    corpo = {"chapa": "G", "setor": "gerência"}
    assert cliente.post("/api/indiretos/alocar", json=corpo).status_code == 200
    alocacao = sessao.query(AlocacaoIndireto).filter_by(CHAPA="G").one()
    assert (alocacao.BASE, alocacao.RESPONSAVEL_CHAPA) == (indiretos.BASE_GERENCIA, "G")
    # em outro setor, base e responsável continuam obrigatórios
    corpo = {"chapa": "G", "setor": "ALMOX"}
    assert cliente.post("/api/indiretos/alocar", json=corpo).status_code == 400


def test_setor_inteiro_ligado_ao_gerente(sessao, monkeypatch):
    from flask import Flask

    import auth
    from database.models import SetorGerencia
    sessao.add(AlocacaoIndireto(CHAPA="900", SETOR=indiretos.SETOR_GERENCIA, BASE="GERAL",
                                RESPONSAVEL_CHAPA="900"))
    sessao.add(AlocacaoIndireto(CHAPA="100", SETOR="FROTA", BASE="BCB", RESPONSAVEL_CHAPA="100"))
    sessao.commit()
    monkeypatch.setattr(indiretos, "SessionLocal", lambda: sessao)
    monkeypatch.setattr(sessao, "close", lambda: None)
    monkeypatch.setattr(auth, "usuario_logado", lambda: {"ignora_vinculos": True, "nome": "T"})
    monkeypatch.setattr(indiretos, "quem_esta_logado", lambda: "T")
    app = Flask(__name__)
    app.register_blueprint(indiretos.bp)
    cliente = app.test_client()
    url = "/api/indiretos/setor-gerente"

    assert cliente.post(url, json={"setor": "frota", "gerente_chapa": "900", "apoio": True}).status_code == 200
    ligacao = sessao.get(SetorGerencia, ("FROTA", ""))
    assert (ligacao.GERENTE_CHAPA, ligacao.APOIO) == ("900", True)
    # arrastar de novo troca a posição, sem criar outra linha
    assert cliente.post(url, json={"setor": "FROTA", "gerente_chapa": "900"}).status_code == 200
    assert sessao.query(SetorGerencia).count() == 1
    assert sessao.get(SetorGerencia, ("FROTA", "")).APOIO is False
    # só o nome de um responsável: outra linha, ao lado da do setor todo
    corpo = {"setor": "FROTA", "responsaveis": ["101"], "gerente_chapa": "900"}
    assert cliente.post(url, json=corpo).status_code == 200
    assert sessao.get(SetorGerencia, ("FROTA", "101")).GERENTE_CHAPA == "900"
    assert sessao.query(SetorGerencia).count() == 2
    # desfazer o nome não mexe no setor todo
    corpo = {"setor": "FROTA", "responsaveis": ["101"], "gerente_chapa": ""}
    assert cliente.post(url, json=corpo).status_code == 200
    assert sessao.query(SetorGerencia).count() == 1
    # só quem está na Gerência recebe setor
    assert cliente.post(url, json={"setor": "FROTA", "gerente_chapa": "100"}).status_code == 404
    # sem gerente: desfaz
    assert cliente.post(url, json={"setor": "FROTA", "gerente_chapa": ""}).status_code == 200
    assert sessao.query(SetorGerencia).count() == 0
