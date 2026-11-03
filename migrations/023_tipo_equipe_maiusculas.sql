-- TIPO EQUIPE (composicoes_equipes.ESTRUTURA) em maiúsculas.
--
-- "Construção" (180 vagas) e "CONSTRUÇÃO" (29) conviviam no banco: a tela já
-- mostrava como uma disciplina só, mas o dado ficava duplicado. O código grava
-- sempre em maiúsculas a partir de agora (ComposicaoEquipe._estrutura_em_maiusculas).
--
-- A troca com acento é feita valor a valor, e não com UPPER(): dependendo do
-- idioma do banco, UPPER() pode não converter "ç" e "ã". O que só tem letras
-- sem acento usa UPPER(), que é seguro nesse caso.
--
-- Pode rodar mais de uma vez: na segunda não muda nada.

UPDATE composicoes_equipes SET "ESTRUTURA" = 'CONSTRUÇÃO' WHERE "ESTRUTURA" = 'Construção';
UPDATE composicoes_equipes SET "ESTRUTURA" = 'CONSTRUÇÃO LEVE' WHERE "ESTRUTURA" = 'Construção Leve';
UPDATE composicoes_equipes SET "ESTRUTURA" = UPPER("ESTRUTURA")
 WHERE "ESTRUTURA" <> UPPER("ESTRUTURA") AND "ESTRUTURA" ~ '^[A-Za-z0-9 ]+$';
