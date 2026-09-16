"""
Modulo converter — Conversione universale tra formati 3D.

Espone:
    - convert_3d_file: funzione di alto livello per convertire tra formati
    - convert_3d_files: funzione per batch processing
    - ConversionResult: risultato della conversione
    - ConversionError: eccezione custom

Supporta:
    - Fase 1: conversione base multi-formato
    - Fase 2: preservazione texture PBR (predisposizione)
    - Fase 3: batch processing e multi-mesh (predisposizione)
"""

from .convert import (
    convert_3d_file,
    convert_3d_files,
    ConversionResult,
    ConversionError,
    SUPPORTED_INPUT_FORMATS,
    SUPPORTED_OUTPUT_FORMATS,
)

__all__ = [
    "convert_3d_file",
    "convert_3d_files",
    "ConversionResult",
    "ConversionError",
    "SUPPORTED_INPUT_FORMATS",
    "SUPPORTED_OUTPUT_FORMATS",
]
