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


# --- Helpers de extração por regex --------------------------------------

PRICE_RE = re.compile(r"([\d\s]{3,})\s*€")
SURFACE_RE = re.compile(r"([\d,.]+)\s*m[²2]")
ROOMS_RE = re.compile(r"(\d+)\s*pi[eè]ces?", re.IGNORECASE)
BEDROOMS_RE = re.compile(r"(\d+)\s*chambres?", re.IGNORECASE)
REF_RE = re.compile(r"[Rr][ée]f\s*:?\s*(\S+)")
DPE_RE = re.compile(r"DPE\s*[:\-]?\s*classe\s*([A-G])|classe\s*([A-G])\s*DPE", re.IGNORECASE)
ANO_CONSTRUCAO_RE = re.compile(
    r"(?:construite?|construction|b[âa]tie?)\s*(?:en)?\s*:?\s*(\d{4})", re.IGNORECASE
)

# Palavras-chave de comodidades a procurar no texto do anúncio (case-insensitive).
# O valor devolvido é a forma normalizada em português para gravar na base de dados.
COMODIDADES_KEYWORDS = {
    "garage": "Garagem",
    "parking": "Parking",
    "piscine": "Piscina",
    "terrasse": "Terraço",
    "balcon": "Varanda",
    "cave": "Cave",
    "ascenseur": "Elevador",
    "jardin": "Jardim",
    "chemin[ée]e": "Lareira",
    "acc[èe]s handicap[ée]": "Acesso mobilidade reduzida",
    "climatisation": "Ar condicionado",
    "meubl[ée]": "Mobilado",
}


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


def extract_dpe(text: str) -> str | None:
    m = DPE_RE.search(text)
    if not m:
        return None
    return (m.group(1) or m.group(2) or "").upper() or None


def extract_ano_construcao(text: str) -> int | None:
    m = ANO_CONSTRUCAO_RE.search(text)
    if not m:
        return None
    ano = int(m.group(1))
    return ano if 1800 <= ano <= 2100 else None


def extract_comodidades(text: str) -> list[str]:
    found = []
    for pattern, label in COMODIDADES_KEYWORDS.items():
        if re.search(pattern, text, re.IGNORECASE):
            found.append(label)
    return found


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
