"""
Modulo CLI — Interfaccia a riga di comando per mesh2u3d.

Espone:
    - main: entry point della CLI

Comandi disponibili:
    - convert: converte un file mesh in un altro formato
    - batch: converte più file in una directory
    - info: mostra informazioni su un file mesh
    - validate: valida un file U3D
"""

from .main import main

__all__ = ["main"]
