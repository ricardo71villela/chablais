"""Scraper para a rede Laforêt — STUB, por completar.

A agência Laforêt Thonon-Évian tem uma página de listagem única que cobre
as duas cidades:
  https://www.laforet.com/agence-immobiliere/thonon-evian/acheter

O que falta antes de este scraper funcionar:
  1. Confirmar o padrão de URL de cada anúncio individual (não visível no
     texto já extraído — os links "Appeler"/"(nouvel onglet)" sugerem que o
     link para o anúncio está noutro elemento, provavelmente a imagem ou o
     título do card).
  2. Confirmar se a paginação usa `?page=N` (visto num URL de exemplo:
     `?page=5`) ou outro mecanismo.
  3. Como a página mistura resultados de Thonon e de Évian, será necessário
     filtrar por cidade a partir do texto de cada card (já presente:
     "THONON LES BAINS (74200)" / "Évian-les-Bains").

Uma vez confirmados os pontos acima, a implementação deve seguir o mesmo
padrão do `century21_scraper.py`: localizar os links de anúncio, subir ao
bloco-pai, extrair com as mesmas funções de `base.py`.
"""
from src.models import Listing
from src.scrapers.base import AgencyScraper, AgencyTarget


class LaforetScraper(AgencyScraper):
    network_name = "Laforet"

    def fetch_listings(self, target: AgencyTarget) -> list[Listing]:
        raise NotImplementedError(
            "Scraper Laforêt ainda não implementado — ver notas no topo deste "
            "ficheiro. Inspecionar o HTML real da página de listagem antes de "
            "avançar."
        )
