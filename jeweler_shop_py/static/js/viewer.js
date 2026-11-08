import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

const host = document.getElementById('viewer');
const status = document.getElementById('viewer-status');
const METALS = {
  gold24: { color: '#ffc94d', metalness: 1, roughness: 0.16 },
  rose18: { color: '#e3a08e', metalness: 1, roughness: 0.22 },
  platinum: { color: '#e8eaee', metalness: 0.97, roughness: 0.08 },
};
const INTRO = 3.4;
const LIGHT_BASE = [2.4, 0.9, 1.8];

let renderer;
try { renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true }); }
catch (_) { status.textContent = '3D preview is not supported on this device'; throw _; }
renderer.setPixelRatio(Math.min(devicePixelRatio, 1.75));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
host.appendChild(renderer.domElement);

const scene = new THREE.Scene();
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
const camera = new THREE.PerspectiveCamera(34, 1, 0.1, 50);
camera.position.set(0, 4, 9);

const lights = [[4, 6, 5], [-5, 2, 3], [0, 3, -6]].map((p) => { const l = new THREE.DirectionalLight(0xffffff, 0); l.position.set(...p); scene.add(l); return l; });

const metalMat = new THREE.MeshPhysicalMaterial({ color: METALS.gold24.color, metalness: 1, roughness: 0.2, clearcoat: 0.3, envMapIntensity: 1.4 });
const gemMat = new THREE.MeshPhysicalMaterial({ color: 0xffffff, metalness: 0, roughness: 0, transmission: 0.92, thickness: 0.8, ior: 2.4, clearcoat: 1, envMapIntensity: 2.5 });
const ring = new THREE.Group();
ring.add(new THREE.Mesh(new THREE.TorusGeometry(1, 0.14, 48, 128), metalMat));
const bezel = new THREE.Mesh(new THREE.CylinderGeometry(0.34, 0.22, 0.22, 8), metalMat); bezel.position.y = 1.2; ring.add(bezel);
const gem = new THREE.Mesh(new THREE.OctahedronGeometry(0.36, 0), gemMat); gem.position.y = 1.52; gem.scale.set(1.05, 1.2, 1.05); ring.add(gem);
ring.rotation.x = 0.2; scene.add(ring);

const shadow = new THREE.Mesh(new THREE.CircleGeometry(1.6, 48), new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.35 }));
shadow.rotation.x = -Math.PI / 2; shadow.position.y = -1.3; scene.add(shadow);

const controls = new OrbitControls(camera, renderer.domElement);
Object.assign(controls, { enablePan: false, enableDamping: true, dampingFactor: 0.06, minDistance: 2.4, maxDistance: 8, autoRotate: true, autoRotateSpeed: 1.1, enabled: false });
controls.target.set(0, 0.4, 0);

const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
let t = reduce ? INTRO : 0, done = false, metal = 'gold24';
const target = new THREE.Color();

function resize() { const w = host.clientWidth, h = host.clientHeight; renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix(); }
new ResizeObserver(resize).observe(host); resize();

const clock = new THREE.Clock();
renderer.setAnimationLoop(() => {
  const dt = Math.min(clock.getDelta(), 0.05);
  const m = METALS[metal];
  target.set(m.color); metalMat.color.lerp(target, 1 - Math.exp(-6 * dt));
  metalMat.metalness = THREE.MathUtils.damp(metalMat.metalness, m.metalness, 6, dt);
  metalMat.roughness = THREE.MathUtils.damp(metalMat.roughness, m.roughness, 6, dt);
  ring.position.y = Math.sin(clock.elapsedTime * 1.1) * 0.04;
  if (!done) {
    t += dt;
    const p = Math.min(t / INTRO, 1), e = 1 - Math.pow(1 - p, 3);
    const a = THREE.MathUtils.lerp(Math.PI * 1.35, 0.35, e), r = THREE.MathUtils.lerp(9, 4.2, e);
    camera.position.set(Math.sin(a) * r, THREE.MathUtils.lerp(4, 0.9, e), Math.cos(a) * r);
    camera.lookAt(0, 0.4, 0);
    lights.forEach((l, i) => (l.intensity = LIGHT_BASE[i] * e));
    if (p >= 1) { done = true; controls.enabled = true; }
  } else controls.update();
  renderer.render(scene, camera);
  if (status) { status.remove(); }
});

document.querySelectorAll('[data-metal]').forEach((b) => b.addEventListener('click', () => {
  metal = b.dataset.metal;
  document.querySelectorAll('[data-metal]').forEach((x) => x.classList.toggle('on', x === b));
}));
const spin = document.getElementById('v-spin');
spin.addEventListener('click', () => { controls.autoRotate = !controls.autoRotate; spin.textContent = controls.autoRotate ? 'Pause spin' : 'Auto-spin'; });
document.getElementById('v-replay').addEventListener('click', () => { t = 0; done = false; controls.enabled = false; lights.forEach((l) => (l.intensity = 0)); });
