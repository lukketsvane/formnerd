import sys, pathlib, numpy as np, trimesh
from scipy.spatial import cKDTree

HER = pathlib.Path(__file__).resolve().parent
A3 = HER.parent
UT = A3 / "print" / "cmf"
UT.mkdir(parents=True, exist_ok=True)

glb = trimesh.load(A3.parent / "arkiv/entropi-a3/03-3d/a3-entropi-pbr.glb", force="mesh", process=False)
tex = np.asarray(glb.visual.material.baseColorTexture.convert("RGB"), dtype=np.uint8)
uv = np.asarray(glb.visual.uv)
v = np.asarray(glb.vertices) @ trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])[:3, :3].T
v *= 120.0 / (v.max(0) - v.min(0)).max()
v -= v.min(0)
tre = cKDTree(v)
H, W = tex.shape[:2]


def farge(punkt, k=4):
    d, i = tre.query(punkt, k=k)
    w = 1.0 / np.maximum(d, 1e-3)
    w /= w.sum(1, keepdims=True)
    px = np.clip((uv[i, 0] % 1.0) * (W - 1), 0, W - 1).astype(int)
    py = np.clip((1 - uv[i, 1] % 1.0) * (H - 1), 0, H - 1).astype(int)
    return (tex[py, px] * w[..., None]).sum(1)


for namn in sys.argv[1:] or ["botn", "topp", "utloysar", "usb-lokk"]:
    m = trimesh.load(A3 / "print/stl" / f"{namn}.stl")
    v = np.array(m.vertices, float)
    grep = (v[:, 1] < 12.0) & (v[:, 0] > 12.0) & (v[:, 0] < 60.0) & (v[:, 2] > 7.0) & (v[:, 2] < 51.0)
    v[grep, 1] -= 0.9
    c = farge(v)
    df, _ = tre.query(m.triangles_center)
    ny = df > 0.6
    tc = m.triangles_center
    for (x0, x1), (y0, y1), (z0, z1) in (((1.5, 17.0), (44.0, 86.0), (69.0, 81.0)), ((25.0, 29.6), (114.0, 120.5), (22.4, 31.6)), ((12.0, 60.0), (-5.0, 12.0), (7.0, 51.0)), ((4.0, 17.0), (60.0, 84.0), (83.0, 85.5))):
        ny &= ~((tc[:, 0] > x0) & (tc[:, 0] < x1) & (tc[:, 1] > y0) & (tc[:, 1] < y1) & (tc[:, 2] > z0) & (tc[:, 2] < z1))
    ny |= (tc[:, 0] > 66.0) & (np.hypot(tc[:, 1] - 65.0, tc[:, 2] - 32.0) < 27.2)
    f = m.faces.reshape(-1)
    hjorne = c[f].reshape(-1, 3, 3)
    hjorne[ny] = [14, 14, 16]
    # kurset tillet to graatonar: lys paa tubane og grepet, moerk paa kjernen
    LYS, MOERK = np.array([150, 154, 154]), np.array([62, 67, 69])
    lys = hjorne.mean(2) > 110
    hjorne[lys] = LYS
    hjorne[~lys] = MOERK
    rr = np.hypot(tc[:, 1] - 65.0, tc[:, 2] - 32.0)
    hjorne[(tc[:, 0] > 70.0) & (rr > 26.9) & (rr < 33.0)] = LYS
    hjorne[(tc[:, 0] > 66.0) & (rr <= 26.9)] = MOERK
    hjorne[(tc[:, 0] < 17.5) & (tc[:, 1] > 44.0) & (tc[:, 1] < 86.0) & (tc[:, 2] > 60.0)] = MOERK
    if namn in ("utloysar", "usb-lokk"):
        hjorne[:] = MOERK
    if namn == "botn":
        skinne = (tc[:, 2] < 6.2) & (tc[:, 0] > 17.5) & (tc[:, 0] < 56.5) & (tc[:, 1] > 17.5) & (tc[:, 1] < 104.5)
        hjorne[skinne] = MOERK
    m = trimesh.Trimesh(m.vertices[f], np.arange(len(f)).reshape(-1, 3), process=False)
    m.visual = trimesh.visual.ColorVisuals(m, vertex_colors=np.c_[hjorne.reshape(-1, 3), np.full(len(f), 255)].astype(np.uint8))
    m.export(UT / f"{namn}.ply")
    print(namn, len(df), "nye flater (svarte):", int(ny.sum()))
