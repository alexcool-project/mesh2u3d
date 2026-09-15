"""
Generatore U3D conforme a ECMA-363 Base Profile.

Il file U3D prodotto contiene la sequenza minima di blocchi richiesta
da un viewer conformante (Adobe Acrobat Reader, Foxit Reader, PDF-XChange):

    1. FILE_HEADER      (in testa, 32 byte)
    2. MESH_DECLARATION (dichiara attributi mesh)
    3. MESH_RESOURCE    (dati binari: posizioni, normali, facce)
    4. MODIFIER_CHAIN   (catena di modificatori applicati al modello)
    5. SHADER           (shader per il materiale)
    6. MATERIAL_RESOURCE (materiale di default)
    7. MODEL_NODE       (nodo che referenzia la mesh e il modifier chain)
    8. GROUP_NODE       (nodo radice della scena)
    9. VIEW_NODE        (vista di default)
   10. LIGHT_NODE       (luce di default, opzionale ma consigliata)

Riferimenti: ECMA-363, 4th Edition (2007), §6 e §8.
"""
from __future__ import annotations

import struct
from pathlib import Path
from typing import Iterable

import numpy as np

from .blocks import (
    BlockType,
    CharacterEncoding,
    CompressionMethod,
    U3DBlock,
)
from ..io.mesh_reader import MeshData


# ---------- Costanti ECMA-363 ----------
# IMPORTANTE: Adobe Acrobat usa il magic "U3DH" (variante Adobe del Base Profile)
# invece di "U3D\x00" (standard ECMA-363 puro). Usiamo "U3DH" per compatibilità.
U3D_MAGIC = b"U3DH"
U3D_VERSION_MAJOR = 1
U3D_VERSION_MINOR = 0
U3D_PROFILE_ID = 0
U3D_DECLARATION_SIZE = 0
U3D_CHARACTER_ENCODING = int(CharacterEncoding.UTF8)
U3D_COMPRESSION = int(CompressionMethod.NONE)
U3D_UNIT_SCALE = 1.0

# File header U3D: 32 byte
# 4s magic, H version, I profile_id, I declaration_size,
# I file_size, I encoding, I compression, f unit_scale, H reserved
_FILE_HEADER_STRUCT = struct.Struct("<4sHIIII If H")


# ---------- Strutture helper ----------

def _pack_string(s: str) -> bytes:
    """Stringa U3D: lunghezza U32 + bytes UTF-8."""
    data = s.encode("utf-8")
    return struct.pack("<I", len(data)) + data


# ---------- MESH_DECLARATION (ECMA-363 §8.5.3) ----------

def _write_mesh_declaration() -> U3DBlock:
    """
    MESH_DECLARATION: dichiara la struttura della mesh.

    Attributi dichiarati:
      - POSITION (id=0): 3 x F32
      - NORMAL   (id=1): 3 x F32
      - FACE     (id=10): 3 x I32
    """
    buf = bytearray()
    buf += struct.pack("<B", 0)          # quality (0 = default)
    buf += b"\x00\x00\x00"                # reserved
    buf += struct.pack("<I", 3)           # numero attributi

    # Ogni attributo: (attribute_type U32, element_count U32, data_type U32)
    # data_type: 5 = F32, 6 = I32
    buf += struct.pack("<III", 0, 3, 5)   # POSITION
    buf += struct.pack("<III", 1, 3, 5)   # NORMAL
    buf += struct.pack("<III", 10, 3, 6)  # FACE

    return U3DBlock(BlockType.MESH_DECLARATION, bytes(buf))


# ---------- MESH_RESOURCE (ECMA-363 §8.5.4) ----------

