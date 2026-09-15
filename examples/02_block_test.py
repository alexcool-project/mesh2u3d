"""Test: creare un U3DBlock e serializzarlo."""
from mesh2u3d.u3d.blocks import BlockType, U3DBlock


def main() -> None:
    # Crea un blocco MESH_DECLARATION con 5 byte di dati "hello"
    block = U3DBlock(BlockType.MESH_DECLARATION, b"hello")

    print(f"Tipo:       {block.block_type.name}")
    print(f"Valore hex: {hex(int(block.block_type))}")
    print(f"Dimensione: {block.size} byte (12 header + 5 data)")

    raw = block.to_bytes()
    print(f"Primi 12 byte (header): {raw[:12].hex()}")
    print(f"Ultimi 5 byte (data):   {raw[12:]}")

    # Verifiche
    assert block.size == 17, f"Attesi 17 byte, trovati {block.size}"
    assert raw[:4] == b"\x32\xff\xff\xff", "BlockType errato nel header"
    assert raw[12:] == b"hello", "Data errata"

    print("\nOK - blocco U3D serializzato correttamente")


if __name__ == "__main__":
    main()