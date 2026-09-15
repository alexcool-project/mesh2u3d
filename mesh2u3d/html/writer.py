"""
Generatore HTML 3D self-contained con three.js.

Produce un singolo file .html che contiene:
  - three.js embedded (via CDN, no dipendenze locali)
  - La mesh serializzata come JSON inline
  - Controlli orbit (rotazione, zoom, pan)
  - UI minimale

Il file risultante è APRIBBILE IN QUALSIASI BROWSER MODERNO
senza installare nulla, senza account, senza Adobe.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from ..io.mesh_reader import MeshData


# ---------- Template HTML ----------

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{ width: 100%; height: 100%; overflow: hidden; background: #1a1a1a; }}
  canvas {{ display: block; }}
  #info {{
    position: absolute;
    top: 10px;
    left: 10px;
    color: #fff;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 13px;
    background: rgba(0,0,0,0.6);
    padding: 10px 14px;
    border-radius: 6px;
    line-height: 1.5;
    pointer-events: none;
  }}
  #info b {{ color: #7cc4ff; }}
  #controls {{
    position: absolute;
    bottom: 10px;
    right: 10px;
    color: #aaa;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 11px;
    background: rgba(0,0,0,0.5);
    padding: 8px 12px;
    border-radius: 6px;
    pointer-events: none;
  }}
</style>
</head>
<body>
<div id="info">
  <b>{title}</b><br>
  Vertici: {vertex_count} &nbsp;|&nbsp; Triangoli: {triangle_count}
</div>
<div id="controls">
  🖱️ Trascina: rotazione &nbsp;|&nbsp; Rotella: zoom &nbsp;|&nbsp; Destro: pan
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
scene.background = new THREE.Color(0x1a1a1a);

const camera = new THREE.PerspectiveCamera(
  45,
  window.innerWidth / window.innerHeight,
  0.1,
  10000
);

const renderer = new THREE.WebGLRenderer({{ antialias: true }});
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(window.devicePixelRatio);
document.body.appendChild(renderer.domElement);

// ---- Geometria ----
const geometry = new THREE.BufferGeometry();
geometry.setAttribute(
  'position',
  new THREE.Float32BufferAttribute(MESH_DATA.vertices_flat, 3)
);
geometry.setIndex(MESH_DATA.triangles_flat);
geometry.computeVertexNormals();

// ---- Materiale ----
const material = new THREE.MeshStandardMaterial({{
  color: 0x4a9eff,
  metalness: 0.3,
  roughness: 0.5,
  flatShading: false,
  side: THREE.DoubleSide,
}});

const mesh = new THREE.Mesh(geometry, material);
scene.add(mesh);

// ---- Centra e scala la camera sulla mesh ----
geometry.computeBoundingSphere();
const center = geometry.boundingSphere.center.clone();
const radius = geometry.boundingSphere.radius;

mesh.position.sub(center);  // Centra la mesh nell'origine

camera.position.set(radius * 2.5, radius * 2, radius * 2.5);
camera.lookAt(0, 0, 0);

// ---- Luci ----
const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
scene.add(ambientLight);

const directionalLight = new THREE.DirectionalLight(0xffffff, 1.2);
directionalLight.position.set(1, 1, 1);
scene.add(directionalLight);

const directionalLight2 = new THREE.DirectionalLight(0xffffff, 0.6);
directionalLight2.position.set(-1, -1, -0.5);
scene.add(directionalLight2);

// ---- Griglia ----
const grid = new THREE.GridHelper(radius * 6, 20, 0x333333, 0x222222);
grid.position.y = -radius;
scene.add(grid);

// ---- Assi ----
const axesHelper = new THREE.AxesHelper(radius * 1.5);
scene.add(axesHelper);

// ---- Controlli orbita ----
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.05;
controls.screenSpacePanning = true;
controls.minDistance = radius * 0.5;
controls.maxDistance = radius * 20;

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
animate();
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
) -> Path:
    """
    Genera un file HTML self-contained con three.js e la mesh embedded.

    Parameters
    ----------
    mesh : MeshData da visualizzare
    output : percorso del file .html risultante
    title : titolo della pagina (default: nome mesh)

    Returns
    -------
    Path al file HTML generato.
    """
    output = Path(output)
    title = title or mesh.name or "3D Viewer"

    html = _HTML_TEMPLATE.format(
        title=title,
        vertex_count=mesh.vertex_count,
        triangle_count=mesh.triangle_count,
        mesh_json=_mesh_to_json(mesh),
    )

    output.write_text(html, encoding="utf-8")
    return output