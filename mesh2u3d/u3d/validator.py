"""
Validatore U3D indipendente.

Legge un file .u3d e verifica:
  - Magic number "U3D\\0" oppure "U3DH"
  - Versione, dimensione, encoding, compressione
  - Sequenza dei blocchi e loro dimensioni
  - Tipi di blocco riconosciuti

Non dipende da Adobe né da altre librerie proprietarie.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass, field
from pathlib import Path

from .blocks import BlockType


_FILE_HEADER_STRUCT = struct.Struct("<4sHIIII If H")
_BLOCK_HEADER_STRUCT = struct.Struct("<III")


@dataclass
class BlockInfo:
    index: int
    block_type: int
    type_name: str
    data_size: int
    metadata_size: int
    offset: int


@dataclass
class U3DValidationReport:
    path: Path
    file_size: int
    magic: bytes
    version_major: int
    version_minor: int
    profile_id: int
    declared_size: int
    encoding: int
    compression: int
    unit_scale: float
    blocks: list[BlockInfo] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def summary(self) -> str:
        lines = []
        lines.append("=" * 70)
        lines.append(f"U3D VALIDATION REPORT: {self.path.name}")
        lines.append("=" * 70)
        lines.append(f"File size:          {self.file_size} byte")
        lines.append(f"Magic:              {self.magic!r}")
        lines.append(f"Version:            {self.version_major}.{self.version_minor}")
        lines.append(f"Profile ID:         {self.profile_id}")
        lines.append(f"Declared size:      {self.declared_size} byte")
        lines.append(f"Encoding:           {self.encoding} (0=UTF-8, 1=UTF-16)")
        lines.append(f"Compression:        {self.compression} (0=None)")
        lines.append(f"Unit scale:         {self.unit_scale}")
        lines.append(f"Blocks found:       {len(self.blocks)}")
        lines.append("")
        lines.append("Blocks (in ordine di apparizione):")
        lines.append("-" * 70)
        for b in self.blocks:
            lines.append(
                f"  [{b.index:02d}] @ 0x{b.offset:06X} "
                f"{b.type_name:<22} data={b.data_size:>8} byte  "
                f"meta={b.metadata_size}"
            )
        lines.append("-" * 70)
        lines.append("")
        if self.warnings:
            lines.append(f"⚠  WARNINGS ({len(self.warnings)}):")
            for w in self.warnings:
                lines.append(f"   - {w}")
            lines.append("")
        if self.errors:
            lines.append(f"❌ ERRORS ({len(self.errors)}):")
            for e in self.errors:
                lines.append(f"   - {e}")
            lines.append("")
        else:
            lines.append("✅ VALIDAZIONE SUPERATA")
            lines.append("")
        return "\n".join(lines)


def _block_type_name(bt: int) -> str:
    try:
        return BlockType(bt).name
    except ValueError:
        return f"UNKNOWN(0x{bt:08X})"


def validate_u3d(path: str | Path) -> U3DValidationReport:
    """Legge e valida un file U3D. Non solleva eccezioni: accumula errori."""
    path = Path(path)
    data = path.read_bytes()
    size = len(data)

    report = U3DValidationReport(
        path=path,
        file_size=size,
        magic=b"",
        version_major=0,
        version_minor=0,
        profile_id=0,
        declared_size=0,
        encoding=0,
        compression=0,
        unit_scale=0.0,
    )

    # --- File header ---
    if size < _FILE_HEADER_STRUCT.size:
        report.errors.append(
            f"File troppo corto per un header U3D: {size} byte"
        )
        return report

    (
        magic,
        version,
        profile_id,
        declaration_size,
        declared_size,
        encoding,
        compression,
        unit_scale,
        reserved,
    ) = _FILE_HEADER_STRUCT.unpack_from(data, 0)

    report.magic = magic
    report.version_major = (version >> 8) & 0xFF
    report.version_minor = version & 0xFF
    report.profile_id = profile_id
    report.declared_size = declared_size
    report.encoding = encoding
    report.compression = compression
    report.unit_scale = unit_scale

    if magic not in (b"U3D\x00", b"U3DH"):
        report.errors.append(f"Magic number non valido: {magic!r}")
    if declared_size != size:
        report.warnings.append(
            f"Dimensione dichiarata ({declared_size}) != dimensione reale ({size})"
        )
    if compression != 0:
        report.warnings.append(
            f"Compressione non standard: {compression} (atteso 0)"
        )
    if encoding not in (0, 1):
        report.warnings.append(f"Encoding sconosciuto: {encoding}")

    # --- Blocchi ---
    offset = _FILE_HEADER_STRUCT.size
    block_index = 0

    while offset < size:
        if offset + _BLOCK_HEADER_STRUCT.size > size:
            report.errors.append(
                f"Header blocco troncato @ offset 0x{offset:X}"
            )
            break

        bt, dsize, msize = _BLOCK_HEADER_STRUCT.unpack_from(data, offset)
        total_block_size = _BLOCK_HEADER_STRUCT.size + dsize + msize
        block_end = offset + total_block_size

        if block_end > size:
            report.errors.append(
                f"Blocco {block_index} eccede il file "
                f"(offset 0x{offset:X}, dichiara {total_block_size} byte)"
            )
            break

        report.blocks.append(BlockInfo(
            index=block_index,
            block_type=bt,
            type_name=_block_type_name(bt),
            data_size=dsize,
            metadata_size=msize,
            offset=offset,
        ))

        if bt == BlockType.FILE_HEADER:
            report.warnings.append(
                "Trovato blocco FILE_HEADER nel body (già nell'header fisso)"
            )

        offset = block_end
        block_index += 1

    # --- Verifica presenza blocchi obbligatori ---
    block_names = {b.type_name for b in report.blocks}
    required = {
        "MESH_DECLARATION",
        "MESH_RESOURCE",
    }
    missing = required - block_names
    if missing:
        report.errors.append(
            f"Blocchi obbligatori mancanti: {sorted(missing)}"
        )

    recommended = {
        "MODIFIER_CHAIN",
        "MODEL_NODE",
        "GROUP_NODE",
        "VIEW_NODE",
    }
    missing_rec = recommended - block_names
    if missing_rec:
        report.warnings.append(
            f"Blocchi consigliati mancanti (viewer potrebbe rifiutare): "
            f"{sorted(missing_rec)}"
        )

    return report
