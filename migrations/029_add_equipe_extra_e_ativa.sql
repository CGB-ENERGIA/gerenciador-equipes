-- Equipe extra e equipe inativa.
--   EXTRA: as vagas da equipe nao entram no previsto do Resumo, so no realizado
--     (como a vaga de Folguista Extra). Quem esta alocado nela soma em "alocados"
--     e aparece como saldo positivo; quem saiu de outra equipe para ela deixa
--     aquela com saldo negativo, e o total geral fecha em zero.
--   ATIVA: equipe inativa some das listas e do Resumo, nao recebe alocacao e,
--     ao ser inativada, os colaboradores dela ficam livres.
-- As equipes existentes ficam como estao: EXTRA = falso e ATIVA = verdadeiro.
--
-- IMPORTANTE: rodar ANTES de publicar o codigo que usa estas colunas. O modelo
-- Equipe passa a le-las, e sem elas no banco toda consulta de equipes falha.

ALTER TABLE equipes
    ADD COLUMN IF NOT EXISTS "EXTRA" BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE equipes
    ADD COLUMN IF NOT EXISTS "ATIVA" BOOLEAN NOT NULL DEFAULT TRUE;
