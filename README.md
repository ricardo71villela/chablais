# Base de dados de imóveis — agências concorrentes (Thonon / Évian)

Projeto privado de ingestão de dados imobiliários das agências concorrentes de
Thonon-les-Bains e Évian-les-Bains (excluindo DECORDIER IMMOBILIER).

⚠️ **Projeto confidencial.** Ver `docs/plano-arquitetura.md` (ou o documento
partilhado) para as regras de discrição: repositório privado, sem menções à
DECORDIER em nenhum commit/README/nome de recurso, User-Agent genérico no
scraper, execução via GitHub Actions (IP não associado à agência).

## Estado atual (piloto)

| Rede | Cobertura | Estado |
|---|---|---|
| CENTURY 21 Chablais-Léman | Thonon + Évian | ✅ Scraper funcional (a validar em produção) |
| Laforêt Thonon-Évian | Thonon + Évian (agência única cobre as duas cidades) | 🚧 Stub — falta confirmar o padrão de URL dos anúncios individuais |
| Restantes ~15 agências | Thonon + Évian | ⏳ Por implementar (ver plano de arquitetura, secção 6) |

## Porquê começar por Century21 e Laforêt

São redes nacionais com o mesmo motor de site em todas as agências da rede —
um scraper por rede cobre múltiplas agências (incluindo, no futuro, fora de
Thonon/Évian se o âmbito crescer).

## Estrutura

```
src/
  models.py              # dataclass Listing (estrutura de um imóvel)
  scrapers/
    base.py               # interface AgencyScraper + helpers de extração
    century21_scraper.py   # scraper funcional (rede Century21)
    laforet_scraper.py     # stub a completar
    config.py              # registo das agências-alvo (site, cidade, rede)
  normalize.py            # limpeza/normalização de preço, superfície, etc.
  upsert_supabase.py       # grava/atualiza na tabela `imoveis`, marca removidos
  main.py                  # orquestrador: corre todos os scrapers registados
sql/
  schema.sql               # esquema Postgres/Supabase (tabelas agencias/imoveis)
.github/workflows/
  ingest.yml                # cron diário via GitHub Actions
```

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # preencher SUPABASE_URL e SUPABASE_KEY
python -m src.main
```

## Antes de pôr em produção

1. Validar manualmente o scraper Century21 contra o site real (a extração
   aqui foi construída a partir de conteúdo já convertido em texto, não do
   HTML bruto — os seletores por padrão de link `/trouver_logement/detail/`
   são estáveis, mas vale a pena confirmar com uma inspeção rápida do DOM).
2. Completar `laforet_scraper.py` com o padrão real de URL dos anúncios
   individuais (inspecionar `view-source:` da página de listagem).
3. Verificar `robots.txt` de cada site antes de ativar o cron em produção.
4. Criar o projeto Supabase novo e aplicar `sql/schema.sql`.
