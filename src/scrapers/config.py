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
    click_selector=[
        "button:has-text('Rechercher')",
        "input[value='Rechercher']",
        "input[value='RECHERCHER']",
        "[type=submit]",
        "text=Rechercher",
    ],
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

# --- Agence Barnoud -----------------------------------------------------
# Confirmado: server-side (sem JS). Detail links em
# /vente/<dep-id>-<dep-slug>/<cidade-id>-<cidade-slug>/<tipo>.../<id>-<slug>/
# Paginação: último segmento do URL é o nº de página; por agora só lê a
# primeira página (10-16 resultados) — a confirmar se vale a pena paginar.
BARNOUD_CONFIG = SiteConfig(
    network_name="Barnoud",
    detail_link_pattern=re.compile(r"/vente/\d+-[^/]+/\d+-[^/]+/.+/\d+-[^/?#]+"),
    page_url_template=None,
)
BARNOUD_TARGETS = [
    AgencyTarget(
        agencia_nome="Agence Barnoud Thonon",
        cidade="Thonon",
        listing_url="https://www.barnoud-immobilier.fr/vente/74-haute-savoie/1-thonon-les-bains/1",
        tipo_transacao="venda",
    ),
    AgencyTarget(
        agencia_nome="Agence Barnoud Évian",
        cidade="Evian",
        listing_url="https://www.barnoud-immobilier.fr/vente/74-haute-savoie/2-evian-les-bains/1",
        tipo_transacao="venda",
    ),
]

# --- Nestenn Évian-Bons -------------------------------------------------
# Confirmado: server-side (sem JS). Detail links terminam em "-ref-<id>"
# diretamente na raiz do domínio. A listagem cobre Thonon + Évian + comunas
# vizinhas (Neuvecelle, Publier, Lugrin, etc.) — usa city_filter.
NESTENN_CONFIG = SiteConfig(
    network_name="Nestenn",
    detail_link_pattern=re.compile(r"-ref-\d+$"),
    page_url_template="{base}?page={page}",
    city_filter={"thonon", "evian", "évian"},
)
NESTENN_TARGETS = [
    AgencyTarget(
        agencia_nome="Nestenn Évian",
        cidade="Evian",
        listing_url="https://immobilier-evian-les-bains.nestenn.com/achat-immobilier",
        tipo_transacao="venda",
    ),
]

# --- Dupraz Immobilier --------------------------------------------------
# Confirmado: server-side (sem JS). Detail links em
# /fiches/<codigo>_<id>/<slug>.html
# ⚠️ Listagem "Annonces par villes" filtra por cidade + tipo em separado
# (apartamento/casa) — o URL da Évian é construído por analogia ao de
# Thonon (mesmo padrão de slug), a confirmar na primeira corrida real.
DUPRAZ_CONFIG = SiteConfig(
    network_name="Dupraz",
    detail_link_pattern=re.compile(r"/fiches/[\d-]+_\d+/[^/?#]+\.html"),
    page_url_template=None,
)
DUPRAZ_TARGETS = [
    AgencyTarget(
        agencia_nome="Dupraz Immobilier Thonon",
        cidade="Thonon",
        listing_url="https://www.dupraz-immobilier.com/ville_bien/Thonon+Les+Bains__1__Vente/immobilier-thonon-les-bains.html",
        tipo_transacao="venda",
    ),
    AgencyTarget(
        agencia_nome="Dupraz Immobilier Thonon",
        cidade="Thonon",
        listing_url="https://www.dupraz-immobilier.com/ville_bien/Thonon+Les+Bains__2__Vente/immobilier-thonon-les-bains.html",
        tipo_transacao="venda",
    ),
    AgencyTarget(
        agencia_nome="Dupraz Immobilier Évian",
        cidade="Evian",
        listing_url="https://www.dupraz-immobilier.com/ville_bien/Evian+Les+Bains__1__Vente/immobilier-evian-les-bains.html",
        tipo_transacao="venda",
    ),
]

# --- TiT Immobilier -------------------------------------------------------
# Plataforma Apimo. Detail links em /fr/propriété/<id> (às vezes codificado
# como /fr/propri%C3%A9t%C3%A9/<id> — o regex cobre as duas formas).
# A listagem cobre todo o território (Abondance, Bernex, Publier, etc.) —
# usa city_filter para só aceitar Thonon/Évian.
TIT_CONFIG = SiteConfig(
    network_name="TiT",
    detail_link_pattern=re.compile(r"/fr/propri[^/]*/\d+"),
    page_url_template="{base}?page={page}",
    city_filter={"thonon", "evian", "évian"},
)
TIT_TARGETS = [
    AgencyTarget(
        agencia_nome="TiT Immobilier",
        cidade="Thonon",
        listing_url="https://tit-immobilier.com/fr/ventes",
        tipo_transacao="venda",
    ),
]

