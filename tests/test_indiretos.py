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


# ---------- vagas (BID)

def cliente_da_api(sessao, monkeypatch):
    from flask import Flask

    import auth
    monkeypatch.setattr(indiretos, "SessionLocal", lambda: sessao)
    monkeypatch.setattr(sessao, "close", lambda: None)
    monkeypatch.setattr(auth, "usuario_logado", lambda: {"ignora_vinculos": True, "nome": "T"})
    monkeypatch.setattr(indiretos, "quem_esta_logado", lambda: "T")
    app = Flask(__name__)
    app.register_blueprint(indiretos.bp)
    return app.test_client()


def planilha_vagas(linhas):
    """Planilha única com a coluna do BID. Cada linha: SETOR, FUNÇÃO (BID) e
    CHAPA OCUPANTE (quem ocupa vai com base e responsável preenchidos)."""
    tabela = []
    for linha in linhas:
        chapa = linha.get("CHAPA OCUPANTE")
        tabela.append({
            "SETOR": linha["SETOR"], "FUNÇÃO (BID)": linha.get("FUNÇÃO (BID)"), "CHAPA INDIRETO": chapa,
            "BASE": linha.get("BASE", "BCB" if chapa else None),
            "CHAPA RESPONSÁVEL": 900 if chapa else None,
        })
    arquivo = io.BytesIO()
    with pd.ExcelWriter(arquivo, engine="openpyxl") as writer:
        colunas = ["SETOR", "FUNÇÃO (BID)", "CHAPA INDIRETO", "BASE", "CHAPA RESPONSÁVEL"]
        pd.DataFrame(tabela, columns=colunas).to_excel(writer, index=False, sheet_name="Alocação")
    arquivo.seek(0)
    return arquivo


def baixar_planilha(cliente):
    dados = cliente.get("/api/indiretos/planilha").data
    tabela = pd.read_excel(io.BytesIO(dados), sheet_name="Alocação", dtype=str).dropna(subset=["SETOR"])
    return tabela.fillna("")


def vagas_de(sessao, setor):
    from database.models import VagaIndireto
    ocupantes = {a.VAGA_ID: a.CHAPA for a in sessao.query(AlocacaoIndireto).all() if a.VAGA_ID}
    return sorted(
        (v.FUNCAO, ocupantes.get(v.id, ""))
        for v in sessao.query(VagaIndireto).filter_by(SETOR=setor).all()
    )


def test_definir_varias_funcoes_de_uma_vez(sessao, monkeypatch):
    from database.models import VagaIndireto
    cliente = cliente_da_api(sessao, monkeypatch)
    sessao.add(AlocacaoIndireto(CHAPA="100", SETOR="GOMAN", BASE="BCB", RESPONSAVEL_CHAPA="900"))
    sessao.commit()
    url = "/api/indiretos/vagas/definir"
    corpo = {"setor": "goman", "linhas": [
        {"atual": "", "funcao": "supervisor operacional", "quantidade": 3},
        {"atual": "", "funcao": "Tec. de Planejamento", "quantidade": 2},
    ]}
    assert cliente.post(url, json=corpo).status_code == 200
    assert vagas_de(sessao, "GOMAN") == [("SUPERVISOR OPERACIONAL", "")] * 3 + [("TEC. DE PLANEJAMENTO", "")] * 2

    vaga = sessao.query(VagaIndireto).filter_by(FUNCAO="SUPERVISOR OPERACIONAL").first()
    assert cliente.post("/api/indiretos/vagas/ocupar", json={"vaga_id": vaga.id, "chapa": "100"}).status_code == 200
    # trocar o nome do cargo mantém quem ocupa; diminuir apaga só as vazias
    corpo = {"setor": "GOMAN", "linhas": [
        {"atual": "SUPERVISOR OPERACIONAL", "funcao": "SUP OPERACIONAL", "quantidade": 1},
        {"atual": "TEC. DE PLANEJAMENTO", "funcao": "TEC. DE PLANEJAMENTO", "quantidade": 0},
    ]}
    assert cliente.post(url, json=corpo).status_code == 200
    assert vagas_de(sessao, "GOMAN") == [("SUP OPERACIONAL", "100")]


