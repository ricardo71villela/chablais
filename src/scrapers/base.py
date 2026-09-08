"""Interface comum a todos os scrapers de agência + helpers de extração.

Nota de confidencialidade: o User-Agent usado aqui é genérico de propósito —
nunca incluir o nome do projeto, da agência de origem (DECORDIER) ou qualquer
identificador que ligue os pedidos HTTP a este projeto.
"""
import logging
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

from src.models import Listing

log = logging.getLogger(__name__)

GENERIC_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

REQUEST_DELAY_SECONDS = 1.5  # rate-limiting educado — não sobrecarregar os sites-alvo


def fetch_html(url: str) -> BeautifulSoup:
    """Descarrega uma página e devolve o BeautifulSoup. Aplica um atraso
    fixo para não bombardear o site (ver REQUEST_DELAY_SECONDS).

    Usa apenas um pedido HTTP simples — não executa JavaScript. Para sites
    que carregam os anúncios via JavaScript (ex. Laforêt), usar
    fetch_html_rendered() em vez desta."""
    resp = requests.get(url, headers={"User-Agent": GENERIC_USER_AGENT}, timeout=20)
    resp.raise_for_status()
    time.sleep(REQUEST_DELAY_SECONDS)
    return BeautifulSoup(resp.text, "html.parser")


def fetch_html_rendered(
    url: str, wait_selector: str | None = None, click_selector: str | None = None
) -> BeautifulSoup:
    """Descarrega uma página usando um browser real (Playwright/Chromium),
    para sites cujo conteúdo é injetado por JavaScript depois do carregamento
    inicial (ex. Laforêt). Mais lento que fetch_html — só usar quando
    necessário.

    `wait_selector`: um seletor CSS a esperar aparecer antes de ler o HTML
    (ex. um link de anúncio), para garantir que o JavaScript já correu.

    `click_selector`: um seletor CSS a clicar depois de fechar os cookies e
    antes de esperar pelo `wait_selector` — para sites cuja pesquisa só
    corre depois de um clique num botão (ex. "Rechercher"), mesmo quando os
    filtros já vêm pré-preenchidos pelo URL.

    Usa wait_until="domcontentloaded" em vez de "networkidle" — muitos sites
    têm scripts de analytics/publicidade que mantêm a rede sempre ativa e
    nunca deixam o "networkidle" disparar, mesmo com o conteúdo principal já
    carregado. O wait_for_selector a seguir garante que esperamos pelo
    conteúdo real, não apenas pelo HTML inicial.

    Tenta também fechar banners de cookies comuns (OneTrust, Axeptio, etc.),
    já que alguns sites só carregam o resto da página depois de uma
    interação do utilizador com esse banner.
    """
    from playwright.sync_api import sync_playwright

    COOKIE_BUTTON_SELECTORS = [
        "#onetrust-accept-btn-handler",
        "button:has-text('Accepter')",
        "button:has-text(\"J'accepte\")",
        "button:has-text('Tout accepter')",
        ".axeptio_widget button",
        "#axeptio_btn_acceptAll",
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=GENERIC_USER_AGENT)
        page.goto(url, timeout=45000, wait_until="domcontentloaded")

        for selector in COOKIE_BUTTON_SELECTORS:
            try:
                page.click(selector, timeout=2000)
                page.wait_for_timeout(500)
                break
            except Exception:
                continue  # este banner não apareceu, tenta o próximo

        if click_selector:
            try:
                page.click(click_selector, timeout=5000)
                page.wait_for_timeout(1000)
            except Exception as e:
                log.info("fetch_html_rendered(%s): falhou a clicar em '%s' (%s)", url, click_selector, e)

        if wait_selector:
            try:
                page.wait_for_selector(wait_selector, timeout=20000)
            except Exception:
                pass  # segue com o que já carregou, mesmo que o seletor não apareça
        else:
            page.wait_for_timeout(3000)  # dá tempo ao JS correr quando não há seletor específico

        html = page.content()
        if wait_selector:
            count = page.locator(wait_selector).count()
            log.info(
                "fetch_html_rendered(%s): %d elementos a corresponder a '%s', HTML com %d chars, título='%s'",
                url, count, wait_selector, len(html), page.title(),
            )
        browser.close()
    time.sleep(REQUEST_DELAY_SECONDS)
    return BeautifulSoup(html, "html.parser")


def fetch_smart(
    url: str,
    detail_link_pattern: re.Pattern,
    wait_selector: str | None = None,
    click_selector: str | None = None,
) -> BeautifulSoup:
    """Tenta primeiro um pedido HTTP simples (rápido); só recorre ao
    Playwright (mais lento) se essa primeira tentativa não encontrar nenhum
    link de anúncio a corresponder a `detail_link_pattern`.

    Isto evita ter de decidir antecipadamente, agência a agência, se o site
    precisa de JavaScript ou não — o próprio código deteta e adapta-se. Usar
    esta função em vez de escolher fetch_html/fetch_html_rendered à mão em
    cada scraper novo.
    """
    try:
        soup = fetch_html(url)
        if any(detail_link_pattern.search(a["href"]) for a in soup.find_all("a", href=True)):
            return soup
        log.info(
            "fetch_smart(%s): pedido simples não encontrou anúncios — a tentar com Playwright",
            url,
        )
    except Exception as e:
        log.info("fetch_smart(%s): pedido simples falhou (%s) — a tentar com Playwright", url, e)

    return fetch_html_rendered(url, wait_selector=wait_selector, click_selector=click_selector)


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
