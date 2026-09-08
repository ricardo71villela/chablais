"""Scraper para agências da rede CENTURY 21 (motor de site comum à rede).

Testado a partir do conteúdo real de:
  https://www.century21-chablais-leman-thonon.com/annonces/achat/

Padrão de URL dos anúncios: /trouver_logement/detail/<id>/
Paginação: /annonces/achat/page-2/, /annonces/achat/page-3/, ...

⚠️ Extração construída a partir de texto já convertido (não do HTML bruto).
O padrão de link é estável (visível nos hrefs), mas os seletores de bloco
usam uma heurística (find_parent) — validar com uma execução real antes de
confiar 100% nos campos preco/superficie/divisões.
"""
import re
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
    fetch_html,
)

DETAIL_LINK_RE = re.compile(r"/trouver_logement/detail/\d+/?$")
MAX_PAGES = 20  # limite de segurança contra loops infinitos


class Century21Scraper(AgencyScraper):
    network_name = "Century21"

    def fetch_listings(self, target: AgencyTarget) -> list[Listing]:
        listings: list[Listing] = []
        seen_urls: set[str] = set()
        page = 1

        while page <= MAX_PAGES:
            page_url = (
                target.listing_url
                if page == 1
                else f"{target.listing_url.rstrip('/')}/page-{page}/"
            )
            soup = fetch_html(page_url)
            anchors = [
                a for a in soup.find_all("a", href=True) if DETAIL_LINK_RE.search(a["href"])
            ]
            if not anchors:
                break

            new_on_page = 0
            for a in anchors:
                href = urljoin(page_url, a["href"])
                if href in seen_urls:
                    continue
                seen_urls.add(href)
                new_on_page += 1

                block = a.find_parent(["article", "li", "div"]) or a
                block_text = block.get_text(" ", strip=True)
                imgs = [
                    img["src"]
                    for img in block.find_all("img", src=True)
                    if img["src"].startswith("http")
                ]

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

            if new_on_page == 0:
                break
            page += 1

        return listings
