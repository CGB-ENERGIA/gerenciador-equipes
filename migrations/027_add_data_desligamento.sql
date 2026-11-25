-- Indicar desligamento: o colaborador "fora de operação" passa a ter dois
-- motivos. Afastamento (AFASTADO + justificativa, como antes) e desligamento
-- (AFASTADO + esta data). Quem tem DATA_DESLIGAMENTO preenchida está
-- desligado; o campo é limpo ao reativar a pessoa.
--
-- IMPORTANTE: rodar ANTES de publicar o código que usa esta coluna. O modelo
-- Colaborador passa a ler DATA_DESLIGAMENTO, e sem ela no banco toda consulta
-- de colaboradores falha.

ALTER TABLE colaboradores
    ADD COLUMN IF NOT EXISTS "DATA_DESLIGAMENTO" DATE;
