# Painel de consulta — imóveis da concorrência

Página única (`index.html`), sem build nem dependências instaladas — só
precisa de ser hospedada como ficheiro estático e apontada ao teu Supabase.

## O que faz

- Lista todos os imóveis ativos (todas as agências), com foto de capa, preço,
  superfície, €/m², divisões, DPE e link para o anúncio original
- Filtros por cidade, agência, venda/arrendamento, estado de contacto e
  preço máximo
- Colunas ordenáveis (clicar no cabeçalho)
- Estatísticas rápidas: nº de imóveis no filtro atual, €/m² médio, e as 3
  agências com €/m² mais alto
- **Notas próprias por imóvel**: um menu de estado (Novo / Contactado /
  Interessante / Descartado) e um campo de texto livre, gravados
  automaticamente no Supabase ao editar

## Antes de usar

### 1. Aplicar a migração no Supabase

Corre `sql/migration_003_dashboard.sql` no SQL Editor do teu projeto
Supabase (o mesmo do scraper). Isto:
- acrescenta as colunas `nota_pessoal` e `estado_contacto` à tabela `imoveis`
- cria uma função `atualizar_nota_imovel` que é a ÚNICA forma de escrita
  permitida a partir do dashboard (protege o resto dos dados de escrita
  acidental ou maliciosa, mesmo que alguém descubra a chave pública)
- ativa Row Level Security com leitura pública (necessário para o
  dashboard funcionar sem login server-side)

### 2. Preencher as credenciais no `index.html`

Abre `index.html` num editor de texto e substitui estas 3 linhas perto do
fim do ficheiro (dentro da tag `<script>`):

```js
const SUPABASE_URL = "COLOCAR_AQUI_O_TEU_SUPABASE_URL";
const SUPABASE_ANON_KEY = "COLOCAR_AQUI_A_TUA_CHAVE_ANON";
const PASSWORD = "MUDAR_ESTA_PASSWORD";
```

- `SUPABASE_URL` e `SUPABASE_ANON_KEY`: Project Settings → API no Supabase.
  Usa a chave **anon / public** aqui (não a `service_role` — essa fica só no
  scraper, nunca num ficheiro que corre no browser).
- `PASSWORD`: escolhe uma palavra-passe à tua escolha. **Aviso de segurança
  honesto**: isto é só um filtro contra acessos casuais (alguém a passar
  pelo link por acaso) — o código roda no browser, por isso uma pessoa que
  souber olhar para o código-fonte da página consegue ver a password. A
  proteção real dos dados vem da Row Level Security (só leitura + a função
  de notas), não desta password. Não uses uma password que uses noutro
  lado.

### 3. Publicar

A forma mais simples: **Vercel**, já que já tens conta.

1. No teu repositório `chablais`, garante que a pasta `dashboard/` está lá
   (faz commit + push como sempre)
2. Vai a vercel.com → Add New → Project → importa o repositório `chablais`
3. Em "Root Directory", escolhe `dashboard`
4. Framework Preset: "Other" (é HTML puro, não precisa de build)
5. Deploy

Vais ficar com um URL tipo `chablais-dashboard.vercel.app` — não partilhes
este link (mantém a confidencialidade do projeto, como o resto).

## Limitações desta primeira versão

- Não pagina os resultados (carrega tudo de uma vez — ainda é pouco volume,
  mas se um dia forem milhares de imóveis, vale a pena paginar)
- A password é só um filtro simples, como explicado acima
- Não tem gráfico/histórico de preços ao longo do tempo (só o estado atual)
