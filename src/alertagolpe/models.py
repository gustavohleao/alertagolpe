"""Unidade de texto indexável pela busca TF-IDF (golpe do catálogo)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    id: str
    page: int
    text: str
    location_label: str = "Golpe"
