-- Alocação do pessoal INDIRETO (página "Indiretos", ver indiretos.py).
--
-- Diferente das equipes, o controle é nominal: não há vagas, só QUEM está em
-- qual SETOR, em qual BASE e sob qual RESPONSÁVEL. Uma linha por indireto.
--
-- - SETOR e BASE são texto (em maiúsculas): o setor "existe" a partir do
--   momento em que alguém é alocado nele, e o mesmo setor em várias bases
--   aparece na tela num cartão só, com uma seção por base.
-- - BASE é escolhida por quem aloca, independente da seção do cadastro.
-- - O responsável é POR PESSOA (no mesmo setor e base pode haver mais de
--   um). Guardado como CHAPA em texto, sem chave estrangeira, para a
--   alocação não sumir se o responsável sair do cadastro.
-- - Sair do cadastro (colaboradores) apaga a alocação do indireto junto.
--
-- IMPORTANTE: rodar ANTES de publicar o código que usa esta tabela.

CREATE TABLE IF NOT EXISTS alocacoes_indiretos (
    id                   SERIAL PRIMARY KEY,
    "CHAPA"              VARCHAR NOT NULL UNIQUE
                         REFERENCES colaboradores ("CHAPA") ON DELETE CASCADE,
    "SETOR"              VARCHAR NOT NULL,
    "BASE"               VARCHAR NOT NULL,
    "RESPONSAVEL_CHAPA"  VARCHAR,
    "OBSERVACAO"         VARCHAR,
    "ALOCADO_POR"        VARCHAR,
    "ALOCADO_EM"         TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_alocacoes_indiretos_setor_base
    ON alocacoes_indiretos ("SETOR", "BASE");
