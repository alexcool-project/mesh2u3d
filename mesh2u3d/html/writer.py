"""
Generatore HTML 3D self-contained con three.js — versione PRO.

Produce un singolo file .html che contiene:
  - three.js embedded (via CDN)
  - La mesh serializzata come JSON inline
  - Controlli avanzati: rotazione, zoom, pan, trasparenza, wireframe
  - Pannello info progetto
  - Logo cubo ArtiFix in alto a destra (link al sito)
  - Controlli interattivi

Il file risultante è APRIBBILE IN QUALSIASI BROWSER MODERNO
senza installare nulla, senza account, senza Adobe.

Autore: alexcool-project
Licenza: MIT
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from ..io.mesh_reader import MeshData


# URL del logo ufficiale ArtiFix (dal repo pubblico mesh2u3d-viewer)
_ARTIFIX_LOGO_URL = (
    "https://raw.githubusercontent.com/alexcool-project/"
    "mesh2u3d-viewer/main/assets/ArchiFix_cubo-logo.png"
)


# ---------- Template HTML ----------

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — ArtiFix 3D Viewer</title>
<link rel="icon" href="{logo_url}">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{
    width: 100%;
    height: 100%;
    overflow: hidden;
    background: #0d1117;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    color: #e6edf3;
  }}
  canvas {{ display: block; }}

  /* Logo cubo ArtiFix (top-right) */
  #artifix-logo {{
    position: absolute;
    top: 16px;
    right: 16px;
    z-index: 10;
    opacity: 0.55;
    transition: opacity 0.3s ease, transform 0.3s ease;
    text-decoration: none;
    display: block;
  }}
  #artifix-logo:hover {{
    opacity: 1.0;
    transform: scale(1.08);
  }}
  #artifix-logo img {{
    width: 56px;
    height: 56px;
    display: block;
    object-fit: contain;
    filter: drop-shadow(0 2px 8px rgba(74, 158, 255, 0.25));
  }}

  /* Info pannello (top-left) */
  #info {{
    position: absolute;
    top: 16px;
    left: 16px;
    background: rgba(13,17,23,0.85);
    backdrop-filter: blur(10px);
    padding: 14px 18px;
    border-radius: 10px;
    border: 1px solid #21262d;
    font-size: 13px;
    line-height: 1.6;
    z-index: 5;
    min-width: 220px;
  }}
  #info .project-name {{
    font-weight: 600;
    font-size: 15px;
    color: #4a9eff;
    margin-bottom: 8px;
  }}
  #info .stat {{
    display: flex;
    justify-content: space-between;
    color: #8b949e;
  }}
  #info .stat .value {{
    color: #e6edf3;
    font-weight: 500;
  }}

  /* Controlli (top-right, sotto il logo) */
  #controls {{
    position: absolute;
    top: 88px;
    right: 16px;
    background: rgba(13,17,23,0.85);
    backdrop-filter: blur(10px);
    padding: 14px;
    border-radius: 10px;
    border: 1px solid #21262d;
    z-index: 5;
    width: 230px;
  }}
  #controls .control-group {{
    margin-bottom: 12px;
  }}
  #controls .control-group:last-child {{
    margin-bottom: 0;
  }}
  #controls label {{
    display: block;
    font-size: 12px;
    color: #8b949e;
    margin-bottom: 6px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  #controls input[type="range"] {{
    width: 100%;
    accent-color: #4a9eff;
  }}
  #controls .row {{
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }}
  #controls button {{
    flex: 1;
    min-width: 60px;
    padding: 8px 10px;
    background: #21262d;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 6px;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.15s ease;
  }}
  #controls button:hover {{
    background: #30363d;
    border-color: #4a9eff;
  }}
  #controls button.active {{
    background: #1f77b4;
    border-color: #4a9eff;
    color: #fff;
  }}

  /* Pulsante reset (bottom-right) */
  #reset-btn {{
    position: absolute;
    bottom: 20px;
    right: 20px;
    padding: 10px 16px;
    background: rgba(13,17,23,0.85);
    backdrop-filter: blur(10px);
    border: 1px solid #21262d;
    border-radius: 8px;
    color: #e6edf3;
    font-size: 13px;
    cursor: pointer;
    z-index: 5;
    transition: all 0.15s ease;
  }}
  #reset-btn:hover {{
    background: #21262d;
    border-color: #4a9eff;
  }}

  /* Istruzioni (bottom-center) */
  #hints {{
    position: absolute;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(13,17,23,0.7);
    backdrop-filter: blur(10px);
    padding: 8px 16px;
    border-radius: 20px;
    font-size: 12px;
    color: #8b949e;
    z-index: 5;
    pointer-events: none;
  }}
  #hints span {{
    margin: 0 8px;
  }}
  #hints b {{
    color: #4a9eff;
    font-weight: 500;
  }}

  /* Responsive */
  @media (max-width: 900px) {{
    #info, #controls, #hints {{ display: none; }}
  }}

  /* Loading */
  #loading {{
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    text-align: center;
    z-index: 20;
    color: #8b949e;
  }}
  #loading .spinner {{
    width: 40px;
    height: 40px;
    border: 3px solid #21262d;
    border-top-color: #4a9eff;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 16px;
  }}
  @keyframes spin {{
    to {{ transform: rotate(360deg); }}
  }}
</style>
</head>
<body>

<div id="loading">
  <div class="spinner"></div>
  Caricamento modello 3D...
</div>

<!-- Logo cubo ArtiFix (top-right, cliccabile) -->
<a id="artifix-logo" href="https://www.artifix.it" target="_blank" rel="noopener" title="Visita ArtiFix.it">
  <img src="{logo_url}" alt="ArtiFix">
</a>

<div id="info">
  <div class="project-name">{title}</div>
  <div class="stat"><span>Vertici</span><span class="value">{vertex_count}</span></div>
  <div class="stat"><span>Triangoli</span><span class="value">{triangle_count}</span></div>
  <div class="stat"><span>Formato</span><span class="value">{source_format}</span></div>
</div>

<div id="controls">
  <div class="control-group">
    <label>Opacità</label>
    <input type="range" id="opacity-slider" min="10" max="100" value="100">
  </div>
  <div class="control-group">
    <label>Visualizzazione</label>
    <div class="row">
      <button id="btn-wireframe" title="Wireframe">📐</button>
      <button id="btn-grid" class="active" title="Griglia">▦</button>
      <button id="btn-axes" class="active" title="Assi XYZ">✛</button>
    </div>
  </div>
  <div class="control-group">
    <label>Materiale</label>
    <div class="row">
      <button id="btn-solid" class="active" title="Solido">◼</button>
      <button id="btn-flat" title="Flat">◧</button>
      <button id="btn-xray" title="X-Ray">◯</button>
    </div>
  </div>
</div>

<button id="reset-btn" title="Reimposta vista">🔄 Reset vista</button>

<div id="hints">
  <span>🖱️ <b>Trascina</b> ruota</span>
  <span>🔍 <b>Rotella</b> zoom</span>
  <span>✋ <b>Destro</b> pan</span>
</div>

<script type="importmap">
{{
  "imports": {{
    "three": "https://unpkg.com/three@0.160.0/build/three.module.js",
    "three/addons/": "https://unpkg.com/three@0.160.0/examples/jsm/"
  }}
}}
</script>

<script type="module">
import * as THREE from 'three';
import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';

// ---- Dati mesh embedded ----
const MESH_DATA = {mesh_json};

// ---- Setup scena ----
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0d1117);

const camera = new THREE.PerspectiveCamera(
  45,
  window.innerWidth / window.innerHeight,
  0.1,
  10000
);

const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: false }});
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.appendChild(renderer.domElement);

// ---- Geometria ----
const geometry = new THREE.BufferGeometry();
geometry.setAttribute(
  'position',
  new THREE.Float32BufferAttribute(MESH_DATA.vertices_flat, 3)
);
geometry.setIndex(MESH_DATA.triangles_flat);
geometry.computeVertexNormals();
geometry.computeBoundingSphere();

// ---- Materiale principale ----
const material = new THREE.MeshStandardMaterial({{
  color: 0x4a9eff,
  metalness: 0.25,
  roughness: 0.45,
  flatShading: false,
  side: THREE.DoubleSide,
  transparent: false,
  opacity: 1.0,
}});

const mesh = new THREE.Mesh(geometry, material);
scene.add(mesh);

// ---- Wireframe overlay (edge detection) ----
const edges = new THREE.EdgesGeometry(geometry, 30);
const lineMaterial = new THREE.LineBasicMaterial({{
  color: 0x1f77b4,
  linewidth: 1,
  transparent: true,
  opacity: 0.5,
}});
const wireframe = new THREE.LineSegments(edges, lineMaterial);
wireframe.visible = false;
mesh.add(wireframe);

// ---- Centra mesh e camera ----
const center = geometry.boundingSphere.center.clone();
const radius = geometry.boundingSphere.radius;

mesh.position.sub(center);

camera.position.set(radius * 2.5, radius * 2, radius * 2.5);
camera.lookAt(0, 0, 0);

// ---- Luci ----
scene.add(new THREE.AmbientLight(0xffffff, 0.5));

const keyLight = new THREE.DirectionalLight(0xffffff, 1.3);
keyLight.position.set(5, 8, 5);
keyLight.castShadow = true;
scene.add(keyLight);

const fillLight = new THREE.DirectionalLight(0x9bc4ff, 0.5);
fillLight.position.set(-5, 3, -5);
scene.add(fillLight);

const rimLight = new THREE.DirectionalLight(0xffffff, 0.4);
rimLight.position.set(0, -5, 0);
scene.add(rimLight);

// ---- Griglia ----
const grid = new THREE.GridHelper(radius * 6, 30, 0x21262d, 0x161b22);
grid.position.y = -radius;
scene.add(grid);

// ---- Assi XYZ ----
const axes = new THREE.AxesHelper(radius * 1.8);
scene.add(axes);

// ---- Controlli orbita ----
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.screenSpacePanning = true;
controls.minDistance = radius * 0.3;
controls.maxDistance = radius * 30;
controls.autoRotate = false;
controls.autoRotateSpeed = 1.5;

// ---- Info camera default (per reset) ----
const DEFAULT_CAM_POS = camera.position.clone();
const DEFAULT_CAM_TARGET = new THREE.Vector3(0, 0, 0);

// ---- Resize ----
window.addEventListener('resize', () => {{
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
}});

// ---- Loop animazione ----
function animate() {{
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}}

// ---- UI: nascondi loading dopo il primo render ----
requestAnimationFrame(() => {{
  requestAnimationFrame(() => {{
    document.getElementById('loading').style.display = 'none';
    animate();
  }});
}});

// ============================================================
// CONTROLLI INTERATTIVI
// ============================================================

// --- Opacità ---
const opacitySlider = document.getElementById('opacity-slider');
opacitySlider.addEventListener('input', (e) => {{
  const val = parseInt(e.target.value) / 100;
  material.transparent = val < 1.0;
  material.opacity = val;
  material.needsUpdate = true;
}});

// --- Wireframe ---
const btnWireframe = document.getElementById('btn-wireframe');
let wireframeOn = false;
btnWireframe.addEventListener('click', () => {{
  wireframeOn = !wireframeOn;
  wireframe.visible = wireframeOn;
  btnWireframe.classList.toggle('active', wireframeOn);
}});

// --- Griglia ---
const btnGrid = document.getElementById('btn-grid');
btnGrid.addEventListener('click', () => {{
  grid.visible = !grid.visible;
  btnGrid.classList.toggle('active', grid.visible);
}});

// --- Assi ---
const btnAxes = document.getElementById('btn-axes');
btnAxes.addEventListener('click', () => {{
  axes.visible = !axes.visible;
  btnAxes.classList.toggle('active', axes.visible);
}});

// --- Materiale: Solido ---
const btnSolid = document.getElementById('btn-solid');
const btnFlat = document.getElementById('btn-flat');
const btnXray = document.getElementById('btn-xray');

btnSolid.addEventListener('click', () => {{
  material.flatShading = false;
  material.transparent = false;
  material.opacity = 1.0;
  material.color.setHex(0x4a9eff);
  material.needsUpdate = true;
  opacitySlider.value = 100;
  btnSolid.classList.add('active');
  btnFlat.classList.remove('active');
  btnXray.classList.remove('active');
}});

btnFlat.addEventListener('click', () => {{
  material.flatShading = true;
  material.transparent = false;
  material.opacity = 1.0;
  material.color.setHex(0x6bb6ff);
  material.needsUpdate = true;
  opacitySlider.value = 100;
  btnFlat.classList.add('active');
  btnSolid.classList.remove('active');
  btnXray.classList.remove('active');
}});

btnXray.addEventListener('click', () => {{
  material.flatShading = false;
  material.transparent = true;
  material.opacity = 0.35;
  material.color.setHex(0x9bc4ff);
  material.needsUpdate = true;
  opacitySlider.value = 35;
  btnXray.classList.add('active');
  btnSolid.classList.remove('active');
  btnFlat.classList.remove('active');
}});

// --- Reset camera ---
document.getElementById('reset-btn').addEventListener('click', () => {{
  camera.position.copy(DEFAULT_CAM_POS);
  controls.target.copy(DEFAULT_CAM_TARGET);
  controls.update();
}});

// --- Doppio click = fullscreen ---
renderer.domElement.addEventListener('dblclick', () => {{
  if (!document.fullscreenElement) {{
    document.documentElement.requestFullscreen();
  }} else {{
    document.exitFullscreen();
  }}
}});
</script>
</body>
</html>
"""


