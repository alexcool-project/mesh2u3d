"""Test: leggere una mesh STL e stamparne le proprietà."""
from pathlib import Path

import trimesh

from mesh2u3d.io.mesh_reader import MeshReader


def main() -> None:
    out_dir = Path("examples")
    out_dir.mkdir(exist_ok=True)
    stl_path = out_dir / "cube.stl"

    # Crea un cubo di test con trimesh
    cube = trimesh.creation.box(extents=(1.0, 1.0, 1.0))
    cube.export(str(stl_path))
    print(f"File STL creato: {stl_path}")

    # Leggi con MeshReader
    mesh = MeshReader.read(stl_path)
    print(f"Nome:      {mesh.name}")
    print(f"Vertici:   {mesh.vertex_count}")
    print(f"Triangoli: {mesh.triangle_count}")
    print(f"Primo vertice: {mesh.vertices[0]}")
    print(f"Primo triangolo: {mesh.triangles[0]}")

    assert mesh.vertex_count == 8, f"Attesi 8 vertici, trovati {mesh.vertex_count}"
    assert mesh.triangle_count == 12, f"Attesi 12 triangoli, trovati {mesh.triangle_count}"
    print("\nOK - lettura mesh funzionante")


if __name__ == "__main__":
    main()