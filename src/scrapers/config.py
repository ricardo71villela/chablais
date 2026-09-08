"""Registo das agências-alvo, agrupadas por scraper/rede.

Para adicionar uma nova agência a uma rede já suportada, basta acrescentar
uma entrada AgencyTarget. Para uma rede nova simples (sem particularidades),
usar o GenericScraper + SiteConfig. Só criar um adapter à parte (ver
century21_scraper.py / laforet_scraper.py) quando o site tiver uma
particularidade que o genérico não cubra.
"""
import re

from src.scrapers.base import AgencyTarget
from src.scrapers.century21_scraper import Century21Scraper
from src.scrapers.laforet_scraper import LaforetScraper
from src.scrapers.generic_scraper import GenericScraper, SiteConfig

CENTURY21_TARGETS = [
    AgencyTarget(
        agencia_nome="CENTURY 21 Chablais-Léman Thonon",
        cidade="Thonon",
        listing_url="https://www.century21-chablais-leman-thonon.com/annonces/achat/",
        tipo_transacao="venda",
    ),
    AgencyTarget(
        agencia_nome="CENTURY 21 Chablais-Léman Thonon",
        cidade="Thonon",
        listing_url="https://www.century21-chablais-leman-thonon.com/annonces/location/",
        tipo_transacao="arrendamento",
    ),
    AgencyTarget(
        agencia_nome="CENTURY 21 Chablais Léman Évian",
        cidade="Evian",
        listing_url="https://www.century21-chablais-leman-evian.com/annonces/achat/",
        tipo_transacao="venda",
    ),
    AgencyTarget(
        agencia_nome="CENTURY 21 Chablais Léman Évian",
        cidade="Evian",
        listing_url="https://www.century21-chablais-leman-evian.com/annonces/location/",
        tipo_transacao="arrendamento",
    ),
]

LAFORET_TARGETS = [
    # nota: uma única página cobre Thonon + Évian + comunas vizinhas; o
    # scraper filtra internamente e só devolve Thonon/Évian (ver
    # laforet_scraper.py). O campo `cidade` aqui é só um valor de partida.
    AgencyTarget(
        agencia_nome="Laforêt Thonon-Évian",
        cidade="Thonon-Evian",
        listing_url="https://www.laforet.com/agence-immobiliere/thonon-evian/acheter",
        tipo_transacao="venda",
    ),
    AgencyTarget(
        agencia_nome="Laforêt Thonon-Évian",
        cidade="Thonon-Evian",
        listing_url="https://www.laforet.com/agence-immobiliere/thonon-evian/louer",
        tipo_transacao="arrendamento",
    ),
]

# --- Poirier Immobilier ----------------------------------------------------
# Confirmado: detail links em /vente/<id-cidade>/<tipo>/<id-slug>
# Cada cidade tem o seu próprio URL de listagem, sem paginação por page= —
# a página já mostra "Voir les X annonces" de uma vez (a confirmar em produção
# se há paginação por scroll/"carregar mais" que este scraper não capta).
POIRIER_CONFIG = SiteConfig(
    network_name="Poirier",
    detail_link_pattern=re.compile(r"/vente/\d+-[^/]+/[^/]+/\d+-[^/?#]+"),
    page_url_template=None,
)
POIRIER_TARGETS = [
    AgencyTarget(
        agencia_nome="Poirier Immobilier Thonon",
        cidade="Thonon",
        listing_url="https://www.poirier-immobilier.com/vente/6-thonon-les-bains/1",
        tipo_transacao="venda",
    ),
    AgencyTarget(
        agencia_nome="Poirier Immobilier Évian",
        cidade="Evian",
        listing_url="https://www.poirier-immobilier.com/vente/5-evian-les-bains/1",
        tipo_transacao="venda",
    ),
]

# --- Imogroup ---------------------------------------------------------------
# Confirmado: detail links em /fr/vente/<slug>/<ID-hexadecimal>
# ex: /fr/vente/appartement-3-pieces-thonon-les-bains-74200/6798CD9C05576143944643
# Listagem filtrada por tipo (site não parece ter uma vista "todos os tipos"
# por cidade) — cobre apartamentos e casas, os tipos mais comuns.
# ⚠️ Site com JS: o formulário de pesquisa já vem pré-preenchido pelo URL,
# mas os anúncios só aparecem depois de clicar em "Rechercher" — usa
# click_selector para simular isso automaticamente.
IMOGROUP_CONFIG = SiteConfig(
    network_name="Imogroup",
    detail_link_pattern=re.compile(r"/fr/vente/[^/?#]+-\d{4,5}/[A-Za-z0-9]{15,}"),
    page_url_template=None,  # a confirmar se há paginação além da 1ª página
    click_selector="button:has-text('Rechercher')",
)
IMOGROUP_TARGETS = [
    AgencyTarget(
        agencia_nome="Imogroup Thonon",
        cidade="Thonon",
        listing_url="https://www.imogroup-thonon-evian.com/fr/vente/appartement/thonon-les-bains/74200",
        tipo_transacao="venda",
    ),
    AgencyTarget(
        agencia_nome="Imogroup Thonon",
        cidade="Thonon",
        listing_url="https://www.imogroup-thonon-evian.com/fr/vente/maison/thonon-les-bains/74200",
        tipo_transacao="venda",
    ),
    AgencyTarget(
        agencia_nome="Imogroup Évian",
        cidade="Evian",
        listing_url="https://www.imogroup-thonon-evian.com/fr/vente/appartement/evian-les-bains/74500",
        tipo_transacao="venda",
    ),
    AgencyTarget(
        agencia_nome="Imogroup Évian",
        cidade="Evian",
        listing_url="https://www.imogroup-thonon-evian.com/fr/vente/maison/evian-les-bains/74500",
        tipo_transacao="venda",
    ),
]

