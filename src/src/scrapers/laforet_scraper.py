"""Scraper para a agência Laforêt Thonon-Évian.

A agência cobre Thonon-Évian e comunas vizinhas (Perrignier, Neuvecelle,
Douvaine, Publier, Saint-Gingolph, Armoy, etc.) na mesma página de listagem:
  https://www.laforet.com/agence-immobiliere/thonon-evian/acheter

Padrão de URL dos anúncios:
  /agence-immobiliere/thonon-evian/acheter/<cidade-slug>/<tipo>-<id>
  ex: /agence-immobiliere/thonon-evian/acheter/thonon-les-bains/appartement-4-pieces-52789637

Como o âmbito do projeto é só Thonon-les-Bains e Évian-les-Bains, este
scraper filtra e descarta os imóveis de outras comunas (Perrignier,
Douvaine, etc.) com base na cidade extraída de cada anúncio.

⚠️ Este site carrega os anúncios via JavaScript (a página inicial vem vazia
com um `requests` simples) — por isso usa fetch_html_rendered() (Playwright)
em vez de fetch_html(). É mais lento a correr, mas é o que funciona aqui.

Atenção: paginação assumida via `?page=N` (visto num URL de exemplo do
mesmo site, para uma página de listagem diferente). Se a paginação não
avançar como esperado, confirmar o mecanismo real.
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
    extract_rooms,
    extract_surface,
    fetch_smart,
)

DETAIL_LINK_RE = re.compile(r"/agence-immobiliere/thonon-evian/(?:acheter|louer)/[^/?#]+/[^/?#]+-\d+")
CITY_RE = re.compile(r"([A-ZÀ-Ü][A-ZÀ-Ü\s\-']{2,})\s*\((\d{5})\)")
MAX_PAGES = 15
CIDADES_ALVO = {"thonon", "evian", "évian"}  # filtra fora comunas vizinhas


class LaforetScraper(AgencyScraper):
    network_name = "Laforet"

    def fetch_listings(self, target: AgencyTarget) -> list[Listing]:
        listings: list[Listing] = []
        seen_urls: set[str] = set()
        page = 1

        while page <= MAX_PAGES:
            page_url = target.listing_url if page == 1 else f"{target.listing_url}?page={page}"
            # Seletor específico do path dos anúncios (não do menu de navegação,
            # que também contém links com "/acheter/" e faria a espera terminar cedo demais)
            wait_selector = "a[href*='/agence-immobiliere/thonon-evian/acheter/'], a[href*='/agence-immobiliere/thonon-evian/louer/']"
            soup = fetch_smart(page_url, DETAIL_LINK_RE, wait_selector=wait_selector)
            anchors = [
                a for a in soup.find_all("a", href=True) if DETAIL_LINK_RE.search(a["href"])
            ]
            if not anchors:
                break

            new_on_page = 0
            # Agrupar todos os links (fotos + link de texto) pelo mesmo href,
            # porque cada imóvel aparece repetido várias vezes na página —
            # precisamos de ver todos antes de escolher qual tem a informação.
            hrefs_para_anchors: dict[str, list] = {}
            for a in anchors:
                href = urljoin(page_url, a["href"])
                hrefs_para_anchors.setdefault(href, []).append(a)

            for href, anchors_do_imovel in hrefs_para_anchors.items():
                if href in seen_urls:
                    continue
                seen_urls.add(href)
                new_on_page += 1

                # Preferimos o link cujo próprio texto já traz o preço
                # (formato "Appartement 390 000 € CIDADE ..."); se nenhum
                # tiver isso, usamos o bloco-pai do primeiro link como reserva.
                block_text = ""
                block = anchors_do_imovel[0]
                for a in anchors_do_imovel:
                    own_text = a.get_text(" ", strip=True)
                    if "€" in own_text:
                        block_text = own_text
                        block = a
                        break
                if not block_text:
                    block = block.find_parent(["article", "li", "div"]) or block
                    block_text = block.get_text(" ", strip=True)

                city_match = CITY_RE.search(block_text)
                cidade_texto = city_match.group(1).strip() if city_match else ""
                cidade_norm = cidade_texto.lower()
                if not any(alvo in cidade_norm for alvo in CIDADES_ALVO):
                    continue  # fora do âmbito (comuna vizinha) — descarta

                imgs = []
                for a in anchors_do_imovel:
                    for img in a.find_all("img", src=True):
                        if img["src"].startswith("http") and img["src"] not in imgs:
                            imgs.append(img["src"])

                listings.append(
                    Listing(
                        agencia_nome=target.agencia_nome,
                        cidade="Thonon" if "thonon" in cidade_norm else "Evian",
                        url_anuncio=href,
                        tipo_transacao=target.tipo_transacao,
                        preco_raw=extract_price(block_text),
                        superficie_raw=extract_surface(block_text),
                        num_divisoes=extract_rooms(block_text),
                        num_quartos=extract_bedrooms(block_text),
                        morada=cidade_texto,
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
