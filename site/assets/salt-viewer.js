import { validateMetadata, section, velocityColor, surveyPoints } from './salt-volume.mjs';

const $ = id => document.getElementById(id);
const host = $('salt-canvas-host'), status = $('salt-status'), controlsPanel = $('salt-controls');
let cleanup = () => {}, loading = false;

async function start() {
  if (loading) return;
  loading = true;
  cleanup(); cleanup = () => {};
  $('retry').hidden = true; controlsPanel.disabled = true;
  $('salt-fallback').hidden = false;
  status.textContent = 'Loading model and 3D viewer…';
  const abort = new AbortController();
  const timeout = setTimeout(() => abort.abort(), 60000);
  let renderer, orbit, observer, scene, scheduled = 0;
  const listeners = [];
  const on = (node, event, fn, options) => { node.addEventListener(event, fn, options); listeners.push(() => node.removeEventListener(event, fn, options)); };
  function disposeObject(object) {
    object.traverse(o => { o.geometry?.dispose(); if (o.material) for (const m of [o.material].flat()) { m.map?.dispose(); m.dispose(); } });
  }
  cleanup = () => {
    clearTimeout(timeout); abort.abort(); cancelAnimationFrame(scheduled);
    listeners.forEach(f => f()); observer?.disconnect(); orbit?.dispose();
    if (scene) disposeObject(scene);
    renderer?.dispose(); host.replaceChildren();
    document.querySelector('.salt-axis-labels').replaceChildren();
  };
  try {
    if (!window.WebGLRenderingContext) throw new Error('WebGL is unavailable');
    const [THREE, { OrbitControls }] = await Promise.all([
      import('./vendor/three.module.js'), import('./vendor/OrbitControls.js')
    ]);
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setClearColor(0x101e2c); renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    const canvas = renderer.domElement;
    canvas.tabIndex = 0; canvas.setAttribute('role', 'img');
    canvas.setAttribute('aria-label', 'Interactive SEG/EAGE 3D salt body with velocity sections');
    canvas.setAttribute('aria-describedby', 'viewer-help');
    async function fetchAsset(name, json = false) {
      const response = await fetch(new URL(`salt/${name}`, import.meta.url), { signal: abort.signal });
      if (!response.ok) throw new Error(`Could not load ${name} (${response.status})`);
      return json ? response.json() : response.arrayBuffer();
    }
    const meta = validateMetadata(await fetchAsset('metadata.json', true));
    const names = ['velocity.bin', 'vertices.bin', 'triangles.bin'];
    const buffers = await Promise.all(names.map(n => fetchAsset(n)));
    names.forEach((n, i) => { if (buffers[i].byteLength !== meta.files[n].bytes) throw new Error(`Incomplete ${n}`); });
    const volume = new Uint16Array(buffers[0]), vertices = new Float32Array(buffers[1]), triangles = new Uint32Array(buffers[2]);
    if (vertices.length !== meta.mesh.vertices * 3 || triangles.length !== meta.mesh.triangles * 3 ||
        !vertices.every(Number.isFinite) || !triangles.every(i => i < meta.mesh.vertices)) throw new Error('Invalid salt mesh');
    clearTimeout(timeout);
    const axes = meta.axes_km, extent = axes.map(a => a[a.length - 1]), min = axes.map(a => a[0]);
    const center = new THREE.Vector3((min[0] + extent[0]) / 2, (min[1] + extent[1]) / 2, -(min[2] + extent[2]) / 2);
    scene = new THREE.Scene();
    scene.add(new THREE.AmbientLight(0xffffff, 1.4));
    const light = new THREE.DirectionalLight(0xffffff, 2.8); light.position.set(-5, -12, 18); scene.add(light);
    const fill = new THREE.DirectionalLight(0xc2ddff, 1.3); fill.position.set(18, 10, -10); scene.add(fill);
    const camera = new THREE.PerspectiveCamera(38, 1, .05, 200);
    camera.up.set(0, 0, 1);
    orbit = new OrbitControls(camera, canvas);
    orbit.target.copy(center); orbit.enablePan = false;
    orbit.minDistance = 5; orbit.maxDistance = 65;
    orbit.rotateSpeed = .65; orbit.zoomSpeed = .8;
    const geom = new THREE.BufferGeometry();
    for (let i = 2; i < vertices.length; i += 3) vertices[i] *= -1;
    for (let i = 0; i < triangles.length; i += 3) [triangles[i + 1], triangles[i + 2]] = [triangles[i + 2], triangles[i + 1]];
    geom.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
    geom.setIndex(new THREE.BufferAttribute(triangles, 1)); geom.computeVertexNormals();
    const salt = new THREE.Mesh(geom, new THREE.MeshPhongMaterial({ color: 0xe9a565, specular: 0x403023, shininess: 24, side: THREE.DoubleSide, transparent: true, opacity: .85, depthWrite: false }));
    salt.renderOrder = 2; scene.add(salt);
    const box = new THREE.Box3(new THREE.Vector3(min[0], min[1], -extent[2]), new THREE.Vector3(extent[0], extent[1], -min[2]));
    scene.add(new THREE.Box3Helper(box, 0x637b8b));
    const labels = [];
    function addLabel(text, point) {
      const element = document.createElement('span'); element.textContent = text;
      document.querySelector('.salt-axis-labels').append(element);
      labels.push({ element, point: new THREE.Vector3(...point) });
    }
    addLabel(`X · ${extent[0].toFixed(2)} km`, [extent[0], min[1], -extent[2]]);
    addLabel(`Y · ${extent[1].toFixed(2)} km`, [min[0], extent[1], -extent[2]]);
    addLabel(`Depth · ${extent[2].toFixed(2)} km`, [min[0], min[1], -extent[2]]);
    function render() {
      scheduled = 0;
      renderer.render(scene, camera);
      const w = host.clientWidth, h = host.clientHeight;
      for (const { element, point } of labels) {
        const p = point.clone().project(camera);
        element.hidden = p.z > 1 || Math.abs(p.x) > 1 || Math.abs(p.y) > 1;
        element.style.left = `${Math.max(5, Math.min(w - element.offsetWidth - 5, (p.x + 1) * w / 2))}px`;
        element.style.top = `${Math.max(42, Math.min(h - 44, (1 - p.y) * h / 2))}px`;
      }
    }
    function requestRender() { if (!scheduled) scheduled = requestAnimationFrame(render); }
    orbit.addEventListener('change', requestRender);
    const presets = { overview: [16, -22, 16], top: [0, -.01, 30], side: [0, -30, 1], below: [15, -22, -14] };
    function setView(name) {
      camera.position.copy(center).add(new THREE.Vector3(...presets[name]));
      orbit.target.copy(center); orbit.update(); requestRender();
    }
    document.querySelectorAll('[data-view]').forEach(b => on(b, 'click', () => setView(b.dataset.view)));
    function zoom(factor) {
      const d = camera.position.clone().sub(orbit.target);
      d.setLength(Math.max(orbit.minDistance, Math.min(orbit.maxDistance, d.length() * factor)));
      camera.position.copy(orbit.target).add(d); orbit.update(); requestRender();
    }
    on($('zoom-in'), 'click', () => zoom(.8)); on($('zoom-out'), 'click', () => zoom(1.25));
    on(canvas, 'keydown', event => {
      const d = camera.position.clone().sub(orbit.target);
      const spherical = new THREE.Spherical().setFromVector3(new THREE.Vector3(d.x, d.z, -d.y));
      if (event.key === 'ArrowLeft') spherical.theta -= .12;
      else if (event.key === 'ArrowRight') spherical.theta += .12;
      else if (event.key === 'ArrowUp') spherical.phi -= .12;
      else if (event.key === 'ArrowDown') spherical.phi += .12;
      else if (event.key === '+' || event.key === '=') { event.preventDefault(); zoom(.8); return; }
      else if (event.key === '-') { event.preventDefault(); zoom(1.25); return; }
      else if (event.key === 'Home') { event.preventDefault(); setView('overview'); return; }
      else return;
      event.preventDefault(); spherical.makeSafe(); d.setFromSpherical(spherical);
      camera.position.copy(orbit.target).add(new THREE.Vector3(d.x, -d.z, d.y)); orbit.update(); requestRender();
    });
    const slices = [null, null, null];
    function updateSlice(axis) {
      const id = 'xyz'[axis], index = Number($(`slice-${id}`).value), value = axes[axis][index];
      $(`${id}-value`).textContent = `${value.toFixed(2)} km`;
      $(`slice-${id}`).setAttribute('aria-valuetext', `${value.toFixed(2)} kilometres${axis === 2 ? ' depth' : ''}`);
      if (slices[axis]) { scene.remove(slices[axis]); disposeObject(slices[axis]); slices[axis] = null; }
      if (!$(`show-${id}`).checked) { requestRender(); return; }
      const { width, height, values, other } = section(volume, meta.shape, axis, index);
      const pixels = new Uint8Array(width * height * 4);
      values.forEach((v, i) => { pixels.set(velocityColor(v), i * 4); pixels[i * 4 + 3] = 255; });
      const texture = new THREE.DataTexture(pixels, width, height, THREE.RGBAFormat);
      texture.colorSpace = THREE.SRGBColorSpace; texture.magFilter = THREE.NearestFilter;
      texture.minFilter = THREE.NearestFilter; texture.needsUpdate = true;
      const positions = [], uv = [], faces = [];
      for (let j = 0; j < height; j++) for (let i = 0; i < width; i++) {
        const p = [0, 0, 0]; p[axis] = value; p[other[0]] = axes[other[0]][i]; p[other[1]] = axes[other[1]][j];
        positions.push(p[0], p[1], -p[2]); uv.push((i + .5) / width, (j + .5) / height);
        if (i < width - 1 && j < height - 1) { const a = j * width + i; faces.push(a, a + 1, a + width, a + 1, a + width + 1, a + width); }
      }
      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
      geometry.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2)); geometry.setIndex(faces);
      const mesh = new THREE.Mesh(geometry, new THREE.MeshBasicMaterial({ map: texture, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1 }));
      slices[axis] = mesh; scene.add(mesh); requestRender();
    }
    for (let a = 0; a < 3; a++) {
      const id = 'xyz'[a], slider = $(`slice-${id}`);
      slider.max = meta.shape[a] - 1;
      on(slider, 'input', () => updateSlice(a)); on($(`show-${id}`), 'change', () => updateSlice(a));
    }
    function updateSalt() {
      salt.visible = $('show-salt').checked;
      const opacity = Number($('salt-opacity').value) / 100;
      salt.material.opacity = opacity; salt.material.transparent = opacity < 1;
      salt.material.depthWrite = opacity === 1; salt.material.needsUpdate = true;
      $('opacity-value').textContent = `${Math.round(opacity * 100)}%`; requestRender();
    }
    on($('show-salt'), 'change', updateSalt); on($('salt-opacity'), 'input', updateSalt);
    let survey;
    function updateSurvey() {
      if (survey) { scene.remove(survey); disposeObject(survey); }
      survey = new THREE.Group();
      for (const points of surveyPoints($('acquisition').value, extent)) {
        const geometry = new THREE.BufferGeometry().setFromPoints(points.map(p => new THREE.Vector3(...p)));
        survey.add(new THREE.Line(geometry, new THREE.LineBasicMaterial({ color: 0x79c4ff, transparent: true, opacity: .45 })));
        survey.add(new THREE.Points(geometry.clone(), new THREE.PointsMaterial({ color: 0x91d0ff, size: .12, sizeAttenuation: true })));
      }
      scene.add(survey); requestRender();
    }
    on($('acquisition'), 'change', updateSurvey);
    function reset() {
      $('show-salt').checked = true; $('salt-opacity').value = 85;
      for (let a = 0; a < 3; a++) { const id = 'xyz'[a]; $(`slice-${id}`).value = Math.floor((meta.shape[a] - 1) / 2); $(`show-${id}`).checked = a === 1; updateSlice(a); }
      $('acquisition').value = 'none'; updateSurvey(); updateSalt(); setView('overview');
    }
    on($('reset'), 'click', reset);
    host.append(canvas);
    function resize() {
      const w = host.clientWidth, h = host.clientHeight;
      if (!w || !h) return;
      renderer.setSize(w, h, false); camera.aspect = w / h;
      // Keep the horizontal model footprint in frame in tall/mobile viewports.
      camera.fov = 2 * Math.atan(Math.tan(19 * Math.PI / 180) * Math.max(1, 1.3 / camera.aspect)) * 180 / Math.PI;
      camera.updateProjectionMatrix(); requestRender();
    }
    if (window.ResizeObserver) { observer = new ResizeObserver(resize); observer.observe(host); }
    on(window, 'resize', resize);
    on(canvas, 'webglcontextlost', event => { event.preventDefault(); controlsPanel.disabled = true; $('salt-fallback').hidden = false; canvas.hidden = true; status.textContent = '3D graphics were interrupted. The static preview is shown.'; $('retry').hidden = false; });
    reset(); resize();
    $('salt-fallback').hidden = true; controlsPanel.disabled = false;
    status.textContent = `${meta.shape.join(' × ')} samples · ${Math.round(meta.mesh.triangles / 1000)}k surface triangles · ready to explore`;
    if (meta.source.kind === 'original') {
      $('crop-tag').textContent = '/ original grid';
      $('model-summary').textContent = `SEG/EAGE 3D Salt Model (1997). Original velocity grid, reduced for display: ${extent[0].toFixed(2)} × ${extent[1].toFixed(2)} km, ${min[2].toFixed(2)}–${extent[2].toFixed(2)} km depth.`;
      $('source-explanation').textContent = 'This viewer uses the original SEG/EAGE velocity grid. The importer reads its 676 × 676 × 210 big-endian float32 samples with X varying fastest. See the metadata for the source checksum and transformations.';
    }
    // Small read-only diagnostic surface for browser tests; no source volume exposed.
    window.saltViewer = { metadata: meta, snapshot: () => ({ slices: 'xyz'.split('').map(id => Number($(`slice-${id}`).value)), saltVisible: salt.visible, opacity: salt.material.opacity, camera: camera.position.toArray(), survey: $('acquisition').value, drawCalls: renderer.info.render.calls }) };
  } catch (error) {
    cleanup(); controlsPanel.disabled = true;
    $('salt-fallback').hidden = false; $('retry').hidden = false;
    status.textContent = location.protocol === 'file:'
      ? 'Interactive loading needs a local web server. The static model and sections are available.'
      : 'The interactive model could not load. The static model and reference sections remain available; retry to load 3D.';
    console.warn('Salt viewer:', error.message);
  } finally { loading = false; }
}
$('retry').addEventListener('click', start);
window.addEventListener('pagehide', () => cleanup(), { once: true });
start();