def _mesh_to_json(mesh: MeshData) -> str:
    """Serializza la mesh come JSON per l'embedding."""
    data = {
        "vertices_flat": mesh.vertices.astype(float).flatten().tolist(),
        "triangles_flat": mesh.triangles.astype(int).flatten().tolist(),
        "vertex_count": mesh.vertex_count,
        "triangle_count": mesh.triangle_count,
    }
    return json.dumps(data, separators=(",", ":"))


def mesh_to_html(
    mesh: MeshData,
    output: str | Path,
    *,
    title: str | None = None,
    source_format: str = "STL",
) -> Path:
    """
    Genera un file HTML 3D self-contained con three.js e la mesh embedded.

    Parameters
    ----------
    mesh : MeshData da visualizzare
    output : percorso del file .html risultante
    title : titolo della pagina (default: nome mesh)
    source_format : formato del file originale (per info)

    Returns
    -------
    Path al file HTML generato.
    """
    output = Path(output)
    title = title or mesh.name or "Modello 3D"

    html = _HTML_TEMPLATE.format(
        title=title,
        vertex_count=f"{mesh.vertex_count:,}".replace(",", "."),
        triangle_count=f"{mesh.triangle_count:,}".replace(",", "."),
        source_format=source_format.upper(),
        logo_url=_ARTIFIX_LOGO_URL,
        mesh_json=_mesh_to_json(mesh),
    )

    output.write_text(html, encoding="utf-8")
    return output