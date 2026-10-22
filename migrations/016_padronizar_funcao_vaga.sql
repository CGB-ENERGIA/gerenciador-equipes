-- Padroniza o nome da função das vagas (composicoes_equipes."FUNÇÃO_ER"):
-- maiúsculas, sem espaço sobrando, e "MUNQUEIRO/MOTORISTA" unificado em
-- "MOTORISTA".
--
-- Antes, a mesma função estava gravada de jeitos diferentes ("Eletricista" e
-- "ELETRICISTA", "Encarregado" e "ENCARREGADO"...) e virava duas colunas na
-- planilha de equipes. A partir desta versão o app grava sempre o nome
-- canônico (ver app.py, funcao_da_vaga); esta migration acerta o que já
-- existia. Não cria nem apaga vaga, e as alocações (membros_equipes) ficam
-- intactas: só muda a escrita da função.
--
-- Pode rodar de novo sem efeito (o que já está padronizado não muda).

UPDATE composicoes_equipes
SET "FUNÇÃO_ER" = UPPER(REGEXP_REPLACE(TRIM("FUNÇÃO_ER"), '\s+', ' ', 'g'))
WHERE "FUNÇÃO_ER" <> UPPER(REGEXP_REPLACE(TRIM("FUNÇÃO_ER"), '\s+', ' ', 'g'));

UPDATE composicoes_equipes
SET "FUNÇÃO_ER" = 'MOTORISTA'
WHERE "FUNÇÃO_ER" = 'MUNQUEIRO/MOTORISTA';
