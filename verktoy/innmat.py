import itertools
import json
import sys
from multiprocessing import Pool

import numpy as np
import trimesh
from scipy import ndimage

N = 200
VEGG = 2.0
KLARING = 0.5
CAM_MB = (27, 42, 20)
CAM = (27, 42, 7)
BATTERI = (34, 50, 6)
MODUL = (10, 10, 8)
KANT = 1


def fyll(m):
    v, f = m.vertices, m.faces
    lo = v.min(0)
    pitch = m.extents[2] / N
    ny, nz, nx = (np.ceil(m.extents / pitch).astype(int) + 2 + 2 * KANT)[[1, 2, 0]]
    t = (v[f] - lo) / pitch + KANT + np.array([0.0, 0.0137, 0.0071])
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
    odde = veksl.sum(2) % 2 == 1
    occ = (np.cumsum(veksl, axis=2) % 2).astype(bool)
    occ[odde] = False
    occ = occ.transpose(2, 0, 1)
    return occ, {"odde_kolonnar": int(odde.sum()), "volum_voksel_mot_mesh": round(float(occ.sum() * pitch**3 / m.volume), 4)}


def storleik(boks, mm):
    return [int(np.ceil((x + 2 * KLARING) / mm)) + 1 for x in boks]


def hjorne(inner, s):
    return np.argwhere(ndimage.minimum_filter(inner, size=s, mode="constant", cval=0)) - np.array(s) // 2


def skjer(inner, lo, s, w):
    lo = np.maximum(np.array(lo) - w, 0)
    inner[lo[0]:lo[0] + s[0] + 2 * w, lo[1]:lo[1] + s[1] + 2 * w, lo[2]:lo[2] + s[2] + 2 * w] = False


def lommar(occ, inner, mm, linser):
    v = int(np.ceil(VEGG / mm))
    hz, hy, d = int(np.ceil(MODUL[0] / 2 / mm)), int(np.ceil(MODUL[1] / 2 / mm)), int(np.ceil(MODUL[2] / mm))
    sentrum = [(int(round(yf * N)) + KANT, int(round(zf * N)) + KANT) for yf, zf in linser]
    (y1, z1), (y2, z2) = sentrum
    if abs(z1 - z2) < 2 * hz + 1 + v and abs(y1 - y2) < 2 * hy + 1 + v:
        raise ValueError("linsene står for tett til at kvar modul får eiga lomme")
    inner = inner.copy()
    for yi, zi in sentrum:
        y0, z0 = yi - hy - v, zi - hz - v
        if min(y0, z0) < 0 or yi + hy + v >= occ.shape[1] or zi + hz + v >= occ.shape[2]:
            raise ValueError(f"linsa {yi, zi} ligg for nær kanten av kroppen")
        flate = occ[:, y0:yi + hy + v + 1, z0:zi + hz + v + 1]
        if not flate.any(axis=0).all():
            raise ValueError(f"linsa {yi, zi} ligg utanfor kroppen")
        xf = int((flate.shape[0] - 1 - np.argmax(flate[::-1], axis=0)).min())
        lo = (xf - v - d, yi - hy, zi - hz)
        s = (d + 1, 2 * hy + 1, 2 * hz + 1)
        if lo[0] < 0 or not inner[lo[0]:lo[0] + s[0], lo[1]:lo[1] + s[1], lo[2]:lo[2] + s[2]].all():
            return None, None
        skjer(inner, lo, s, v - 1)
    return inner, sentrum


