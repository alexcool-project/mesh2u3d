"""Analizza un file U3D di riferimento per capire la struttura corretta."""
from __future__ import annotations

import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from mesh2u3d.u3d.blocks import BlockType


_FILE_HEADER_STRUCT = struct.Struct("<4sHIIII If H")
_BLOCK_HEADER_STRUCT = struct.Struct("<III")


def _name(bt: int) -> str:
    try:
        return BlockType(bt).name
    except ValueError:
        return f"UNKNOWN(0x{bt:08X})"


def analyze(path: Path) -> None:
    data = path.read_bytes()
    size = len(data)

    print("=" * 75)
    print(f"ANALISI FILE U3D: {path.name}")
    print("=" * 75)
    print(f"Dimensione totale: {size} byte ({size / 1024 / 1024:.2f} MB)")
    print()

    # --- File header (32 byte) ---
    (
        magic, version, profile_id, declaration_size,
        declared_size, encoding, compression, unit_scale, reserved,
    ) = _FILE_HEADER_STRUCT.unpack_from(data, 0)

    print("FILE HEADER (32 byte):")
    print(f"  Magic:             {magic!r}")
    print(f"  Version:           {(version >> 8) & 0xFF}.{version & 0xFF}")
    print(f"  Profile ID:        {profile_id}")
    print(f"  Declaration size:  {declaration_size}")
    print(f"  Declared size:     {declared_size}")
    print(f"  Encoding:          {encoding}")
    print(f"  Compression:       {compression}")
    print(f"  Unit scale:        {unit_scale}")
    print(f"  Reserved:          {reserved}")
    print()

    # --- Blocchi ---
    print("BLOCCHI (in ordine di apparizione, max 50):")
    print("-" * 75)
    print(f"{'Idx':>3}  {'Offset':>8}  {'Tipo':<22}  {'DataSize':>10}  {'MetaSize':>8}")
    print("-" * 75)

    offset = _FILE_HEADER_STRUCT.size
    idx = 0
    block_counts: dict[str, int] = {}

    while offset < size and idx < 50:
        if offset + _BLOCK_HEADER_STRUCT.size > size:
            print(f"  [!] Header blocco troncato @ 0x{offset:X}")
            break

        bt, dsize, msize = _BLOCK_HEADER_STRUCT.unpack_from(data, offset)
        total = _BLOCK_HEADER_STRUCT.size + dsize + msize
        name = _name(bt)

        print(
            f"{idx:>3}  0x{offset:06X}  {name:<22}  "
            f"{dsize:>10}  {msize:>8}"
        )

        block_counts[name] = block_counts.get(name, 0) + 1

        if bt == int(BlockType.MESH_DECLARATION):
            data_start = offset + _BLOCK_HEADER_STRUCT.size
            preview = data[data_start:data_start + 32].hex()
            print(f"      └─ primi 32 byte: {preview}")

        if bt == int(BlockType.MESH_RESOURCE):
            data_start = offset + _BLOCK_HEADER_STRUCT.size
            preview = data[data_start:data_start + 32].hex()
            print(f"      └─ primi 32 byte: {preview}")

        if bt == int(BlockType.MODEL_NODE):
            data_start = offset + _BLOCK_HEADER_STRUCT.size
            name_len = struct.unpack_from("<I", data, data_start)[0]
            if name_len < 1000:
                name_bytes = data[data_start + 4:data_start + 4 + name_len]
                print(f"      └─ nome modello: {name_bytes.decode('utf-8', errors='replace')!r}")

        offset += total
        idx += 1

    print("-" * 75)
    print(f"Totale blocchi analizzati: {idx}")
    if offset < size:
        print(f"Bytes non analizzati: {size - offset} (oltre il limite di 50 blocchi)")
    else:
        print(f"✅ File consumato completamente")

    print()
    print("CONTEGGIO TIPI DI BLOCCO:")
    print("-" * 75)
    for name, count in sorted(block_counts.items()):
        print(f"  {name:<25} x {count}")

    print()
    print("CONFRONTO CON IL NOSTRO WRITER:")
    print("-" * 75)
    our_blocks = {
        "MESH_DECLARATION", "MESH_RESOURCE", "MODIFIER_CHAIN",
        "SHADER", "MATERIAL_RESOURCE", "MODEL_NODE",
        "GROUP_NODE", "VIEW_NODE", "LIGHT_NODE",
    }
    ref_blocks = set(block_counts.keys())
    missing = ref_blocks - our_blocks
    print(f"  Blocchi che il riferimento ha e noi NO:")
    if missing:
        for m in sorted(missing):
            print(f"    ❌ {m} (x{block_counts[m]})")
    else:
        print(f"    (nessuno)")
    print()
    print(f"  Blocchi che noi abbiamo e il riferimento NO:")
    extra = our_blocks - ref_blocks
    if extra:
        for e in sorted(extra):
            print(f"    ⚠  {e}")
    else:
        print(f"    (nessuno)")


def main() -> None:
    ref_path = Path("reference/reference.u3d")
    if not ref_path.exists():
        print(f"❌ File non trovato: {ref_path}")
        sys.exit(1)

    analyze(ref_path)


if __name__ == "__main__":
    main()