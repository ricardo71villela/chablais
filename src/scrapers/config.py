"""Registo das agências-alvo, agrupadas por scraper/rede.

Para adicionar uma nova agência a uma rede já suportada, basta acrescentar
uma entrada AgencyTarget. Para uma rede nova, criar um adapter (ver
century21_scraper.py como referência) e registar aqui.
"""
from src.scrapers.base import AgencyTarget
from src.scrapers.century21_scraper import Century21Scraper
from src.scrapers.laforet_scraper import LaforetScraper

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
    AgencyTarget(
        agencia_nome="Laforêt Thonon-Évian",
        cidade="Thonon",  # nota: esta página cobre Thonon + Évian, ver stub
        listing_url="https://www.laforet.com/agence-immobiliere/thonon-evian/acheter",
        tipo_transacao="venda",
    ),
]

# Cada entrada: (instância do scraper, lista de targets)
REGISTRY = [
    (Century21Scraper(), CENTURY21_TARGETS),
    (LaforetScraper(), LAFORET_TARGETS),  # ainda lança NotImplementedError
]