def grovt(occ, k):
    s = [n // k * k for n in occ.shape]
    o = occ[: s[0], : s[1], : s[2]]
    return o.reshape(s[0] // k, k, s[1] // k, k, s[2] // k, k).all(axis=(1, 3, 5))


def mellomvegg(mm, k):
    return int(np.ceil((VEGG / mm + k - 1) / k))


def to_boksar(inner, mm, k, b, c):
    w = mellomvegg(mm, k)
    mm = mm * k
    kart = {pc: (storleik(pc, mm),) for pc in set(itertools.permutations(c))}
    kart = {pc: (s, hjorne(inner, s)) for pc, (s,) in kart.items()}
    for pb in set(itertools.permutations(b)):
        sb = storleik(pb, mm)
        PB = hjorne(inner, sb)
        if not len(PB):
            continue
        for pc, (sc, PC) in kart.items():
            if not len(PC):
                continue
            for k in range(3):
                if PC[:, k].max() - PB[:, k].min() >= sb[k] - 1 + w:
                    return [(pb, PB[PB[:, k].argmin()]), (pc, PC[PC[:, k].argmax()])]
                if PB[:, k].max() - PC[:, k].min() >= sc[k] - 1 + w:
                    return [(pb, PB[PB[:, k].argmax()]), (pc, PC[PC[:, k].argmin()])]
    return None


def tre_boksar(inner, mm, k, a, b, c, maks=80):
    w = mellomvegg(mm, k)
    mmk = mm * k
    for pa in set(itertools.permutations(a)):
        sa = storleik(pa, mmk)
        PA = hjorne(inner, sa)
        if not len(PA):
            continue
        ytst = [PA[f(PA[:, k])] for k in range(3) for f in (np.argmin, np.argmax)]
        steg = max(1, len(PA) // maks)
        for p in ytst + list(PA[::steg]):
            rest = inner.copy()
            skjer(rest, p, sa, w - 1)
            r = to_boksar(rest, mm, k, b, c)
            if r:
                return [(pa, p)] + r
    return None


def analyse(m, linser=None, k=2):
    occ, kontroll = fyll(m)
    avstand = ndimage.distance_transform_edt(occ)

    grunn = []

    def plassering(breidd):
        mm = breidd / N
        inner = avstand >= VEGG / mm + 0.5
        sentrum = None
        if linser:
            try:
                inner, sentrum = lommar(occ, inner, mm, linser)
            except ValueError as e:
                grunn.append(str(e))
                return None
            if inner is None:
                return None
        r = tre_boksar(grovt(inner, k), mm, k, CAM_MB, CAM, BATTERI)
        return r and {"boksar": [{"mål_mm": list(pb), "nedre_hjørne_mm": [round(float(x * mm * k - KANT * mm), 1) for x in p]} for pb, p in r], "linsesentrum_yz_mm": sentrum and [[round((y - KANT) * mm, 1), round((z - KANT) * mm, 1)] for y, z in sentrum]}

    lo, hi = 40, next((b for b in range(250, 40, -10) if plassering(b)), None)
    if hi is None:
        return {"minste_breidd_mm": None, "grunn": grunn[-1] if grunn else None, **kontroll}
    while hi - lo > 1:
        mid = (lo + hi) // 2
        lo, hi = (lo, mid) if plassering(mid) else (mid, hi)
    monoton = all(plassering(b) for b in range(hi, hi + 4)) and not any(plassering(b) for b in range(hi - 3, hi))
    e = m.extents / m.extents[2]
    res = {"minste_breidd_mm": hi, "hogd_mm": round(hi * e[1]), "djupn_mm": round(hi * e[0]), "monoton_rundt_svaret": monoton, **kontroll, "plassering": plassering(hi)}
    if linser:
        res["linseavstand_mm"] = round(float(np.hypot(*np.subtract(*linser))) * hi, 1)
    return res


def kjor(jobb):
    p, l = jobb
    m = trimesh.load(p, force="mesh")
    return p, analyse(m, l)


if __name__ == "__main__":
    linser = {p: l["linser"] for p, l in json.load(open(sys.argv[1])).items() if not p.startswith("_")}
    jobbar = [(p, l) for p in linser for l in (None, linser[p])]
    with Pool(int(sys.argv[2]) if len(sys.argv) > 2 else 3) as pool:
        ut = pool.map(kjor, jobbar)
    res = {p: {} for p in linser}
    for (p, l), (_, r) in zip(jobbar, ut):
        res[p]["med_kameralommar_ved_linsene" if l else "nedre_grense_utan_lommar"] = r
    print(json.dumps({"føresetnader": {"N": N, "vegg_mm": VEGG, "klaring_per_side_mm": KLARING, "kort_og_usb_kort": CAM_MB, "kort": CAM, "batteri": BATTERI, "kameramodul_breidd_hogd_djupn": MODUL}, "resultat": res}, indent=2, ensure_ascii=False))
