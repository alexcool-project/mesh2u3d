"""Decomprime un file U3D compresso con header 'U3DH'."""
from __future__ import annotations

import struct
import sys
import zlib
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


def decompress_reference(src: Path, dst: Path) -> None:
    data = src.read_bytes()
    size = len(data)

    print("=" * 75)
    print(f"DECOMPRESSIONE FILE U3D: {src.name}")
    print("=" * 75)
    print(f"Dimensione totale compressa: {size} byte ({size / 1024 / 1024:.2f} MB)")
    print()

    # --- Header ---
    (
        magic, version, profile_id, declaration_size,
        declared_size, encoding, compression, unit_scale, reserved,
    ) = _FILE_HEADER_STRUCT.unpack_from(data, 0)

    print("HEADER (raw):")
    print(f"  Magic:             {magic!r}")
    print(f"  Version:           {(version >> 8) & 0xFF}.{version & 0xFF}")
    print(f"  Compression:       {compression}")
    print()

    if magic != b"U3DH":
        print(f"⚠ Magic non è 'U3DH' — è {magic!r}")
        print("  Provo comunque a cercare un flusso zlib nei dati...")

    # --- Cerca un flusso zlib nel body ---
    # Il body parte dopo l'header (32 byte)
    body = data[32:]

    # Prova zlib.decompress
    try:
        decompressed = zlib.decompress(body)
        print(f"✅ Decompresso con successo!")
        print(f"   Byte compressi:    {len(body)}")
        print(f"   Byte decompressi:  {len(decompressed)}")
        print(f"   Ratio:             {len(decompressed) / len(body):.2f}x")
    except zlib.error as e:
        print(f"❌ zlib.decompress fallito: {e}")

        # Prova a cercare l'offset giusto
        print("\n🔍 Provo a cercare l'offset del flusso zlib...")
        # Un flusso zlib inizia con 0x78 (0x78 0x01, 0x78 0x9C, 0x78 0xDA)
        for offset in range(32, min(len(data), 200)):
            if data[offset] == 0x78 and data[offset + 1] in (0x01, 0x5E, 0x9C, 0xDA):
                try:
                    decompressed = zlib.decompress(data[offset:])
                    print(f"✅ Trovato flusso zlib @ offset 0x{offset:X}")
                    print(f"   Byte decompressi: {len(decompressed)}")
                    break
                except zlib.error:
                    continue
        else:
            print("❌ Nessun flusso zlib trovato")
            print("\nProviamo raw deflate (-15):")
            for offset in range(32, min(len(data), 500)):
                try:
                    d = zlib.decompressobj(-15)
                    decompressed = d.decompress(data[offset:])
                    if len(decompressed) > 100:
                        print(f"✅ Trovato raw deflate @ offset 0x{offset:X}")
                        print(f"   Byte decompressi: {len(decompressed)}")
                        break
                except zlib.error:
                    continue
            else:
                print("❌ Nessun raw deflate trovato")
                return

    # --- Scrivi il file decompresso ---
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(decompressed)
    print(f"\n💾 File decompresso scritto in: {dst}")

    # --- Analizza il file decompresso ---
    print()
    print("=" * 75)
    print(f"ANALISI DEL FILE DECOMPRESSO")
    print("=" * 75)

    (
        magic2, version2, profile2, decl2,
        declared2, enc2, comp2, scale2, res2,
    ) = _FILE_HEADER_STRUCT.unpack_from(decompressed, 0)

    print(f"Magic:        {magic2!r}")
    print(f"Version:      {(version2 >> 8) & 0xFF}.{version2 & 0xFF}")
    print(f"Compression:  {comp2}")
    print(f"Declared:     {declared2} byte")
    print(f"Actual:       {len(decompressed)} byte")
    print()

    # Analizza blocchi
    offset = _FILE_HEADER_STRUCT.size
    idx = 0
    counts: dict[str, int] = {}

    print(f"{'Idx':>3}  {'Offset':>8}  {'Tipo':<22}  {'DataSize':>10}  {'MetaSize':>8}")
    print("-" * 75)

    while offset < len(decompressed) and idx < 100:
        if offset + _BLOCK_HEADER_STRUCT.size > len(decompressed):
            print(f"  [!] Header troncato @ 0x{offset:X}")
            break

        bt, dsize, msize = _BLOCK_HEADER_STRUCT.unpack_from(decompressed, offset)
        total = _BLOCK_HEADER_STRUCT.size + dsize + msize
        name = _name(bt)

        print(f"{idx:>3}  0x{offset:06X}  {name:<22}  {dsize:>10}  {msize:>8}")
        counts[name] = counts.get(name, 0) + 1

        offset += total
        idx += 1

    print("-" * 75)
    print(f"Totale blocchi: {idx}")
    print()
    print("CONTEGGIO:")
    for name, c in sorted(counts.items()):
        print(f"  {name:<25} x {c}")

    # Confronto
    print()
    print("CONFRONTO CON IL NOSTRO WRITER:")
    our = {
        "MESH_DECLARATION", "MESH_RESOURCE", "MODIFIER_CHAIN",
        "SHADER", "MATERIAL_RESOURCE", "MODEL_NODE",
        "GROUP_NODE", "VIEW_NODE", "LIGHT_NODE",
    }
    ref = set(counts.keys())
    missing = ref - our
    extra = our - ref
    print(f"  Blocchi che il riferimento ha e noi NO:")
    if missing:
        for m in sorted(missing):
            print(f"    ❌ {m} (x{counts[m]})")
    else:
        print(f"    (nessuno)")
    print(f"  Blocchi che noi abbiamo e il riferimento NO:")
    if extra:
        for e in sorted(extra):
            print(f"    ⚠  {e}")
    else:
        print(f"    (nessuno)")


def main() -> None:
    src = Path("reference/reference.u3d")
    dst = Path("reference/reference_decompressed.u3d")

    if not src.exists():
        print(f"❌ File non trovato: {src}")
        sys.exit(1)

    decompress_reference(src, dst)


if __name__ == "__main__":
    main()