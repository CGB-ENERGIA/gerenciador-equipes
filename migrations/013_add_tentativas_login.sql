-- Tentativas de login que falharam, para limitar força bruta (ver app.py,
-- limite_de_tentativas_atingido).
--
-- Fica no banco, e não na memória do processo, porque na Vercel cada
-- requisição pode cair numa instância diferente: um contador em memória
-- zeraria a cada instância nova e não limitaria nada.
--
-- USUARIO é o login digitado (em maiúsculas), exista ele ou não — assim o
-- limite vale também para quem tenta adivinhar nomes de usuário. Linhas com
-- mais de 1 dia são apagadas pelo próprio app a cada falha registrada.

CREATE TABLE IF NOT EXISTS tentativas_login (
    id          SERIAL PRIMARY KEY,
    "USUARIO"   VARCHAR NOT NULL,
    "IP"        VARCHAR,
    "CRIADO_EM" TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_tentativas_login_usuario_criado
    ON tentativas_login ("USUARIO", "CRIADO_EM");

CREATE INDEX IF NOT EXISTS ix_tentativas_login_ip_criado
    ON tentativas_login ("IP", "CRIADO_EM");
