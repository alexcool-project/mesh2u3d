"""Lettura universale di mesh 3D -> MeshData."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class MeshData:
    """Rappresentazione minimale di mesh triangolare."""

    vertices: np.ndarray
    triangles: np.ndarray
    normals: np.ndarray | None = None
    name: str = "mesh"

    def __post_init__(self) -> None:
        self.vertices = np.ascontiguousarray(self.vertices, dtype=np.float32)
        self.triangles = np.ascontiguousarray(self.triangles, dtype=np.int32)
        if self.normals is not None:
            self.normals = np.ascontiguousarray(self.normals, dtype=np.float32)

        if self.vertices.ndim != 2 or self.vertices.shape[1] != 3:
            raise ValueError(
                f"vertices deve essere (N,3), trovato {self.vertices.shape}"
            )
        if self.triangles.ndim != 2 or self.triangles.shape[1] != 3:
            raise ValueError(
                f"triangles deve essere (M,3), trovato {self.triangles.shape}"
            )

    @property
    def vertex_count(self) -> int:
        return len(self.vertices)

    @property
    def triangle_count(self) -> int:
        return len(self.triangles)


class MeshReader:
    """Factory per leggere mesh da vari formati."""

    SUPPORTED = {".stl", ".obj", ".ply", ".glb", ".gltf", ".off"}

    @classmethod
    def read(cls, path: str | Path) -> MeshData:
        path = Path(path)
        ext = path.suffix.lower()
        if ext not in cls.SUPPORTED:
            raise ValueError(
                f"Formato non supportato: {ext}. Usa {sorted(cls.SUPPORTED)}"
            )

        import trimesh

        loaded = trimesh.load(str(path), force="mesh")

        if isinstance(loaded, trimesh.Scene):
            if not loaded.geometry:
                raise ValueError(f"Nessuna geometria in {path}")
            loaded = trimesh.util.concatenate(tuple(loaded.geometry.values()))

        normals = None
        try:
            vn = getattr(loaded, "vertex_normals", None)
            if vn is not None and len(vn):
                normals = np.asarray(vn, dtype=np.float32)
        except Exception:
            pass

        return MeshData(
            vertices=np.asarray(loaded.vertices, dtype=np.float32),
            triangles=np.asarray(loaded.faces, dtype=np.int32),
            normals=normals,
            name=path.stem,
        )

    @classmethod
    def from_trimesh(cls, mesh, name: str = "mesh") -> MeshData:
        """Costruisce MeshData da un oggetto trimesh.Trimesh."""
        normals = None
        try:
            vn = getattr(mesh, "vertex_normals", None)
            if vn is not None and len(vn):
                normals = np.asarray(vn, dtype=np.float32)
        except Exception:
            pass
        return MeshData(
            vertices=np.asarray(mesh.vertices, dtype=np.float32),
            triangles=np.asarray(mesh.faces, dtype=np.int32),
            normals=normals,
            name=name,
        )