def _compute_vertex_normals(mesh: MeshData) -> np.ndarray:
    """Calcola normali per-vertice medie dalle facce."""
    v = mesh.vertices
    t = mesh.triangles
    v0 = v[t[:, 0]]
    v1 = v[t[:, 1]]
    v2 = v[t[:, 2]]
    face_normals = np.cross(v1 - v0, v2 - v0)
    normals = np.zeros_like(v, dtype=np.float32)
    for i in range(3):
        np.add.at(normals, t[:, i], face_normals)
    norms = np.linalg.norm(normals, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return (normals / norms).astype(np.float32)


def _write_mesh_resource(mesh: MeshData) -> U3DBlock:
    """
    MESH_RESOURCE: dati binari della mesh.

    Struttura:
      - Continuation (U32) = 0 (nessun blocco successivo)
      - VertexCount (U32)
      - Positions (VertexCount x 3 x F32)
      - Normals   (VertexCount x 3 x F32)
      - Faces     (FaceCount  x 3 x I32)
    """
    buf = bytearray()
    buf += struct.pack("<I", 0)  # continuation
    buf += struct.pack("<I", mesh.vertex_count)

    # Posizioni
    buf += mesh.vertices.astype("<f4").tobytes()

    # Normali (calcolate se assenti)
    if mesh.normals is not None and len(mesh.normals) == mesh.vertex_count:
        normals = mesh.normals.astype(np.float32)
    else:
        normals = _compute_vertex_normals(mesh)
    buf += normals.astype("<f4").tobytes()

    # Facce
    buf += mesh.triangles.astype("<i4").tobytes()

    return U3DBlock(BlockType.MESH_RESOURCE, bytes(buf))


# ---------- MODIFIER_CHAIN (ECMA-363 §8.4.1) ----------

def _write_modifier_chain(name: str = "DefaultModifierChain") -> U3DBlock:
    """
    MODIFIER_CHAIN: catena di modificatori applicati al modello.

    Struttura (Base Profile):
      - Name (stringa)
      - Chain type (U32): 0 = None
      - Num modifier (U32): 0 (nessun modificatore)
    """
    buf = bytearray()
    buf += _pack_string(name)
    buf += struct.pack("<I", 0)  # chain type = None
    buf += struct.pack("<I", 0)  # num modifiers = 0
    return U3DBlock(BlockType.MODIFIER_CHAIN, bytes(buf))


# ---------- SHADER (ECMA-363 §8.6.1) ----------

def _write_shader(name: str = "DefaultShader") -> U3DBlock:
    """
    SHADER: shader per il materiale (Base Profile = Lambert-like).

    Struttura semplificata Base Profile:
      - Name (stringa)
      - Shader type (U32): 0 = Basic
      - Num light (U32): 0
    """
    buf = bytearray()
    buf += _pack_string(name)
    buf += struct.pack("<I", 0)  # shader type = Basic
    buf += struct.pack("<I", 0)  # num lights
    return U3DBlock(BlockType.SHADER, bytes(buf))


# ---------- MATERIAL_RESOURCE (ECMA-363 §8.6.2) ----------

def _write_material_resource(
    name: str = "DefaultMaterial",
    ambient: tuple[float, float, float, float] = (0.2, 0.2, 0.2, 1.0),
    diffuse: tuple[float, float, float, float] = (0.8, 0.8, 0.8, 1.0),
    specular: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0),
    emissive: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0),
    shininess: float = 0.0,
) -> U3DBlock:
    """
    MATERIAL_RESOURCE: materiale di default (grigio chiaro Lambert-like).

    Struttura:
      - Name (stringa)
      - Ambient  (4 x F32)
      - Diffuse  (4 x F32)
      - Specular (4 x F32)
      - Emissive (4 x F32)
      - Reflectivity (F32)
      - Opacity (F32)
      - Shininess (F32)
    """
    buf = bytearray()
    buf += _pack_string(name)
    for color in (ambient, diffuse, specular, emissive):
        for c in color:
            buf += struct.pack("<f", float(c))
    buf += struct.pack("<f", 0.0)   # reflectivity
    buf += struct.pack("<f", 1.0)   # opacity
    buf += struct.pack("<f", shininess)
    return U3DBlock(BlockType.MATERIAL_RESOURCE, bytes(buf))


# ---------- MODEL_NODE (ECMA-363 §8.3.5) ----------

def _write_model_node(
    name: str,
    parent_name: str,
    mesh_resource_idx: int,
    modifier_chain_idx: int,
) -> U3DBlock:
    """
    MODEL_NODE: nodo della scena che referenzia una mesh + modifier chain.

    Struttura:
      - Name (stringa)
      - Parent node name (stringa; "" per root)
      - Resource index: MESH_RESOURCE (U32)
      - Resource index: MODIFIER_CHAIN (U32)
      - Visibility (U8): 1 = visible
      - Transform matrix (16 x F32) - identità
    """
    buf = bytearray()
    buf += _pack_string(name)
    buf += _pack_string(parent_name)
    buf += struct.pack("<I", mesh_resource_idx)
    buf += struct.pack("<I", modifier_chain_idx)
    buf += struct.pack("<B", 1)   # visible

    # Matrice di identità 4x4 (column-major)
    identity = [
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 0.0, 1.0,
    ]
    for v in identity:
        buf += struct.pack("<f", v)

    return U3DBlock(BlockType.MODEL_NODE, bytes(buf))


# ---------- GROUP_NODE (ECMA-363 §8.3.4) ----------

def _write_group_node(name: str, children: list[str]) -> U3DBlock:
    """
    GROUP_NODE: nodo di raggruppamento (radice della scena).

    Struttura:
      - Name (stringa)
      - Parent node name (stringa; "" per root)
      - Num children (U32)
      - Children names (strings)
      - Visibility (U8)
      - Transform matrix (identità)
    """
    buf = bytearray()
    buf += _pack_string(name)
    buf += _pack_string("")  # root
    buf += struct.pack("<I", len(children))
    for child in children:
        buf += _pack_string(child)
    buf += struct.pack("<B", 1)

    identity = [1.0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 1.0]
    for v in identity:
        buf += struct.pack("<f", v)

    return U3DBlock(BlockType.GROUP_NODE, bytes(buf))


# ---------- VIEW_NODE (ECMA-363 §8.3.6) ----------

