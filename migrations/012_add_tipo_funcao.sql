-- Adiciona TIPO_FUNÇÃO em colaboradores: classifica o colaborador como
-- "DIRETO" ou "INDIRETO". So quem esta marcado "DIRETO" entra no conjunto de
-- colaboradores disponiveis para alocacao (ver app.py, obter_colaboradores
-- e obter_pessoas_nao_alocadas).
--
-- Preenchido a partir de agora pela planilha de cadastro de colaboradores
-- (coluna obrigatoria TIPO_FUNÇÃO -- ver
-- database/importacao/importar_colaboradores.py). Colaboradores ja
-- cadastrados ficam com o campo vazio ate a proxima planilha ser aplicada.

ALTER TABLE colaboradores
    ADD COLUMN IF NOT EXISTS "TIPO_FUNÇÃO" VARCHAR;
