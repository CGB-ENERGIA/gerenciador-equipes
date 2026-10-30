-- Organograma geral dos Indiretos: setor ligado a um gerente.
--
-- Arrastar um setor para um gerente liga o setor INTEIRO (todas as bases) a
-- ele: abaixo dele ou, com APOIO, ao lado da linha. Arrastar só o nome de um
-- responsável do setor liga só ele e quem está abaixo dele: RESPONSAVEL_CHAPA
-- preenchido (vazio = o setor todo). O que não tem linha segue as bases
-- marcadas nos gerentes. SETOR é texto, como em
-- alocacoes_indiretos, e o gerente é CHAPA em texto, sem chave estrangeira:
-- gerente que saiu da Gerência só faz o setor voltar à regra das bases.
--
-- IMPORTANTE: rodar ANTES de publicar o código que usa esta tabela.

CREATE TABLE IF NOT EXISTS setores_gerencia (
    "SETOR"              VARCHAR NOT NULL,
    "RESPONSAVEL_CHAPA"  VARCHAR NOT NULL DEFAULT '',
    "GERENTE_CHAPA"      VARCHAR NOT NULL,
    "APOIO"              BOOLEAN NOT NULL DEFAULT FALSE,
    "ALOCADO_POR"        VARCHAR,
    "ALOCADO_EM"         TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY ("SETOR", "RESPONSAVEL_CHAPA")
);
