"""Finn tubane som ryggar i høgdekartet (z sett ovanfrå) og skriv dei inn i form_maal.json."""
import json, pathlib
import numpy as np, trimesh
from scipy import ndimage
from skimage.morphology import skeletonize

HER = pathlib.Path(__file__).resolve().parent
M = trimesh.load(HER / "../../arkiv/entropi-a3/03-3d/a3-entropi-print-120mm.stl")
H = 0.5
xs, ys = np.arange(0, 92, H), np.arange(0, 121, H)
gx, gy = np.meshgrid(xs, ys, indexing="ij")
O = np.c_[gx.ravel(), gy.ravel(), np.full(gx.size, 150.0)]
loc, ir, _ = M.ray.intersects_location(O, np.tile([0, 0, -1.0], (len(O), 1)), multiple_hits=False)
Z = np.full(gx.shape, np.nan)
Z.ravel()[ir] = loc[:, 2]
Z = np.nan_to_num(Z, nan=0.0)

hx, hy = 31.1, 103.9
ux, uy = 45.5, 13.5
mask = Z > 59.0
mask &= ~((gx < 18.5) & (gy > 44) & (gy < 86))
mask &= ~(np.hypot(gx - hx, gy - hy) < 18.5)
mask &= ~(np.hypot(gx - ux, gy - uy) < 9.8)
mask = ndimage.binary_opening(mask, iterations=2)
edt = ndimage.distance_transform_edt(mask) * H
sk = skeletonize(mask)
nab = ndimage.convolve(sk.astype(int), np.ones((3, 3), int), mode="constant") - 1
junc = sk & (nab > 2)
grein = sk & ~ndimage.binary_dilation(junc, iterations=1)
lab, n = ndimage.label(grein, structure=np.ones((3, 3)))
ut = []
for k in range(1, n + 1):
    ii, jj = np.nonzero(lab == k)
    if len(ii) < 12:
        continue
    pts = np.c_[xs[ii], ys[jj]]
    d = np.linalg.norm(pts[:, None] - pts[None], axis=2)
    a = int(np.argmax(d[0]))
    b = int(np.argmax(d[a]))
    orden = [a]
    rest = set(range(len(pts))) - {a}
    while rest:
        nx = min(rest, key=lambda q: d[orden[-1], q])
        if d[orden[-1], nx] > 2.5:
            break
        orden.append(nx); rest.remove(nx)
    p = pts[orden]
    r = edt[ii, jj][orden]
    z = Z[ii, jj][orden]
    ut.append({"n": int(len(p)), "start": p[0].round(1).tolist(), "slutt": p[-1].round(1).tolist(), "r_median": round(float(np.median(r)), 2), "z_median": round(float(np.median(z)), 1),
               "punkt": np.c_[p, z, r].round(2).tolist()})
ut.sort(key=lambda g: -g["n"])
for g in ut:
    print(g["n"], g["start"], g["slutt"], "r", g["r_median"], "z", g["z_median"])
    for q in g["punkt"][::4]:
        print("    ", q)
fm = json.loads((HER / "form_maal.json").read_text())
fm["ryggar"] = ut
(HER / "form_maal.json").write_text(json.dumps(fm))
