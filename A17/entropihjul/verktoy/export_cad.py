import sys, os, json
from build123d import Compound, Color, export_step, export_stl, export_gltf
from gen import load, log, valid

pref, name, dst = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(dst, exist_ok=True)
COL = {'ring': (0.62, 0.62, 0.61), 'cap': (0.80, 0.80, 0.79), 'paint': (0.03, 0.03, 0.03), 'base': (0.74, 0.74, 0.73)}
LBL = {'ring': 'ring_riflet', 'cap': 'lokk', 'paint': 'indeks_lakk', 'base': 'fotring'}
parts = []
for n in ('ring', 'cap', 'paint', 'base'):
    p = f'{pref}_{n}.brep'
    if not os.path.exists(p):
        continue
    s = load(p)
    assert valid(s), n
    s.label = f'{name}_{LBL[n]}'
    s.color = Color(*COL[n])
    parts.append(s)
asm = Compound(label=name, children=parts)
export_step(asm, f'{dst}/{name}.step')
export_stl(Compound(parts), f'{dst}/{name}.stl', tolerance=0.01, angular_tolerance=0.25)
export_gltf(asm, f'{dst}/{name}.glb', binary=True, linear_deflection=0.01, angular_deflection=0.3)
for f in sorted(os.listdir(dst)):
    if f.startswith(name):
        log(f, os.path.getsize(f'{dst}/{f}') // 1024, 'kB')
