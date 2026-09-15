"""Test: genera un U3D e lo valida con il validator indipendente."""
from pathlib import Path

import trimesh

from mesh2u3d.io.mesh_reader import MeshReader
from mesh2u3d.u3d.writer import mesh_to_u3d
from mesh2u3d.u3d.validator import validate_u3d


def main() -> None:
    out_dir = Path("examples")
    out_dir.mkdir(exist_ok=True)

    stl_path = out_dir / "cube_val.stl"
    u3d_path = out_dir / "cube_val.u3d"

    # Genera mesh di test
    cube = trimesh.creation.box(extents=(1.0, 1.0, 1.0))
    cube.export(str(stl_path))

    # Leggi + genera U3D
    mesh = MeshReader.read(stl_path)
    mesh_to_u3d(mesh, u3d_path)
    print(f"U3D generato: {u3d_path} ({u3d_path.stat().st_size} byte)")

    # Valida
    report = validate_u3d(u3d_path)
    print(report.summary())

    if not report.is_valid:
        raise SystemExit("❌ Validazione FALLITA")

    print("OK - file U3D valido")


if __name__ == "__main__":
    main()