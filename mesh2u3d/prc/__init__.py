"""
Modulo PRC — Scrittura di file PRC (ISO 14739-1).

PRC (Product Representation Compact) è un formato binario per la
rappresentazione di modelli 3D, supportato nativamente da Adobe
Acrobat/Reader.

Questo modulo implementa un writer MINIMALE che genera file PRC
sufficienti per essere aperti da Adobe Acrobat/Reader.

Espone:
    - PRCWriter: classe principale per la scrittura
    - mesh_to_prc: funzione di alto livello
    - PRCError: eccezione custom

Limitazioni (v0.2.0 - Opzione A minima):
    - Nessun supporto texture
    - Nessun supporto materiali avanzati (PBR)
    - Nessun supporto luci
    - Geometria triangolare semplice

Roadmap:
    - v0.3.0: Texture e materiali base
    - v0.4.0: Materiali PBR completi
"""

from .writer import (
    PRCWriter,
    mesh_to_prc,
    PRCError,
)

__all__ = [
    "PRCWriter",
    "mesh_to_prc",
    "PRCError",
]
