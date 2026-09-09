-- Migração: suporte a notas pessoais e estado de contacto por imóvel,
-- para o dashboard de consulta. Corre no SQL Editor do Supabase.

alter table imoveis add column if not exists nota_pessoal text;
alter table imoveis add column if not exists estado_contacto text default 'novo';
-- valores sugeridos para estado_contacto: 'novo', 'contactado', 'interessante', 'descartado'

-- Função para atualizar só a nota/estado (usada pelo dashboard) — evita dar
-- permissão de escrita direta e total sobre a tabela `imoveis` à chave
-- pública (anon) usada no browser.
create or replace function atualizar_nota_imovel(
    p_imovel_id uuid,
    p_nota text,
    p_estado text
) returns void
language sql
security definer
as $$
    update imoveis
    set nota_pessoal = p_nota,
        estado_contacto = p_estado
    where id = p_imovel_id;
$$;

-- Row Level Security: o dashboard lê imoveis/agencias com a chave "anon"
-- (pública, mas o acesso de escrita fica limitado à função acima).
alter table imoveis enable row level security;
alter table agencias enable row level security;

drop policy if exists "leitura publica imoveis" on imoveis;
create policy "leitura publica imoveis" on imoveis for select using (true);

drop policy if exists "leitura publica agencias" on agencias;
create policy "leitura publica agencias" on agencias for select using (true);

-- Não criar policy de UPDATE/INSERT/DELETE para anon — a única escrita
-- possível é via atualizar_nota_imovel (security definer), que corre com
-- os privilégios do dono da função, não do chamador.
grant execute on function atualizar_nota_imovel(uuid, text, text) to anon;
