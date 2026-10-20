import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
let chromium;
try { ({ chromium } = await import('playwright')); } catch { ({ chromium } = await import('/opt/node22/lib/node_modules/playwright/index.mjs')); }

const root = path.dirname(new URL(import.meta.url).pathname);
const [glb, out] = process.argv.slice(2);

const page_html = `<!doctype html><html><body style="margin:0;background:#fff">
<canvas id="c" width="1200" height="1200"></canvas>
<script type="importmap">{"imports":{"three":"/node_modules/three/build/three.module.js","three/addons/":"/node_modules/three/examples/jsm/"}}</script>
<script type="module">
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
const S = 600;
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setSize(S, S);
renderer.setClearColor(0xffffff, 1);
const scene = new THREE.Scene();
scene.add(new THREE.HemisphereLight(0xffffff, 0x666666, 1.6));
const key = new THREE.DirectionalLight(0xffffff, 1.6);
scene.add(key);
const gltf = await new GLTFLoader().loadAsync('/model.glb');
const obj = gltf.scene;
const mat = new THREE.MeshStandardMaterial({ color: 0xb8bab8, roughness: 0.7, metalness: 0 });
obj.traverse(o => { if (o.isMesh) o.material = mat; });
scene.add(obj);
const box = new THREE.Box3().setFromObject(obj);
const c = box.getCenter(new THREE.Vector3());
const r = box.getSize(new THREE.Vector3()).length() / 2;
const cam = new THREE.PerspectiveCamera(30, 1, 0.01, 100);
const views = [[1, 0, 0, 'front +X'], [1, 0.55, 0.9, '3/4'], [0, 1, 0.001, 'top +Y'], [-1, 0.3, -0.6, 'back']];
const ctx = document.getElementById('c').getContext('2d');
views.forEach(([x, y, z, label], i) => {
  const d = new THREE.Vector3(x, y, z).normalize();
  cam.position.copy(c).addScaledVector(d, r / Math.sin(THREE.MathUtils.degToRad(15)) * 1.05);
  cam.up.set(...(label.startsWith('top') ? [-1, 0, 0] : [0, 1, 0]));
  cam.lookAt(c);
  key.position.copy(cam.position).add(new THREE.Vector3(0, r * 2, 0));
  renderer.render(scene, cam);
  ctx.drawImage(renderer.domElement, (i % 2) * S, Math.floor(i / 2) * S);
  ctx.fillStyle = '#555'; ctx.font = '20px sans-serif'; ctx.fillText(label, (i % 2) * S + 12, Math.floor(i / 2) * S + 28);
});
document.title = 'done';
</script></body></html>`;

const server = http.createServer((req, res) => {
  if (req.url === '/') return res.end(page_html);
  if (req.url === '/model.glb') return res.end(fs.readFileSync(glb));
  const f = path.join(root, decodeURIComponent(req.url));
  res.setHeader('Content-Type', 'text/javascript');
  res.end(fs.readFileSync(f));
}).listen(0);
const port = server.address().port;
const browser = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
const page = await browser.newPage({ viewport: { width: 1200, height: 1200 } });
page.on('pageerror', e => console.error(e));
await page.goto(`http://127.0.0.1:${port}/`);
await page.waitForFunction(() => document.title === 'done', null, { timeout: 120000 });
await page.locator('#c').screenshot({ path: out });
await browser.close();
server.close();
