"""Liga o supervisor e o coordenador de cada vaga à conta de usuário.

O nome escrito na vaga (ComposicaoEquipe.SUPERVISOR / COORDENADOR) continua
sendo o que as telas, os filtros e as planilhas mostram. SUPERVISOR_ID e
COORDENADOR_ID dizem de qual conta é esse nome: preenchidos sempre que o nome
é igual ao NOME de uma conta daquele nível (sem diferença de maiúsculas e
acentos), e vazios quando não há conta ou há mais de uma com o mesmo nome.

Tudo acontece antes de cada gravação (before_flush), então vale para qualquer
caminho que mexa em vaga ou em conta: tela de vagas, planilhas, Folguista
Extra, tela e planilha de usuários. Renomear uma conta troca o nome em todas
as vagas ligadas a ela, e quem passou a ter conta é ligado na hora.

Por enquanto a ligação é só informação: o acesso continua pelos vínculos
(ver auth.py). Ver migrations/024.
"""

import unicodedata

from sqlalchemy import event, inspect
from sqlalchemy.orm import Session

from database.models import ComposicaoEquipe, Usuario

# (campo do nome, campo da conta, níveis de conta aceitos). O coordenador da
# vaga pode ser um Gerente: há equipes que respondem direto a ele.
CAMPOS = (
    ("SUPERVISOR", "SUPERVISOR_ID", ("SUPERVISOR",)),
    ("COORDENADOR", "COORDENADOR_ID", ("COORDENADOR", "GERENTE")),
)


def nome_comparavel(nome):
    texto = unicodedata.normalize("NFKD", str(nome or "").strip().upper())
    return " ".join(texto.encode("ascii", "ignore").decode().split())


def _contas_por_nome(session):
    """{nivel: {nome comparável: [ids]}} de todas as contas."""
    por_nivel = {}
    for conta_id, nome, nivel in session.query(Usuario.id, Usuario.NOME, Usuario.NIVEL).all():
        por_nivel.setdefault(nivel, {}).setdefault(nome_comparavel(nome), []).append(conta_id)
    return por_nivel


def ligar_vaga(composicao, contas):
    for campo_nome, campo_id, niveis in CAMPOS:
        nome = nome_comparavel(getattr(composicao, campo_nome))
        ids = [i for nivel in niveis for i in contas.get(nivel, {}).get(nome, [])]
        conta_id = ids[0] if len(ids) == 1 and getattr(composicao, campo_nome) else None
        if getattr(composicao, campo_id) != conta_id:
            setattr(composicao, campo_id, conta_id)


def _mudou(objeto, *campos):
    estado = inspect(objeto)
    return any(estado.attrs[campo].history.has_changes() for campo in campos)


@event.listens_for(Session, "before_flush")
def _antes_de_gravar(session, _contexto, _instancias):
    vagas = [
        objeto for objeto in list(session.new) + list(session.dirty)
        if isinstance(objeto, ComposicaoEquipe)
        and (objeto in session.new or _mudou(objeto, "SUPERVISOR", "COORDENADOR"))
    ]
    contas_mexidas = [
        objeto for objeto in list(session.new) + list(session.dirty) + list(session.deleted)
        if isinstance(objeto, Usuario)
        and (objeto in session.new or objeto in session.deleted or _mudou(objeto, "NOME", "NIVEL"))
    ]
    if not vagas and not contas_mexidas:
        return

    with session.no_autoflush:
        # conta renomeada: o nome novo vai para as vagas que já eram dela
        for conta in contas_mexidas:
            if conta in session.new or conta in session.deleted or conta.id is None:
                continue
            if not _mudou(conta, "NOME"):
                continue
            for campo_nome, campo_id, _niveis in CAMPOS:
                ligadas = session.query(ComposicaoEquipe).filter(
                    getattr(ComposicaoEquipe, campo_id) == conta.id
                ).all()
                for vaga in ligadas:
                    setattr(vaga, campo_nome, conta.NOME)
                    if vaga not in vagas:
                        vagas.append(vaga)

        contas = _contas_por_nome(session)
        # contas novas ainda sem id entram depois do flush: o próximo
        # religamento (relink abaixo) cuida delas
        if contas_mexidas:
            for conta in contas_mexidas:
                if conta in session.deleted and conta.id is not None:
                    for nivel_nomes in contas.values():
                        for ids in nivel_nomes.values():
                            if conta.id in ids:
                                ids.remove(conta.id)
            vagas = session.query(ComposicaoEquipe).all() + [v for v in vagas if v in session.new]

        for vaga in vagas:
            ligar_vaga(vaga, contas)


@event.listens_for(Session, "after_flush_postexec")
def _depois_de_gravar(session, _contexto):
    """Conta criada nesta gravação só tem id depois do flush: liga as vagas
    que já tinham o nome dela."""
    novas = session.info.pop("contas_novas_para_ligar", None)
    if not novas:
        return
    contas = _contas_por_nome(session)
    with session.no_autoflush:
        for vaga in session.query(ComposicaoEquipe).all():
            ligar_vaga(vaga, contas)


@event.listens_for(Session, "after_flush")
def _marcar_contas_novas(session, _contexto):
    if any(isinstance(objeto, Usuario) for objeto in session.new):
        session.info["contas_novas_para_ligar"] = True
