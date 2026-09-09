"""Exporta os imóveis ativos para um CSV simples, para cruzamento manual no
Radar Léman (que corre à parte, no seu próprio ambiente).

Só exporta campos não-identificáveis do lado da agência de origem — cidade,
tipo, área, preço — nunca nomes de proprietários nem moradas (essas o
scraper nem tem). O cruzamento por área (±5%) para descobrir a morada
provável e o dono corre inteiramente do lado do Radar Léman, com os dados
BAN/DVF/cadastro que só lá existem.

Uso:
    python -m src.export_para_radar_leman
    (ou, para um caminho de saída específico)
    python -m src.export_para_radar_leman --output /caminho/para/ficheiro.csv
"""
import argparse
import csv
import logging

from dotenv import load_dotenv

load_dotenv()

from src.upsert_supabase import get_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

CAMPOS = [
    "cidade",
    "tipo_transacao",
    "tipo_imovel",
    "superficie_m2",
    "superficie_terreno_m2",
    "num_divisoes",
    "num_quartos",
    "preco",
    "dpe_classe",
    "ano_construcao",
    "agencia_nome",
    "url_anuncio",
]


def exportar(output_path: str) -> int:
    client = get_client()

    resp = (
        client.table("imoveis")
        .select("cidade,tipo_transacao,tipo_imovel,superficie_m2,superficie_terreno_m2,"
                "num_divisoes,num_quartos,preco,dpe_classe,ano_construcao,url_anuncio,"
                "agencias(nome)")
        .eq("estado", "ativo")
        .execute()
    )

    linhas = []
    for row in resp.data:
        linha = {campo: row.get(campo) for campo in CAMPOS if campo != "agencia_nome"}
        linha["agencia_nome"] = row["agencias"]["nome"] if row.get("agencias") else None
        linhas.append(linha)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CAMPOS)
        writer.writeheader()
        writer.writerows(linhas)

    return len(linhas)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", default="concorrencia_ativa.csv",
        help="Caminho do CSV de saída (default: concorrencia_ativa.csv, na pasta atual)",
    )
    args = parser.parse_args()

    total = exportar(args.output)
    log.info("Exportados %d imóveis ativos para %s", total, args.output)
