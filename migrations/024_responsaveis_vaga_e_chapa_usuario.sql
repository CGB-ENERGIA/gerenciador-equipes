-- Supervisor e coordenador da vaga ligados à conta de usuário, e chapa na conta.
--
-- O nome escrito na vaga continua sendo o que as telas mostram; as colunas
-- novas dizem de qual conta ele é. O sistema preenche sozinho quando o nome é
-- igual ao de uma conta do nível (ver database/responsaveis_vaga.py). Conta
-- excluída deixa a vaga só com o nome.
--
-- IMPORTANTE: rodar ANTES de publicar o código que usa estas colunas.

ALTER TABLE composicoes_equipes
    ADD COLUMN IF NOT EXISTS "SUPERVISOR_ID" INTEGER REFERENCES usuarios(id) ON DELETE SET NULL;
ALTER TABLE composicoes_equipes
    ADD COLUMN IF NOT EXISTS "COORDENADOR_ID" INTEGER REFERENCES usuarios(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS ix_composicoes_supervisor_id ON composicoes_equipes ("SUPERVISOR_ID");
CREATE INDEX IF NOT EXISTS ix_composicoes_coordenador_id ON composicoes_equipes ("COORDENADOR_ID");

ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS "CHAPA" VARCHAR;
CREATE UNIQUE INDEX IF NOT EXISTS uq_usuarios_chapa ON usuarios ("CHAPA") WHERE "CHAPA" IS NOT NULL;
