"""Interface comum a todos os scrapers de agência + helpers de extração.

Nota de confidencialidade: o User-Agent usado aqui é genérico de propósito —
nunca incluir o nome do projeto, da agência de origem (DECORDIER) ou qualquer
identificador que ligue os pedidos HTTP a este projeto.
"""
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

from src.models import Listing

GENERIC_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

REQUEST_DELAY_SECONDS = 1.5  # rate-limiting educado — não sobrecarregar os sites-alvo


def fetch_html(url: str) -> BeautifulSoup:
    """Descarrega uma página e devolve o BeautifulSoup. Aplica um atraso
    fixo para não bombardear o site (ver REQUEST_DELAY_SECONDS)."""
    resp = requests.get(url, headers={"User-Agent": GENERIC_USER_AGENT}, timeout=20)
    resp.raise_for_status()
    time.sleep(REQUEST_DELAY_SECONDS)
    return BeautifulSoup(resp.text, "html.parser")


# --- Helpers de extração por regex (preço, superfície, divisões) ----------

PRICE_RE = re.compile(r"([\d\s]{3,})\s*€")
SURFACE_RE = re.compile(r"([\d,.]+)\s*m[²2]")
ROOMS_RE = re.compile(r"(\d+)\s*pi[eè]ces?", re.IGNORECASE)
BEDROOMS_RE = re.compile(r"(\d+)\s*chambres?", re.IGNORECASE)
REF_RE = re.compile(r"[Rr][ée]f\s*:?\s*(\S+)")


def extract_price(text: str) -> str | None:
    m = PRICE_RE.search(text)
    return m.group(1).replace(" ", "").strip() if m else None


def extract_surface(text: str) -> str | None:
    m = SURFACE_RE.search(text)
    return m.group(1).replace(",", ".") if m else None


def extract_rooms(text: str) -> int | None:
    m = ROOMS_RE.search(text)
    return int(m.group(1)) if m else None


def extract_bedrooms(text: str) -> int | None:
    m = BEDROOMS_RE.search(text)
    return int(m.group(1)) if m else None


def extract_ref(text: str) -> str | None:
    m = REF_RE.search(text)
    return m.group(1) if m else None


@dataclass
class AgencyTarget:
    """Configuração de uma agência a fazer scraping (uma entrada por
    cidade/agência, mesmo dentro da mesma rede)."""

    agencia_nome: str
    cidade: str          # 'Thonon' | 'Evian'
    listing_url: str
    tipo_transacao: str = "venda"


class AgencyScraper(ABC):
    """Cada rede/site implementa esta interface."""

    #: nome da rede, usado apenas para logging (nunca em nomes de recursos
    #: publicamente visíveis, ver nota de confidencialidade no README)
    network_name: str = "generico"

    @abstractmethod
    def fetch_listings(self, target: AgencyTarget) -> list[Listing]:
        """Devolve a lista de imóveis encontrados para esta agência/cidade."""
        raise NotImplementedError
