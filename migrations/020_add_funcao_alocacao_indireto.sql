-- Função exibida para o indireto na página Indiretos (ver indiretos.py, rota
-- /api/indiretos/funcao). Escolhida entre as funções que já existem no
-- cadastro, para manter o padrão, e usada no cartão e na ordenação por cargo.
--
-- Fica na ALOCAÇÃO, e não no cadastro (colaboradores."FUNÇÃO"): o cadastro
-- vem da planilha do RH e a troca se perderia na próxima importação.
-- NULL = usa a função do cadastro.
--
-- IMPORTANTE: rodar ANTES de publicar o código que usa esta coluna. Sem ela a
-- página Indiretos e a aba Indiretos da exportação do Resumo falham.

ALTER TABLE alocacoes_indiretos
    ADD COLUMN IF NOT EXISTS "FUNCAO" VARCHAR;
