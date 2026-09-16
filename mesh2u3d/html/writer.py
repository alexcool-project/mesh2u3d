"""
Generatore HTML 3D self-contained con three.js — versione PRO.

Produce un singolo file .html che contiene:
  - three.js embedded (via CDN)
  - La mesh serializzata come JSON inline
  - Controlli avanzati: rotazione, zoom, pan, trasparenza, wireframe
  - Pannello info progetto (desktop + mobile compatto)
  - Logo cubo ArtiFix in alto a destra (link al sito)
  - Controlli interattivi responsive (pannello modale su mobile)
  - Pulsante "Scatta foto" (screenshot professionale con dati file)
  - Pulsante "Scarica HTML" (per uso offline)

Supporta due lingue: IT (default) e EN.

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


# ---------- Stringhe multilingua per il viewer ----------

_VIEWER_LABELS = {
    "it": {
        "loading": "Caricamento modello 3D...",
        "vertex_short": "Vertici",
        "triangle_short": "Triangoli",
        "format_short": "Formato",
        "controls_title": "🎛️ Controlli",
        "opacity_label": "Opacità",
        "display_label": "Visualizzazione",
        "material_label": "Materiale",
        "reset_btn": "🔄 Reset",
        "hints_rotate": "Trascina ruota",
        "hints_zoom": "Rotella zoom",
        "hints_pan": "Destro pan",
        "logo_title": "Visita ArtiFix.it",
        "btn_wireframe": "Wireframe",
        "btn_grid": "Griglia",
        "btn_axes": "Assi",
        "btn_solid": "Solido",
        "btn_flat": "Flat",
        "btn_xray": "X-Ray",
        # --- NUOVI PULSANTI ---
        "btn_screenshot": "📸 Scatta foto",
        "btn_screenshot_title": "Salva uno screenshot professionale del modello",
        "btn_download_html": "💾 Scarica HTML",
        "btn_download_html_title": "Salva il file HTML per aprirlo offline",
        "screenshot_success": "✅ Screenshot salvato!",
        "screenshot_error": "❌ Errore durante lo screenshot",
        "download_success": "✅ File HTML scaricato!",
    },
    "en": {
        "loading": "Loading 3D model...",
        "vertex_short": "Vertices",
        "triangle_short": "Triangles",
        "format_short": "Format",
        "controls_title": "🎛️ Controls",
        "opacity_label": "Opacity",
        "display_label": "Display",
        "material_label": "Material",
        "reset_btn": "🔄 Reset",
        "hints_rotate": "Drag rotate",
        "hints_zoom": "Scroll zoom",
        "hints_pan": "Right-click pan",
        "logo_title": "Visit ArtiFix.it",
        "btn_wireframe": "Wireframe",
        "btn_grid": "Grid",
        "btn_axes": "Axes",
        "btn_solid": "Solid",
        "btn_flat": "Flat",
        "btn_xray": "X-Ray",
        # --- NEW BUTTONS ---
        "btn_screenshot": "📸 Take screenshot",
        "btn_screenshot_title": "Save a professional screenshot of the model",
        "btn_download_html": "💾 Download HTML",
        "btn_download_html_title": "Save the HTML file to open it offline",
        "screenshot_success": "✅ Screenshot saved!",
        "screenshot_error": "❌ Screenshot error",
        "download_success": "✅ HTML file downloaded!",
    },
}


# ---------- Template HTML ----------

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="{lang_iso}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>{title} — ArtiFix 3D Viewer</title>
<link rel="icon" href="{logo_url}">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; -webkit-tap-highlight-color: transparent; }}
  html, body {{
    width: 100%;
    height: 100%;
    overflow: hidden;
    background: #0d1117;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    color: #e6edf3;
  }}
  canvas {{ display: block; touch-action: none; }}

  #artifix-logo {{
    position: absolute;
    top: 16px;
    right: 16px;
    z-index: 10;
    opacity: 0.55;
    transition: opacity 0.3s ease, transform 0.3s ease;
    text-decoration: none;
    display: block;
    pointer-events: auto;
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

  /* --- ACTION BUTTONS (screenshot + download HTML) --- */
  #action-buttons {{
    position: absolute;
    top: 16px;
    left: 16px;
    z-index: 10;
    display: flex;
    flex-direction: column;
    gap: 8px;
    pointer-events: auto;
  }}
  .action-btn {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 10px 14px;
    background: rgba(13,17,23,0.85);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid #21262d;
    border-radius: 8px;
    color: #e6edf3;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s ease;
    text-decoration: none;
    font-family: inherit;
  }}
  .action-btn:hover {{
    background: #21262d;
    border-color: #4a9eff;
    transform: translateY(-1px);
  }}
  .action-btn:active {{
    transform: translateY(0);
  }}
  .action-btn.success {{
    background: #1f4a2e;
    border-color: #2ecc71;
    color: #2ecc71;
  }}
  .action-btn.error {{
    background: #4a1f1f;
    border-color: #e74c3c;
    color: #e74c3c;
  }}

  #info {{
    position: absolute;
    top: 130px;
    left: 16px;
    background: rgba(13,17,23,0.85);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
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

  #controls {{
    position: absolute;
    top: 200px;
    right: 16px;
    background: rgba(13,17,23,0.85);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
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

  #reset-btn {{
    position: absolute;
    bottom: 20px;
    right: 20px;
    padding: 10px 16px;
    background: rgba(13,17,23,0.85);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid #21262d;
    border-radius: 8px;
    color: #e6edf3;
    font-size: 13px;
    cursor: pointer;
    z-index: 15;
    transition: all 0.15s ease;
    pointer-events: auto;
  }}
  #reset-btn:hover {{
    background: #21262d;
    border-color: #4a9eff;
  }}

  #hints {{
    position: absolute;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(13,17,23,0.7);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
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

  #info-mobile {{
    display: none;
    position: absolute;
    top: 100px;
    left: 14px;
    background: rgba(13,17,23,0.9);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    padding: 10px 14px;
    border-radius: 10px;
    border: 1px solid #21262d;
    font-size: 12px;
    line-height: 1.5;
    color: #8b949e;
    z-index: 5;
    max-width: 55%;
    pointer-events: none;
  }}
  #info-mobile .name {{
    font-size: 14px;
    font-weight: 600;
    color: #4a9eff;
    margin-bottom: 6px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }}
  #info-mobile .stat {{
    display: flex;
    justify-content: space-between;
    gap: 8px;
  }}
  #info-mobile .stat .value {{
    color: #e6edf3;
    font-weight: 500;
  }}

  #controls-toggle {{
    display: none;
    position: fixed;
    bottom: 24px;
    right: 24px;
    width: 56px;
    height: 56px;
    border-radius: 50%;
    background: linear-gradient(135deg, #1f77b4 0%, #4a9eff 100%);
    border: none;
    color: #ffffff;
    font-size: 24px;
    cursor: pointer;
    z-index: 1000;
    box-shadow: 0 4px 16px rgba(74, 158, 255, 0.5);
    transition: transform 0.15s ease;
    pointer-events: auto;
    -webkit-appearance: none;
    appearance: none;
  }}
  #controls-toggle:active {{
    transform: scale(0.9);
  }}

  #controls-modal {{
    display: none;
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: rgba(13,17,23,0.98);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-top-left-radius: 20px;
    border-top-right-radius: 20px;
    border-top: 1px solid #21262d;
    padding: 20px;
    z-index: 2000;
    max-height: 70vh;
    overflow-y: auto;
    transform: translateY(100%);
    transition: transform 0.3s ease;
    pointer-events: auto;
  }}
  #controls-modal.open {{
    transform: translateY(0);
  }}
  #controls-modal .modal-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid #21262d;
  }}
  #controls-modal .modal-header h3 {{
    font-size: 16px;
    color: #4a9eff;
    font-weight: 600;
  }}
  #controls-modal .close-btn {{
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: #21262d;
    border: none;
    color: #e6edf3;
    font-size: 18px;
    cursor: pointer;
    pointer-events: auto;
  }}
  #controls-modal .control-group {{
    margin-bottom: 18px;
  }}
  #controls-modal label {{
    display: block;
    font-size: 13px;
    color: #8b949e;
    margin-bottom: 8px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  #controls-modal input[type="range"] {{
    width: 100%;
    accent-color: #4a9eff;
    height: 8px;
    pointer-events: auto;
  }}
  #controls-modal .row {{
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
  }}
  #controls-modal button.btn-control {{
    flex: 1;
    min-width: 70px;
    padding: 14px 10px;
    background: #21262d;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 8px;
    font-size: 18px;
    cursor: pointer;
    transition: all 0.15s ease;
    pointer-events: auto;
    -webkit-appearance: none;
    appearance: none;
  }}
  #controls-modal button.btn-control.active {{
    background: #1f77b4;
    border-color: #4a9eff;
    color: #fff;
  }}

  @media (max-width: 900px) {{
    #info, #controls, #hints {{ display: none; }}
    #info-mobile {{ display: block; }}
    #controls-toggle {{ display: flex; align-items: center; justify-content: center; }}
    #controls-modal {{ display: block; }}

    #artifix-logo img {{ width: 42px; height: 42px; }}
    #artifix-logo {{ top: 12px; right: 12px; }}

    #action-buttons {{
      top: 12px;
      left: 12px;
      flex-direction: row;
      gap: 6px;
    }}
    .action-btn {{
      padding: 8px 10px;
      font-size: 12px;
    }}

    #reset-btn {{
      bottom: 24px;
      right: 90px;
      padding: 12px 18px;
      font-size: 13px;
      border-radius: 28px;
      background: rgba(13,17,23,0.9);
      box-shadow: 0 2px 8px rgba(0,0,0,0.4);
    }}
  }}

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
  {loading_text}
</div>

<a id="artifix-logo" href="https://www.artifix.it" target="_blank" rel="noopener" title="{logo_title}">
  <img src="{logo_url}" alt="ArtiFix">
</a>

<div id="action-buttons">
  <button class="action-btn" id="btn-screenshot" title="{btn_screenshot_title}">
    {btn_screenshot}
  </button>
  <button class="action-btn" id="btn-download-html" title="{btn_download_html_title}">
    {btn_download_html}
  </button>
</div>

<div id="info">
  <div class="project-name">{title}</div>
  <div class="stat"><span>{vertex_short}</span><span class="value">{vertex_count}</span></div>
  <div class="stat"><span>{triangle_short}</span><span class="value">{triangle_count}</span></div>
  <div class="stat"><span>{format_short}</span><span class="value">{source_format}</span></div>
</div>

<div id="info-mobile">
  <div class="name">{title}</div>
  <div class="stat"><span>{vertex_short}</span><span class="value">{vertex_count}</span></div>
  <div class="stat"><span>{triangle_short}</span><span class="value">{triangle_count}</span></div>
  <div class="stat"><span>{format_short}</span><span class="value">{source_format}</span></div>
</div>

<div id="controls">
  <div class="control-group">
    <label>{opacity_label}</label>
    <input type="range" id="opacity-slider" min="10" max="100" value="100">
  </div>
  <div class="control-group">
    <label>{display_label}</label>
    <div class="row">
      <button id="btn-wireframe" title="{btn_wireframe}">📐</button>
      <button id="btn-grid" class="active" title="{btn_grid}">▦</button>
      <button id="btn-axes" class="active" title="{btn_axes}">✛</button>
    </div>
  </div>
  <div class="control-group">
    <label>{material_label}</label>
    <div class="row">
      <button id="btn-solid" class="active" title="{btn_solid}">◼</button>
      <button id="btn-flat" title="{btn_flat}">◧</button>
      <button id="btn-xray" title="{btn_xray}">◯</button>
    </div>
  </div>
</div>

<button id="controls-toggle" title="{controls_title}">⚙️</button>

<div id="controls-modal">
  <div class="modal-header">
    <h3>{controls_title}</h3>
    <button class="close-btn" id="controls-modal-close">✕</button>
  </div>

  <div class="control-group">
    <label>{opacity_label}</label>
    <input type="range" id="opacity-slider-mobile" min="10" max="100" value="100">
  </div>

  <div class="control-group">
    <label>{display_label}</label>
    <div class="row">
      <button class="btn-control" id="btn-wireframe-mobile" title="{btn_wireframe}">📐</button>
      <button class="btn-control active" id="btn-grid-mobile" title="{btn_grid}">▦</button>
      <button class="btn-control active" id="btn-axes-mobile" title="{btn_axes}">✛</button>
    </div>
  </div>

  <div class="control-group">
    <label>{material_label}</label>
    <div class="row">
      <button class="btn-control active" id="btn-solid-mobile" title="{btn_solid}">◼</button>
      <button class="btn-control" id="btn-flat-mobile" title="{btn_flat}">◧</button>
      <button class="btn-control" id="btn-xray-mobile" title="{btn_xray}">◯</button>
    </div>
  </div>
</div>

<button id="reset-btn" title="Reset view">{reset_btn}</button>

<div id="hints">
  <span>🖱️ <b>{hints_rotate}</b></span>
  <span>🔍 <b>{hints_zoom}</b></span>
  <span>✋ <b>{hints_pan}</b></span>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>

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

const MESH_DATA = {mesh_json};
const PROJECT_TITLE = "{title}";
const STATS = {{
  vertex_short: "{vertex_short}",
  vertex_count: "{vertex_count}",
  triangle_short: "{triangle_short}",
  triangle_count: "{triangle_count}",
  format_short: "{format_short}",
  source_format: "{source_format}"
}};

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0d1117);

const camera = new THREE.PerspectiveCamera(
  45,
  window.innerWidth / window.innerHeight,
  0.1,
  10000
);

const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: false, preserveDrawingBuffer: true }});
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.appendChild(renderer.domElement);

const geometry = new THREE.BufferGeometry();
geometry.setAttribute(
  'position',
  new THREE.Float32BufferAttribute(MESH_DATA.vertices_flat, 3)
);
geometry.setIndex(MESH_DATA.triangles_flat);
geometry.computeVertexNormals();
geometry.computeBoundingSphere();

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

const center = geometry.boundingSphere.center.clone();
const radius = geometry.boundingSphere.radius;

mesh.position.sub(center);

camera.position.set(radius * 2.5, radius * 2, radius * 2.5);
camera.lookAt(0, 0, 0);

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

const grid = new THREE.GridHelper(radius * 6, 30, 0x21262d, 0x161b22);
grid.position.y = -radius;
scene.add(grid);

const axes = new THREE.AxesHelper(radius * 1.8);
scene.add(axes);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.screenSpacePanning = true;
controls.minDistance = radius * 0.3;
controls.maxDistance = radius * 30;
controls.autoRotate = false;
controls.autoRotateSpeed = 1.5;
controls.touches = {{
  ONE: THREE.TOUCH.ROTATE,
  TWO: THREE.TOUCH.DOLLY_PAN,
}};

const DEFAULT_CAM_POS = camera.position.clone();
const DEFAULT_CAM_TARGET = new THREE.Vector3(0, 0, 0);

window.addEventListener('resize', () => {{
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
}});

function animate() {{
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}}

requestAnimationFrame(() => {{
  requestAnimationFrame(() => {{
    document.getElementById('loading').style.display = 'none';
    animate();
  }});
}});

const opacitySlider = document.getElementById('opacity-slider');
const opacitySliderMobile = document.getElementById('opacity-slider-mobile');

function setOpacity(val) {{
  const v = parseInt(val) / 100;
  material.transparent = v < 1.0;
  material.opacity = v;
  material.needsUpdate = true;
  if (opacitySlider) opacitySlider.value = val;
  if (opacitySliderMobile) opacitySliderMobile.value = val;
}}

opacitySlider.addEventListener('input', (e) => setOpacity(e.target.value));
opacitySliderMobile.addEventListener('input', (e) => setOpacity(e.target.value));

const btnWireframe = document.getElementById('btn-wireframe');
const btnWireframeMobile = document.getElementById('btn-wireframe-mobile');
let wireframeOn = false;

function toggleWireframe() {{
  wireframeOn = !wireframeOn;
  wireframe.visible = wireframeOn;
  btnWireframe.classList.toggle('active', wireframeOn);
  btnWireframeMobile.classList.toggle('active', wireframeOn);
}}

btnWireframe.addEventListener('click', toggleWireframe);
btnWireframeMobile.addEventListener('click', toggleWireframe);

const btnGrid = document.getElementById('btn-grid');
const btnGridMobile = document.getElementById('btn-grid-mobile');

function toggleGrid() {{
  grid.visible = !grid.visible;
  btnGrid.classList.toggle('active', grid.visible);
  btnGridMobile.classList.toggle('active', grid.visible);
}}

btnGrid.addEventListener('click', toggleGrid);
btnGridMobile.addEventListener('click', toggleGrid);

const btnAxes = document.getElementById('btn-axes');
const btnAxesMobile = document.getElementById('btn-axes-mobile');

function toggleAxes() {{
  axes.visible = !axes.visible;
  btnAxes.classList.toggle('active', axes.visible);
  btnAxesMobile.classList.toggle('active', axes.visible);
}}

btnAxes.addEventListener('click', toggleAxes);
btnAxesMobile.addEventListener('click', toggleAxes);

const btnSolid = document.getElementById('btn-solid');
const btnFlat = document.getElementById('btn-flat');
const btnXray = document.getElementById('btn-xray');
const btnSolidMobile = document.getElementById('btn-solid-mobile');
const btnFlatMobile = document.getElementById('btn-flat-mobile');
const btnXrayMobile = document.getElementById('btn-xray-mobile');

function setMaterial(mode) {{
  [btnSolid, btnFlat, btnXray, btnSolidMobile, btnFlatMobile, btnXrayMobile].forEach(b => b.classList.remove('active'));

  if (mode === 'solid') {{
    material.flatShading = false;
    material.transparent = false;
    material.opacity = 1.0;
    material.color.setHex(0x4a9eff);
    material.needsUpdate = true;
    btnSolid.classList.add('active');
    btnSolidMobile.classList.add('active');
    setOpacity(100);
  }} else if (mode === 'flat') {{
    material.flatShading = true;
    material.transparent = false;
    material.opacity = 1.0;
    material.color.setHex(0x6bb6ff);
    material.needsUpdate = true;
    btnFlat.classList.add('active');
    btnFlatMobile.classList.add('active');
    setOpacity(100);
  }} else if (mode === 'xray') {{
    material.flatShading = false;
    material.transparent = true;
    material.opacity = 0.35;
    material.color.setHex(0x9bc4ff);
    material.needsUpdate = true;
    btnXray.classList.add('active');
    btnXrayMobile.classList.add('active');
    setOpacity(35);
  }}
}}

btnSolid.addEventListener('click', () => setMaterial('solid'));
btnFlat.addEventListener('click', () => setMaterial('flat'));
btnXray.addEventListener('click', () => setMaterial('xray'));
btnSolidMobile.addEventListener('click', () => setMaterial('solid'));
btnFlatMobile.addEventListener('click', () => setMaterial('flat'));
btnXrayMobile.addEventListener('click', () => setMaterial('xray'));

document.getElementById('reset-btn').addEventListener('click', () => {{
  camera.position.copy(DEFAULT_CAM_POS);
  controls.target.copy(DEFAULT_CAM_TARGET);
  controls.update();
}});

const controlsToggle = document.getElementById('controls-toggle');
const controlsModal = document.getElementById('controls-modal');
const controlsModalClose = document.getElementById('controls-modal-close');

function openControlsModal(e) {{
  e.preventDefault();
  e.stopPropagation();
  controlsModal.classList.add('open');
}}

function closeControlsModal(e) {{
  if (e) {{
    e.preventDefault();
    e.stopPropagation();
  }}
  controlsModal.classList.remove('open');
}}

controlsToggle.addEventListener('click', openControlsModal);
controlsToggle.addEventListener('touchstart', openControlsModal, {{ passive: false }});

controlsModalClose.addEventListener('click', closeControlsModal);
controlsModalClose.addEventListener('touchstart', closeControlsModal, {{ passive: false }});

controlsModal.addEventListener('click', (e) => {{
  if (e.target === controlsModal) {{
    closeControlsModal();
  }}
}});

renderer.domElement.addEventListener('dblclick', () => {{
  if (!document.fullscreenElement) {{
    document.documentElement.requestFullscreen();
  }} else {{
    document.exitFullscreen();
  }}
}});

// ---------- SCREENSHOT BUTTON ----------
document.getElementById('btn-screenshot').addEventListener('click', async function() {{
  const btn = this;
  const originalText = btn.textContent;

  try {{
    const canvas = renderer.domElement;

    // Crea un canvas composito
    const compositeCanvas = document.createElement('canvas');
    compositeCanvas.width = canvas.width;
    compositeCanvas.height = canvas.height;
    const ctx = compositeCanvas.getContext('2d');

    // Disegna il canvas WebGL
    ctx.drawImage(canvas, 0, 0);

    // Aggiungi watermark con dati del file (in alto a sinistra)
    const fontSize = Math.max(16, Math.floor(compositeCanvas.width / 60));
    const smallFontSize = Math.floor(fontSize * 0.75);
    const padding = fontSize * 1.2;
    let currentY = padding;

    // --- Nome progetto (blu) ---
    ctx.font = `bold ${{fontSize}}px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`;
    ctx.fillStyle = 'rgba(74, 158, 255, 0.95)';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    ctx.fillText(PROJECT_TITLE, padding, currentY);

    // --- Righe statistiche ---
    currentY += fontSize * 1.8;

    const stats = [
        {{ label: STATS.vertex_short, value: STATS.vertex_count }},
        {{ label: STATS.triangle_short, value: STATS.triangle_count }},
        {{ label: STATS.format_short, value: STATS.source_format }}
    ];

    ctx.font = `${{smallFontSize}}px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`;

    const valueRightEdge = padding + fontSize * 7;

    for (const stat of stats) {{
        // Label (grigio)
        ctx.fillStyle = 'rgba(139, 148, 158, 0.9)';
        ctx.textAlign = 'left';
        ctx.fillText(stat.label, padding, currentY);

        // Value (bianco) - allineato a destra
        ctx.fillStyle = 'rgba(230, 237, 243, 0.95)';
        ctx.textAlign = 'right';
        ctx.fillText(stat.value, valueRightEdge, currentY);
        ctx.textAlign = 'left';

        currentY += smallFontSize * 1.6;
    }}

    // Genera il blob PNG
    const dataUrl = compositeCanvas.toDataURL('image/png');

    // Crea il download
    const link = document.createElement('a');
    const safeTitle = PROJECT_TITLE.replace(/[^a-zA-Z0-9_-]/g, '_');
    const today = new Date().toISOString().split('T')[0];
    link.download = `${{safeTitle}}_${{today}}.png`;
    link.href = dataUrl;
    link.click();

    btn.classList.add('success');
    btn.textContent = '{screenshot_success}';
    setTimeout(() => {{
      btn.classList.remove('success');
      btn.textContent = originalText;
    }}, 2000);

  }} catch (err) {{
    console.error('Screenshot error:', err);
    btn.classList.add('error');
    btn.textContent = '{screenshot_error}';
    setTimeout(() => {{
      btn.classList.remove('error');
      btn.textContent = originalText;
    }}, 2000);
  }}
}});

// ---------- DOWNLOAD HTML BUTTON ----------
document.getElementById('btn-download-html').addEventListener('click', function() {{
  const btn = this;
  const originalText = btn.textContent;

  try {{
    // Recupera il sorgente HTML della pagina corrente
    const htmlSource = '<!DOCTYPE html>\\n' + document.documentElement.outerHTML;

    // Crea il blob
    const blob = new Blob([htmlSource], {{ type: 'text/html;charset=utf-8' }});
    const url = URL.createObjectURL(blob);

    // Crea il download
    const link = document.createElement('a');
    const today = new Date().toISOString().split('T')[0];
    const safeTitle = PROJECT_TITLE.replace(/[^a-zA-Z0-9_-]/g, '_');
    link.download = `${{safeTitle}}_${{today}}.html`;
    link.href = url;
    link.click();

    // Cleanup
    setTimeout(() => URL.revokeObjectURL(url), 1000);

    btn.classList.add('success');
    btn.textContent = '{download_success}';
    setTimeout(() => {{
      btn.classList.remove('success');
      btn.textContent = originalText;
    }}, 2000);

  }} catch (err) {{
    console.error('Download error:', err);
    btn.classList.add('error');
    btn.textContent = '{screenshot_error}';
    setTimeout(() => {{
      btn.classList.remove('error');
      btn.textContent = originalText;
    }}, 2000);
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
    lang: str = "it",
) -> Path:
    """
    Genera un file HTML 3D self-contained con three.js e la mesh embedded.

    Parameters
    ----------
    mesh : MeshData da visualizzare
    output : percorso del file .html risultante
    title : titolo della pagina (default: nome mesh)
    source_format : formato del file originale (per info)
    lang : lingua del viewer ("it" o "en", default "it")

    Returns
    -------
    Path al file HTML generato.
    """
    output = Path(output)
    title = title or mesh.name or "Modello 3D"

    # Normalizza lang
    lang = (lang or "it").lower()
    if lang not in _VIEWER_LABELS:
        lang = "it"
    labels = _VIEWER_LABELS[lang]
    lang_iso = "it" if lang == "it" else "en"

    html = _HTML_TEMPLATE.format(
        title=title,
        lang_iso=lang_iso,
        vertex_count=f"{mesh.vertex_count:,}".replace(",", "."),
        triangle_count=f"{mesh.triangle_count:,}".replace(",", "."),
        source_format=source_format.upper(),
        logo_url=_ARTIFIX_LOGO_URL,
        mesh_json=_mesh_to_json(mesh),
        loading_text=labels["loading"],
        vertex_short=labels["vertex_short"],
        triangle_short=labels["triangle_short"],
        format_short=labels["format_short"],
        controls_title=labels["controls_title"],
        opacity_label=labels["opacity_label"],
        display_label=labels["display_label"],
        material_label=labels["material_label"],
        reset_btn=labels["reset_btn"],
        hints_rotate=labels["hints_rotate"],
        hints_zoom=labels["hints_zoom"],
        hints_pan=labels["hints_pan"],
        logo_title=labels["logo_title"],
        btn_wireframe=labels["btn_wireframe"],
        btn_grid=labels["btn_grid"],
        btn_axes=labels["btn_axes"],
        btn_solid=labels["btn_solid"],
        btn_flat=labels["btn_flat"],
        btn_xray=labels["btn_xray"],
        # --- NUOVE STRINGHE ---
        btn_screenshot=labels["btn_screenshot"],
        btn_screenshot_title=labels["btn_screenshot_title"],
        btn_download_html=labels["btn_download_html"],
        btn_download_html_title=labels["btn_download_html_title"],
        screenshot_success=labels["screenshot_success"],
        screenshot_error=labels["screenshot_error"],
        download_success=labels["download_success"],
    )

    output.write_text(html, encoding="utf-8")
    return output