# --- Cabinet Greneche -----------------------------------------------------
# Plataforma Apimo (mesma família do TiT). Server-side, sem JS. Detail
# links em /fr/propriete/<tipo>+<transacao>+<cidade>+<slug>+<id>
# A listagem cobre Sciez, Thollon, Publier, etc. — usa city_filter.
GRENECHE_CONFIG = SiteConfig(
    network_name="Greneche",
    detail_link_pattern=re.compile(r"/fr/propriete/[^/?#]+"),
    page_url_template="{base}?page={page}",
    city_filter={"thonon", "evian", "évian"},
)
GRENECHE_TARGETS = [
    AgencyTarget(
        agencia_nome="Cabinet Greneche",
        cidade="Evian",
        listing_url="https://grenecheimmo.fr/fr/ventes-2",
        tipo_transacao="venda",
    ),
]

# --- Agence Lehmann -------------------------------------------------------
# Mesma plataforma Apimo que a Greneche e a TiT. Server-side, sem JS.
GRENECHE_DETAIL_RE = re.compile(r"/fr/propriete/[^/?#]+")  # reutilizado
LEHMANN_CONFIG = SiteConfig(
    network_name="Lehmann",
    detail_link_pattern=GRENECHE_DETAIL_RE,
    page_url_template="{base}?page={page}",
    city_filter={"thonon", "evian", "évian"},
)
LEHMANN_TARGETS = [
    AgencyTarget(
        agencia_nome="Agence Lehmann",
        cidade="Evian",
        listing_url="https://lehmann-immo.com/fr/acheter",
        tipo_transacao="venda",
    ),
]

# --- Leman Property --------------------------------------------------------
# WordPress/WPML, server-side. Páginas já filtradas por cidade — sem
# necessidade de city_filter. Detail links em
# /vente/<tipo>/<cidade-slug>/<slug>/
LEMAN_PROPERTY_CONFIG = SiteConfig(
    network_name="LemanProperty",
    detail_link_pattern=re.compile(r"/vente/[a-z]+/[^/]+/[^/?#]+/"),
    page_url_template=None,  # a confirmar se há paginação além da 1ª página
)
LEMAN_PROPERTY_TARGETS = [
    AgencyTarget(
        agencia_nome="Leman Property Thonon",
        cidade="Thonon",
        listing_url="https://www.leman-property.com/acheter/thonon-les-bains/",
        tipo_transacao="venda",
    ),
    AgencyTarget(
        agencia_nome="Leman Property Évian",
        cidade="Evian",
        listing_url="https://www.leman-property.com/acheter/evian-les-bains/",
        tipo_transacao="venda",
    ),
]

# --- Evian Sotheby's International Realty ----------------------------------
# Server-side. Listagem geral mistura Sciez, Chens-sur-Léman, Nernier, etc.
# — usa city_filter. ⚠️ Paginação por "Load more" (AJAX) — só a 1ª página
# (~10 mais recentes) é capturada por agora.
SOTHEBYS_CONFIG = SiteConfig(
    network_name="EvianSothebys",
    detail_link_pattern=re.compile(r"/en/annonces/ref-[^/]+/[^/?#]+"),
    page_url_template=None,
    city_filter={"thonon", "évian", "evian"},
)
SOTHEBYS_TARGETS = [
    AgencyTarget(
        agencia_nome="Evian Sotheby's International Realty",
        cidade="Evian",
        listing_url="https://www.evian-sothebysrealty.com/en/annonces/",
        tipo_transacao="venda",
    ),
]

# --- A&P Immobilier ------------------------------------------------------
# Confirmado: server-side. Detail links em /vente/1-thonon-les-bains/<tipo>/
# .../<id>-<slug>/ (sem segmento de departamento, ao contrário da Barnoud).
AP_CONFIG = SiteConfig(
    network_name="AeP",
    detail_link_pattern=re.compile(r"/vente/\d+-[^/]+/.+/\d+-[^/?#]+"),
    page_url_template=None,
)
AP_TARGETS = [
    AgencyTarget(
        agencia_nome="A&P Immobilier",
        cidade="Thonon",
        listing_url="https://www.immobilierapi.com/vente/1-thonon-les-bains/1",
        tipo_transacao="venda",
    ),
]

# --- Christelle Vannier Immobilier -----------------------------------------
# Mesma plataforma Apimo (Greneche/Lehmann). Listagem mistura Bellevaux,
# Allinges, Féternes, Cervens — usa city_filter.
VANNIER_CONFIG = SiteConfig(
    network_name="Vannier",
    detail_link_pattern=GRENECHE_DETAIL_RE,
    page_url_template="{base}?page={page}",
    city_filter={"thonon", "evian", "évian"},
)
VANNIER_TARGETS = [
    AgencyTarget(
        agencia_nome="Christelle Vannier Immobilier",
        cidade="Thonon",
        listing_url="https://cvannier-immobilier.com/fr/vente",
        tipo_transacao="venda",
    ),
]

