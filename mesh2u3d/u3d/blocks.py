"""Definizione blocchi U3D secondo ECMA-363."""
from __future__ import annotations

import struct
from dataclasses import dataclass
from enum import IntEnum
from typing import ClassVar


class BlockType(IntEnum):
    """Tipi di blocco U3D (ECMA-363, Tabella 4)."""

    FILE_HEADER = 0x00443355
    MODIFIER_CHAIN = 0xFFFFFF3C
    CLOD_MODIFIER = 0xFFFFFF3B
    GROUP_NODE = 0xFFFFFF3A
    MODEL_NODE = 0xFFFFFF39
    VIEW_NODE = 0xFFFFFF38
    LIGHT_NODE = 0xFFFFFF37
    SHADER = 0xFFFFFF36
    MATERIAL_RESOURCE = 0xFFFFFF35
    TEXTURE_RESOURCE = 0xFFFFFF34
    MOTION_RESOURCE = 0xFFFFFF33
    MESH_DECLARATION = 0xFFFFFF32
    MESH_RESOURCE = 0xFFFFFF31
    MESH_CONTINUATION = 0xFFFFFF30
    BONE_WEIGHT = 0xFFFFFF2F
    POINT_CLOUD = 0xFFFFFF2E
    LINE_SET = 0xFFFFFF2D
    NEW_OBJECT = 0xFFFFFF2C


class CharacterEncoding(IntEnum):
    """Codifiche caratteri supportate (ECMA-363 §6.1.3)."""

    UTF8 = 0
    UTF16 = 1


class CompressionMethod(IntEnum):
    """Metodi di compressione (ECMA-363 §6.1.4)."""

    NONE = 0
    ECF = 1
    DEFLATE = 2


@dataclass
class U3DBlock:
    """
    Blocco generico U3D.

    Struttura ECMA-363 §6.3:
        [BlockType:U32][DataSize:U32][MetadataSize:U32][Metadata][Data]
    """

    block_type: BlockType
    data: bytes
    metadata_size: int = 0

    HEADER_STRUCT: ClassVar[struct.Struct] = struct.Struct("<III")

    def to_bytes(self) -> bytes:
        """Serializza il blocco in formato binario U3D."""
        header = self.HEADER_STRUCT.pack(
            int(self.block_type),
            len(self.data),
            self.metadata_size,
        )
        return header + self.data

    @property
    def size(self) -> int:
        """Dimensione totale del blocco (header + data)."""
        return self.HEADER_STRUCT.size + self.metadata_size + len(self.data)