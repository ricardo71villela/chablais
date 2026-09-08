"""Orquestrador: corre todos os scrapers registados e grava no Supabase."""
import logging

from dotenv import load_dotenv

load_dotenv()

from src.normalize import normalize
from src.scrapers.config import REGISTRY
from src.upsert_supabase import get_client, get_or_create_agencia, mark_duplicates, upsert_listings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def main() -> None:
    client = get_client()

    for scraper, targets in REGISTRY:
        # Agrupar targets pela mesma agência (ex. venda + arrendamento juntam-se
        # antes de decidir o que ficou "removido")
        por_agencia: dict[tuple[str, str], list[dict]] = {}

        for target in targets:
            key = (target.agencia_nome, target.cidade)
            try:
                listings = scraper.fetch_listings(target)
            except NotImplementedError as e:
                log.warning("Scraper %s ainda não implementado: %s", scraper.network_name, e)
                continue
            except Exception:
                log.exception(
                    "Falha ao processar %s (%s)", target.agencia_nome, target.listing_url
                )
                continue

            log.info(
                "%s — %s (%s): %d imóveis encontrados",
                scraper.network_name,
                target.agencia_nome,
                target.tipo_transacao,
                len(listings),
            )
            por_agencia.setdefault(key, []).extend(normalize(l) for l in listings)

        for (agencia_nome, cidade), normalized_listings in por_agencia.items():
            agencia_id = get_or_create_agencia(
                client, agencia_nome, cidade, rede=scraper.network_name
            )
            upsert_listings(client, agencia_id, normalized_listings)
            log.info("Gravados %d imóveis para %s", len(normalized_listings), agencia_nome)

    log.info("A procurar duplicados entre agências...")
    total_marcados = mark_duplicates(client)
    log.info("Duplicados marcados nesta corrida: %d", total_marcados)


if __name__ == "__main__":
    main()
