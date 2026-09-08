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
            listing.descricao,
        ]
    )
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def dedup_fingerprint(cidade: str | None, tipo_transacao: str, preco: float | None,
                       superficie_m2: float | None, num_divisoes: int | None) -> str | None:
    """Fingerprint aproximado para detetar o MESMO imóvel anunciado por
    agências diferentes (partilha de mandato, ou o mesmo bem em dois
    portais). Arredonda preço e superfície para absorver pequenas
    diferenças de arredondamento entre sites.

    Devolve None se faltar informação suficiente para comparar com segurança
    (evita falsos positivos ao juntar imóveis por dados incompletos).
    """
    if preco is None or superficie_m2 is None or not cidade:
        return None
    preco_arredondado = round(preco / 1000) * 1000
    superficie_arredondada = round(superficie_m2)
    raw = "|".join(
        str(x)
        for x in [cidade.lower(), tipo_transacao, preco_arredondado, superficie_arredondada, num_divisoes]
    )
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def normalize(listing: Listing) -> dict[str, Any]:
    """Converte um Listing bruto no dicionário pronto para gravar em `imoveis`."""
    preco = to_float(listing.preco_raw)
    superficie = to_float(listing.superficie_raw)

    return {
        "url_anuncio": listing.url_anuncio,
        "tipo_transacao": listing.tipo_transacao,
        "preco": preco,
        "superficie_m2": superficie,
        "num_divisoes": listing.num_divisoes,
        "num_quartos": listing.num_quartos,
        "morada": listing.morada,
        "cidade": listing.cidade,
        "fotos": listing.fotos,
        "foto_capa": listing.foto_capa,
        "descricao": listing.descricao,
        "dpe_classe": listing.dpe_classe,
        "ano_construcao": listing.ano_construcao,
        "comodidades": listing.comodidades,
        "referencia_agencia": listing.referencia_agencia,
        "hash_conteudo": content_hash(listing),
        "fingerprint_duplicado": dedup_fingerprint(
            listing.cidade, listing.tipo_transacao, preco, superficie, listing.num_divisoes
        ),
    }
