"""Scraper genérico, configurável por site — evita reescrever a mesma lógica
(agrupar links duplicados, extrair preço/superfície/comodidades, paginar)
para cada agência independente.

Como usar: criar uma instância de SiteConfig com o padrão de link dos
anúncios dessa agência, e registá-la em config.py. Só é preciso escrever um
scraper à parte (como century21_scraper.py ou laforet_scraper.py) quando o
site tiver uma particularidade que este genérico não cubra (ex. filtro de
comunas vizinhas, paginação num formato muito específico).
"""
import re
from dataclasses import dataclass
from urllib.parse import urljoin

from src.models import Listing
from src.scrapers.base import (
    AgencyScraper,
    AgencyTarget,
    extract_ano_construcao,
    extract_bedrooms,
    extract_comodidades,
    extract_dpe,
    extract_price,
    extract_ref,
    extract_rooms,
    extract_surface,
    fetch_smart,
)

MAX_PAGES = 15


@dataclass
class SiteConfig:
    network_name: str
    detail_link_pattern: re.Pattern
    #: como construir o URL da página N (N>=2). Usa "{base}" e "{page}".
    #: Deixar a None desativa a paginação (só lê a primeira página).
    page_url_template: str | None = "{base}?page={page}"
    wait_selector: str | None = None
    #: seletor a clicar antes de esperar pelos anúncios (ex. botão
    #: "Rechercher"), para sites cuja pesquisa só corre depois de um clique.
    click_selector: str | None = None
    #: se o site mistura comunas vizinhas na mesma listagem (ex. "Achat
    #: appartement Thonon" também mostra Sciez, Cranves-Sales...), passar
    #: aqui as palavras (minúsculas) que têm de aparecer no texto do bloco
    #: para o imóvel ser aceite. None desativa o filtro.
    city_filter: set[str] | None = None


class GenericScraper(AgencyScraper):
    def __init__(self, config: SiteConfig):
        self.config = config
        self.network_name = config.network_name

    def fetch_listings(self, target: AgencyTarget) -> list[Listing]:
        listings: list[Listing] = []
        seen_urls: set[str] = set()
        page = 1

        while page <= MAX_PAGES:
            if page == 1:
                page_url = target.listing_url
            elif self.config.page_url_template:
                page_url = self.config.page_url_template.format(
                    base=target.listing_url, page=page
                )
            else:
                break  # paginação desativada para este site

            soup = fetch_smart(
                page_url,
                self.config.detail_link_pattern,
                wait_selector=self.config.wait_selector,
                click_selector=self.config.click_selector,
            )
            anchors = [
                a
                for a in soup.find_all("a", href=True)
                if self.config.detail_link_pattern.search(a["href"])
            ]
            if not anchors:
                break

            hrefs_para_anchors: dict[str, list] = {}
            for a in anchors:
                href = urljoin(page_url, a["href"])
                hrefs_para_anchors.setdefault(href, []).append(a)

            new_on_page = 0
            for href, grupo in hrefs_para_anchors.items():
                if href in seen_urls:
                    continue
                seen_urls.add(href)
                new_on_page += 1

                block_text = ""
                block = grupo[0]
                for a in grupo:
                    own_text = a.get_text(" ", strip=True)
                    if "€" in own_text:
                        block_text = own_text
                        block = a
                        break
                if not block_text:
                    block = block.find_parent(["article", "li", "div"]) or block
                    block_text = block.get_text(" ", strip=True)

                if self.config.city_filter:
                    texto_lower = block_text.lower()
                    if not any(cidade in texto_lower for cidade in self.config.city_filter):
                        continue  # comuna vizinha fora do âmbito — descarta

                imgs = []
                for a in grupo:
                    for img in a.find_all("img", src=True):
                        if img["src"].startswith("http") and img["src"] not in imgs:
                            imgs.append(img["src"])

                listings.append(
                    Listing(
                        agencia_nome=target.agencia_nome,
                        cidade=target.cidade,
                        url_anuncio=href,
                        tipo_transacao=target.tipo_transacao,
                        preco_raw=extract_price(block_text),
                        superficie_raw=extract_surface(block_text),
                        num_divisoes=extract_rooms(block_text),
                        num_quartos=extract_bedrooms(block_text),
                        referencia_agencia=extract_ref(block_text),
                        fotos=imgs,
                        foto_capa=imgs[0] if imgs else None,
                        titulo=block_text[:150],
                        descricao=block_text,
                        dpe_classe=extract_dpe(block_text),
                        ano_construcao=extract_ano_construcao(block_text),
                        comodidades=extract_comodidades(block_text),
                    )
                )

            if new_on_page == 0 or not self.config.page_url_template:
                break
            page += 1

        return listings
