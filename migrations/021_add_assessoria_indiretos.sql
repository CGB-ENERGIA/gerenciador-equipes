-- Página Indiretos: assessoria no organograma e subsetor.
--
-- ASSESSORIA — organograma (ver indiretos.py, rota
-- /api/indiretos/organograma). O organograma é pessoa a pessoa: cada um fica
-- abaixo de quem responde (o RESPONSAVEL_CHAPA que já existe). Esta coluna
-- marca quem é ASSESSORIA do seu responsável: aparece ao lado da linha dele,
-- fora da cadeia principal.
--
-- IMPORTANTE: rodar ANTES de publicar o código que usa esta coluna. Sem ela,
-- a página Indiretos e a exportação do Resumo falham.

ALTER TABLE alocacoes_indiretos
    ADD COLUMN IF NOT EXISTS "ASSESSORIA" BOOLEAN NOT NULL DEFAULT FALSE;

-- SUBSETOR — subdivisão opcional do setor (ex.: OBRAS, EPI/EPC), em
-- maiúsculas. Filtro da página e aparece no organograma; não nos cartões.
ALTER TABLE alocacoes_indiretos
    ADD COLUMN IF NOT EXISTS "SUBSETOR" VARCHAR;

-- BASES_RESPONSAVEL — bases do setor pelas quais a pessoa responde no
-- organograma (siglas separadas por vírgula, ex.: "BCB" ou "BCB,BDC").
ALTER TABLE alocacoes_indiretos
    ADD COLUMN IF NOT EXISTS "BASES_RESPONSAVEL" VARCHAR;

-- ABAIXO_DE_FUNCAO — no desenho, a pessoa fica pendurada abaixo do bloco
-- desta função (os colegas que respondem ao mesmo chefe), sem ligar a uma
-- pessoa específica. O responsável continua sendo o chefe do bloco.
ALTER TABLE alocacoes_indiretos
    ADD COLUMN IF NOT EXISTS "ABAIXO_DE_FUNCAO" VARCHAR;
