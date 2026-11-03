"""Troca os nomes curtos de supervisor e coordenador das vagas ("EDDY",
"LUIS FILIPE") pelo nome completo da conta de usuário, para a vaga ficar
ligada à conta (ver database/responsaveis_vaga.py).

Só troca quando o nome da vaga corresponde ao começo do nome de UMA conta
aceita no campo (LUIS FILIPE -> LUIS FILIPE SOUSA LIMA): Supervisor no
supervisor; Coordenador ou Gerente no coordenador. O que não tem conta, ou
tem mais de uma possível, fica como está e aparece na lista para decidir à mão.

Casos que a regra não resolve (apelido, segundo nome, dois com o mesmo
primeiro nome) vão com --nome "NOME NA VAGA=NOME COMPLETO DA CONTA"; o nome
completo precisa ser o de uma conta, e vale para supervisor e coordenador.

Uso (rodar depois de migrations/024):
    python -m database.ligar_nomes_das_vagas            # só mostra a proposta
    python -m database.ligar_nomes_das_vagas --aplicar  # grava
    python -m database.ligar_nomes_das_vagas --nome "RAIMUNDO=RAIMUNDO NONATO ..."
"""

import sys

from database.database import SessionLocal
from database.models import ComposicaoEquipe, Usuario
from database.responsaveis_vaga import CAMPOS, nome_comparavel


def conta_do_nome_curto(nome, contas_do_nivel):
    partes = nome_comparavel(nome).split()
    if not partes:
        return None, []
    candidatas = [
        conta for conta in contas_do_nivel
        if nome_comparavel(conta.NOME).split()[:len(partes)] == partes
    ]
    return (candidatas[0] if len(candidatas) == 1 else None), candidatas


def main(aplicar, manuais=None):
    session = SessionLocal()
    try:
        contas = session.query(Usuario).all()
        vagas = session.query(ComposicaoEquipe).all()
        trocas, pendentes = {}, {}
        manuais = {nome_comparavel(k): v for k, v in (manuais or {}).items()}
        for campo_nome, _campo_id, niveis in CAMPOS:
            do_nivel = [conta for conta in contas if conta.NIVEL in niveis]
            for nome in sorted({getattr(v, campo_nome) for v in vagas if getattr(v, campo_nome)}):
                escolhido = manuais.get(nome_comparavel(nome))
                if escolhido:
                    conta = next(
                        (c for c in do_nivel if nome_comparavel(c.NOME) == nome_comparavel(escolhido)),
                        None,
                    )
                    if conta:
                        trocas[(campo_nome, nome)] = conta.NOME
                    else:
                        pendentes[(campo_nome, nome)] = [f"(indicado: {escolhido}, mas não há conta de {' ou '.join(niveis).lower()} com esse nome)"]
                    continue
                conta, candidatas = conta_do_nome_curto(nome, do_nivel)
                if conta and nome_comparavel(conta.NOME) != nome_comparavel(nome):
                    trocas[(campo_nome, nome)] = conta.NOME
                elif not conta:
                    pendentes[(campo_nome, nome)] = [c.NOME for c in candidatas]

        print("Vão ser trocados:")
        for (campo, nome), completo in trocas.items():
            print(f"  {campo:12} {nome!r:28} -> {completo}")
        print("Ficam como estão (decidir à mão):")
        for (campo, nome), candidatas in pendentes.items():
            if candidatas and candidatas[0].startswith("(indicado"):
                motivo = candidatas[0]
            else:
                motivo = f"mais de uma conta: {', '.join(candidatas)}" if candidatas else "nenhuma conta"
            print(f"  {campo:12} {nome!r:28} {motivo}")

        if not aplicar:
            print("\nNada foi gravado. Rode com --aplicar para gravar as trocas.")
            return

        alteradas = 0
        for vaga in vagas:
            for campo_nome, _campo_id, _niveis in CAMPOS:
                novo = trocas.get((campo_nome, getattr(vaga, campo_nome)))
                if novo:
                    setattr(vaga, campo_nome, novo)
                    alteradas += 1
        session.commit()
        print(f"\n{alteradas} campo(s) de vaga atualizado(s).")
    finally:
        session.close()


def manuais_da_linha_de_comando(argumentos):
    manuais = {}
    for indice, argumento in enumerate(argumentos):
        if argumento == "--nome" and indice + 1 < len(argumentos):
            vaga, _, conta = argumentos[indice + 1].partition("=")
            if vaga.strip() and conta.strip():
                manuais[vaga.strip()] = conta.strip()
    return manuais


if __name__ == "__main__":
    main("--aplicar" in sys.argv, manuais_da_linha_de_comando(sys.argv))
