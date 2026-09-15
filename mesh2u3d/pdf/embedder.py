"""Incorpora uno stream U3D in un PDF 1.7 come annotazione 3D."""
from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    ArrayObject,
    DecodedStreamObject,
    DictionaryObject,
    NameObject,
    NumberObject,
)


def _add_u3d_stream(writer: PdfWriter, u3d_bytes: bytes) -> DictionaryObject:
    """Crea stream PDF /EmbeddedFile con subtype /U3D."""
    stream = DecodedStreamObject()
    stream.set_data(u3d_bytes)
    stream.update({
        NameObject("/Type"): NameObject("/EmbeddedFile"),
        NameObject("/Subtype"): NameObject("/U3D"),
    })
    return writer._add_object(stream)


def _add_3d_dict(writer: PdfWriter, stream_ref: DictionaryObject) -> DictionaryObject:
    """Dizionario /3D che referenzia lo stream U3D."""
    d = DictionaryObject()
    d.update({
        NameObject("/Type"): NameObject("/3D"),
        NameObject("/Subtype"): NameObject("/U3D"),
        NameObject("/Stream"): stream_ref,
    })
    return writer._add_object(d)


def _add_3d_annotation(
    writer: PdfWriter,
    page,
    ddd_ref: DictionaryObject,
    rect: tuple[float, float, float, float],
) -> None:
    """Aggiunge un'annotazione /3D alla pagina PDF."""
    annot = DictionaryObject()
    annot.update({
        NameObject("/Type"): NameObject("/Annot"),
        NameObject("/Subtype"): NameObject("/3D"),
        NameObject("/Rect"): ArrayObject([NumberObject(v) for v in rect]),
        NameObject("/F"): NumberObject(4),
        NameObject("/3DD"): ddd_ref,
        NameObject("/3DV"): NameObject("/F"),
        NameObject("/3DA"): NameObject("/PO"),
    })
    annot_ref = writer._add_object(annot)

    if "/Annots" not in page:
        page[NameObject("/Annots")] = ArrayObject()
    page[NameObject("/Annots")].append(annot_ref)


def embed_u3d_in_pdf(
    u3d_path: str | Path,
    pdf_output: str | Path,
    *,
    pdf_base: str | Path | None = None,
    rect: tuple[float, float, float, float] = (50.0, 400.0, 545.0, 800.0),
    title: str = "3D Model",
) -> Path:
    """
    Crea un PDF 1.7 con annotazione 3D incorporata.

    Parameters
    ----------
    u3d_path : percorso al file .u3d
    pdf_output : percorso PDF risultante
    pdf_base : PDF esistente (opzionale) a cui aggiungere l'annotazione
    rect : bounding box dell'annotazione (punti PDF)
    title : titolo del PDF
    """
    u3d_bytes = Path(u3d_path).read_bytes()

    writer = PdfWriter()
    # Forza PDF 1.7 (richiesto per annotazioni 3D)
    writer.pdf_header = b"%PDF-1.7"

    if pdf_base:
        reader = PdfReader(str(pdf_base))
        for page in reader.pages:
            writer.add_page(page)
    else:
        writer.add_blank_page(width=595, height=842)  # A4

    stream_ref = _add_u3d_stream(writer, u3d_bytes)
    ddd_ref = _add_3d_dict(writer, stream_ref)
    _add_3d_annotation(writer, writer.pages[0], ddd_ref, rect)

    writer.add_metadata({
        "/Title": title,
        "/Creator": "mesh2u3d",
        "/Producer": "mesh2u3d",
    })

    with open(pdf_output, "wb") as f:
        writer.write(f)

    return Path(pdf_output)