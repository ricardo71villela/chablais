"""Scraper para agências da rede CENTURY 21 (motor de site comum à rede).

Testado a partir do conteúdo real de:
  https://www.century21-chablais-leman-thonon.com/annonces/achat/

Padrão de URL dos anúncios: /trouver_logement/detail/<id>/
Paginação: /annonces/achat/page-2/, /annonces/achat/page-3/, ...

⚠️ Extração construída a partir de texto já convertido (não do HTML bruto).
O padrão de link é estável (visível nos hrefs). Auditoria de 13/set:
corrigido bug que fazia preco/superficie/tipo ficarem sempre vazios — o
ancestral mais próximo do link é só a foto, sem o preço (ver
climb_to_content_block em base.py); e corrigido duplicação de linhas por
não agrupar os vários links (foto + texto) do mesmo imóvel.
"""
import logging
import re
from urllib.parse import urljoin

from src.models import Listing
from src.scrapers.base import (
    AgencyScraper,
    AgencyTarget,
    climb_to_content_block,
    extract_ano_construcao,
    extract_bedrooms,
    extract_comodidades,
    extract_dpe,
    extract_price,
    extract_ref,
    extract_rooms,
    extract_surface,
    extract_terrain_surface,
    extract_tipo_imovel,
    fetch_smart,
)

DETAIL_LINK_RE = re.compile(r"/trouver_logement/detail/\d+/?$")
MAX_PAGES = 20  # limite de segurança contra loops infinitos

log = logging.getLogger(__name__)


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
            try:
                soup = fetch_smart(page_url, DETAIL_LINK_RE)
            except Exception:
                # Mesmo bug encontrado no generic_scraper.py em 13/set: uma
                # falha a meio da paginação não pode perder as páginas já
                # recolhidas — devolve o que já há em vez de levantar.
                log.warning(
                    "Century21 — %s (%s): falha a obter a página %d (%s) — a "
                    "devolver %d imóvel/imóveis já recolhido(s) até aqui",
                    target.agencia_nome, target.tipo_transacao, page, page_url, len(listings),
                )
                break
            anchors = [
                a for a in soup.find_all("a", href=True) if DETAIL_LINK_RE.search(a["href"])
            ]
            if not anchors:
                break

            # Agrupar todos os links (foto + texto) pelo mesmo href — o
            # mesmo imóvel costuma aparecer repetido no cartão (link da
            # imagem e link do título/preço); sem agrupar, cada um vira uma
            # linha DUPLICADA. Ver auditoria de 13/set.
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

                # Preferir o link cujo próprio texto já traz o preço; só
                # recorrer a subir ancestrais (climb_to_content_block) se
                # nenhum dos links do grupo tiver o preço no próprio texto.
                block_text = ""
                block = grupo[0]
                for a in grupo:
                    own_text = a.get_text(" ", strip=True)
                    if "€" in own_text:
                        block_text = own_text
                        block = a
                        break
                if not block_text:
                    block, block_text = climb_to_content_block(block)

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
                        tipo_imovel=extract_tipo_imovel(block_text),
                        superficie_terreno_raw=extract_terrain_surface(block_text),
                    )
                )

            if new_on_page == 0:
                break
            page += 1

        return listings