@pytest.mark.parametrize("linhas", [
    # abaixo das ocupadas: nada muda, nem a linha que estava certa
    [{"atual": "SUP", "funcao": "SUP", "quantidade": 0}, {"atual": "", "funcao": "NOVA", "quantidade": 2}],
    # mesmo cargo em duas linhas
    [{"atual": "", "funcao": "X", "quantidade": 1}, {"atual": "", "funcao": "x", "quantidade": 1}],
    # renomear para um cargo que já existe e continua
    [{"atual": "TEC", "funcao": "SUP", "quantidade": 1}, {"atual": "SUP", "funcao": "SUP", "quantidade": 1}],
    [{"atual": "", "funcao": "", "quantidade": 1}],
    [{"atual": "", "funcao": "X", "quantidade": -1}],
])
def test_definir_vagas_recusa_tudo_ou_nada(sessao, monkeypatch, linhas):
    from database.models import VagaIndireto
    cliente = cliente_da_api(sessao, monkeypatch)
    vaga = VagaIndireto(SETOR="GOMAN", FUNCAO="SUP")
    sessao.add_all([vaga, VagaIndireto(SETOR="GOMAN", FUNCAO="TEC"),
                    AlocacaoIndireto(CHAPA="100", SETOR="GOMAN", BASE="BCB", RESPONSAVEL_CHAPA="900")])
    sessao.flush()
    sessao.query(AlocacaoIndireto).filter_by(CHAPA="100").one().VAGA_ID = vaga.id
    sessao.commit()
    antes = vagas_de(sessao, "GOMAN")
    resposta = cliente.post("/api/indiretos/vagas/definir", json={"setor": "GOMAN", "linhas": linhas})
    assert resposta.status_code == 400
    assert vagas_de(sessao, "GOMAN") == antes


def test_definir_vagas_troca_dois_nomes_entre_si(sessao, monkeypatch):
    from database.models import VagaIndireto
    cliente = cliente_da_api(sessao, monkeypatch)
    sessao.add_all([VagaIndireto(SETOR="GOMAN", FUNCAO="A"), VagaIndireto(SETOR="GOMAN", FUNCAO="B"),
                    VagaIndireto(SETOR="GOMAN", FUNCAO="B")])
    sessao.commit()
    corpo = {"setor": "GOMAN", "linhas": [
        {"atual": "A", "funcao": "B", "quantidade": 1},
        {"atual": "B", "funcao": "A", "quantidade": 2},
    ]}
    assert cliente.post("/api/indiretos/vagas/definir", json=corpo).status_code == 200
    assert vagas_de(sessao, "GOMAN") == [("A", ""), ("A", ""), ("B", "")]


def test_ocupar_vaga_so_quem_esta_no_setor_e_troca_o_ocupante(sessao, monkeypatch):
    from database.models import VagaIndireto
    cliente = cliente_da_api(sessao, monkeypatch)
    vaga = VagaIndireto(SETOR="GOMAN", FUNCAO="TEC")
    sessao.add_all([
        vaga,
        AlocacaoIndireto(CHAPA="100", SETOR="GOMAN", BASE="BCB", RESPONSAVEL_CHAPA="900"),
        AlocacaoIndireto(CHAPA="101", SETOR="FROTA", BASE="BCB", RESPONSAVEL_CHAPA="900"),
    ])
    sessao.commit()
    url = "/api/indiretos/vagas/ocupar"
    assert cliente.post(url, json={"vaga_id": vaga.id, "chapa": "101"}).status_code == 400
    assert cliente.post(url, json={"vaga_id": vaga.id, "chapa": "100"}).status_code == 200
    # mudar de setor pela tela deixa a vaga vazia (era do setor anterior)
    corpo = {"chapa": "100", "setor": "FROTA", "base": "BCB", "responsavel_chapa": "900"}
    assert cliente.post("/api/indiretos/alocar", json=corpo).status_code == 200
    assert sessao.query(AlocacaoIndireto).filter_by(CHAPA="100").one().VAGA_ID is None
    # escolher vaga de outro setor ou já ocupada: recusa
    corpo = {"chapa": "101", "setor": "FROTA", "base": "BCB", "responsavel_chapa": "900", "vaga_id": vaga.id}
    assert cliente.post("/api/indiretos/alocar", json=corpo).status_code == 400
    corpo = {"chapa": "101", "setor": "GOMAN", "base": "BCB", "responsavel_chapa": "900", "vaga_id": vaga.id}
    assert cliente.post("/api/indiretos/alocar", json=corpo).status_code == 200
    assert vagas_de(sessao, "GOMAN") == [("TEC", "101")]