def _write_view_node(name: str = "DefaultView") -> U3DBlock:
    """
    VIEW_NODE: vista di default della scena.

    Struttura:
      - Name (stringa)
      - Parent node name (stringa)
      - View attributes flags (U32)
      - Projection mode (U8): 1 = orthographic
      - Field of view (F32)
      - Aspect ratio (F32)
      - Near clip (F32)
      - Far clip (F32)
    """
    buf = bytearray()
    buf += _pack_string(name)
    buf += _pack_string("")
    buf += struct.pack("<I", 0)      # attributes flags
    buf += struct.pack("<B", 1)      # orthographic
    buf += struct.pack("<f", 45.0)   # fov
    buf += struct.pack("<f", 1.0)    # aspect
    buf += struct.pack("<f", 0.1)    # near
    buf += struct.pack("<f", 1000.0) # far
    return U3DBlock(BlockType.VIEW_NODE, bytes(buf))


# ---------- LIGHT_NODE (ECMA-363 §8.3.7) ----------

def _write_light_node(
    name: str = "DefaultLight",
    light_type: int = 0,  # 0 = ambient, 1 = directional, 2 = point, 3 = spot
) -> U3DBlock:
    """
    LIGHT_NODE: luce di default (ambient).

    Struttura semplificata:
      - Name (stringa)
      - Parent node name (stringa)
      - Light type (U8)
      - Color (4 x F32)
      - Intensity (F32)
      - Visibility (U8)
    """
    buf = bytearray()
    buf += _pack_string(name)
    buf += _pack_string("")
    buf += struct.pack("<B", light_type)
    for c in (1.0, 1.0, 1.0, 1.0):
        buf += struct.pack("<f", c)
    buf += struct.pack("<f", 1.0)  # intensity
    buf += struct.pack("<B", 1)    # visible
    return U3DBlock(BlockType.LIGHT_NODE, bytes(buf))


# ---------- U3DWriter ----------

class U3DWriter:
    """
    Genera un file U3D conforme a ECMA-363 Base Profile.

    Ordine di emissione dei blocchi (rispetta ECMA-363 §6.3):
      MESH_DECLARATION, MESH_RESOURCE,
      MODIFIER_CHAIN, SHADER, MATERIAL_RESOURCE,
      MODEL_NODE, GROUP_NODE, VIEW_NODE, LIGHT_NODE
    """

    def __init__(self, unit_scale: float = 1.0) -> None:
        self.unit_scale = unit_scale
        self._blocks: list[U3DBlock] = []

    def add_mesh(self, mesh: MeshData, node_name: str | None = None) -> "U3DWriter":
        """Aggiunge una mesh alla scena U3D."""
        name = node_name or mesh.name or "Mesh"

        # Resource index (contatori separati per tipo di risorsa)
        mesh_resource_idx = 0      # primo MESH_RESOURCE
        modifier_chain_idx = 0     # primo MODIFIER_CHAIN

        # Blocchi mesh
        self._blocks.append(_write_mesh_declaration())
        self._blocks.append(_write_mesh_resource(mesh))

        # Blocchi modifier/shader/material
        self._blocks.append(_write_modifier_chain(f"MC_{name}"))
        self._blocks.append(_write_shader(f"Shader_{name}"))
        self._blocks.append(_write_material_resource(f"Material_{name}"))

        # Nodo modello
        self._blocks.append(_write_model_node(
            name=name,
            parent_name="Root",
            mesh_resource_idx=mesh_resource_idx,
            modifier_chain_idx=modifier_chain_idx,
        ))

        # Nodo radice della scena (raggruppa i model node)
        self._blocks.append(_write_group_node(
            name="Root",
            children=[name],
        ))

        # Vista e luce di default
        self._blocks.append(_write_view_node(f"View_{name}"))
        self._blocks.append(_write_light_node(f"Light_{name}"))

        return self

    def _build_file_header(self, body_size: int) -> bytes:
        total_size = _FILE_HEADER_STRUCT.size + body_size
        return _FILE_HEADER_STRUCT.pack(
            U3D_MAGIC,
            (U3D_VERSION_MAJOR << 8) | U3D_VERSION_MINOR,
            U3D_PROFILE_ID,
            U3D_DECLARATION_SIZE,
            total_size,
            U3D_CHARACTER_ENCODING,
            U3D_COMPRESSION,
            self.unit_scale,
            0,
        )

    def to_bytes(self) -> bytes:
        body = b"".join(b.to_bytes() for b in self._blocks)
        return self._build_file_header(len(body)) + body

    def write(self, path: str | Path) -> Path:
        path = Path(path)
        path.write_bytes(self.to_bytes())
        return path


# ---------- API pubbliche ----------

def mesh_to_u3d(mesh: MeshData, output: str | Path) -> Path:
    """Scorciatoia: una mesh -> file .u3d."""
    return U3DWriter().add_mesh(mesh).write(output)


def meshes_to_u3d(meshes: Iterable[MeshData], output: str | Path) -> Path:
    """Scorciatoia: più mesh -> file .u3d (una scena)."""
    writer = U3DWriter()
    for m in meshes:
        writer.add_mesh(m)
    return writer.write(output)