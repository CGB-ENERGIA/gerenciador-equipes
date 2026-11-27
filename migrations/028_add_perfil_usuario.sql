-- Perfil de cada conta: DIRETO ou INDIRETO.
--   DIRETO: ve as equipes do proprio vinculo (base/setor/tipo) e aloca nelas,
--     como sempre foi.
--   INDIRETO: ve Resumo, Banco de Dados e Indiretos inteiros (so leitura na
--     operacao) e aloca/remove na tela de Indiretos apenas no proprio setor
--     (vinculo "SETOR_INDIRETO", gravado em usuarios_vinculos — sem coluna nova).
-- Contas existentes ficam DIRETO, que e o comportamento de hoje; o administrador
-- reclassifica quem precisar na tela de Usuarios.
--
-- IMPORTANTE: rodar ANTES de publicar o codigo que usa esta coluna. O modelo
-- Usuario passa a ler PERFIL, e sem ela no banco o login falha.

ALTER TABLE usuarios
    ADD COLUMN IF NOT EXISTS "PERFIL" VARCHAR NOT NULL DEFAULT 'DIRETO';
