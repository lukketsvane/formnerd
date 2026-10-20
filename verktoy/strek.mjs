import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
let chromium;
try { ({ chromium } = await import('playwright')); } catch { ({ chromium } = await import('/opt/node22/lib/node_modules/playwright/index.mjs')); }

const [scenefil, utmappe] = process.argv.slice(2);
const scene = JSON.parse(fs.readFileSync(scenefil, 'utf8'));
const three = process.env.THREE_DIR;

const page_html = `<!doctype html><html><body style="margin:0;background:#fff">
<script type="importmap">{"imports":{"three":"/three/build/three.module.js","three/addons/":"/three/examples/jsm/"}}</script>
<script type="module">
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
const sc = await (await fetch('/scene.json')).json();
const S = sc.storleik || 1600;
const renderer = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true });
renderer.setSize(S, S);
renderer.outputColorSpace = THREE.LinearSRGBColorSpace;
document.body.appendChild(renderer.domElement);
const loader = new GLTFLoader();
const sceneT = new THREE.Scene();
const objekt = [];
for (const [i, o] of sc.objekt.entries()) {
  const g = await loader.loadAsync('/fil/' + encodeURIComponent(o.fil));
  const grp = g.scene;
  grp.traverse(m => { if (m.isMesh && !m.geometry.attributes.normal) m.geometry.computeVertexNormals(); });
  grp.position.set(...(o.flytt || [0, 0, 0]));
  grp.userData.id = i + 1;
  sceneT.add(grp);
  objekt.push(grp);
}
const box = new THREE.Box3();
for (const o of objekt) box.expandByObject(o);
const c = box.getCenter(new THREE.Vector3());
const r = box.getSize(new THREE.Vector3()).length() / 2 * (sc.zoom || 1.08);
const d = new THREE.Vector3(...sc.retning).normalize();
const cam = new THREE.OrthographicCamera(-r, r, r, -r, 0.1, 10 * r);
cam.position.copy(c).addScaledVector(d, 4 * r);
cam.up.set(...(sc.opp || [0, 1, 0]));
cam.lookAt(c);
cam.updateProjectionMatrix();
cam.updateMatrixWorld(true);
const proj = (v) => { const p = v.clone().project(cam); return [(p.x + 1) / 2 * S, (1 - p.y) / 2 * S]; };
window.__ankre = (sc.ankre || []).map(a => proj(new THREE.Vector3(...a)));
const buf = (mat) => { sceneT.overrideMaterial = mat; renderer.setClearColor(0x000000, 0); renderer.render(sceneT, cam); return renderer.domElement.toDataURL('image/png'); };
const out = {};
out.normal = buf(new THREE.MeshNormalMaterial());
const dm = new THREE.ShaderMaterial({
  vertexShader: 'varying float vz; void main(){ vec4 mv = modelViewMatrix*vec4(position,1.0); vz = -mv.z; gl_Position = projectionMatrix*mv; }',
  fragmentShader: 'uniform float n; uniform float f; varying float vz; void main(){ float t=(vz-n)/(f-n); gl_FragColor=vec4(floor(t*255.0)/255.0, fract(t*255.0), 0.0, 1.0); }',
  uniforms: { n: { value: 3 * r - 2 * r }, f: { value: 5 * r + 2 * r } }
});
out.djupn = buf(dm);
const ids = [];
for (const o of objekt) {
  const col = new THREE.Color().setRGB((o.userData.id) / 255, 0, 0);
  o.traverse(m => { if (m.isMesh) m.userData.idmat = new THREE.MeshBasicMaterial({ color: col }); });
}
sceneT.overrideMaterial = null;
for (const o of objekt) o.traverse(m => { if (m.isMesh) { m.userData.orig = m.material; m.material = m.userData.idmat; } });
renderer.setClearColor(0x000000, 1); renderer.render(sceneT, cam);
out.id = renderer.domElement.toDataURL('image/png');
for (const o of objekt) o.traverse(m => { if (m.isMesh) m.material = m.userData.orig; });
sceneT.add(new THREE.HemisphereLight(0xffffff, 0x888888, 1.2));
const dl = new THREE.DirectionalLight(0xffffff, 1.4); dl.position.copy(cam.position).add(new THREE.Vector3(0, r * 3, 0)); sceneT.add(dl);
for (const [i, o] of objekt.entries()) {
  const farge = new THREE.Color(sc.objekt[i].farge || '#c8cac8');
  o.traverse(m => { if (m.isMesh) m.material = new THREE.MeshStandardMaterial({ color: farge, roughness: 0.75, metalness: 0 }); });
}
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.setClearColor(0xffffff, 1); renderer.render(sceneT, cam);
out.farge = renderer.domElement.toDataURL('image/png');
window.__ut = out;
document.title = 'ferdig';
</script></body></html>`;

const server = http.createServer((req, res) => {
  const u = decodeURIComponent(req.url);
  if (u === '/') return res.end(page_html);
  if (u === '/scene.json') return res.end(JSON.stringify(scene));
  if (u.startsWith('/fil/')) return res.end(fs.readFileSync(u.slice(5)));
  if (u.startsWith('/three/')) { res.setHeader('Content-Type', 'text/javascript'); return res.end(fs.readFileSync(path.join(three, u.slice(7)))); }
  res.statusCode = 404; res.end();
}).listen(0);
const browser = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
const page = await browser.newPage({ viewport: { width: scene.storleik || 1600, height: scene.storleik || 1600 } });
page.on('pageerror', e => console.error(e));
await page.goto(`http://127.0.0.1:${server.address().port}/`);
await page.waitForFunction(() => document.title === 'ferdig', null, { timeout: 300000 });
const ut = await page.evaluate(() => window.__ut);
const ankre = await page.evaluate(() => window.__ankre);
fs.mkdirSync(utmappe, { recursive: true });
for (const [k, v] of Object.entries(ut)) fs.writeFileSync(path.join(utmappe, k + '.png'), Buffer.from(v.split(',')[1], 'base64'));
fs.writeFileSync(path.join(utmappe, 'ankre.json'), JSON.stringify(ankre));
await browser.close();
server.close();
