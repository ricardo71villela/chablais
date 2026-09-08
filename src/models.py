"""Modelo de dados de um imóvel extraído de um site de agência."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Listing:
    """Um imóvel tal como extraído (antes de normalização)."""

    agencia_nome: str
    cidade: str                     # 'Thonon' | 'Evian'
    url_anuncio: str
    tipo_transacao: str             # 'venda' | 'arrendamento'
    preco_raw: Optional[str] = None
    superficie_raw: Optional[str] = None
    num_divisoes: Optional[int] = None
    num_quartos: Optional[int] = None
    morada: Optional[str] = None
    referencia_agencia: Optional[str] = None
    fotos: list[str] = field(default_factory=list)
    foto_capa: Optional[str] = None       # imagem principal/capa do anúncio
    titulo: Optional[str] = None
    descricao: Optional[str] = None       # texto completo do bloco/anúncio
    dpe_classe: Optional[str] = None      # classe energética A-G, quando publicada
    ano_construcao: Optional[int] = None
    comodidades: list[str] = field(default_factory=list)  # ex. Garagem, Piscina, Terraço
