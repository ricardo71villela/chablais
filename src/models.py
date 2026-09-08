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
    titulo: Optional[str] = None
    descricao: Optional[str] = None
