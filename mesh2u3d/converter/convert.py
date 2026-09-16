"""
Converter universale per mesh 3D.

Fornisce una singola funzione `convert_3d_file()` che:
    - Legge qualsiasi formato mesh supportato da MeshReader
    - Scrive qualsiasi formato di output supportato (U3D, HTML, PDF)
    - Supporta batch processing (lista di file)

Architettura sinergica (Fase 1 + 2 + 3):
    - Fase 1: conversione base multi-formato
    - Fase 2: preservazione texture PBR (parametro preserve_textures)
    - Fase 3: batch processing e multi-mesh (parametro batch)

Autore: alexcool-project
Licenza: MIT
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from ..io.mesh_reader import MeshReader, MeshData
from ..u3d.writer import mesh_to_u3d
from ..html.writer import mesh_to_html
from ..pdf.embedder import embed_u3d_in_pdf


# --- Formati supportati ---

SUPPORTED_INPUT_FORMATS: set[str] = {
    "stl", "obj", "ply", "glb", "gltf", "off", "dae", "3mf", "fbx",
}

SUPPORTED_OUTPUT_FORMATS: set[str] = {
    "u3d", "html", "pdf",
}


# --- Eccezioni custom ---

class ConversionError(Exception):
    """Errore durante la conversione di un file 3D."""
    pass


# --- Risultato della conversione ---

@dataclass
class ConversionResult:
    """Risultato di una conversione."""
    input_path: str
    output_path: str
    input_format: str
    output_format: str
    success: bool
    error: str | None = None
    mesh_stats: dict[str, Any] = field(default_factory=dict)


# --- Helper interni ---

def _normalize_ext(path: str | Path) -> str:
    """Estrae l'estensione normalizzata (senza punto, minuscola)."""
    return Path(path).suffix.lower().lstrip(".")


def _validate_input(path: str | Path) -> tuple[Path, str]:
    """Valida il file di input e restituisce (path, formato)."""
    p = Path(path)
    if not p.exists():
        raise ConversionError(f"File di input non trovato: {p}")
    if not p.is_file():
        raise ConversionError(f"Il percorso non è un file: {p}")
    ext = _normalize_ext(p)
    if ext not in SUPPORTED_INPUT_FORMATS:
        raise ConversionError(
            f"Formato di input non supportato: .{ext}. "
            f"Supportati: {sorted(SUPPORTED_INPUT_FORMATS)}"
        )
    return p, ext


def _validate_output(path: str | Path) -> tuple[Path, str]:
    """Valida il file di output e restituisce (path, formato)."""
    p = Path(path)
    ext = _normalize_ext(p)
    if ext not in SUPPORTED_OUTPUT_FORMATS:
        raise ConversionError(
            f"Formato di output non supportato: .{ext}. "
            f"Supportati: {sorted(SUPPORTED_OUTPUT_FORMATS)}"
        )
    p.parent.mkdir(parents=True, exist_ok=True)
    return p, ext


def _mesh_stats(mesh: MeshData) -> dict[str, Any]:
    """Estrae statistiche dalla mesh."""
    return {
        "vertex_count": mesh.vertex_count,
        "triangle_count": mesh.triangle_count,
        "name": getattr(mesh, "name", "unknown"),
    }


# --- Funzione principale (Fase 1) ---

