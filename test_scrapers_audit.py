"""Testes da auditoria agência-a-agência de 13/set/2026.

Reproduz os três bugs reais encontrados (confirmados contra o HTML ao vivo
de várias agências, e no caso do bug 3 contra a corrida real do Ricardo) e
confirma que ficam corrigidos:

1. Separador de milhares com espaço especial (\xa0 /  ) fazia o preço/
   superfície ficar sempre vazio, mesmo quando o texto extraído já tinha o
   valor certo — a conversão para número (float()) falhava em silêncio.
   Confirmado em produção: Cabinet Greneche, Nestenn.

2. O código antigo parava sempre no primeiro ancestral article/li/div do
   link do anúncio, mesmo quando esse ancestral era só um wrapper da
   fotografia sem preço nenhum lá dentro — o preço só aparecia vários
   níveis acima. Confirmado em produção: Poirier, Cap Terrains, Century21,
   Dupraz Immobilier (6 de 18 agências tinham este problema).

3. Uma falha a obter uma página a meio da paginação (ex. Playwright sem o
   browser instalado, acionado quando fetch_smart recorre a ele por não
   encontrar mais anúncios em HTTP simples — o fim normal da paginação)
   fazia fetch_listings() levantar exceção e perder TODOS os imóveis já
   recolhidos nas páginas anteriores, porque main.py descarta a corrida
   inteira dessa agência quando isso acontece. Confirmado na corrida real
   de 13/set do Ricardo: explicava sozinho o preço em falta a 100% em 5
   agências inteiras de página única (Cabinet Greneche, Agence Lehmann,
   TiT Immobilier, Christelle Vannier Immobilier, Nestenn Évian), mesmo já
   com os bugs 1 e 2 corrigidos.

Corre com: python3 test_scrapers_audit.py
"""
import re
import sys
from unittest.mock import patch

from bs4 import BeautifulSoup

sys.path.insert(0, ".")

from src.normalize import to_float, normalize
from src.scrapers.base import (
    AgencyTarget,
    climb_to_content_block,
    extract_price,
    extract_terrain_surface,
)
from src.scrapers.century21_scraper import Century21Scraper
from src.scrapers.generic_scraper import GenericScraper, SiteConfig
from src.scrapers.laforet_scraper import LaforetScraper
from src.models import Listing

FALHAS = []


def check(nome, condicao, detalhe=""):
    status = "OK" if condicao else "FALHOU"
    print(f"[{status}] {nome} {detalhe}")
    if not condicao:
        FALHAS.append(nome)


# --- Bug 1: separador de milhares com espaço especial -----------------------

def test_to_float_espaco_insecavel():
    # \xa0 (non-breaking space) e   (narrow no-break space) são usados
    # por muitos sites franceses em vez do espaço normal.
    check("to_float com \\xa0", to_float("315\xa0000") == 315000.0)
    check("to_float com \\u202f", to_float("602 500") == 602500.0)
    check("to_float com espaço normal (continua a funcionar)", to_float("315 000") == 315000.0)
    check("to_float com vírgula decimal", to_float("124,11") == 124.11)


def test_extract_price_espaco_insecavel():
    texto = "Vente 315 000 € Évian-les-Bains"
    preco_raw = extract_price(texto)
    check(
        "extract_price limpa espaço insecável",
        preco_raw is not None and to_float(preco_raw) == 315000.0,
        f"(preco_raw={preco_raw!r})",
    )


def test_extract_terrain_surface_espaco_insecavel():
    texto = "Terrain de 1 200 m² constructible"
    raw = extract_terrain_surface(texto)
    check(
        "extract_terrain_surface limpa espaço insecável",
        raw is not None and to_float(raw) == 1200.0,
        f"(raw={raw!r})",
    )


def test_normalize_end_to_end_espaco_insecavel():
    # Reproduz exatamente o caso real da Cabinet Greneche: o extrator já
    # encontra o preço certo no texto, mas antes da correção normalize()
    # devolvia None porque float() rejeitava o espaço insecável.
    listing = Listing(
        agencia_nome="Cabinet Greneche",
        cidade="Evian",
        url_anuncio="https://example.com/1",
        tipo_transacao="venda",
        preco_raw="315 000",
    )
    norm = normalize(listing)
    check("normalize() não perde o preço com espaço insecável", norm["preco"] == 315000.0)


