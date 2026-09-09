"""Grava/atualiza os imóveis na tabela `imoveis` do Supabase.

Estratégia:
  - upsert por `url_anuncio` (chave única) — cria se não existe, atualiza
    `ultima_atualizacao` e `hash_conteudo` se mudou.
  - no fim de cada corrida por agência, marca como 'removido' todos os
    imóveis dessa agência que não apareceram na corrida atual (deixaram de
    estar publicados).
  - no fim de TODAS as agências, corre uma passagem de deduplicação: quando
    duas agências diferentes anunciam o que parece ser o mesmo imóvel
    (mesmo `fingerprint_duplicado` — cidade, tipo, preço e superfície
    aproximados), aponta o mais recente para o mais antigo via
    `possivel_duplicado_de`, sem apagar nenhum dos dois registos.
"""
import os
from collections import defaultdict
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


def mark_duplicates(client: Client) -> int:
    """Agrupa os imóveis ativos por `fingerprint_duplicado` e, para cada
    grupo que envolva mais do que uma agência, aponta os registos mais
    recentes para o mais antigo (`possivel_duplicado_de`).

    Devolve o número de registos marcados como duplicado nesta passagem.
    Corre a lógica de agrupamento em Python (o volume de dados é pequeno
    o suficiente para isso ser simples e fiável).
    """
    resp = (
        client.table("imoveis")
        .select("id,agencia_id,fingerprint_duplicado,primeira_deteccao,possivel_duplicado_de")
        .eq("estado", "ativo")
        .not_.is_("fingerprint_duplicado", "null")
        .execute()
    )

    grupos: dict[str, list[dict]] = defaultdict(list)
    for row in resp.data:
        grupos[row["fingerprint_duplicado"]].append(row)

    marcados = 0
    for fingerprint, itens in grupos.items():
        agencias_envolvidas = {i["agencia_id"] for i in itens}
        if len(itens) < 2 or len(agencias_envolvidas) < 2:
            continue  # não é duplicado entre agências diferentes — ignora

        itens.sort(key=lambda i: i["primeira_deteccao"])
        canonico = itens[0]
        for duplicado in itens[1:]:
            if duplicado.get("possivel_duplicado_de") == canonico["id"]:
                continue  # já estava marcado corretamente
            client.table("imoveis").update(
                {"possivel_duplicado_de": canonico["id"]}
            ).eq("id", duplicado["id"]).execute()
            marcados += 1

    return marcados
