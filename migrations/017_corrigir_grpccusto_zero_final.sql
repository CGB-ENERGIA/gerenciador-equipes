-- Devolve o zero final perdido no GRPCCUSTO ("2.17" -> "2.170").
--
-- No Excel o código do grupo de centro de custo costuma estar gravado como
-- NÚMERO, e 2.170 é o mesmo número que 2.17: a importação lia "2.17". Os
-- códigos têm sempre 3 dígitos depois do ponto (2.127, 2.169, 2.170...), então
-- completar com zeros à direita devolve o código original. A partir desta
-- versão o app já grava no formato certo (ver
-- database/importacao/importar_colaboradores.py, codigo_grupo_ccusto); esta
-- migration acerta o que já estava gravado.
--
-- Pode rodar de novo sem efeito.

UPDATE rateios
SET "GRPCCUSTO" = "GRPCCUSTO" || REPEAT('0', 3 - LENGTH(SPLIT_PART("GRPCCUSTO", '.', 2)))
WHERE "GRPCCUSTO" ~ '^[0-9]+\.[0-9]{1,2}$';

UPDATE colaboradores
SET "GRPCCUSTO" = "GRPCCUSTO" || REPEAT('0', 3 - LENGTH(SPLIT_PART("GRPCCUSTO", '.', 2)))
WHERE "GRPCCUSTO" ~ '^[0-9]+\.[0-9]{1,2}$';