# --- Bug 2: bloco de texto demasiado estreito (find_parent parava cedo) ----

def _card_html_preco_longe():
    """Reproduz a estrutura real da Poirier/Cap Terrains/Century21/Dupraz:
    o link do anúncio está dentro de um <div> pequeno (só a foto), e o
    preço só aparece vários níveis acima."""
    return """
    <div class="grid">
      <div class="item__block">
        <div class="item__content">
          <p>Thonon-les-Bains Appartement 3 pièces 76 m² 260 000 €</p>
          <div class="links-group">
            <div class="links-group__wrapper">
              <a class="cta" href="/vente/6-thonon/appartement/123-bem">Voir le bien</a>
            </div>
          </div>
        </div>
      </div>
      <div class="item__block">
        <div class="item__content">
          <p>Outro imóvel, não deve aparecer aqui — 999 999 €</p>
          <a href="/vente/6-thonon/appartement/999-outro">Voir</a>
        </div>
      </div>
    </div>
    """


def test_climb_to_content_block_encontra_preco_longe():
    soup = BeautifulSoup(_card_html_preco_longe(), "html.parser")
    a = soup.find("a", href=lambda h: h and "123-bem" in h)
    block, text = climb_to_content_block(a)
    check(
        "climb_to_content_block sobe até encontrar o preço",
        "260 000 €" in text,
        f"(texto={text[:60]!r}...)",
    )
    check(
        "climb_to_content_block NÃO mistura com o cartão vizinho",
        "999 999" not in text,
        f"(texto={text[:80]!r}...)",
    )


def test_climb_to_content_block_reserva_quando_nunca_encontra():
    # Nenhum ancestral tem "€" (ex. anúncio sem preço publicado, como a
    # Ripaille) — deve cair no comportamento antigo (article/li/div mais
    # próximo), não rebentar nem devolver vazio por acidente.
    html = '<article><div><a href="/x">Voir</a></div></article>'
    soup = BeautifulSoup(html, "html.parser")
    a = soup.find("a")
    block, text = climb_to_content_block(a)
    check(
        "climb_to_content_block tem reserva quando não há preço em lado nenhum",
        block.name == "div",
    )


def test_climb_to_content_block_preco_perto_continua_rapido():
    # Caso já funcionava antes (preço no primeiro div) — confirmar que não
    # regride nem sobe desnecessariamente.
    html = """
    <div class="card">
      <a href="/x">Casa 495 000 €</a>
    </div>
    """
    soup = BeautifulSoup(html, "html.parser")
    a = soup.find("a")
    block, text = climb_to_content_block(a)
    check("climb_to_content_block para no nível certo quando já está perto", "495 000" in text)


# --- Bug 3: falha a meio da paginação perdia as páginas já recolhidas -----

def _pagina_1_com_um_imovel(href="/anuncio/1"):
    """Uma única página com 1 imóvel — preço e superfície separados por
    texto, como acontece sempre nos blocos reais (nunca ficam colados um
    ao outro; ver bloco real do Cabinet Greneche em greneche_real.html)."""
    return BeautifulSoup(
        f'<div><a href="{href}">Thonon Vente 300 000 € '
        f'Bel appartement lumineux 50 m2</a></div>',
        "html.parser",
    )


