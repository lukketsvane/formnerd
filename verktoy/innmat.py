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
    hi = next((b for b in range(hi, lo, -10) if test(b)), None)
    if hi is None:
        return None
    while hi - lo > 1:
        mid = (lo + hi) // 2
        lo, hi = (lo, mid) if test(mid) else (mid, hi)
    return hi


CAM_MB = (27, 42, 25)
CAM = (27, 42, 12)
BATTERI = (34, 50, 6)
MODUL = (12, 12, 8)


def lommar(occ, breidd_mm, linser, modul=MODUL):
    mm = breidd_mm / N
    occ = occ.copy()
    v = VEGG / mm
    for yf, zf in linser:
        yi, zi = int(round(yf * N)), int(round(zf * N))
        hy, hz, d = modul[1] / 2 / mm, modul[0] / 2 / mm, modul[2] / mm
        y0, y1 = int(np.floor(yi - hy - v)), int(np.ceil(yi + hy + v)) + 1
        z0, z1 = int(np.floor(zi - hz - v)), int(np.ceil(zi + hz + v)) + 1
        flate = occ[:, y0:y1, z0:z1]
        if min(y0, z0) < 0 or not flate.any(axis=0).all():
            return None
        xf = int((flate.shape[0] - 1 - np.argmax(flate[::-1], axis=0)).min())
        x0, x1 = int(np.floor(xf - 2 * v - d)), xf + 1
        if x0 < 0 or not occ[x0:x1, y0:y1, z0:z1].all():
            return None
        occ[int(np.floor(xf - v - d)):int(np.ceil(xf - v)) + 1, int(np.floor(yi - hy)):int(np.ceil(yi + hy)) + 1, int(np.floor(zi - hz)):int(np.ceil(zi + hz)) + 1] = False
    return occ


def grovt(occ, k=2):
    s = [n // k * k for n in occ.shape]
    o = occ[: s[0], : s[1], : s[2]]
    return o.reshape(s[0] // k, k, s[1] // k, k, s[2] // k, k).all(axis=(1, 3, 5))


def fit(occ, mm, boks):
    s = [int(np.ceil((x + 2 * VEGG) / mm)) for x in boks]
    return s, np.argwhere(ndimage.minimum_filter(occ, size=s, mode="constant", cval=0))


def to_passar(occ, mm, a, b):
    v = VEGG / mm
    kart = {}
    for pb in set(itertools.permutations(b)):
        kart[pb] = fit(occ, mm, pb)
    for pa in set(itertools.permutations(a)):
        sa, PA = fit(occ, mm, pa)
        if not len(PA):
            continue
        for sb, PB in kart.values():
            if not len(PB):
                continue
            for k in range(3):
                gap = (sa[k] + sb[k]) / 2 - v
                if PB[:, k].max() - PA[:, k].min() >= gap or PA[:, k].max() - PB[:, k].min() >= gap:
                    return True
    return False


def tre_passar(occ, mm, a, b, c):
    for pa in set(itertools.permutations(a)):
        sa, PA = fit(occ, mm, pa)
        if not len(PA):
            continue
        kandidatar = {tuple(PA[f(PA[:, k])]) for k in range(3) for f in (np.argmin, np.argmax)}
        for p in kandidatar:
            core = [int(np.ceil(x / mm)) for x in pa]
            lo = [p[k] - sa[k] // 2 + (sa[k] - core[k]) // 2 for k in range(3)]
            rest = occ.copy()
            rest[lo[0]:lo[0] + core[0], lo[1]:lo[1] + core[1], lo[2]:lo[2] + core[2]] = False
            if to_passar(rest, mm, b, c):
                return True
    return False


def pakking(occ, linser=None, k=2):
    def test(breidd):
        o = lommar(occ, breidd, linser) if linser else occ
        if o is None:
            return False
        return tre_passar(grovt(o, k), breidd / N * k, CAM_MB, CAM, BATTERI)
    return test


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "--linser":
    linser = json.loads(sys.argv[2])
    res = {}
    for p in sys.argv[3:]:
        m = trimesh.load(p, force="mesh")
        m.merge_vertices()
        occ = fyll(m)
        e = m.extents / m.extents[2]
        b0 = minste_breidd(pakking(occ))
        b1 = minste_breidd(pakking(occ, linser.get(p)))
        res[p] = {
            "linser_brøkdel_av_breidd": linser.get(p),
            "linseavstand_brøkdel_av_breidd": round(float(np.hypot(*np.subtract(*linser[p]))), 3) if p in linser else None,
            "cam_mb_cam_batteri": {"minste_breidd_mm": b0, "hogd_mm": round(b0 * e[1]) if b0 else None, "djupn_mm": round(b0 * e[0]) if b0 else None},
            "cam_mb_cam_batteri_og_kameramodular_ved_linsene": {"minste_breidd_mm": b1, "hogd_mm": round(b1 * e[1]) if b1 else None, "djupn_mm": round(b1 * e[0]) if b1 else None},
        }
    print(json.dumps(res, indent=2, ensure_ascii=False))
    sys.exit()


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
