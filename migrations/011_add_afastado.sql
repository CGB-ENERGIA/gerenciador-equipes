-- Adiciona o status "afastado" ao colaborador: AFASTADO (bool) e a
-- justificativa exigida na tela pra marcar esse status (Banco de Dados >
-- Colaboradores > clicar num colaborador livre > "Marcar como afastado").
--
-- Afastado e um status do colaborador, nao uma alocacao -- por isso fica em
-- colaboradores, sem precisar de base/equipe/vaga (ver app.py, rota
-- /api/colaboradores/afastar).

ALTER TABLE colaboradores
    ADD COLUMN IF NOT EXISTS "AFASTADO" BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE colaboradores
    ADD COLUMN IF NOT EXISTS "JUSTIFICATIVA_AFASTAMENTO" TEXT;
