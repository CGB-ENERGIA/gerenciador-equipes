-- Vagas dos Indiretos (BID): o previsto de cada setor, uma linha por vaga.
--
-- vagas_indiretos — SETOR + FUNCAO (a função do BID); ORDEM é a posição da
-- função no BID do setor (a tela e a planilha seguem essa ordem). BASE e
-- RESPONSAVEL_CHAPA (opcionais) dizem onde a vaga vazia fica no organograma:
-- abaixo de quem e em qual base; vazios = fora da cadeia. Quem ocupa a vaga é a
-- alocação com VAGA_ID dela; a função real da pessoa pode ser outra (vaga de
-- SUPERVISOR OPERACIONAL ocupada por um SUPERVISOR DE CONSTRUÇÃO II).
--
-- alocacoes_indiretos.VAGA_ID — a vaga que a pessoa ocupa (uma pessoa por
-- vaga). Vazio = EXTRA no setor. Apagar a vaga deixa a pessoa como extra;
-- tirar a pessoa do setor deixa a vaga vazia.
--
-- IMPORTANTE: rodar ANTES de publicar o código que usa esta tabela.

CREATE TABLE IF NOT EXISTS vagas_indiretos (
    id            SERIAL PRIMARY KEY,
    "SETOR"       VARCHAR NOT NULL,
    "FUNCAO"      VARCHAR NOT NULL,
    "ORDEM"       INTEGER NOT NULL DEFAULT 0,
    "BASE"               VARCHAR,
    "RESPONSAVEL_CHAPA"  VARCHAR,
    "CRIADO_POR"  VARCHAR,
    "CRIADO_EM"   TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_vagas_indiretos_id ON vagas_indiretos (id);

ALTER TABLE alocacoes_indiretos
    ADD COLUMN IF NOT EXISTS "VAGA_ID" INTEGER UNIQUE
    REFERENCES vagas_indiretos (id) ON DELETE SET NULL;
