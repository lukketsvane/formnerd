import sys, json, pathlib, numpy as np, trimesh
from scipy.spatial import cKDTree
import saum as sm_

HER = pathlib.Path(__file__).resolve().parent
A3 = HER.parent
UT = A3 / "print" / "cmf"
UT.mkdir(parents=True, exist_ok=True)
LYS, MOERK = np.array([150, 154, 154], np.uint8), np.array([62, 67, 69], np.uint8)
k = np.load(UT / "klasse.npz")
tre = cKDTree(k["punkt"])
klasse = k["klasse"]
saum = cKDTree(k["saum"]) if len(k["saum"]) else None
K = json.loads((HER / "delar_konfig.json").read_text())
hx, hy = json.loads((A3 / "print" / "kontroll.json").read_text())["hjul"]["senter"]

felt = k["felt"]
saum_side, lys_pluss, lys_minus = k["saum_side"], k["saum_lys_pluss"], k["saum_lys_minus"]
for namn in sys.argv[1:] or ["botn", "topp", "utloysar", "usb-lokk", "hjulaksel"]:
    m = trimesh.load(A3 / "print/stl" / f"{namn}.stl", process=False)
    v = np.asarray(m.vertices)
    d, i = tre.query(v, k=6)
    w = 1.0 / np.maximum(d, 1e-3)
    lys = (felt[i] * w).sum(1) / w.sum(1) > 0.5
    if saum is not None:
        ds, js = saum.query(v)
        naer = ds < 2.5
        side = np.einsum("ij,ij->i", v - k["saum"][js], saum_side[js])
        lys[naer] = np.where(side[naer] > 0, lys_pluss[js[naer]], lys_minus[js[naer]])
        lys[naer & (np.abs(side) < 0.3)] = False
    moerk_r, lys_r = sm_.regel(v, K, hx, hy)
    lys[lys_r] = True
    lys[moerk_r] = False
    if namn in ("utloysar", "usb-lokk", "hjulaksel"):
        lys[:] = False
    farge = np.where(lys[:, None], LYS, MOERK)
    m.visual = trimesh.visual.ColorVisuals(m, vertex_colors=np.c_[farge, np.full(len(v), 255, np.uint8)])
    m.export(UT / f"{namn}.ply")
    print(namn, len(v), "lyse punkt:", int(lys.sum()))