def test_planilha_com_bid_substitui_o_setor_e_reaproveita_as_vagas(sessao, monkeypatch):
    from database.models import VagaIndireto
    cliente = cliente_da_api(sessao, monkeypatch)
    antiga = VagaIndireto(SETOR="GOMAN", FUNCAO="TEC")
    outra = VagaIndireto(SETOR="FROTA", FUNCAO="ANALISTA")
    sessao.add_all([
        antiga, outra,
        AlocacaoIndireto(CHAPA="100", SETOR="GOMAN", BASE="BCB", RESPONSAVEL_CHAPA="900"),
        AlocacaoIndireto(CHAPA="101", SETOR="GOMAN", BASE="BCB", RESPONSAVEL_CHAPA="900"),
    ])
    sessao.flush()
    sessao.query(AlocacaoIndireto).filter_by(CHAPA="100").one().VAGA_ID = antiga.id
    sessao.commit()
    id_antiga = antiga.id

    # o 101 não está na planilha: continua no setor, como extra
    linhas = [
        {"SETOR": "goman", "FUNÇÃO (BID)": "tec", "CHAPA OCUPANTE": 100},
        {"SETOR": "GOMAN", "FUNÇÃO (BID)": "SUPERVISOR", "CHAPA OCUPANTE": None},
        {"SETOR": "GOMAN", "FUNÇÃO (BID)": "SUPERVISOR", "CHAPA OCUPANTE": None},
    ]
    previa = cliente.post("/api/indiretos/planilha/previa",
                          data={"arquivo": (planilha_vagas(linhas), "v.xlsx")})
    assert previa.status_code == 200
    resumo = previa.get_json()["vagas"][0]
    assert (resumo["depois"], resumo["criadas"], resumo["vazias"], resumo["extras"]) == (3, 2, 2, 1)
    # a prévia não grava
    assert vagas_de(sessao, "GOMAN") == [("TEC", "100")]

    aplicar = cliente.post("/api/indiretos/planilha/aplicar",
                           data={"arquivo": (planilha_vagas(linhas), "v.xlsx")})
    assert aplicar.status_code == 200
    assert vagas_de(sessao, "GOMAN") == [("SUPERVISOR", ""), ("SUPERVISOR", ""), ("TEC", "100")]
    # a pessoa continua na mesma vaga; setor fora da planilha fica como está
    assert sessao.query(AlocacaoIndireto).filter_by(CHAPA="100").one().VAGA_ID == id_antiga
    assert vagas_de(sessao, "FROTA") == [("ANALISTA", "")]


def test_planilha_aloca_e_poe_na_vaga_na_mesma_linha(sessao, monkeypatch):
    cliente = cliente_da_api(sessao, monkeypatch)
    sessao.add(AlocacaoIndireto(CHAPA="101", SETOR="FROTA", BASE="BCB", RESPONSAVEL_CHAPA="900"))
    sessao.commit()
    # 100 sem setor e 101 em outro setor: a linha aloca/move e já ocupa a vaga
    linhas = [
        {"SETOR": "GOMAN", "FUNÇÃO (BID)": "TEC", "CHAPA OCUPANTE": 100},
        {"SETOR": "GOMAN", "FUNÇÃO (BID)": "TEC", "CHAPA OCUPANTE": 101},
    ]
    resposta = cliente.post("/api/indiretos/planilha/aplicar",
                            data={"arquivo": (planilha_vagas(linhas), "v.xlsx")})
    assert resposta.status_code == 200
    assert (resposta.get_json()["alocados"], resposta.get_json()["movidos"]) == (1, 1)
    assert vagas_de(sessao, "GOMAN") == [("TEC", "100"), ("TEC", "101")]


@pytest.mark.parametrize("linha, trecho", [
    ({"SETOR": "GOMAN", "FUNÇÃO (BID)": "TEC", "CHAPA OCUPANTE": 999}, "não encontrada"),
    ({"SETOR": "GOMAN", "FUNÇÃO (BID)": "TEC", "CHAPA OCUPANTE": 200}, "não INDIRETO"),
    ({"SETOR": "", "FUNÇÃO (BID)": "TEC", "CHAPA OCUPANTE": None}, "SETOR"),
    ({"SETOR": "GOMAN", "FUNÇÃO (BID)": "TEC", "CHAPA OCUPANTE": None, "BASE": "BCB"}, "CHAPA INDIRETO"),
])
def test_planilha_com_bid_recusa_linhas_invalidas(sessao, linha, trecho):
    plano = indiretos.analisar_planilha_indiretos(planilha_vagas([linha]), sessao)
    assert trecho in plano["erros"][0]["erro"]


