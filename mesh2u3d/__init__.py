"""
mesh2u3d — Convert 3D meshes to U3D (ECMA-363), HTML 3D, and PDF.

Libreria Python open source (MIT) per la conversione di mesh 3D in:
  - U3D (ECMA-363)
  - HTML 3D (three.js, self-contained)
  - PDF con U3D embedded
  - PRC (ISO 14739-1) [roadmap]

Autore: alexcool-project
Licenza: MIT
Repository: https://github.com/alexcool-project/mesh2u3d
"""

from __future__ import annotations

__version__ = "0.1.0"
__author__ = "alexcool-project"
__license__ = "MIT"

# --- IO: Lettura mesh ---
from .io.mesh_reader import MeshData, MeshReader

# --- U3D: Writer + Validator ---
from .u3d.writer import mesh_to_u3d, meshes_to_u3d
from .u3d.validator import validate_u3d, ValidationReport

# --- HTML: Viewer ---
from .html.writer import mesh_to_html

# --- PDF: Embedder ---
from .pdf.embedder import embed_u3d_in_pdf, mesh_to_pdf

# --- Converter: API di alto livello (Fase 1) ---
from .converter.convert import convert_3d_file, convert_batch

# --- API pubblica ---
__all__ = [
    # Versione
    "__version__",
    "__author__",
    "__license__",
    # IO
    "MeshData",
    "MeshReader",
    # U3D
    "mesh_to_u3d",
    "meshes_to_u3d",
    "validate_u3d",
    "ValidationReport",
    # HTML
    "mesh_to_html",
    # PDF
    "embed_u3d_in_pdf",
    "mesh_to_pdf",
    # Converter (Fase 1)
    "convert_3d_file",
    "convert_batch",
]
