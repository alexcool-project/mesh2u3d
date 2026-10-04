# mesh2u3d

> **v0.2.1 — Viewer HTML offline validato in produzione** ✅

**Ultima release stabile:** [v0.2.1](https://github.com/alexcool-project/mesh2u3d/releases/tag/v0.2.1)
**Validato il:** 2026-10-04
**Testato su:** ArtiFix (`artifix.streamlit.app`)

---

## 🎯 Stato del progetto

| Feature | Stato |
|---|---|
| Conversione Mesh → U3D | ✅ Stabile |
| Conversione Mesh → PDF (3D embedded) | ✅ Stabile |
| **Viewer HTML 3D self-contained** | ✅ **Validato in produzione** |
| **Viewer HTML funzionante offline (`file://`)** | ✅ **Validato in produzione** |
| Screenshot professionale con watermark | ✅ Validato |
| Download HTML per condivisione | ✅ Validato |

## 🔒 Note per lo sviluppo futuro

Il viewer HTML è **stabile e validato**. Per evitare regressioni:

### Regole da rispettare

1. **Non modificare `_read_asset()` senza test offline.** Legge i file JS da `assets/` e li inlinea come testo. Deve restare una semplice `read_text()`, **senza replace o escape aggiuntivi**.

2. **Attenzione ai backslash nel template HTML.** In `writer.py`, il `_HTML_TEMPLATE` contiene codice JS. Ogni `\n` **dentro il template** (per esempio in `const htmlSource = '...\\n'`) va scritto con **doppio backslash** (`\\n`), altrimenti Python lo trasforma in newline reale e rompe la stringa JS.

3. **Non usare `str.format()`** per popolare il template: usare sempre `str.replace()` con segnaposto nella forma `__NOME__`. Il template contiene `{` e `}` del CSS/JS che `str.format()` interpreterebbe come segnaposto.

4. **Testare sempre in `file://`.** Ogni modifica al viewer va testata:
   - **Online:** apri `https://viewer.artifix.it/v/XXX.html`
   - **Offline:** scarica l'HTML, doppio click, verifica che la mesh appaia
   - **Screenshot:** verifica filename troncato e nessuna sovrapposizione

5. **Non tornare a CDN esterni.** three.js e OrbitControls devono restare **inline** in `assets/`. Se serve aggiornare, sostituire il file `.js` in `assets/`, mai passare a `<script src="https://...">`.

### File critici

| File | Ruolo |
|---|---|
| `mesh2u3d/html/writer.py` | Genera l'HTML self-contained |
| `mesh2u3d/html/assets/three.min.js` | three.js r147 UMD (inline) |
| `mesh2u3d/html/assets/OrbitControls.min.js` | OrbitControls r147 UMD (inline) |
| `pyproject.toml` → `[tool.setuptools.package-data]` | Include gli asset nel wheel |
| `MANIFEST.in` | Include gli asset in sdist |

### ⚠️ Errori che hanno rotto il viewer in passato

- **`</script>` in `three.min.js`** → **falso allarme**, il file è già safe
- **`str.format()` con CSS/JS** → `ValueError: expected ':'` → risolto con `str.replace()`
- **Backslash singolo `\n` nel template** → `SyntaxError: Invalid or unexpected token` → risolto con `\\n`
- **`_read_asset()` con escape** → ha rotto il parsing HTML → **non aggiungere escape**

---

Convert 3D meshes to U3D (ECMA-363) and embed them into PDF files.

## Installation

```bash
pip install mesh2u3d
```

## Quick Start

```python
from mesh2u3d import mesh_to_pdf
mesh_to_pdf("model.stl", "model.pdf")
```

## License

MIT
