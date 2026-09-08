"""Normalização dos campos brutos extraídos pelos scrapers."""
import hashlib
from typing import Any

from src.models import Listing


def to_float(raw: str | None) -> float | None:
    if not raw:
        return None
    try:
        return float(raw.replace(",", "."))
    except ValueError:
        return None


def content_hash(listing: Listing) -> str:
    """Hash dos campos relevantes — usado para detetar alterações (preço,
    descrição) sem comparar campo a campo."""
    raw = "|".join(
        str(x)
        for x in [
            listing.preco_raw,
            listing.superficie_raw,
            listing.num_divisoes,
            listing.num_quartos,
            listing.titulo,
        ]
    )
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def normalize(listing: Listing) -> dict[str, Any]:
    """Converte um Listing bruto no dicionário pronto para gravar em `imoveis`."""
    return {
        "url_anuncio": listing.url_anuncio,
        "tipo_transacao": listing.tipo_transacao,
        "preco": to_float(listing.preco_raw),
        "superficie_m2": to_float(listing.superficie_raw),
        "num_divisoes": listing.num_divisoes,
        "num_quartos": listing.num_quartos,
        "morada": listing.morada,
        "cidade": listing.cidade,
        "fotos": listing.fotos,
        "referencia_agencia": listing.referencia_agencia,
        "hash_conteudo": content_hash(listing),
    }
