-- Autocadastro: a pessoa cria a propria conta na tela de login e um
-- administrador aprova (ver app.py, solicitar_cadastro / aprovar_usuario).
--
-- PENDENTE = TRUE marca a conta que ainda espera aprovacao. Ela nasce com
-- ATIVO = FALSE, entao nao entra no sistema ate ser aprovada. Contas ja
-- existentes ficam como estao (PENDENTE = FALSE).

ALTER TABLE usuarios
    ADD COLUMN IF NOT EXISTS "PENDENTE" BOOLEAN NOT NULL DEFAULT FALSE;
