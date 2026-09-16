"""
mesh2u3d — Libreria Python per convertire mesh 3D in U3D, HTML 3D, PRC e PDF 3D.

API pubblica di alto livello:
    - MeshReader / MeshData
    - U3DWriter / mesh_to_u3d / meshes_to_u3d
    - mesh_to_html
    - PRCWriter / mesh_to_prc
    - embed_u3d_in_pdf
    - convert_3d_file (universale, multi-formato)

Supporto bilingue IT/EN per il viewer HTML.

Versione: 0.2.0
Licenza: MIT
"""

from __future__ import annotations

__version__ = "0.2.0"
__author__ = "alexcool-project"
__license__ = "MIT"

# --- IO: lettura mesh universale ---
from .io.mesh_reader import MeshReader, MeshData

# --- U3D: scrittura e validazione ECMA-363 ---
from .u3d.writer import U3DWriter, mesh_to_u3d, meshes_to_u3d
from .u3d.validator import validate_u3d, U3DValidationReport

# --- PRC: scrittura ISO 14739-1 (NOVITÀ v0.2.0) ---
from .prc.writer import PRCWriter, mesh_to_prc, PRCError

# --- HTML: viewer three.js self-contained (IT/EN) ---
from .html.writer import mesh_to_html

# --- PDF: embed U3D in PDF 1.7 ---
from .pdf.embedder import embed_u3d_in_pdf

# --- Converter universale (NOVITÀ v0.2.0) ---
from .converter import convert_3d_file

# --- CLI (NOVITÀ v0.2.0) ---
from .cli import main as cli_main


__all__ = [
    "__version__",
    "__author__",
    "__license__",
    # IO
    "MeshReader",
    "MeshData",
    # U3D
    "U3DWriter",
    "mesh_to_u3d",
    "meshes_to_u3d",
    "validate_u3d",
    "U3DValidationReport",
    # PRC
    "PRCWriter",
    "mesh_to_prc",
    "PRCError",
    # HTML
    "mesh_to_html",
    # PDF
    "embed_u3d_in_pdf",
    # Converter
    "convert_3d_file",
    # CLI
    "cli_main",
]
