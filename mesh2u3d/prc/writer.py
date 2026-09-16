"""
PRC Writer — Scrittura di file PRC (ISO 14739-1).

Questo modulo implementa un writer MINIMALE che genera file PRC
sufficienti per essere aperti da Adobe Acrobat/Reader.

Strategia (Opzione A minima):
    - Geometria triangolare semplice
    - Nessuna texture
    - Nessun materiale avanzato
    - Solo i blocchi essenziali

Struttura del file PRC generato:
    [FILE_HEADER]        Header principale (32 byte)
    [FILE_STRUCTURE]     Struttura del file
    [CONTENT_HEADER]     Header del contenuto
    [GEOMETRY_HEADER]    Header della geometria
    [TESSELLATION]       Mesh triangolare (vertici + triangoli)
    [SCENE_HEADER]       Header della scena
    [SCENE_STRUCTURE]    Struttura della scena
    [END_OF_FILE]        Chiusura del file

Autore: alexcool-project
Licenza: MIT
"""

from __future__ import annotations

import struct
from pathlib import Path
from typing import Any

from ..io.mesh_reader import MeshData
from .blocks import (
    PRC_MAGIC,
    PRC_VERSION_MAJOR,
    PRC_VERSION_MINOR,
    PRC_HEADER_SIZE,
    PRCBlock,
    PRCBlockType,
)


# --- Eccezione custom ---

class PRCError(Exception):
    """Errore durante la scrittura di un file PRC."""
    pass


# --- PRC Writer ---

