"""Test: genera un HTML 3D self-contained da una mesh STL."""
from pathlib import Path

import trimesh

from mesh2u3d.io.mesh_reader import MeshReader
from mesh2u3d.html.writer import mesh_to_html


def main() -> None:
    out_dir = Path("examples")
    out_dir.mkdir(exist_ok=True)

    # Crea mesh di test (cubo)
    stl_path = out_dir / "cube_html.stl"
    html_path = out_dir / "cube.html"

    cube = trimesh.creation.box(extents=(1.0, 1.0, 1.0))
    cube.export(str(stl_path))
    print(f"STL di input: {stl_path}")

    # Converti in HTML
    mesh = MeshReader.read(stl_path)
    mesh_to_html(mesh, html_path, title="Cubo di test")
    print(f"HTML scritto: {html_path} ({html_path.stat().st_size} byte)")

    # Verifica contenuto
    content = html_path.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content, "HTML non valido"
    assert "three.module.js" in content, "three.js non embedded"
    assert "MESH_DATA" in content, "Dati mesh non embedded"
    assert content.count("vertices_flat") >= 1, "Vertici mancanti"

    print("\nOK - HTML 3D generato correttamente.")
    print(f"Apri il file nel browser: {html_path.resolve()}")


if __name__ == "__main__":
    main()