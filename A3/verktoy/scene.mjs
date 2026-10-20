import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright-core';

const spec = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const root = path.dirname(new URL(import.meta.url).pathname);
const nm = process.env.NODE_MODULES_DIR || path.join(root, 'node_modules');

const page = `<!doctype html><html><body style="margin:0;background:#fff">
<script type="importmap">{"imports":{"three":"/nm/three/build/three.module.js","three/addons/":"/nm/three/examples/jsm/"}}</script>
<script type="module">
import * as THREE from 'three';
import { STLLoader } from 'three/addons/loaders/STLLoader.js';
import { PLYLoader } from 'three/addons/loaders/PLYLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { mergeVertices } from 'three/addons/utils/BufferGeometryUtils.js';
const spec = await (await fetch('/spec.json')).json();
const [W, H] = spec.size || [1600, 1200];
const r = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
r.setPixelRatio(1); r.setSize(W, H); r.localClippingEnabled = true; r.outputColorSpace = THREE.SRGBColorSpace;
r.toneMapping = THREE.ACESFilmicToneMapping; r.toneMappingExposure = spec.exposure || 0.9;
document.body.appendChild(r.domElement);
const scene = new THREE.Scene(); scene.background = new THREE.Color(spec.bg || 0xffffff);
scene.environment = new THREE.PMREMGenerator(r).fromScene(new RoomEnvironment(), 0.04).texture;
const key = new THREE.DirectionalLight(0xffffff, 1.4); key.position.set(-60, -120, 200); scene.add(key);
const outlineMat = (w) => new THREE.ShaderMaterial({
  uniforms: { w: { value: w } }, side: THREE.BackSide,
  vertexShader: 'uniform float w; void main(){ vec4 p = modelViewMatrix * vec4(position + normal * w, 1.0); gl_Position = projectionMatrix * p; }',
  fragmentShader: 'void main(){ gl_FragColor = vec4(0.0,0.0,0.0,1.0); }' });
const loader = new STLLoader();
const box = new THREE.Box3();
for (const o of spec.objects) {
  const buf = await (await fetch('/f/' + encodeURIComponent(o.stl || o.ply))).arrayBuffer();
  let g = o.ply ? new PLYLoader().parse(buf) : loader.parse(buf);
  if (!o.ply) { g.deleteAttribute('normal'); g = mergeVertices(g, 1e-4); }
  g.computeVertexNormals();
  const clip = o.clip ? [new THREE.Plane(new THREE.Vector3(...o.clip.slice(0, 3)), o.clip[3])] : [];
  const grp = new THREE.Group();
  if (o.style === 'ikea') {
    const fm = new THREE.MeshBasicMaterial({ color: o.color ?? 0xffffff, polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1, transparent: (o.opacity ?? 1) < 1, opacity: o.opacity ?? 1 }); fm.toneMapped = false;
    const fill = new THREE.Mesh(g, fm);
    grp.add(fill);
    if (!o.noOutline) grp.add(new THREE.Mesh(g, outlineMat(o.outline ?? spec.outline ?? 0.35)));
    const lm = new THREE.LineBasicMaterial({ color: 0x000000, transparent: (o.opacity ?? 1) < 1, opacity: Math.min(1, (o.opacity ?? 1) * 1.6) }); lm.toneMapped = false;
    const e = new THREE.LineSegments(new THREE.EdgesGeometry(g, o.crease ?? 35), lm);
    grp.add(e);
    if (o.shade) { const sh = new THREE.Mesh(g, new THREE.MeshLambertMaterial({ color: 0xffffff, transparent: true, opacity: o.shade })); grp.add(sh); }
  } else {
    grp.add(new THREE.Mesh(g, new THREE.MeshStandardMaterial({ color: o.ply ? 0xffffff : (o.color ?? 0xcccccc), vertexColors: !!o.ply, roughness: o.rough ?? 0.6, metalness: 0, transparent: (o.opacity ?? 1) < 1, opacity: o.opacity ?? 1, side: THREE.DoubleSide, clippingPlanes: clip })));
  }
  if (o.pos) grp.position.set(...o.pos);
  scene.add(grp); if (!o.noFit) box.expandByObject(grp);
}
if (spec.light !== false) scene.add(new THREE.AmbientLight(0xffffff, spec.ambient ?? 0.35));
if (spec.fill) { const fl = new THREE.DirectionalLight(0xffffff, spec.fill); fl.position.set(120, 80, 60); scene.add(fl); }
if (spec.ground) { const gm = new THREE.Mesh(new THREE.PlaneGeometry(2000, 2000), new THREE.ShadowMaterial({ opacity: 0.18 })); gm.position.z = spec.ground; scene.add(gm); }
const c = spec.target ? new THREE.Vector3(...spec.target) : box.getCenter(new THREE.Vector3());
const size = box.getSize(new THREE.Vector3()).length();
const dir = new THREE.Vector3(...(spec.dir || [1, -1, 0.8])).normalize();
const asp = W / H, span = (spec.span || size * 0.62);
const cam = spec.persp ? new THREE.PerspectiveCamera(spec.fov || 25, asp, 1, 5000) : new THREE.OrthographicCamera(-span * asp, span * asp, span, -span, -5000, 5000);
cam.up.set(...(spec.up || [0, 0, 1]));
cam.position.copy(c).addScaledVector(dir, spec.persp ? size * 2.2 : 1000); cam.lookAt(c);
cam.updateProjectionMatrix(); cam.updateMatrixWorld();
r.render(scene, cam);
const proj = (spec.anchors || []).map(p => { const v = new THREE.Vector3(...p).project(cam); return [(v.x + 1) / 2 * W, (1 - v.y) / 2 * H]; });
window.result = { png: r.domElement.toDataURL('image/png'), anchors: proj };
</script></body></html>`;

const server = http.createServer((req, res) => {
  const u = decodeURIComponent(req.url);
  if (u === '/') { res.setHeader('content-type', 'text/html'); return res.end(page); }
  if (u === '/spec.json') { res.setHeader('content-type', 'application/json'); return res.end(JSON.stringify(spec)); }
  if (u.startsWith('/f/')) return fs.createReadStream(u.slice(3)).on('error', () => { res.statusCode = 404; res.end(); }).pipe(res);
  if (u.startsWith('/nm/')) { res.setHeader('content-type', 'text/javascript'); return fs.createReadStream(path.join(nm, u.slice(4))).on('error', () => { res.statusCode = 404; res.end(); }).pipe(res); }
  res.statusCode = 404; res.end();
}).listen(0);

const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell', args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const p = await browser.newPage({ viewport: { width: (spec.size || [1600])[0], height: (spec.size || [0, 1200])[1] } });
p.on('pageerror', e => console.error('pageerror', e.message));
await p.goto(`http://localhost:${server.address().port}/`);
await p.waitForFunction('window.result', null, { timeout: 600000 });
const res = await p.evaluate('window.result');
fs.writeFileSync(spec.out, Buffer.from(res.png.split(',')[1], 'base64'));
if (spec.anchors) fs.writeFileSync(spec.out.replace(/\.png$/, '.anchors.json'), JSON.stringify(res.anchors));
await browser.close(); server.close();
console.log('ok', spec.out);
