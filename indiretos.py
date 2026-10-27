"""Alocação do pessoal INDIRETO (página "Indiretos").

Controle nominal, sem vagas: cada indireto fica num SETOR, numa BASE (que
quem aloca escolhe, independente do cadastro) e sob um RESPONSÁVEL — por
pessoa, então no mesmo setor e base pode haver mais de um. Tabela
alocacoes_indiretos (migrations/018), uma linha por indireto.

Rotas num Blueprint próprio para não engordar o app.py. Por enquanto só o
Administrador usa (auth.exige_administrador), enquanto a página está em
liberação gradual.

A planilha segue o padrão das outras (baixar -> preencher -> prévia ->
aplicar) e, como a de usuários, NUNCA tira ninguém: quem não aparece na
planilha continua onde está. Para tirar alguém do setor, use a tela.
"""

import io
import re
from datetime import datetime, timezone

import pandas as pd
from flask import Blueprint, jsonify, request, send_file
from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Font
from openpyxl.worksheet.datavalidation import DataValidation

import auth
import planilhas_estilo as estilo
from database.database import SessionLocal
from database.models import AlocacaoIndireto, Colaborador

bp = Blueprint("indiretos", __name__)

TIPO_INDIRETO = "INDIRETO"
BASES_PADRAO = ("BCB", "BDC", "ITM", "PDS", "PDT", "STI", "SPOT STI")

ABA_ALOCACAO = "Alocação"
COL_SETOR = "SETOR"
COL_BASE = "BASE"
COL_RESPONSAVEL = "CHAPA RESPONSÁVEL"
COL_INDIRETO = "CHAPA INDIRETO"
COL_OBSERVACAO = "OBSERVAÇÃO"
COLUNAS_OBRIGATORIAS = (COL_SETOR, COL_BASE, COL_RESPONSAVEL, COL_INDIRETO)
COLUNAS_PLANILHA = (
    COL_SETOR, COL_BASE, COL_RESPONSAVEL, "NOME RESPONSÁVEL",
    COL_INDIRETO, "NOME INDIRETO", "FUNÇÃO INDIRETO", COL_OBSERVACAO,
)
LINHAS_EXTRAS_PLANILHA = 600


# ============================================================
# NORMALIZAÇÃO
# ============================================================

