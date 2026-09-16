"""
Incorpora stream U3D o PRC in un PDF 1.7 come annotazione 3D.

Supporta due formati:
    - U3D (ECMA-363) — supportato da Foxit, PDF-XChange, ecc.
    - PRC (ISO 14739-1) — supportato nativamente da Adobe Acrobat/Reader

Autore: alexcool-project
Licenza: MIT
"""

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


# --- Stream embedded file ---

def _add_embedded_stream(
    writer: PdfWriter,
    data: bytes,
    subtype: str,
) -> DictionaryObject:
    """
    Crea stream PDF /EmbeddedFile con subtype /U3D o /PRC.

    Parameters
    ----------
    writer : PdfWriter
        Writer PDF a cui aggiungere lo stream.
    data : bytes
        Contenuto binario (U3D o PRC).
    subtype : str
        Sottotipo: "U3D" o "PRC".
    """
    stream = DecodedStreamObject()
    stream.set_data(data)
    stream.update({
        NameObject("/Type"): NameObject("/EmbeddedFile"),
        NameObject("/Subtype"): NameObject(f"/{subtype}"),
    })
    return writer._add_object(stream)


# --- Dizionario /3D ---

def _add_3d_dict(
    writer: PdfWriter,
    stream_ref: DictionaryObject,
    subtype: str = "U3D",
) -> DictionaryObject:
    """
    Dizionario /3D che referenzia lo stream U3D o PRC.

    Parameters
    ----------
    writer : PdfWriter
        Writer PDF.
    stream_ref : DictionaryObject
        Riferimento allo stream embedded.
    subtype : str
        Sottotipo: "U3D" o "PRC".
    """
    d = DictionaryObject()
    d.update({
        NameObject("/Type"): NameObject("/3D"),
        NameObject("/Subtype"): NameObject(f"/{subtype}"),
        NameObject("/Stream"): stream_ref,
    })
    return writer._add_object(d)


# --- Annotazione 3D ---

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


# --- API U3D ---

def embed_u3d_in_pdf(
    u3d_path: str | Path,
    pdf_output: str | Path,
    *,
    pdf_base: str | Path | None = None,
    rect: tuple[float, float, float, float] = (50.0, 400.0, 545.0, 800.0),
    title: str = "3D Model",
) -> Path:
    """
    Crea un PDF 1.7 con annotazione 3D incorporata (U3D).

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
    writer.pdf_header = b"%PDF-1.7"

    if pdf_base:
        reader = PdfReader(str(pdf_base))
        for page in reader.pages:
            writer.add_page(page)
    else:
        writer.add_blank_page(width=595, height=842)  # A4

    stream_ref = _add_embedded_stream(writer, u3d_bytes, subtype="U3D")
    ddd_ref = _add_3d_dict(writer, stream_ref, subtype="U3D")
    _add_3d_annotation(writer, writer.pages[0], ddd_ref, rect)

    writer.add_metadata({
        "/Title": title,
        "/Creator": "mesh2u3d",
        "/Producer": "mesh2u3d",
    })

    with open(pdf_output, "wb") as f:
        writer.write(f)

    return Path(pdf_output)


# --- API PRC (NOVITÀ v0.2.0) ---

def embed_prc_in_pdf(
    prc_path: str | Path,
    pdf_output: str | Path,
    *,
    pdf_base: str | Path | None = None,
    rect: tuple[float, float, float, float] = (50.0, 400.0, 545.0, 800.0),
    title: str = "3D Model",
) -> Path:
    """
    Crea un PDF 1.7 con annotazione 3D incorporata (PRC).

    PRC è supportato nativamente da Adobe Acrobat/Reader.
    Questo è il metodo consigliato per la massima compatibilità.

    Parameters
    ----------
    prc_path : percorso al file .prc
    pdf_output : percorso PDF risultante
    pdf_base : PDF esistente (opzionale) a cui aggiungere l'annotazione
    rect : bounding box dell'annotazione (punti PDF)
    title : titolo del PDF
    """
    prc_bytes = Path(prc_path).read_bytes()

    writer = PdfWriter()
    writer.pdf_header = b"%PDF-1.7"

    if pdf_base:
        reader = PdfReader(str(pdf_base))
        for page in reader.pages:
            writer.add_page(page)
    else:
        writer.add_blank_page(width=595, height=842)  # A4

    stream_ref = _add_embedded_stream(writer, prc_bytes, subtype="PRC")
    ddd_ref = _add_3d_dict(writer, stream_ref, subtype="PRC")
    _add_3d_annotation(writer, writer.pages[0], ddd_ref, rect)

    writer.add_metadata({
        "/Title": title,
        "/Creator": "mesh2u3d",
        "/Producer": "mesh2u3d",
    })

    with open(pdf_output, "wb") as f:
        writer.write(f)

    return Path(pdf_output)


__all__ = [
    "embed_u3d_in_pdf",
    "embed_prc_in_pdf",
]
