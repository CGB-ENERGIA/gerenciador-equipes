-- Observação livre sobre o colaborador (ver app.py, rota
-- /api/colaboradores/observacao). Ex.: "férias de 01/11 a 30/11" para quem
-- continua alocado na vaga — diferente do afastamento, não libera a vaga nem
-- muda o status. Aparece no Banco de Dados (vaga e lista de colaboradores).
--
-- OBSERVACAO_POR guarda o LOGIN do usuário como texto (mesmo critério de
-- AFASTADO_POR, migrations/014).
--
-- IMPORTANTE: rodar ANTES de publicar o código que usa estas colunas. O
-- modelo Colaborador passa a ler as três, e sem elas no banco toda consulta
-- de colaboradores falha.

ALTER TABLE colaboradores
    ADD COLUMN IF NOT EXISTS "OBSERVACAO" VARCHAR;

ALTER TABLE colaboradores
    ADD COLUMN IF NOT EXISTS "OBSERVACAO_POR" VARCHAR;

ALTER TABLE colaboradores
    ADD COLUMN IF NOT EXISTS "OBSERVACAO_EM" TIMESTAMPTZ;
