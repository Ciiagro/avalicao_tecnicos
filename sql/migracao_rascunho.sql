-- Suporte a rascunho: até agora, toda avaliação enviada já era definitiva.
-- Agora existem dois estados:
--   'rascunho'   -> pode ser reaberta e editada de novo, com perguntas em branco
--   'finalizada' -> travada, sem volta (é o que "ja_avaliado" trata como concluída)
--
-- Todas as avaliações já existentes no banco viram 'finalizada' (elas já
-- eram avaliações completas e definitivas, feitas antes desse recurso
-- existir — não devem virar rascunho nem ficar editáveis retroativamente).

ALTER TABLE avaliacoes_tecnicos
    ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'finalizada';

-- nota_final pode ficar em branco num rascunho ainda sem nenhuma pergunta
-- respondida — por isso também remove a trava NOT NULL dela, se existir.
ALTER TABLE avaliacoes_tecnicos
    ALTER COLUMN nota_final DROP NOT NULL;
