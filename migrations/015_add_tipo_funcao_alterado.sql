-- Quem mudou o TIPO_FUNÇÃO do colaborador na tela (DIRETO/INDIRETO), e
-- quando (ver app.py, rota /api/colaboradores/tipo-funcao). Mesmo padrão de
-- AFASTADO_POR/AFASTADO_EM (migrations/014): login como texto, não id, pra
-- sobreviver à exclusão do usuário.
--
-- IMPORTANTE: rodar ANTES de publicar o código que usa estas colunas.
--
-- Quem teve o TIPO_FUNÇÃO definido só pela planilha (nunca trocado na tela)
-- fica com os dois campos vazios.

ALTER TABLE colaboradores
    ADD COLUMN IF NOT EXISTS "TIPO_FUNÇÃO_ALTERADO_POR" VARCHAR;

ALTER TABLE colaboradores
    ADD COLUMN IF NOT EXISTS "TIPO_FUNÇÃO_ALTERADO_EM" TIMESTAMPTZ;