def test_generic_scraper_preserva_paginas_ja_recolhidas():
    config = SiteConfig(
        network_name="Teste",
        detail_link_pattern=re.compile(r"/anuncio/\d+"),
        page_url_template="{base}?page={page}",
    )
    target = AgencyTarget(
        agencia_nome="Agencia Teste", cidade="Thonon", listing_url="https://exemplo.fr/lista"
    )
    chamadas = {"n": 0}

    def fetch_smart_fake(url, pattern, **kwargs):
        chamadas["n"] += 1
        if chamadas["n"] == 1:
            return _pagina_1_com_um_imovel()
        # Simula o crash real do Playwright (browser não instalado) que
        # acontece quando fetch_smart cai no fallback ao chegar ao fim
        # normal da paginação.
        raise RuntimeError("BrowserType.launch: Executable doesn't exist (simulado)")

    with patch("src.scrapers.generic_scraper.fetch_smart", side_effect=fetch_smart_fake):
        listings = GenericScraper(config).fetch_listings(target)

    check(
        "GenericScraper preserva imóveis da página 1 quando a página 2 falha",
        len(listings) == 1 and listings[0].preco_raw == "300000",
        f"(listings={len(listings)}, preco_raw={listings[0].preco_raw if listings else None!r})",
    )


def test_laforet_scraper_preserva_paginas_ja_recolhidas():
    target = AgencyTarget(
        agencia_nome="Laforet Teste",
        cidade="Thonon",
        listing_url="https://www.laforet.com/agence-immobiliere/thonon-evian/acheter",
    )
    href = "/agence-immobiliere/thonon-evian/acheter/thonon-les-bains/appartement-1"
    pagina_1 = BeautifulSoup(
        f'<div><a href="{href}">THONON-LES-BAINS (74200) Vente 300 000 € '
        f"Bel appartement lumineux 50 m2</a></div>",
        "html.parser",
    )
    chamadas = {"n": 0}

    def fetch_smart_fake(url, pattern, **kwargs):
        chamadas["n"] += 1
        if chamadas["n"] == 1:
            return pagina_1
        raise RuntimeError("BrowserType.launch: Executable doesn't exist (simulado)")

    with patch("src.scrapers.laforet_scraper.fetch_smart", side_effect=fetch_smart_fake):
        listings = LaforetScraper().fetch_listings(target)

    check(
        "LaforetScraper preserva imóveis da página 1 quando a página 2 falha",
        len(listings) == 1 and listings[0].preco_raw == "300000",
        f"(listings={len(listings)}, preco_raw={listings[0].preco_raw if listings else None!r})",
    )


def test_century21_scraper_preserva_paginas_ja_recolhidas():
    target = AgencyTarget(
        agencia_nome="Century21 Teste",
        cidade="Thonon",
        listing_url="https://www.century21-teste.com/annonces/achat",
    )
    href = "/trouver_logement/detail/12345/"
    pagina_1 = BeautifulSoup(
        f'<div><a href="{href}">Thonon Vente 300 000 € '
        f"Bel appartement lumineux 50 m2</a></div>",
        "html.parser",
    )
    chamadas = {"n": 0}

    def fetch_smart_fake(url, pattern, **kwargs):
        chamadas["n"] += 1
        if chamadas["n"] == 1:
            return pagina_1
        raise RuntimeError("BrowserType.launch: Executable doesn't exist (simulado)")

    with patch("src.scrapers.century21_scraper.fetch_smart", side_effect=fetch_smart_fake):
        listings = Century21Scraper().fetch_listings(target)

    check(
        "Century21Scraper preserva imóveis da página 1 quando a página 2 falha",
        len(listings) == 1 and listings[0].preco_raw == "300000",
        f"(listings={len(listings)}, preco_raw={listings[0].preco_raw if listings else None!r})",
    )


if __name__ == "__main__":
    test_to_float_espaco_insecavel()
    test_extract_price_espaco_insecavel()
    test_extract_terrain_surface_espaco_insecavel()
    test_normalize_end_to_end_espaco_insecavel()
    test_climb_to_content_block_encontra_preco_longe()
    test_climb_to_content_block_reserva_quando_nunca_encontra()
    test_climb_to_content_block_preco_perto_continua_rapido()
    test_generic_scraper_preserva_paginas_ja_recolhidas()
    test_laforet_scraper_preserva_paginas_ja_recolhidas()
    test_century21_scraper_preserva_paginas_ja_recolhidas()

    print()
    if FALHAS:
        print(f"FALHARAM {len(FALHAS)} TESTE(S): {FALHAS}")
        sys.exit(1)
    print("TODOS OS TESTES PASSARAM")