# --- Ripaille Immobilier --------------------------------------------------
# WordPress simples, server-side. Site pequeno, sem preço/superfície
# publicados na maioria dos cartões — os campos ficam a None quando não há
# essa informação (não é um erro do scraper). ⚠️ A listagem mistura biens
# "en ce moment" (à venda) e "vendues" (vendidos) sem distinção clara no
# link em si — pode incluir alguns já vendidos.
RIPAILLE_CONFIG = SiteConfig(
    network_name="Ripaille",
    detail_link_pattern=re.compile(r"/portfolio/[^/?#]+/?$"),
    page_url_template=None,
)
RIPAILLE_TARGETS = [
    AgencyTarget(
        agencia_nome="Ripaille Immobilier",
        cidade="Thonon",
        listing_url="https://www.ripaille-immobilier.com/biens/",
        tipo_transacao="venda",
    ),
]

# --- Peillex Gestion --------------------------------------------------------
# ⚠️ Mesma plataforma problemática do Imogroup (JS + botão "Rechercher"),
# e ao contrário das outras agências, NUNCA consegui ver um anúncio real
# desta agência (nem sequer em texto de resultados de pesquisa) — o padrão
# de link abaixo é uma estimativa, não uma confirmação. Se a primeira
# corrida der 0 resultados, os ficheiros em debug_artifacts/ (screenshot +
# pedidos de rede) vão dizer-nos o padrão real a usar.
PEILLEX_CONFIG = SiteConfig(
    network_name="Peillex",
    detail_link_pattern=re.compile(r"/vente/[^/]+/[^/]+/\d{5}/[^/?#]+"),
    page_url_template=None,
    click_selector=[
        "button:has-text('Rechercher')",
        "input[value='Rechercher']",
        "input[value='RECHERCHER']",
        "[type=submit]",
        "text=Rechercher",
    ],
)
PEILLEX_TARGETS = [
    AgencyTarget(
        agencia_nome="Peillex Gestion",
        cidade="Thonon",
        listing_url="https://www.groupe-peillex.fr/vente/appartement/thonon-les-bains/74200",
        tipo_transacao="venda",
    ),
    AgencyTarget(
        agencia_nome="Peillex Gestion",
        cidade="Thonon",
        listing_url="https://www.groupe-peillex.fr/vente/maison/thonon-les-bains/74200",
        tipo_transacao="venda",
    ),
]

# --- Cap Terrains Immo ------------------------------------------------------
# Confirmado: detail links em /bien/<slug>-<id>/. WordPress, provavelmente
# server-side (à parte da minha própria pesquisa ter sido bloqueada uma vez
# — pode ser um bloqueio pontual, o fetch_smart tenta na mesma o caminho
# rápido primeiro).
CAP_TERRAINS_CONFIG = SiteConfig(
    network_name="CapTerrains",
    detail_link_pattern=re.compile(r"/bien/[^/?#]+-\d+/?"),
    page_url_template=None,
)
CAP_TERRAINS_TARGETS = [
    AgencyTarget(
        agencia_nome="Cap Terrains Immo",
        cidade="Thonon",
        listing_url="https://capterrainsimmo.fr/appartements/",
        tipo_transacao="venda",
    ),
    AgencyTarget(
        agencia_nome="Cap Terrains Immo",
        cidade="Thonon",
        listing_url="https://capterrainsimmo.fr/maisons/",
        tipo_transacao="venda",
    ),
    AgencyTarget(
        agencia_nome="Cap Terrains Immo",
        cidade="Thonon",
        listing_url="https://capterrainsimmo.fr/terrains/",
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
    (GenericScraper(BARNOUD_CONFIG), BARNOUD_TARGETS),
    (GenericScraper(NESTENN_CONFIG), NESTENN_TARGETS),
    (GenericScraper(DUPRAZ_CONFIG), DUPRAZ_TARGETS),
    (GenericScraper(TIT_CONFIG), TIT_TARGETS),
    (GenericScraper(GRENECHE_CONFIG), GRENECHE_TARGETS),
    (GenericScraper(LEHMANN_CONFIG), LEHMANN_TARGETS),
    (GenericScraper(LEMAN_PROPERTY_CONFIG), LEMAN_PROPERTY_TARGETS),
    (GenericScraper(SOTHEBYS_CONFIG), SOTHEBYS_TARGETS),
    (GenericScraper(AP_CONFIG), AP_TARGETS),
    (GenericScraper(VANNIER_CONFIG), VANNIER_TARGETS),
    (GenericScraper(RIPAILLE_CONFIG), RIPAILLE_TARGETS),
    (GenericScraper(PEILLEX_CONFIG), PEILLEX_TARGETS),
    (GenericScraper(CAP_TERRAINS_CONFIG), CAP_TERRAINS_TARGETS),
]
