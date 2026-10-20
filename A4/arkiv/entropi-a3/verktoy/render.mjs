import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright-core';

const [glbPath, outPrefix, mode = 'tekstur'] = process.argv.slice(2);
const root = path.dirname(new URL(import.meta.url).pathname);

const page = `<!doctype html><html><body style="margin:0;background:#fff">
<script type="importmap">{"imports":{"three":"/node_modules/three/build/three.module.js","three/addons/":"/node_modules/three/examples/jsm/"}}</script>
<script type="module">
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
const W = 900, H = 900;
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setSize(W, H); renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.outputColorSpace = THREE.SRGBColorSpace; renderer.toneMappingExposure = 0.8;
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene(); scene.background = new THREE.Color(0xf2f2f2);
scene.environment = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(), 0.04).texture;
const key = new THREE.DirectionalLight(0xffffff, 1.2); key.position.set(3, 5, 4); scene.add(key);
const gltf = await new GLTFLoader().loadAsync('/model.glb');
const obj = gltf.scene;
if ('${mode}' === 'leire') obj.traverse(o => { if (o.isMesh) { if (!o.geometry.attributes.normal) o.geometry.computeVertexNormals(); o.material = new THREE.MeshStandardMaterial({ color: 0xa8a8a8, roughness: 0.5 }); } });
const box = new THREE.Box3().setFromObject(obj), c = box.getCenter(new THREE.Vector3()), s = box.getSize(new THREE.Vector3());
obj.position.sub(c); scene.add(obj);
const r = Math.max(s.x, s.y, s.z);
const cam = new THREE.PerspectiveCamera(30, W / H, r / 100, r * 100);
window.views = { size: [s.x, s.y, s.z] };
window.shot = (az, el) => {
  const d = r * 2.3, a = az * Math.PI / 180, e = el * Math.PI / 180;
  cam.position.set(d * Math.cos(e) * Math.sin(a), d * Math.sin(e), d * Math.cos(e) * Math.cos(a));
  cam.lookAt(0, 0, 0); renderer.render(scene, cam);
  return renderer.domElement.toDataURL('image/png');
};
window.ready = true;
</script></body></html>`;

const server = http.createServer((req, res) => {
  if (req.url === '/') { res.setHeader('content-type', 'text/html'); return res.end(page); }
  if (req.url === '/model.glb') return fs.createReadStream(glbPath).pipe(res);
  const f = path.join(root, decodeURIComponent(req.url));
  if (!f.startsWith(root) || !fs.existsSync(f)) { res.statusCode = 404; return res.end(); }
  res.setHeader('content-type', f.endsWith('.js') ? 'text/javascript' : 'application/octet-stream');
  fs.createReadStream(f).pipe(res);
}).listen(0);

const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell', args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const p = await browser.newPage();
p.on('pageerror', e => console.error('pageerror', e.message));
await p.goto(`http://localhost:${server.address().port}/`);
await p.waitForFunction('window.ready === true', null, { timeout: 180000 });
console.log('bbox', JSON.stringify(await p.evaluate('window.views.size')));
const views = [['skra-framme', 35, 15], ['grepside', 0, 5], ['bak', -90, 5], ['linse', 90, 5], ['skra-bak', 215, 15], ['topp', 0, 80]];
for (const [name, az, el] of views) {
  const url = await p.evaluate(([a, e]) => window.shot(a, e), [az, el]);
  fs.writeFileSync(`${outPrefix}-${mode}-${name}.png`, Buffer.from(url.split(',')[1], 'base64'));
}
await browser.close(); server.close();
console.log('done');
