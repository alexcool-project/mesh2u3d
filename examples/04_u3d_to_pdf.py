"""Test: U3D -> PDF con annotazione 3D."""
from pathlib import Path

from mesh2u3d.pdf.embedder import embed_u3d_in_pdf


def main() -> None:
    u3d_path = Path("examples/cube.u3d")
    pdf_path = Path("examples/cube.pdf")

    if not u3d_path.exists():
        raise FileNotFoundError(
            f"Prima esegui examples/03_mesh_to_u3d.py per creare {u3d_path}"
        )

    embed_u3d_in_pdf(u3d_path, pdf_path, title="Test Cube 3D")

    size = pdf_path.stat().st_size
    print(f"PDF scritto: {pdf_path} ({size} byte)")

    data = pdf_path.read_bytes()
    print(f"Header PDF: {data[:8]}")

    assert data[:5] == b"%PDF-", "Header PDF non valido"
    assert size > 1000, "PDF troppo piccolo"
    print("\nOK - PDF 3D generato.")
    print("Apri il file con Adobe Acrobat Reader DC per vedere il cubo 3D.")


if __name__ == "__main__":
    main()