-- Quem marcou o colaborador como afastado, e quando (ver app.py, rota
-- /api/colaboradores/afastar). Aparece nas tabelas de afastados e de não
-- alocados, ao lado da justificativa.
--
-- AFASTADO_POR guarda o NOME do usuário como texto, e não o id: o registro
-- continua legível mesmo que o usuário seja excluído depois.
--
-- IMPORTANTE: rodar ANTES de publicar o código que usa estas colunas. O
-- modelo Colaborador passa a ler as duas, e sem elas no banco toda consulta
-- de colaboradores falha.
--
-- Quem já estava afastado antes desta migration fica com os dois campos
-- vazios (a tela mostra "não registrado").

ALTER TABLE colaboradores
    ADD COLUMN IF NOT EXISTS "AFASTADO_POR" VARCHAR;

ALTER TABLE colaboradores
    ADD COLUMN IF NOT EXISTS "AFASTADO_EM" TIMESTAMPTZ;
