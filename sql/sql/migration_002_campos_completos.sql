-- Migração: adiciona os novos campos (descrição completa, DPE, ano de
-- construção, comodidades, foto de capa) e o suporte a deduplicação.
-- Corre isto no SQL Editor do Supabase — é seguro correr mesmo que já
-- tenhas dados na tabela (usa "if not exists" em tudo).

alter table imoveis add column if not exists foto_capa text;
alter table imoveis add column if not exists descricao text;
alter table imoveis add column if not exists dpe_classe text;
alter table imoveis add column if not exists ano_construcao int;
alter table imoveis add column if not exists comodidades text[] default '{}';
alter table imoveis add column if not exists fingerprint_duplicado text;
alter table imoveis add column if not exists possivel_duplicado_de uuid references imoveis(id);

create index if not exists idx_imoveis_fingerprint on imoveis(fingerprint_duplicado);
