"""Grava/atualiza os imóveis na tabela `imoveis` do Supabase.

Estratégia:
  - upsert por `url_anuncio` (chave única) — cria se não existe, atualiza
    `ultima_atualizacao` e `hash_conteudo` se mudou.
  - no fim de cada corrida por agência, marca como 'removido' todos os
    imóveis dessa agência que não apareceram na corrida atual (deixaram de
    estar publicados).
"""
import os
from datetime import datetime, timezone

from supabase import Client, create_client


def get_client() -> Client:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_KEY"]
    return create_client(url, key)


def get_or_create_agencia(client: Client, nome: str, cidade: str, rede: str) -> str:
    existing = (
        client.table("agencias").select("id").eq("nome", nome).eq("cidade", cidade).execute()
    )
    if existing.data:
        return existing.data[0]["id"]
    inserted = (
        client.table("agencias")
        .insert({"nome": nome, "cidade": cidade, "rede": rede})
        .execute()
    )
    return inserted.data[0]["id"]


def upsert_listings(client: Client, agencia_id: str, listings: list[dict]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    seen_urls = [l["url_anuncio"] for l in listings]

    for listing in listings:
        listing = {**listing, "agencia_id": agencia_id, "ultima_atualizacao": now, "estado": "ativo"}
        client.table("imoveis").upsert(listing, on_conflict="url_anuncio").execute()

    # Marcar como removidos os que já não aparecem nesta corrida
    if seen_urls:
        (
            client.table("imoveis")
            .update({"estado": "removido"})
            .eq("agencia_id", agencia_id)
            .not_.in_("url_anuncio", seen_urls)
            .eq("estado", "ativo")
            .execute()
        )
