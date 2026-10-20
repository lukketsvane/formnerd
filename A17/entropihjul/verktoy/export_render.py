import sys, json, time
import numpy as np
from build123d import GeomType, Compound
from gen import load, log
from tess import mesh_shape, face_tris, merge

pref = sys.argv[1]
lin = float(sys.argv[2]) if len(sys.argv) > 2 else 0.004
p = json.load(open(f'{pref}_params.json'))
HR = p['HR']; z1 = HR + p['CAP_UP']
FIN = dict(ring_top=p.get('FIN_RING_TOP', 'blast'), cap_top=p.get('FIN_CAP_TOP', 'spun'), cap_dish=p.get('FIN_CAP_DISH', 'spun'),
           cap_side=p.get('FIN_CAP_SIDE', 'brushz'), chamfer=p.get('FIN_CHAMFER', 'polish'))


def classify(part, f):
    gt = f.geom_type
    c = f.center()
    if part == 'paint':
        return 'paint'
    if part == 'base':
        if gt == GeomType.CYLINDER:
            return 'brushz'
        if gt == GeomType.CONE:
            return 'polish'
        return 'spun'
    if gt == GeomType.CONE:
        return FIN['chamfer']
    if part == 'ring':
        if gt == GeomType.PLANE and abs(c.Z - HR) < 1e-3:
            return FIN['ring_top']
        return 'blast'
    if part == 'cap':
        r = float(np.hypot(c.X, c.Y))
        if gt == GeomType.PLANE and abs(c.Z - z1) < 1e-3:
            return FIN['cap_top']
        if gt == GeomType.CYLINDER and abs(r) < 1e-3 and f.area > 1.0:
            return FIN['cap_side']
        if gt in (GeomType.SPHERE, GeomType.TORUS, GeomType.BSPLINE, GeomType.BEZIER, GeomType.REVOLUTION, GeomType.OTHER) and c.Z > z1 - p.get('DISH_DEPTH', 2) - 0.5:
            return FIN['cap_dish']
        if gt == GeomType.CYLINDER:
            return FIN['cap_side']
        return 'polish'
    return 'blast'


out = {}
names = []
for part in ('ring', 'cap', 'paint', 'base'):
    try:
        s = load(f'{pref}_{part}.brep')
    except Exception:
        continue
    t = time.time()
    mesh_shape(s, lin if part == 'ring' else lin * 0.6, 0.08 if part == 'ring' else 0.05)
    groups = {}
    for f in s.faces():
        tr = face_tris(f)
        if tr is None:
            continue
        groups.setdefault(classify(part, f), []).append(tr)
    for g, chunks in groups.items():
        v, fa, n = merge(chunks)
        key = f'{part}__{g}'
        out[key + '_v'] = v; out[key + '_f'] = fa; out[key + '_n'] = n
        names.append(key)
        log(key, len(fa))
out['names'] = np.array(names)
np.savez(f'{pref}_render.npz', **out)
log('saved', f'{pref}_render.npz')
