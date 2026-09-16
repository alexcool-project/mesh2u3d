"""
Blocchi e costanti del formato PRC (ISO 14739-1).

Il formato PRC è un formato binario strutturato in blocchi (chunk).
Ogni blocco ha un tipo, una dimensione e un contenuto specifico.

Questo modulo definisce:
    - I tipi di blocco principali (PRCBlockType)
    - Le costanti di formato (header, magic number)
    - Le strutture dati di base per la scrittura

Riferimenti:
    - ISO 14739-1:2014 — Document management
    - Product Representation Compact (PRC) format
    - Adobe PDF 1.7 with PRC embedded

Limitazioni v0.2.0 (Opzione A minima):
    - Solo i blocchi essenziali per la geometria
    - Nessun supporto texture/materiali
"""

from __future__ import annotations

from enum import IntEnum


# --- Magic number e header ---

# Magic number del formato PRC (ISO 14739-1)
PRC_MAGIC = b"PRC"

# Versione del formato supportata
PRC_VERSION_MAJOR = 7
PRC_VERSION_MINOR = 0

# Dimensione dell'header PRC (in byte)
PRC_HEADER_SIZE = 32


# --- Tipi di blocco PRC ---

class PRCBlockType(IntEnum):
    """
    Tipi di blocco del formato PRC.

    Solo i blocchi essenziali per la geometria sono implementati
    nella versione 0.2.0 (Opzione A minima).
    """
    # --- Blocchi di header ---
    FILE_HEADER = 0x0001
    FILE_STRUCTURE = 0x0002

    # --- Blocchi di contenuto ---
    CONTENT_HEADER = 0x0010
    CONTENT_STRUCTURE = 0x0011

    # --- Blocchi di geometria ---
    GEOMETRY_HEADER = 0x0020
    TESSELLATION = 0x0021           # Mesh triangolare
    TESSELLATION_HEADER = 0x0022

    # --- Blocchi di scena ---
    SCENE_HEADER = 0x0030
    SCENE_STRUCTURE = 0x0031

    # --- Blocchi di chiusura ---
    END_OF_FILE = 0xFFFF


# --- Costanti per la geometria ---

# Massimo numero di vertici per blocco TESSELLATION
MAX_VERTICES_PER_BLOCK = 65535

# Massimo numero di triangoli per blocco TESSELLATION
MAX_TRIANGLES_PER_BLOCK = 65535


# --- Nomi leggibili dei blocchi ---

BLOCK_NAMES = {
    PRCBlockType.FILE_HEADER: "FILE_HEADER",
    PRCBlockType.FILE_STRUCTURE: "FILE_STRUCTURE",
    PRCBlockType.CONTENT_HEADER: "CONTENT_HEADER",
    PRCBlockType.CONTENT_STRUCTURE: "CONTENT_STRUCTURE",
    PRCBlockType.GEOMETRY_HEADER: "GEOMETRY_HEADER",
    PRCBlockType.TESSELLATION: "TESSELLATION",
    PRCBlockType.TESSELLATION_HEADER: "TESSELLATION_HEADER",
    PRCBlockType.SCENE_HEADER: "SCENE_HEADER",
    PRCBlockType.SCENE_STRUCTURE: "SCENE_STRUCTURE",
    PRCBlockType.END_OF_FILE: "END_OF_FILE",
}


def block_type_name(bt: int) -> str:
    """Restituisce il nome leggibile di un tipo di blocco."""
    try:
        return BLOCK_NAMES.get(PRCBlockType(bt), f"UNKNOWN(0x{bt:04X})")
    except ValueError:
        return f"UNKNOWN(0x{bt:04X})"


# --- Struttura di un blocco PRC ---

class PRCBlock:
    """
    Rappresenta un blocco PRC.

    Ogni blocco ha:
        - type: tipo di blocco (PRCBlockType)
        - data: contenuto binario del blocco
        - metadata: metadati opzionali
    """

    __slots__ = ("block_type", "data", "metadata")

    def __init__(
        self,
        block_type: PRCBlockType,
        data: bytes = b"",
        metadata: bytes = b"",
    ) -> None:
        self.block_type = block_type
        self.data = data
        self.metadata = metadata

    @property
    def size(self) -> int:
        """Dimensione totale del blocco (header + data + metadata)."""
        return 12 + len(self.data) + len(self.metadata)

    def to_bytes(self) -> bytes:
        """
        Serializza il blocco in formato binario PRC.

        Struttura del blocco:
            - 4 byte: tipo di blocco (uint32)
            - 4 byte: dimensione dati (uint32)
            - 4 byte: dimensione metadata (uint32)
            - N byte: dati
            - M byte: metadata
        """
        import struct
        header = struct.pack(
            "<III",
            int(self.block_type),
            len(self.data),
            len(self.metadata),
        )
        return header + self.data + self.metadata

    def __repr__(self) -> str:
        return (
            f"PRCBlock(type={block_type_name(self.block_type)}, "
            f"data_size={len(self.data)}, meta_size={len(self.metadata)})"
        )


__all__ = [
    "PRC_MAGIC",
    "PRC_VERSION_MAJOR",
    "PRC_VERSION_MINOR",
    "PRC_HEADER_SIZE",
    "PRCBlockType",
    "MAX_VERTICES_PER_BLOCK",
    "MAX_TRIANGLES_PER_BLOCK",
    "BLOCK_NAMES",
    "block_type_name",
    "PRCBlock",
]