def convert_3d_file(
    input_path: str | Path,
    output_path: str | Path,
    *,
    preserve_textures: bool = False,
    batch: bool = False,
    scene: Any = None,
    title: str | None = None,
    source_format: str | None = None,
    lang: str = "it",
    **kwargs: Any,
) -> ConversionResult:
    """
    Converte un file mesh 3D tra formati supportati.

    Parameters
    ----------
    input_path : str | Path
        Percorso del file di input (STL, OBJ, PLY, GLB, GLTF, OFF, DAE, 3MF, FBX).
    output_path : str | Path
        Percorso del file di output (U3D, HTML, PDF).
    preserve_textures : bool, default False
        [FASE 2] Preserva texture e materiali PBR (per GLB/GLTF).
    batch : bool, default False
        [FASE 3] Modalità batch (input è una lista di file).
    scene : Any, default None
        [FASE 3] Scena multi-mesh (sovrascrive input_path).
    title : str | None
        Titolo del progetto (usato per HTML/PDF).
    source_format : str | None
        Formato di origine (auto-rilevato se None).
    lang : str, default "it"
        Lingua per il viewer HTML ("it" o "en").
    **kwargs
        Parametri aggiuntivi passati ai writer specifici.

    Returns
    -------
    ConversionResult
        Risultato della conversione con stato e statistiche.

    Examples
    --------
    >>> from mesh2u3d import convert_3d_file
    >>> result = convert_3d_file("cube.stl", "cube.u3d")
    >>> result = convert_3d_file("model.glb", "model.html", preserve_textures=True)
    """
    # Fase 3: modalità batch
    if batch and isinstance(input_path, (list, tuple)):
        return _convert_batch(input_path, output_path, **kwargs)

    # Fase 1: conversione singola
    try:
        in_p, in_ext = _validate_input(input_path)
        out_p, out_ext = _validate_output(output_path)

        mesh = MeshReader.read(str(in_p))
        if mesh is None:
            raise ConversionError(f"Impossibile leggere il file: {in_p}")

        # Fase 2: lettura texture (predisposizione)
        textures = None
        if preserve_textures and in_ext in ("glb", "gltf"):
            try:
                from ..io.texture_reader import read_textures
                textures = read_textures(str(in_p))
            except ImportError:
                textures = None

        src_fmt = source_format or in_ext.upper()

        if out_ext == "u3d":
            mesh_to_u3d(mesh, str(out_p))
        elif out_ext == "html":
            mesh_to_html(
                mesh,
                str(out_p),
                title=title or mesh.name,
                source_format=src_fmt,
                lang=lang,
            )
        elif out_ext == "pdf":
            with tempfile.NamedTemporaryFile(suffix=".u3d", delete=False) as tmp:
                tmp_u3d = Path(tmp.name)
            try:
                mesh_to_u3d(mesh, str(tmp_u3d))
                embed_u3d_in_pdf(
                    tmp_u3d,
                    out_p,
                    title=title or mesh.name,
                )
            finally:
                try:
                    tmp_u3d.unlink()
                except OSError:
                    pass
        else:
            raise ConversionError(f"Formato di output non gestito: .{out_ext}")

        return ConversionResult(
            input_path=str(in_p),
            output_path=str(out_p),
            input_format=in_ext,
            output_format=out_ext,
            success=True,
            mesh_stats=_mesh_stats(mesh),
        )

    except ConversionError as e:
        return ConversionResult(
            input_path=str(input_path),
            output_path=str(output_path),
            input_format=_normalize_ext(input_path),
            output_format=_normalize_ext(output_path),
            success=False,
            error=str(e),
        )
    except Exception as e:
        return ConversionResult(
            input_path=str(input_path),
            output_path=str(output_path),
            input_format=_normalize_ext(input_path),
            output_format=_normalize_ext(output_path),
            success=False,
            error=f"Errore inatteso: {e}",
        )


# --- Funzione batch (Fase 3) ---

def convert_3d_files(
    input_paths: Iterable[str | Path],
    output_dir: str | Path,
    *,
    output_format: str = "u3d",
    **kwargs: Any,
) -> list[ConversionResult]:
    """
    [FASE 3] Converte una lista di file in una directory di output.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    results: list[ConversionResult] = []
    for in_path in input_paths:
        in_p = Path(in_path)
        out_name = in_p.stem + "." + output_format.lstrip(".")
        out_p = out_dir / out_name
        result = convert_3d_file(in_p, out_p, **kwargs)
        results.append(result)
    return results


def _convert_batch(
    input_paths: Iterable[str | Path],
    output_dir: str | Path,
    **kwargs: Any,
) -> ConversionResult:
    """Wrapper interno per modalità batch."""
    output_format = kwargs.pop("output_format", "u3d")
    results = convert_3d_files(input_paths, output_dir, output_format=output_format, **kwargs)
    if not results:
        raise ConversionError("Nessun file convertito in modalità batch")
    return results[0]
