"""
CLI per mesh2u3d — Entry point principale.

Comandi:
    convert: converte un file mesh in un altro formato
    batch: converte più file in una directory
    info: mostra informazioni su un file mesh
    validate: valida un file U3D

Autore: alexcool-project
Licenza: MIT
"""

from __future__ import annotations

import argparse
import sys
import glob

from .. import __version__
from ..converter import (
    convert_3d_file,
    convert_3d_files,
    SUPPORTED_OUTPUT_FORMATS,
)
from ..io.mesh_reader import MeshReader
from ..u3d.validator import validate_u3d


def cmd_convert(args: argparse.Namespace) -> int:
    """Comando: convert."""
    print(f"🔄 Conversione: {args.input} → {args.output}")
    result = convert_3d_file(
        args.input,
        args.output,
        preserve_textures=args.preserve_textures,
        title=args.title,
        lang=args.lang,
    )
    if result.success:
        print(f"✅ Conversione completata!")
        print(f"   Input:  {result.input_path} ({result.input_format})")
        print(f"   Output: {result.output_path} ({result.output_format})")
        if result.mesh_stats:
            print(f"   Vertici: {result.mesh_stats.get('vertex_count', 'N/A')}")
            print(f"   Triangoli: {result.mesh_stats.get('triangle_count', 'N/A')}")
        return 0
    else:
        print(f"❌ Errore: {result.error}", file=sys.stderr)
        return 1


def cmd_batch(args: argparse.Namespace) -> int:
    """Comando: batch."""
    files = []
    for pattern in args.inputs:
        files.extend(glob.glob(pattern))
    if not files:
        print("❌ Nessun file trovato", file=sys.stderr)
        return 1
    print(f"🔄 Batch: {len(files)} file → {args.output_dir} ({args.format})")
    results = convert_3d_files(
        files,
        args.output_dir,
        output_format=args.format,
        preserve_textures=args.preserve_textures,
        lang=args.lang,
    )
    ok = sum(1 for r in results if r.success)
    ko = len(results) - ok
    print(f"✅ Completati: {ok} | ❌ Falliti: {ko}")
    for r in results:
        status = "✅" if r.success else "❌"
        print(f"   {status} {r.input_path} → {r.output_path}")
        if not r.success:
            print(f"      Errore: {r.error}")
    return 0 if ko == 0 else 1


def cmd_info(args: argparse.Namespace) -> int:
    """Comando: info."""
    try:
        mesh = MeshReader.read(args.input)
        print(f"📦 File: {args.input}")
        print(f"   Nome:       {getattr(mesh, 'name', 'unknown')}")
        print(f"   Vertici:    {mesh.vertex_count}")
        print(f"   Triangoli:  {mesh.triangle_count}")
        return 0
    except Exception as e:
        print(f"❌ Errore: {e}", file=sys.stderr)
        return 1


def cmd_validate(args: argparse.Namespace) -> int:
    """Comando: validate."""
    try:
        report = validate_u3d(args.input)
        print(f"🔍 Validazione: {args.input}")
        print(report.summary())
        return 0 if report.is_valid else 1
    except Exception as e:
        print(f"❌ Errore: {e}", file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    """Costruisce il parser degli argomenti."""
    parser = argparse.ArgumentParser(
        prog="mesh2u3d",
        description="mesh2u3d — Convert 3D meshes to U3D, HTML, and PDF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"mesh2u3d {__version__}")

    subparsers = parser.add_subparsers(dest="command", required=True)

    p_convert = subparsers.add_parser("convert", help="Convert a 3D file")
    p_convert.add_argument("input", help="Input file (STL, OBJ, PLY, GLB, ...)")
    p_convert.add_argument("output", help="Output file (U3D, HTML, PDF)")
    p_convert.add_argument("--title", help="Title for HTML/PDF", default=None)
    p_convert.add_argument("--lang", choices=["it", "en"], default="it")
    p_convert.add_argument("--preserve-textures", action="store_true")
    p_convert.set_defaults(func=cmd_convert)

    p_batch = subparsers.add_parser("batch", help="Batch convert multiple files")
    p_batch.add_argument("inputs", nargs="+", help="Input files (glob patterns)")
    p_batch.add_argument("--output-dir", required=True, help="Output directory")
    p_batch.add_argument("--format", default="u3d", choices=list(SUPPORTED_OUTPUT_FORMATS))
    p_batch.add_argument("--lang", choices=["it", "en"], default="it")
    p_batch.add_argument("--preserve-textures", action="store_true")
    p_batch.set_defaults(func=cmd_batch)

    p_info = subparsers.add_parser("info", help="Show info about a 3D file")
    p_info.add_argument("input", help="Input file")
    p_info.set_defaults(func=cmd_info)

    p_validate = subparsers.add_parser("validate", help="Validate a U3D file")
    p_validate.add_argument("input", help="Input U3D file")
    p_validate.set_defaults(func=cmd_validate)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point della CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
