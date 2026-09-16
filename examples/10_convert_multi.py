"""
Esempio 10 — Converter multi-formato (Fase 1 + Fase 2 + Fase 3).

Mostra come usare:
    - Fase 1: convert_3d_file() per conversioni base
    - Fase 2: preserve_textures=True per texture PBR
    - Fase 3: convert_3d_files() per batch processing

Esegui:
    python examples/10_convert_multi.py
"""

from pathlib import Path
import tempfile

from mesh2u3d import convert_3d_file, convert_3d_files


def main():
    """Esempio completo di conversione multi-formato."""
    tmp = Path(tempfile.mkdtemp(prefix="mesh2u3d_example_"))
    print(f"📁 Directory di lavoro: {tmp}")

    # --- FASE 1: Conversione base ---
    print("\n=== FASE 1: Conversione base ===")

    import trimesh
    cube = trimesh.creation.box((1, 1, 1))
    cube.export(str(tmp / "cube.stl"))
    print(f"✅ Creato: {tmp / 'cube.stl'}")

    result = convert_3d_file(tmp / "cube.stl", tmp / "cube.u3d")
    print(f"   STL → U3D: {'✅' if result.success else '❌'}")
    if result.success:
        print(f"      Vertici: {result.mesh_stats['vertex_count']}")
        print(f"      Triangoli: {result.mesh_stats['triangle_count']}")

    result = convert_3d_file(
        tmp / "cube.stl", tmp / "cube_it.html",
        title="Il mio cubo", lang="it"
    )
    print(f"   STL → HTML (IT): {'✅' if result.success else '❌'}")

    result = convert_3d_file(
        tmp / "cube.stl", tmp / "cube_en.html",
        title="My cube", lang="en"
    )
    print(f"   STL → HTML (EN): {'✅' if result.success else '❌'}")

    result = convert_3d_file(tmp / "cube.stl", tmp / "cube.pdf", title="Il mio cubo")
    print(f"   STL → PDF: {'✅' if result.success else '❌'}")

    # --- FASE 2: Texture PBR (predisposizione) ---
    print("\n=== FASE 2: Texture PBR (predisposizione) ===")
    result = convert_3d_file(
        tmp / "cube.stl", tmp / "cube_tex.html",
        preserve_textures=True,
        title="Cubo con texture (predisposizione)"
    )
    print(f"   STL → HTML (preserve_textures=True): {'✅' if result.success else '❌'}")

    # --- FASE 3: Batch processing ---
    print("\n=== FASE 3: Batch processing ===")
    for i, size in enumerate([1, 2, 3]):
        mesh = trimesh.creation.box((size, size, size))
        mesh.export(str(tmp / f"cube_{i}.stl"))
    print(f"✅ Creati 3 file: cube_0.stl, cube_1.stl, cube_2.stl")

    results = convert_3d_files(
        [tmp / "cube_0.stl", tmp / "cube_1.stl", tmp / "cube_2.stl"],
        tmp / "out_u3d",
        output_format="u3d",
    )
    print(f"   Batch U3D: {sum(1 for r in results if r.success)}/{len(results)} completati")

    results = convert_3d_files(
        [tmp / "cube_0.stl", tmp / "cube_1.stl", tmp / "cube_2.stl"],
        tmp / "out_html",
        output_format="html",
        lang="en",
    )
    print(f"   Batch HTML (EN): {sum(1 for r in results if r.success)}/{len(results)} completati")

    print("\n=== Riepilogo ===")
    print(f"📁 File generati in: {tmp}")
    for f in sorted(tmp.rglob("*")):
        if f.is_file():
            size = f.stat().st_size
            print(f"   {f.relative_to(tmp)} ({size:,} bytes)")


if __name__ == "__main__":
    main()