def texto_padrao(valor):
    """Maiúsculas, sem espaço sobrando — setor e base são comparados assim
    (mesma ideia de funcao_da_vaga no app.py)."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return ""
    return " ".join(str(valor).split()).upper()


def chapa_da_celula(valor):
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return ""
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)
    chapa = str(valor).strip()
    if re.fullmatch(r"\d+\.0", chapa):
        chapa = chapa[:-2]
    return chapa


def texto_livre(valor):
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    texto = str(valor).strip()
    return texto or None


def base_do_cadastro(colaborador):
    # import tardio: app.py importa este módulo
    from app import base_da_secao
    return base_da_secao(colaborador.SEÇÃO)["codigo"] or ""


def quem_esta_logado():
    return (auth.usuario_logado() or {}).get("usuario")


# ============================================================
# LEITURA
# ============================================================

def descrever_pessoa(colaborador, alocacao):
    return {
        "chapa": colaborador.CHAPA,
        "nome": colaborador.NOME or "",
        "funcao": colaborador.FUNÇÃO or "",
        "base_cadastro": base_do_cadastro(colaborador),
        "afastado": bool(colaborador.AFASTADO),
        "alocacao": None if not alocacao else {
            "setor": alocacao.SETOR,
            "base": alocacao.BASE,
            "responsavel_chapa": alocacao.RESPONSAVEL_CHAPA,
            "observacao": alocacao.OBSERVACAO or "",
            "alocado_por": alocacao.ALOCADO_POR or "",
            "alocado_em": alocacao.ALOCADO_EM.isoformat() if alocacao.ALOCADO_EM else "",
        },
    }


@bp.route("/api/indiretos", methods=["GET"])
@auth.exige_administrador
def obter_indiretos():
    """Tudo que a página precisa: os indiretos (com a alocação de cada um),
    quem pode ser responsável (o cadastro inteiro, para pesquisar por nome ou
    chapa) e as bases."""
    session = SessionLocal()
    try:
        alocacoes = {a.CHAPA: a for a in session.query(AlocacaoIndireto).all()}
        colaboradores = session.query(Colaborador).order_by(Colaborador.NOME).all()

        pessoas = [
            descrever_pessoa(c, alocacoes.get(c.CHAPA))
            for c in colaboradores
            if (c.TIPO_FUNÇÃO or "").upper() == TIPO_INDIRETO
        ]
        responsaveis = [
            {"chapa": c.CHAPA, "nome": c.NOME or "", "funcao": c.FUNÇÃO or ""}
            for c in colaboradores
        ]
        bases = list(BASES_PADRAO) + sorted(
            {a.BASE for a in alocacoes.values()} - set(BASES_PADRAO)
        )
        return jsonify({"pessoas": pessoas, "responsaveis": responsaveis, "bases": bases})
    except Exception as erro:
        print(f"[ERRO] obter_indiretos: {erro}")
        return jsonify({"erro": "Não foi possível carregar os indiretos."}), 500
    finally:
        session.close()


# ============================================================
# AÇÕES DA TELA
# ============================================================

def _corpo():
    dados = request.get_json(silent=True)
    return dados if isinstance(dados, dict) else {}


def _colaborador(session, chapa):
    return session.query(Colaborador).filter(Colaborador.CHAPA == chapa).first()


@bp.route("/api/indiretos/alocar", methods=["POST"])
@auth.exige_administrador
def alocar_indireto():
    """Aloca ou move: grava setor, base e responsável do indireto."""
    dados = _corpo()
    chapa = chapa_da_celula(dados.get("chapa"))
    setor = texto_padrao(dados.get("setor"))
    base = texto_padrao(dados.get("base"))
    responsavel = chapa_da_celula(dados.get("responsavel_chapa"))
    observacao = texto_livre(dados.get("observacao"))

    if not (chapa and setor and base and responsavel):
        return jsonify({"erro": "Informe indireto, setor, base e responsável."}), 400

    session = SessionLocal()
    try:
        pessoa = _colaborador(session, chapa)
        if not pessoa or (pessoa.TIPO_FUNÇÃO or "").upper() != TIPO_INDIRETO:
            return jsonify({"erro": "Indireto não encontrado no cadastro."}), 404
        if not _colaborador(session, responsavel):
            return jsonify({"erro": "Responsável não encontrado no cadastro."}), 404

        alocacao = session.query(AlocacaoIndireto).filter(AlocacaoIndireto.CHAPA == chapa).first()
        if not alocacao:
            alocacao = AlocacaoIndireto(CHAPA=chapa)
            session.add(alocacao)
        alocacao.SETOR = setor
        alocacao.BASE = base
        alocacao.RESPONSAVEL_CHAPA = responsavel
        if "observacao" in dados:
            alocacao.OBSERVACAO = observacao
        alocacao.ALOCADO_POR = quem_esta_logado()
        alocacao.ALOCADO_EM = datetime.now(timezone.utc)
        session.commit()
        return jsonify({"sucesso": True})
    except Exception as erro:
        session.rollback()
        print(f"[ERRO] alocar_indireto: {erro}")
        return jsonify({"erro": "Não foi possível alocar o indireto."}), 500
    finally:
        session.close()


@bp.route("/api/indiretos/responsavel", methods=["POST"])
@auth.exige_administrador
def trocar_responsavel_indiretos():
    """Troca o responsável de um ou mais indiretos de uma vez (o grupo de um
    responsável dentro de uma seção, por exemplo)."""
    dados = _corpo()
    chapas = [chapa_da_celula(c) for c in (dados.get("chapas") or []) if chapa_da_celula(c)]
    responsavel = chapa_da_celula(dados.get("responsavel_chapa"))
    if not chapas or not responsavel:
        return jsonify({"erro": "Informe as pessoas e o novo responsável."}), 400

    session = SessionLocal()
    try:
        if not _colaborador(session, responsavel):
            return jsonify({"erro": "Responsável não encontrado no cadastro."}), 404
        alteradas = (
            session.query(AlocacaoIndireto)
            .filter(AlocacaoIndireto.CHAPA.in_(chapas))
            .update(
                {
                    AlocacaoIndireto.RESPONSAVEL_CHAPA: responsavel,
                    AlocacaoIndireto.ALOCADO_POR: quem_esta_logado(),
                    AlocacaoIndireto.ALOCADO_EM: datetime.now(timezone.utc),
                },
                synchronize_session=False,
            )
        )
        session.commit()
        return jsonify({"sucesso": True, "alteradas": alteradas})
    except Exception as erro:
        session.rollback()
        print(f"[ERRO] trocar_responsavel_indiretos: {erro}")
        return jsonify({"erro": "Não foi possível trocar o responsável."}), 500
    finally:
        session.close()


@bp.route("/api/indiretos/alocacao/<chapa>", methods=["DELETE"])
@auth.exige_administrador
def remover_alocacao_indireto(chapa):
    session = SessionLocal()
    try:
        removidas = (
            session.query(AlocacaoIndireto)
            .filter(AlocacaoIndireto.CHAPA == chapa_da_celula(chapa))
            .delete(synchronize_session=False)
        )
        session.commit()
        if not removidas:
            return jsonify({"erro": "Este indireto não está alocado."}), 404
        return jsonify({"sucesso": True})
    except Exception as erro:
        session.rollback()
        print(f"[ERRO] remover_alocacao_indireto: {erro}")
        return jsonify({"erro": "Não foi possível tirar do setor."}), 500
    finally:
        session.close()


# ============================================================
# PLANILHA: GERAR
# ============================================================

def montar_planilha_indiretos(session):
    """Planilha de cadastro já com as alocações de hoje, mais as abas de apoio
    (Indiretos, com quem falta; Colaboradores, para achar o responsável;
    Bases). As colunas de nome são fórmulas só para conferência: a análise
    lê apenas SETOR, BASE, as duas chapas e a observação."""
    colaboradores = session.query(Colaborador).order_by(Colaborador.NOME).all()
    alocacoes = (
        session.query(AlocacaoIndireto)
        .order_by(AlocacaoIndireto.SETOR, AlocacaoIndireto.BASE, AlocacaoIndireto.CHAPA)
        .all()
    )
    indiretos = [c for c in colaboradores if (c.TIPO_FUNÇÃO or "").upper() == TIPO_INDIRETO]
    bases = list(BASES_PADRAO) + sorted({a.BASE for a in alocacoes} - set(BASES_PADRAO))

    livro = Workbook()
    aba = livro.active
    aba.title = ABA_ALOCACAO
    for i, titulo in enumerate(COLUNAS_PLANILHA, start=1):
        aba.cell(row=1, column=i, value=titulo)

    preencher = {1, 2, 3, 5, 8}
    ultima = len(alocacoes) + LINHAS_EXTRAS_PLANILHA + 1

    def busca(celula, coluna):
        return (
            f'=IF({celula}="","",IFERROR(INDEX(Colaboradores!${coluna}:${coluna},'
            f'MATCH({celula}&"",Colaboradores!$A:$A,0)),"CHAPA NÃO ENCONTRADA"))'
        )

    for n, alocacao in enumerate(alocacoes, start=2):
        aba.cell(row=n, column=1, value=alocacao.SETOR)
        aba.cell(row=n, column=2, value=alocacao.BASE)
        aba.cell(row=n, column=3, value=alocacao.RESPONSAVEL_CHAPA or "")
        aba.cell(row=n, column=5, value=alocacao.CHAPA)
        aba.cell(row=n, column=8, value=alocacao.OBSERVACAO or "")

    for n in range(2, ultima + 1):
        for c in range(1, len(COLUNAS_PLANILHA) + 1):
            celula = aba.cell(row=n, column=c)
            celula.border = estilo.BORDA
            celula.font = Font(name=estilo.FONTE, size=10, color="0000FF" if c in preencher else "000000")
            celula.fill = estilo.FUNDO_PREENCHER if c in preencher else estilo.FUNDO_CONSULTA
        aba.cell(row=n, column=3).number_format = "@"
        aba.cell(row=n, column=5).number_format = "@"
        aba.cell(row=n, column=4, value=busca(f"C{n}", "B"))
        aba.cell(row=n, column=6, value=busca(f"E{n}", "B"))
        aba.cell(row=n, column=7, value=busca(f"E{n}", "C"))

    for c, (titulo, largura) in enumerate(zip(COLUNAS_PLANILHA, (26, 12, 18, 34, 16, 34, 30, 30)), start=1):
        celula = aba.cell(row=1, column=c)
        celula.font, celula.fill, celula.border = estilo.FONTE_CABECALHO, estilo.FUNDO_CABECALHO, estilo.BORDA
        celula.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        celula.comment = Comment(
            "Preencha esta coluna." if c in preencher
            else "Automático: confere a chapa no cadastro. Não digite aqui.",
            "Gerenciador de Equipes",
        )
        aba.column_dimensions[celula.column_letter].width = largura
    aba.row_dimensions[1].height = 30
    aba.freeze_panes = "A2"
    aba.auto_filter.ref = f"A1:H{ultima}"
    aba.sheet_properties.tabColor = estilo.BORDO

    lista_bases = DataValidation(
        type="list", formula1=f"=Bases!$A$2:$A${len(bases) + 1}", allow_blank=True,
        errorStyle="warning", errorTitle="Base fora da lista",
        error="Essa sigla não está na lista de bases. Confirme se está certa.",
    )
    aba.add_data_validation(lista_bases)
    lista_bases.add(f"B2:B{ultima}")

    vermelho = estilo.fundo_condicional("FBE9E7")
    fonte_vermelha = Font(name=estilo.FONTE, size=10, bold=True, color="B3261E")
    for faixa, ref in ((f"D2:D{ultima}", "D2"), (f"F2:G{ultima}", "F2")):
        aba.conditional_formatting.add(
            faixa, FormulaRule(formula=[f'{ref}="CHAPA NÃO ENCONTRADA"'], fill=vermelho, font=fonte_vermelha)
        )
    aba.conditional_formatting.add(
        f"E2:E{ultima}",
        FormulaRule(
            formula=[f'AND(E2<>"",COUNTIF($E$2:$E${ultima},E2)>1)'],
            fill=estilo.fundo_condicional("FDF0CD"), font=estilo.FONTE_ALERTA,
        ),
    )

    # ---------- Indiretos (com quem já está na planilha)
    aba_ind = livro.create_sheet("Indiretos")
    cab = ["CHAPA", "NOME", "FUNÇÃO", "BASE (CADASTRO)", "SITUAÇÃO", "JÁ NA PLANILHA?"]
    for i, t in enumerate(cab, start=1):
        aba_ind.cell(row=1, column=i, value=t)
    for n, c in enumerate(indiretos, start=2):
        valores = [c.CHAPA, c.NOME or "", c.FUNÇÃO or "", base_do_cadastro(c), c.SITUAÇÃO or ""]
        for i, v in enumerate(valores, start=1):
            aba_ind.cell(row=n, column=i, value=v)
        aba_ind.cell(row=n, column=6, value=f'=IF(COUNTIF({ABA_ALOCACAO}!$E$2:$E${ultima},A{n}&"")>0,"SIM","FALTA")')
    estilo.estilizar_aba(aba_ind, consulta=True)
    fim = len(indiretos) + 1
    aba_ind.conditional_formatting.add(f"F2:F{fim}", FormulaRule(
        formula=['F2="FALTA"'], fill=estilo.fundo_condicional("FDF0CD"), font=estilo.FONTE_ALERTA))
    aba_ind.conditional_formatting.add(f"F2:F{fim}", FormulaRule(
        formula=['F2="SIM"'], fill=estilo.fundo_condicional("E6F2EA"),
        font=Font(name=estilo.FONTE, size=10, bold=True, color="1B6B45")))
    aba_ind["H1"], aba_ind["H2"], aba_ind["H3"] = "Indiretos no cadastro", "Já na planilha", "Faltam"
    aba_ind["I1"] = f"=COUNTA(A2:A{fim})"
    aba_ind["I2"] = f'=COUNTIF(F2:F{fim},"SIM")'
    aba_ind["I3"] = "=I1-I2"
    for ref in ("H1", "H2", "H3"):
        aba_ind[ref].font = Font(name=estilo.FONTE, size=10, bold=True, color=estilo.BORDO)
    for ref in ("I1", "I2", "I3"):
        aba_ind[ref].font = Font(name=estilo.FONTE, size=10, bold=True)
    aba_ind.column_dimensions["H"].width = 22

    # ---------- Colaboradores (para achar o responsável) e Bases
    aba_col = livro.create_sheet("Colaboradores")
    for i, t in enumerate(["CHAPA", "NOME", "FUNÇÃO", "TIPO", "BASE (CADASTRO)", "SITUAÇÃO"], start=1):
        aba_col.cell(row=1, column=i, value=t)
    for n, c in enumerate(colaboradores, start=2):
        for i, v in enumerate([c.CHAPA, c.NOME or "", c.FUNÇÃO or "", c.TIPO_FUNÇÃO or "",
                               base_do_cadastro(c), c.SITUAÇÃO or ""], start=1):
            aba_col.cell(row=n, column=i, value=v)
    estilo.estilizar_aba(aba_col, consulta=True)

    aba_bases = livro.create_sheet("Bases")
    aba_bases.cell(row=1, column=1, value="BASE")
    for n, b in enumerate(bases, start=2):
        aba_bases.cell(row=n, column=1, value=b)
    estilo.estilizar_aba(aba_bases, consulta=True)

    estilo.adicionar_instrucoes(
        livro,
        "Planilha de alocação de indiretos",
        [
            ("Para que serve", "Informar em qual SETOR e BASE cada indireto trabalha e quem é o RESPONSÁVEL dele. Uma linha por indireto. O arquivo já vem com as alocações de hoje."),
            ("Onde preencher", "Aba ALOCAÇÃO, nas colunas amarelas: SETOR, BASE, CHAPA RESPONSÁVEL, CHAPA INDIRETO e OBSERVAÇÃO (opcional)."),
            ("Colunas automáticas", "NOME RESPONSÁVEL, NOME INDIRETO e FUNÇÃO INDIRETO (cinza) se preenchem pela chapa, só para conferir. \"CHAPA NÃO ENCONTRADA\" em vermelho = chapa errada ou fora do cadastro."),
            ("SETOR", "Escreva sempre do mesmo jeito (o sistema guarda em maiúsculas). O mesmo setor em várias bases aparece na tela num cartão só, com uma seção por base."),
            ("BASE", "Escolha na lista. Você decide a base, independente da seção do cadastro da pessoa."),
            ("RESPONSÁVEL", "Chapa de quem responde pelo indireto. É por pessoa: no mesmo setor e base pode haver responsáveis diferentes. Pode ser qualquer colaborador (aba COLABORADORES)."),
            ("CHAPA INDIRETO", "Cada indireto uma vez só (repetido fica laranja). A aba INDIRETOS mostra quem ainda falta."),
            ("Nunca tira ninguém", "Quem não estiver na planilha continua onde está. Para tirar alguém do setor, use o menu da pessoa na tela Indiretos."),
            ("Antes de aplicar", "Envie o arquivo em Indiretos > Planilha de cadastro: o sistema mostra uma prévia do que muda e só grava quando você confirmar."),
        ],
    )
    livro.active = 0
    return livro


@bp.route("/api/indiretos/planilha", methods=["GET"])
@auth.exige_administrador
def baixar_planilha_indiretos():
    session = SessionLocal()
    try:
        livro = montar_planilha_indiretos(session)
        buffer = io.BytesIO()
        livro.save(buffer)
        buffer.seek(0)
        return send_file(
            buffer,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name="alocacao-indiretos.xlsx",
        )
    except Exception as erro:
        print(f"[ERRO] baixar_planilha_indiretos: {erro}")
        return jsonify({"erro": "Não foi possível gerar a planilha."}), 500
    finally:
        session.close()


# ============================================================
# PLANILHA: ANALISAR / APLICAR
# ============================================================

def _ler_aba(arquivo):
    """Aba "Alocação" pelo nome (o modelo antigo tinha Instruções primeiro);
    se não houver, a primeira aba que tenha as colunas."""
    try:
        abas = pd.read_excel(arquivo, sheet_name=None, dtype=object)
    except Exception as erro:
        raise ValueError(f"Não foi possível ler a planilha: {erro}")
    df = abas.get(ABA_ALOCACAO)
    if df is None:
        df = next(
            (d for d in abas.values() if set(COLUNAS_OBRIGATORIAS) <= {str(c).strip() for c in d.columns}),
            None,
        )
    if df is None:
        raise ValueError(f"A planilha precisa da aba \"{ABA_ALOCACAO}\" com as colunas {', '.join(COLUNAS_OBRIGATORIAS)}.")
    df.columns = [str(c).strip() for c in df.columns]
    faltando = [c for c in COLUNAS_OBRIGATORIAS if c not in df.columns]
    if faltando:
        raise ValueError(f"A planilha precisa das colunas {', '.join(faltando)}.")
    return df


def analisar_planilha_indiretos(arquivo, session):
    """Monta o plano sem gravar nada: alocar (novos), mover (setor ou base
    mudou), atualizar (só responsável/observação mudou), sem mudança e erros."""
    df = _ler_aba(arquivo)
    colaboradores = {c.CHAPA: c for c in session.query(Colaborador).all()}
    atuais = {a.CHAPA: a for a in session.query(AlocacaoIndireto).all()}

    plano = {"alocar": [], "mover": [], "atualizar": [], "sem_mudanca": 0, "erros": []}
    vistos = {}

    for indice, linha in df.iterrows():
        numero = int(indice) + 2
        setor = texto_padrao(linha.get(COL_SETOR))
        base = texto_padrao(linha.get(COL_BASE))
        responsavel = chapa_da_celula(linha.get(COL_RESPONSAVEL))
        chapa = chapa_da_celula(linha.get(COL_INDIRETO))
        observacao = texto_livre(linha.get(COL_OBSERVACAO)) if COL_OBSERVACAO in df.columns else None

        if not (setor or base or responsavel or chapa):
            continue  # linha preparada e não usada

        def erro(mensagem):
            plano["erros"].append({"linha": numero, "chapa": chapa or "—", "erro": mensagem})

        faltam = [n for n, v in (("SETOR", setor), ("BASE", base),
                                 ("CHAPA RESPONSÁVEL", responsavel), ("CHAPA INDIRETO", chapa)) if not v]
        if faltam:
            erro(f"Falta preencher: {', '.join(faltam)}.")
            continue
        pessoa = colaboradores.get(chapa)
        if not pessoa:
            erro("CHAPA INDIRETO não encontrada no cadastro.")
            continue
        if (pessoa.TIPO_FUNÇÃO or "").upper() != TIPO_INDIRETO:
            erro(f"{pessoa.NOME} está como {pessoa.TIPO_FUNÇÃO or 'sem tipo'} no cadastro, não INDIRETO.")
            continue
        chefe = colaboradores.get(responsavel)
        if not chefe:
            erro("CHAPA RESPONSÁVEL não encontrada no cadastro.")
            continue
        if chapa in vistos:
            erro(f"Indireto repetido: já aparece na linha {vistos[chapa]}.")
            continue
        vistos[chapa] = numero

        item = {
            "linha": numero, "chapa": chapa, "nome": pessoa.NOME,
            "setor": setor, "base": base,
            "responsavel_chapa": responsavel, "responsavel_nome": chefe.NOME,
            "observacao": observacao,
        }
        atual = atuais.get(chapa)
        if not atual:
            plano["alocar"].append(item)
        elif (atual.SETOR, atual.BASE) != (setor, base):
            item["de"] = f"{atual.SETOR} · {atual.BASE}"
            plano["mover"].append(item)
        elif atual.RESPONSAVEL_CHAPA != responsavel or (atual.OBSERVACAO or None) != observacao:
            mudou = []
            if atual.RESPONSAVEL_CHAPA != responsavel:
                antigo = colaboradores.get(atual.RESPONSAVEL_CHAPA)
                mudou.append(f"responsável: {antigo.NOME if antigo else atual.RESPONSAVEL_CHAPA or '—'} → {chefe.NOME}")
            if (atual.OBSERVACAO or None) != observacao:
                mudou.append("observação")
            item["mudancas"] = mudou
            plano["atualizar"].append(item)
        else:
            plano["sem_mudanca"] += 1

    return plano


def _arquivo_enviado():
    arquivo = request.files.get("arquivo")
    if not arquivo:
        raise ValueError("Arquivo não enviado.")
    return arquivo


@bp.route("/api/indiretos/planilha/previa", methods=["POST"])
@auth.exige_administrador
def prever_planilha_indiretos():
    session = SessionLocal()
    try:
        return jsonify(analisar_planilha_indiretos(_arquivo_enviado(), session))
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    except Exception as erro:
        print(f"[ERRO] prever_planilha_indiretos: {erro}")
        return jsonify({"erro": "Não foi possível analisar a planilha."}), 500
    finally:
        session.close()


@bp.route("/api/indiretos/planilha/aplicar", methods=["POST"])
@auth.exige_administrador
def aplicar_planilha_indiretos():
    """Reanalisa (o banco pode ter mudado desde a prévia) e grava. Com
    qualquer erro na planilha, não grava nada."""
    session = SessionLocal()
    try:
        plano = analisar_planilha_indiretos(_arquivo_enviado(), session)
        if plano["erros"]:
            return jsonify({"erro": "Corrija os erros da planilha antes de aplicar.", **plano}), 400

        agora = datetime.now(timezone.utc)
        quem = quem_esta_logado()
        atuais = {a.CHAPA: a for a in session.query(AlocacaoIndireto).all()}
        for item in plano["alocar"] + plano["mover"] + plano["atualizar"]:
            alocacao = atuais.get(item["chapa"])
            if not alocacao:
                alocacao = AlocacaoIndireto(CHAPA=item["chapa"])
                session.add(alocacao)
            alocacao.SETOR = item["setor"]
            alocacao.BASE = item["base"]
            alocacao.RESPONSAVEL_CHAPA = item["responsavel_chapa"]
            alocacao.OBSERVACAO = item["observacao"]
            alocacao.ALOCADO_POR = quem
            alocacao.ALOCADO_EM = agora
        session.commit()
        return jsonify({
            "sucesso": True,
            "alocados": len(plano["alocar"]),
            "movidos": len(plano["mover"]),
            "atualizados": len(plano["atualizar"]),
            "sem_mudanca": plano["sem_mudanca"],
        })
    except ValueError as erro:
        session.rollback()
        return jsonify({"erro": str(erro)}), 400
    except Exception as erro:
        session.rollback()
        print(f"[ERRO] aplicar_planilha_indiretos: {erro}")
        return jsonify({"erro": "Não foi possível aplicar a planilha."}), 500
    finally:
        session.close()