def test_planilha_com_bid_recusa_ocupante_repetido(sessao):
    linhas = [{"SETOR": "GOMAN", "FUNÇÃO (BID)": "TEC", "CHAPA OCUPANTE": 100}] * 2
    plano = indiretos.analisar_planilha_indiretos(planilha_vagas(linhas), sessao)
    assert "repetido" in plano["erros"][0]["erro"]


def test_planilha_sem_a_coluna_do_bid_nao_mexe_nas_vagas(sessao, monkeypatch):
    from database.models import VagaIndireto
    cliente = cliente_da_api(sessao, monkeypatch)
    sessao.add(VagaIndireto(SETOR="ALMOXARIFADO", FUNCAO="TEC"))
    sessao.commit()
    resposta = cliente.post("/api/indiretos/planilha/aplicar", data={"arquivo": (planilha([linha()]), "p.xlsx")})
    assert resposta.status_code == 200
    assert vagas_de(sessao, "ALMOXARIFADO") == [("TEC", "")]


def test_planilha_baixa_no_formato_do_bid(sessao, monkeypatch):
    cliente = cliente_da_api(sessao, monkeypatch)
    resposta = cliente.get("/api/indiretos/planilha")
    assert resposta.status_code == 200
    abas = pd.read_excel(io.BytesIO(resposta.data), sheet_name=None)
    assert list(abas["Alocação"].columns[:3]) == ["SETOR", "FUNÇÃO (BID)", "CHAPA INDIRETO"]


def test_planilha_traz_e_aceita_extras_com_bid_em_branco(sessao, monkeypatch):
    from database.models import VagaIndireto
    cliente = cliente_da_api(sessao, monkeypatch)
    vaga = VagaIndireto(SETOR="GOMAN", FUNCAO="TEC")
    sessao.add_all([
        vaga,
        AlocacaoIndireto(CHAPA="100", SETOR="GOMAN", BASE="BCB", RESPONSAVEL_CHAPA="900"),
        AlocacaoIndireto(CHAPA="101", SETOR="GOMAN", BASE="BCB", RESPONSAVEL_CHAPA="900"),
    ])
    sessao.flush()
    sessao.query(AlocacaoIndireto).filter_by(CHAPA="100").one().VAGA_ID = vaga.id
    sessao.commit()

    # baixada: a vaga e, no fim do setor, o extra com FUNÇÃO (BID) em branco
    baixada = baixar_planilha(cliente)
    assert baixada[["FUNÇÃO (BID)", "CHAPA INDIRETO"]].values.tolist() == [["TEC", "100"], ["", "101"]]
    # reenviar sem mexer: nada muda
    previa = cliente.post("/api/indiretos/planilha/previa",
                          data={"arquivo": (io.BytesIO(cliente.get("/api/indiretos/planilha").data), "p.xlsx")})
    corpo = previa.get_json()
    assert not corpo["erros"] and not corpo["vagas"] and not corpo["alocar"] + corpo["mover"] + corpo["atualizar"]

    # o ocupante passa a extra e o extra ganha a vaga: nada de vaga nova
    linhas = [
        {"SETOR": "GOMAN", "FUNÇÃO (BID)": "TEC", "CHAPA OCUPANTE": 101},
        {"SETOR": "GOMAN", "FUNÇÃO (BID)": None, "CHAPA OCUPANTE": 100},
    ]
    resposta = cliente.post("/api/indiretos/planilha/aplicar",
                            data={"arquivo": (planilha_vagas(linhas), "v.xlsx")})
    assert resposta.status_code == 200
    assert vagas_de(sessao, "GOMAN") == [("TEC", "101")]
    # extra levado para outro setor: muda de setor e a vaga do GOMAN fica vazia
    linhas = [{"SETOR": "FROTA", "FUNÇÃO (BID)": None, "CHAPA OCUPANTE": 101}]
    assert cliente.post("/api/indiretos/planilha/aplicar",
                        data={"arquivo": (planilha_vagas(linhas), "v.xlsx")}).status_code == 200
    assert vagas_de(sessao, "GOMAN") == [("TEC", "")]