class PRCWriter:
    """
    Writer per file PRC (ISO 14739-1).

    Esempio d'uso:
        >>> from mesh2u3d.prc import PRCWriter
        >>> from mesh2u3d.io.mesh_reader import MeshReader
        >>> mesh = MeshReader.read("model.stl")
        >>> writer = PRCWriter()
        >>> writer.write(mesh, "model.prc")

    Oppure con l'API di alto livello:
        >>> from mesh2u3d.prc import mesh_to_prc
        >>> mesh_to_prc(mesh, "model.prc")
    """

    def __init__(
        self,
        *,
        version_major: int = PRC_VERSION_MAJOR,
        version_minor: int = PRC_VERSION_MINOR,
        unit_scale: float = 1.0,
    ) -> None:
        """
        Inizializza il writer PRC.

        Parameters
        ----------
        version_major : int
            Versione major del formato PRC (default: 7).
        version_minor : int
            Versione minor del formato PRC (default: 0).
        unit_scale : float
            Scala dell'unità di misura (default: 1.0 = millimetri).
        """
        self.version_major = version_major
        self.version_minor = version_minor
        self.unit_scale = unit_scale

    # --- Header ---

    def _build_file_header(self, total_size: int) -> bytes:
        """
        Costruisce l'header principale del file PRC (32 byte).

        Struttura:
            - 4 byte:  magic "PRC\\0"
            - 2 byte:  versione major
            - 2 byte:  versione minor
            - 4 byte:  dimensione totale del file
            - 4 byte:  offset al primo blocco
            - 4 byte:  numero di blocchi
            - 4 byte:  unit scale (float)
            - 8 byte:  riservato
        """
        magic = PRC_MAGIC + b"\x00"  # "PRC\0"
        header = struct.pack(
            "<4sHHIII f 8s",
            magic,
            self.version_major,
            self.version_minor,
            total_size,
            PRC_HEADER_SIZE,  # offset al primo blocco
            0,  # numero di blocchi (aggiornato dopo)
            self.unit_scale,
            b"\x00" * 8,
        )
        return header

    # --- Blocchi di struttura ---

    def _build_file_structure(self) -> bytes:
        """Costruisce il blocco FILE_STRUCTURE (metadati)."""
        # Struttura minimale: versione formato + tipo file
        return struct.pack("<HH", self.version_major, 0x0001)

    def _build_content_header(self) -> bytes:
        """Costruisce il blocco CONTENT_HEADER."""
        # Struttura minimale: numero di contenuti + tipo
        return struct.pack("<II", 1, 0x0001)

    def _build_geometry_header(self, vertex_count: int, triangle_count: int) -> bytes:
        """Costruisce il blocco GEOMETRY_HEADER."""
        return struct.pack("<II", vertex_count, triangle_count)

    def _build_scene_header(self) -> bytes:
        """Costruisce il blocco SCENE_HEADER."""
        # Struttura minimale: numero di nodi + tipo scena
        return struct.pack("<II", 1, 0x0001)

    def _build_scene_structure(self) -> bytes:
        """Costruisce il blocco SCENE_STRUCTURE."""
        # Struttura minimale: identità + unità
        return struct.pack("<I f", 1, self.unit_scale)

    # --- Geometria ---

    def _build_tessellation(self, mesh: MeshData) -> bytes:
        """
        Costruisce il blocco TESSELLATION con la geometria.

        Struttura:
            - 4 byte:  numero di vertici
            - 4 byte:  numero di triangoli
            - N*12 byte: vertici (float32 x3)
            - M*12 byte: triangoli (uint32 x3)
        """
        vertices = mesh.vertices.astype("float32")
        triangles = mesh.triangles.astype("uint32")

        vertex_count = len(vertices)
        triangle_count = len(triangles)

        if vertex_count > 65535:
            raise PRCError(
                f"Troppi vertici per un singolo blocco: {vertex_count} "
                f"(massimo 65535)"
            )

        # Header del blocco
        header = struct.pack("<II", vertex_count, triangle_count)

        # Vertici (flat)
        vertices_flat = vertices.flatten()
        vertices_bytes = struct.pack(f"<{len(vertices_flat)}f", *vertices_flat)

        # Triangoli (flat)
        triangles_flat = triangles.flatten()
        triangles_bytes = struct.pack(f"<{len(triangles_flat)}I", *triangles_flat)

        return header + vertices_bytes + triangles_bytes

    # --- Scrittura completa ---

    def to_bytes(self, mesh: MeshData) -> bytes:
        """
        Genera il contenuto binario del file PRC.

        Parameters
        ----------
        mesh : MeshData
            Mesh da convertire in PRC.

        Returns
        -------
        bytes
            Contenuto binario del file PRC.
        """
        blocks: list[PRCBlock] = []

        # 1. FILE_STRUCTURE
        blocks.append(PRCBlock(
            PRCBlockType.FILE_STRUCTURE,
            data=self._build_file_structure(),
        ))

        # 2. CONTENT_HEADER
        blocks.append(PRCBlock(
            PRCBlockType.CONTENT_HEADER,
            data=self._build_content_header(),
        ))

        # 3. GEOMETRY_HEADER
        blocks.append(PRCBlock(
            PRCBlockType.GEOMETRY_HEADER,
            data=self._build_geometry_header(
                vertex_count=mesh.vertex_count,
                triangle_count=mesh.triangle_count,
            ),
        ))

        # 4. TESSELLATION (geometria vera e propria)
        blocks.append(PRCBlock(
            PRCBlockType.TESSELLATION,
            data=self._build_tessellation(mesh),
        ))

        # 5. SCENE_HEADER
        blocks.append(PRCBlock(
            PRCBlockType.SCENE_HEADER,
            data=self._build_scene_header(),
        ))

        # 6. SCENE_STRUCTURE
        blocks.append(PRCBlock(
            PRCBlockType.SCENE_STRUCTURE,
            data=self._build_scene_structure(),
        ))

        # 7. END_OF_FILE
        blocks.append(PRCBlock(
            PRCBlockType.END_OF_FILE,
            data=b"",
        ))

        # Serializza i blocchi
        blocks_bytes = b"".join(b.to_bytes() for b in blocks)

        # Costruisce l'header (con dimensione totale corretta)
        total_size = PRC_HEADER_SIZE + len(blocks_bytes)
        file_header = self._build_file_header(total_size=total_size)

        # Aggiorna il numero di blocchi nell'header
        file_header = (
            file_header[:12]
            + struct.pack("<I", len(blocks))
            + file_header[16:]
        )

        # Concatena header + blocchi
        return file_header + blocks_bytes

    def write(self, mesh: MeshData, output_path: str | Path) -> Path:
        """
        Scrive un file PRC su disco.

        Parameters
        ----------
        mesh : MeshData
            Mesh da convertire.
        output_path : str | Path
            Percorso del file `.prc` risultante.

        Returns
        -------
        Path
            Percorso del file generato.
        """
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        data = self.to_bytes(mesh)
        output.write_bytes(data)

        return output


# --- API di alto livello ---

def mesh_to_prc(
    mesh: MeshData,
    output_path: str | Path,
    *,
    version_major: int = PRC_VERSION_MAJOR,
    version_minor: int = PRC_VERSION_MINOR,
    unit_scale: float = 1.0,
) -> Path:
    """
    Converte una mesh in un file PRC (ISO 14739-1).

    Parameters
    ----------
    mesh : MeshData
        Mesh da convertire.
    output_path : str | Path
        Percorso del file `.prc` risultante.
    version_major : int
        Versione major del formato PRC.
    version_minor : int
        Versione minor del formato PRC.
    unit_scale : float
        Scala dell'unità di misura.

    Returns
    -------
    Path
        Percorso del file generato.

    Examples
    --------
    >>> from mesh2u3d.prc import mesh_to_prc
    >>> mesh_to_prc(mesh, "model.prc")
    """
    writer = PRCWriter(
        version_major=version_major,
        version_minor=version_minor,
        unit_scale=unit_scale,
    )
    return writer.write(mesh, output_path)


__all__ = [
    "PRCWriter",
    "mesh_to_prc",
    "PRCError",
]
