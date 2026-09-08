-- Esquema Supabase/Postgres — base de dados de imóveis das agências concorrentes
-- Aplicar num projeto Supabase novo e separado (ver plano de arquitetura, secção 10)

create extension if not exists "uuid-ossp";

create table if not exists agencias (
    id          uuid primary key default uuid_generate_v4(),
    nome        text not null,
    rede        text,                 -- ex. 'Century21', 'Laforet', 'Independente'
    cidade      text not null,        -- 'Thonon' | 'Evian'
    site_url    text,
    ativo       boolean not null default true,
    criado_em   timestamptz not null default now()
);

create table if not exists imoveis (
    id                  uuid primary key default uuid_generate_v4(),
    agencia_id          uuid not null references agencias(id) on delete cascade,
    url_anuncio         text not null unique,
    tipo_transacao      text not null,          -- 'venda' | 'arrendamento'
    preco               numeric,
    moeda               text default 'EUR',
    superficie_m2       numeric,
    num_divisoes        int,
    num_quartos         int,
    morada              text,
    cidade              text,
    fotos               text[] default '{}',
    referencia_agencia  text,                   -- ref. interna da agência (ex. "157523")
    hash_conteudo       text,                   -- para deteção rápida de alterações
    primeira_deteccao   timestamptz not null default now(),
    ultima_atualizacao  timestamptz not null default now(),
    estado              text not null default 'ativo'  -- 'ativo' | 'removido'
);

create index if not exists idx_imoveis_agencia on imoveis(agencia_id);
create index if not exists idx_imoveis_estado on imoveis(estado);
create index if not exists idx_imoveis_cidade on imoveis(cidade);
