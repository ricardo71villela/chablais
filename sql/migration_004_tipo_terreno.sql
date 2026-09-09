-- Migração: acrescenta tipo_imovel e superficie_terreno_m2 — preparação
-- para a ponte com o Radar Léman (cruzamento por área, ±5%).
-- Corre no SQL Editor do Supabase.

alter table imoveis add column if not exists tipo_imovel text;
alter table imoveis add column if not exists superficie_terreno_m2 numeric;

create index if not exists idx_imoveis_tipo_imovel on imoveis(tipo_imovel);
