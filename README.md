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
  ingest.yml                # cron mensal via GitHub Actions
```

## Setup

```bash
pip install -r requirements.txt
playwright install chromium   # necessário para o scraper do Laforêt (site com JS)
cp .env.example .env   # preencher SUPABASE_URL e SUPABASE_KEY
python -m src.main
```

## Deteção automática: JavaScript ou não?

Cada scraper novo deve usar `fetch_smart(url, DETAIL_LINK_RE, wait_selector=...)`
em vez de escolher `fetch_html`/`fetch_html_rendered` à mão. Esta função tenta
primeiro um pedido HTTP simples (rápido); só recorre ao Playwright (mais lento)
se essa tentativa não encontrar nenhum link de anúncio. Isto evita ter de
adivinhar, site a site, se o conteúdo é carregado por JavaScript ou não — o
próprio código deteta isso e adapta-se, o mesmo mecanismo que resolveu o caso
do Laforêt.

## Antes de adicionar uma agência nova

1. Confirmar o padrão de URL dos anúncios individuais e da listagem
   (inspecionar `view-source:` da página, ou pedir para eu verificar).
2. Escrever o `DETAIL_LINK_RE` e usar `fetch_smart` — não é preciso decidir
   antecipadamente se precisa de Playwright.
3. Verificar `robots.txt` do site antes de ativar em produção.
4. Testar localmente (ou via GitHub Actions) antes de dar como concluído.
