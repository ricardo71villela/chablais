-- Migração: colunas para o resultado da ponte de cruzamento com o Radar
-- Léman (candidatos_cruzamento_melhor.csv — o candidato mais parecido em
-- área, um por anúncio), para aparecer no dashboard.
-- Corre no SQL Editor do Supabase — é seguro correr mesmo com dados já
-- existentes (usa "if not exists" em tudo).

alter table imoveis add column if not exists radar_leman_match_label text;             -- morada (casa/apartamento) ou "Parcela <ref>" (terreno)
alter table imoveis add column if not exists radar_leman_match_link text;              -- link Google Maps
alter table imoveis add column if not exists radar_leman_match_tipo text;              -- 'apartamento' | 'casa' | 'terreno_livre'
alter table imoveis add column if not exists radar_leman_match_diferenca_pct numeric;  -- diferença de área do candidato escolhido
alter table imoveis add column if not exists radar_leman_match_atualizado_em timestamptz;

create index if not exists idx_imoveis_radar_leman_match
    on imoveis(radar_leman_match_tipo)
    where radar_leman_match_tipo is not null;

-- Não é preciso mexer em RLS: a policy "leitura publica imoveis" (ver
-- migration_003_dashboard.sql) já cobre "select *", e estas colunas não são
-- escritas pelo dashboard (só pelo script atualizar_matches_radar_leman.py,
-- que corre com a chave service_role, fora do browser).
