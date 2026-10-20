import itertools
import json
import sys

import numpy as np
import trimesh
from scipy import ndimage

PAKKER = {
    "to_cam": (58, 42, 12),
    "to_cam_pluss_mb": (58, 42, 25),
}
VEGG = 2.0
N = 200


def fyll(m):
    v, f = m.vertices, m.faces
    lo = v.min(0)
    pitch = m.extents[2] / N
    ny, nz, nx = (np.ceil(m.extents / pitch).astype(int) + 2)[[1, 2, 0]]
    t = (v[f] - lo) / pitch + np.array([0.0, 0.0137, 0.0071])
    ylo, yhi = np.ceil(t[:, :, 1].min(1)).astype(int), np.floor(t[:, :, 1].max(1)).astype(int)
    zlo, zhi = np.ceil(t[:, :, 2].min(1)).astype(int), np.floor(t[:, :, 2].max(1)).astype(int)
    cy, cz = np.clip(yhi - ylo + 1, 0, None), np.clip(zhi - zlo + 1, 0, None)
    n = cy * cz
    k = np.repeat(np.arange(len(f)), n)
    i = np.arange(n.sum()) - np.repeat(np.cumsum(n) - n, n)
    yy = ylo[k] + i // np.maximum(cz[k], 1)
    zz = zlo[k] + i % np.maximum(cz[k], 1)
    a, b, c = t[k, 0], t[k, 1], t[k, 2]
    d = (b[:, 1] - c[:, 1]) * (a[:, 2] - c[:, 2]) + (c[:, 2] - b[:, 2]) * (a[:, 1] - c[:, 1])
    ok = np.abs(d) > 1e-12
    d = np.where(ok, d, 1)
    w1 = ((b[:, 1] - c[:, 1]) * (zz - c[:, 2]) + (c[:, 2] - b[:, 2]) * (yy - c[:, 1])) / d
    w2 = ((c[:, 1] - a[:, 1]) * (zz - c[:, 2]) + (a[:, 2] - c[:, 2]) * (yy - c[:, 1])) / d
    w3 = 1 - w1 - w2
    inne = ok & (w1 >= 0) & (w2 >= 0) & (w3 >= 0)
    x = w1 * a[:, 0] + w2 * b[:, 0] + w3 * c[:, 0]
    yy, zz, x = yy[inne], zz[inne], np.clip(np.ceil(x[inne]).astype(int), 0, nx - 1)
    veksl = np.zeros((ny, nz, nx), np.int32)
    np.add.at(veksl, (yy, zz, x), 1)
    occ = (np.cumsum(veksl, axis=2) % 2).astype(bool)
    occ[veksl.sum(2) % 2 == 1] = False
    return occ.transpose(2, 0, 1)


def passar(occ, breidd_mm, boks):
    mm = breidd_mm / N
    w, h, d = boks
    size = [int(np.ceil((s + 2 * VEGG) / mm)) for s in (d, h, w)]
    return bool(ndimage.minimum_filter(occ, size=size, mode="constant", cval=0).any())


def treffpunkt(occ, size):
    return np.argwhere(ndimage.minimum_filter(occ, size=size, mode="constant", cval=0))


def delt_passar(occ, breidd_mm, a, b):
    mm = breidd_mm / N
    for pa in set(itertools.permutations(a)):
        sa = [int(np.ceil((s + 2 * VEGG) / mm)) for s in pa]
        PA = treffpunkt(occ, sa)
        if not len(PA):
            continue
        for pb in set(itertools.permutations(b)):
            sb = [int(np.ceil((s + 2 * VEGG) / mm)) for s in pb]
            PB = treffpunkt(occ, sb)
            if not len(PB):
                continue
            for k in range(3):
                gap = (sa[k] + sb[k]) / 2
                if PB[:, k].max() - PA[:, k].min() >= gap or PA[:, k].max() - PB[:, k].min() >= gap:
                    return True
    return False


def minste_breidd(test, lo=40, hi=250):
    if not test(hi):
        return None
    while hi - lo > 1:
        mid = (lo + hi) // 2
        lo, hi = (lo, mid) if test(mid) else (mid, hi)
    return hi


if __name__ == "__main__":
    res = {}
    for p in sys.argv[1:]:
        m = trimesh.load(p, force="mesh")
        m.merge_vertices()
        occ = fyll(m)
        e = m.extents / m.extents[2]
        res[p] = {"fyllgrad": round(float(occ.mean()), 3)}
        testar = {namn: (lambda br, boks=boks: passar(occ, br, boks)) for namn, boks in PAKKER.items()}
        testar["delt_i_to_rom"] = lambda br: delt_passar(occ, br, (27, 42, 25), (27, 42, 12))
        for namn, test in testar.items():
            b = minste_breidd(test)
            res[p][namn] = {"minste_breidd_mm": b, "hogd_mm": round(b * e[1]) if b else None, "djupn_mm": round(b * e[0]) if b else None}
    print(json.dumps(res, indent=2, ensure_ascii=False))