# --- Square Habitat -----------------------------------------------------
# Confirmado: server-side (sem JS), mas a listagem por cidade mistura
# comunas vizinhas ("Appartements à proximité") — usa city_filter para só
# aceitar Thonon/Évian. Detail links: /square-habitat-des-savoie/annonces/
# biens/achat-ancien/<tipo>/<cidade-slug>/<uuid>, ou para o neuf:
# /annonces/programmes/achat-neuf/<cidade-slug>/<uuid>
SQUARE_HABITAT_CONFIG = SiteConfig(
    network_name="SquareHabitat",
    detail_link_pattern=re.compile(
        r"/square-habitat-des-savoie/annonces/biens/achat-ancien/[^/?#]+/[^/?#]+/[0-9a-f-]{36}"
        r"|/annonces/programmes/achat-neuf/[^/?#]+/[0-9a-f-]{36}"
    ),
    page_url_template=None,  # a confirmar se há paginação além da 1ª página
    city_filter={"thonon", "evian", "évian"},
)
SQUARE_HABITAT_TARGETS = [
    AgencyTarget(
        agencia_nome="Square Habitat Thonon",
        cidade="Thonon",
        listing_url="https://www.squarehabitat.fr/annonces/achat/bien/appartement/immobilier/auvergne-rhone-alpes/haute-savoie/thonon-les-bains-74200",
        tipo_transacao="venda",
    ),
    AgencyTarget(
        agencia_nome="Square Habitat Thonon",
        cidade="Thonon",
        listing_url="https://www.squarehabitat.fr/annonces/achat/bien/maison/immobilier/auvergne-rhone-alpes/haute-savoie/thonon-les-bains-74200",
        tipo_transacao="venda",
    ),
    AgencyTarget(
        agencia_nome="Square Habitat Évian",
        cidade="Evian",
        listing_url="https://www.squarehabitat.fr/annonces/achat/bien/appartement/immobilier/auvergne-rhone-alpes/haute-savoie/evian-les-bains-74500",
        tipo_transacao="venda",
    ),
    AgencyTarget(
        agencia_nome="Square Habitat Évian",
        cidade="Evian",
        listing_url="https://www.squarehabitat.fr/annonces/achat/bien/maison/immobilier/auvergne-rhone-alpes/haute-savoie/evian-les-bains-74500",
        tipo_transacao="venda",
    ),
]

# --- BARNES Léman -----------------------------------------------------
# Confirmado: server-side (sem JS). Detail links em
# /en/luxury-real-estate/<cidade-slug>/<tipo>/<slug>-<id>
# Nota: usa a versão inglesa do site (/en/) — a francesa tem URLs diferentes
# e não foi testada; a versão inglesa funciona bem e os dados são os mesmos.
BARNES_CONFIG = SiteConfig(
    network_name="Barnes",
    detail_link_pattern=re.compile(r"/en/luxury-real-estate/[^/?#]+/[^/?#]+/[^/?#]+-\d+"),
    page_url_template=None,  # ~14 resultados numa só página; a confirmar se há mais
)
BARNES_TARGETS = [
    AgencyTarget(
        agencia_nome="BARNES Léman Thonon",
        cidade="Thonon",
        listing_url="https://www.barnes-leman.com/en/luxury-real-estate/thonon-les-bains-74200/",
        tipo_transacao="venda",
    ),
    AgencyTarget(
        agencia_nome="BARNES Léman Évian",
        cidade="Evian",
        listing_url="https://www.barnes-leman.com/en/luxury-real-estate/evian-les-bains-74500/",
        tipo_transacao="venda",
    ),
]

# Cada entrada: (instância do scraper, lista de targets)
REGISTRY = [
    (Century21Scraper(), CENTURY21_TARGETS),
    (LaforetScraper(), LAFORET_TARGETS),
    (GenericScraper(POIRIER_CONFIG), POIRIER_TARGETS),
    (GenericScraper(IMOGROUP_CONFIG), IMOGROUP_TARGETS),
    (GenericScraper(SQUARE_HABITAT_CONFIG), SQUARE_HABITAT_TARGETS),
    (GenericScraper(BARNES_CONFIG), BARNES_TARGETS),
]
