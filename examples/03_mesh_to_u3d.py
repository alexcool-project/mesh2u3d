"""Test: mesh STL -> file U3D."""
from pathlib import Path

import trimesh

from mesh2u3d.io.mesh_reader import MeshReader
from mesh2u3d.u3d.writer import mesh_to_u3d


def main() -> None:
    out_dir = Path("examples")
    out_dir.mkdir(exist_ok=True)
    stl_path = out_dir / "cube.stl"
    u3d_path = out_dir / "cube.u3d"

    # Crea STL di test
    cube = trimesh.creation.box(extents=(1.0, 1.0, 1.0))
    cube.export(str(stl_path))

    # Leggi e converti in U3D
    mesh = MeshReader.read(stl_path)
    mesh_to_u3d(mesh, u3d_path)

    size = u3d_path.stat().st_size
    print(f"U3D scritto: {u3d_path} ({size} byte)")

    data = u3d_path.read_bytes()
    print(f"Magic number: {data[:4]}")
    print(f"Primi 32 byte (header): {data[:32].hex()}")

    # Accetta sia "U3D\x00" (ECMA-363 standard) sia "U3DH" (variante Adobe)
    assert data[:4] in (b"U3D\x00", b"U3DH"), (
        f"Magic number U3D non valido: {data[:4]!r}"
    )
    assert size > 32, "File U3D troppo piccolo"
    print("\nOK - file U3D generato correttamente")


if __name__ == "__main__":
    main()