def ordem_do_bid(sessao, setor):
    from database.models import VagaIndireto
    vagas = sessao.query(VagaIndireto).filter_by(SETOR=setor).order_by(VagaIndireto.ORDEM, VagaIndireto.id)
    return list(dict.fromkeys(v.FUNCAO for v in vagas))


def test_ordem_do_bid_segue_as_linhas_da_tela_e_da_planilha(sessao, monkeypatch):
    cliente = cliente_da_api(sessao, monkeypatch)
    url = "/api/indiretos/vagas/definir"
    corpo = {"setor": "GOMAN", "linhas": [
        {"atual": "", "funcao": "TEC", "quantidade": 2},
        {"atual": "", "funcao": "GERENTE", "quantidade": 1},
        {"atual": "", "funcao": "AUXILIAR", "quantidade": 1},
    ]}
    assert cliente.post(url, json=corpo).status_code == 200
    assert ordem_do_bid(sessao, "GOMAN") == ["TEC", "GERENTE", "AUXILIAR"]
    # arrastar: mesmas funções em outra ordem, sem mudar quantidade
    corpo = {"setor": "GOMAN", "linhas": [
        {"atual": "GERENTE", "funcao": "GERENTE", "quantidade": 1},
        {"atual": "AUXILIAR", "funcao": "AUXILIAR", "quantidade": 1},
        {"atual": "TEC", "funcao": "TEC", "quantidade": 2},
    ]}
    assert cliente.post(url, json=corpo).status_code == 200
    assert ordem_do_bid(sessao, "GOMAN") == ["GERENTE", "AUXILIAR", "TEC"]

    # planilha: só a ordem mudou e mesmo assim conta como mudança
    linhas = [{"SETOR": "GOMAN", "FUNÇÃO (BID)": f, "CHAPA OCUPANTE": None}
              for f in ("TEC", "AUXILIAR", "TEC", "GERENTE")]
    previa = cliente.post("/api/indiretos/planilha/previa",
                          data={"arquivo": (planilha_vagas(linhas), "v.xlsx")}).get_json()
    assert [s["setor"] for s in previa["vagas"]] == ["GOMAN"]
    assert cliente.post("/api/indiretos/planilha/aplicar",
                        data={"arquivo": (planilha_vagas(linhas), "v.xlsx")}).status_code == 200
    assert ordem_do_bid(sessao, "GOMAN") == ["TEC", "AUXILIAR", "GERENTE"]
    # a planilha baixada vem na ordem do BID
    assert list(baixar_planilha(cliente)["FUNÇÃO (BID)"]) == ["TEC", "TEC", "AUXILIAR", "GERENTE"]


def test_posicionar_vagas_no_organograma(sessao, monkeypatch):
    from database.models import VagaIndireto
    cliente = cliente_da_api(sessao, monkeypatch)
    a, b, c = VagaIndireto(SETOR="GOMAN", FUNCAO="TEC"), VagaIndireto(SETOR="GOMAN", FUNCAO="TEC"), VagaIndireto(SETOR="FROTA", FUNCAO="X")
    sessao.add_all([a, b, c])
    sessao.commit()
    url = "/api/indiretos/vagas/posicao"
    assert cliente.post(url, json={"vaga_ids": [a.id, b.id], "base": "bcb", "responsavel_chapa": "900"}).status_code == 200
    assert {(v.BASE, v.RESPONSAVEL_CHAPA) for v in (a, b)} == {("BCB", "900")}
    # só a base; depois de volta para a caixa
    assert cliente.post(url, json={"vaga_ids": [a.id], "base": "BDC"}).status_code == 200
    assert (a.BASE, a.RESPONSAVEL_CHAPA) == ("BDC", None)
    assert cliente.post(url, json={"vaga_ids": [a.id]}).status_code == 200
    assert (a.BASE, a.RESPONSAVEL_CHAPA) == (None, None)
    # base inventada, responsável fora do cadastro, setores misturados: recusa
    assert cliente.post(url, json={"vaga_ids": [a.id], "base": "XYZ"}).status_code == 400
    assert cliente.post(url, json={"vaga_ids": [a.id], "responsavel_chapa": "777"}).status_code == 404
    assert cliente.post(url, json={"vaga_ids": [a.id, c.id]}).status_code == 400
