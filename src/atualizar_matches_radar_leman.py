"""Grava na tabela `imoveis` o resultado da ponte de cruzamento com o Radar
Léman, para aparecer no dashboard como um selo "🎯 Radar Léman" por anúncio.

Lê o CSV já reduzido a 1 candidato por anúncio (o mais parecido em área —
ver ponte_radar_leman_concorrencia.py e a coluna extra
`diferenca_relevante_pct`, calculada na sessão de 13/set/2026) e atualiza
cada imóvel correspondente (por `url_anuncio`, chave única da tabela).

Antes de correr pela primeira vez: aplicar
sql/migration_005_radar_leman_match.sql no SQL Editor do Supabase.

Uso:
    python3 -m src.atualizar_matches_radar_leman candidatos_cruzamento_melhor.csv
"""
import argparse
import logging

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

from datetime import datetime, timezone

from src.upsert_supabase import get_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def _label(row: pd.Series) -> str | None:
    """Morada quando existe (casa/apartamento); caso contrário a referência
    cadastral da parcela (terreno livre não tem morada, só geometria)."""
    endereco = row.get("radar_leman_endereco")
    if pd.notna(endereco):
        return endereco
    radar_id = row.get("radar_leman_id")
    return f"Parcela {radar_id}" if pd.notna(radar_id) else None


def atualizar(caminho_csv: str) -> tuple[int, int]:
    df = pd.read_csv(caminho_csv)
    client = get_client()
    agora = datetime.now(timezone.utc).isoformat()

    atualizados = 0
    nao_encontrados = 0

    for _, row in df.iterrows():
        diferenca = row.get("diferenca_relevante_pct")
        payload = {
            "radar_leman_match_label": _label(row),
            "radar_leman_match_link": row.get("radar_leman_link") if pd.notna(row.get("radar_leman_link")) else None,
            "radar_leman_match_tipo": row.get("tipo_cruzamento"),
            "radar_leman_match_diferenca_pct": float(diferenca) if pd.notna(diferenca) else None,
            "radar_leman_match_atualizado_em": agora,
        }
        resp = (
            client.table("imoveis")
            .update(payload)
            .eq("url_anuncio", row["concorrencia_url"])
            .execute()
        )
        if resp.data:
            atualizados += 1
        else:
            nao_encontrados += 1
            log.warning("url_anuncio não encontrado na tabela imoveis: %s", row["concorrencia_url"])

    return atualizados, nao_encontrados


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "csv", nargs="?", default="candidatos_cruzamento_melhor.csv",
        help="Caminho do CSV com 1 candidato por anúncio (default: candidatos_cruzamento_melhor.csv)",
    )
    args = parser.parse_args()

    atualizados, nao_encontrados = atualizar(args.csv)
    log.info("Matches gravados: %d", atualizados)
    if nao_encontrados:
        log.warning("Não encontrados na tabela imoveis (url_anuncio não bateu): %d", nao_encontrados)
