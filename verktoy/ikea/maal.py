import glob
import json
import os
import sys
import time

import numpy as np
from PIL import Image
from scipy import ndimage
from skimage.morphology import skeletonize
from skimage.transform import hough_circle, hough_circle_peaks

HER = os.path.dirname(os.path.abspath(__file__))
REF = os.path.normpath(os.path.join(HER, "..", "..", "referansar", "ikea-monteringsstil"))
FW_PT = 551.28
REF_SIDER = {"01-framside.jpg": "cover", "03-deloversikt.jpg": "inventory", "04-beslag.jpg": "hardware", "05-eksplodert-oversikt.jpg": "exploded",
             "06-steg-forstorringsbobler.jpg": "step", "07-steg-underdelar.jpg": "step", "09-steg-multiplikator.jpg": "step", "10-atvaring-verktoy.jpg": "warnings"}
GRENSER = {"tomme": 18.0, "daud": 25.0, "lin": (0.26, 0.62), "min_figurar": 4, "ppi": 300, "vekt": (0.80, 1.10)}


def ramme(ink):
    H, W = ink.shape
    rr, kk = np.nonzero(ink.mean(1) > 0.6)[0], np.nonzero(ink.mean(0) > 0.6)[0]
    t, b, v, h = rr[rr < H / 2], rr[rr > H / 2], kk[kk < W / 2], kk[kk > W / 2]
    t0, b1 = (t.min() if len(t) else 0), (b.max() if len(b) else H - 1)
    l0, r1 = (v.min() if len(v) else 0), (h.max() if len(h) else W - 1)

    def løp(sett, i, steg):
        n = 0
        while i in sett:
            n, i = n + 1, i + steg
        return n
    tj = np.median([løp(set(t.tolist()), t0, 1), løp(set(b.tolist()), b1, -1), løp(set(v.tolist()), l0, 1), løp(set(h.tolist()), r1, -1)])
    return int(l0), int(t0), int(r1), int(b1), float(tj)


def storste_tomme(occ):
    H, W = occ.shape
    h = np.zeros(W, int)
    best = (0, None)
    for y in range(H):
        h = np.where(occ[y], 0, h + 1)
        st = []
        for x in range(W + 1):
            cur = h[x] if x < W else 0
            start = x
            while st and st[-1][1] >= cur:
                s, hh = st.pop()
                if hh * (x - s) > best[0]:
                    best = (hh * (x - s), (s, y - hh + 1, x, y + 1))
                start = s
            st.append((start, cur))
    return best


def mal(g, tersk=140):
    ink = g < tersk
    l0, t0, r1, b1, tj = ramme(ink)
    fw, fh = r1 - l0, b1 - t0
    k = int(max(tj, 1)) + 3
    sub = ink[t0 + k:b1 - k, l0 + k:r1 - k]
    sh, sw = sub.shape
    r = max(2, int(round(0.012 * fw)))
    lab, _ = ndimage.label(ndimage.binary_dilation(sub, np.ones((3, 3)), iterations=r))
    kl = []
    for sl in ndimage.find_objects(lab):
        bh, bw = max(1, sl[0].stop - sl[0].start - 2 * r), max(1, sl[1].stop - sl[1].start - 2 * r)
        kl.append({"bbox": [sl[1].start + r + l0 + k, sl[0].start + r + t0 + k, bw, bh], "a": bw * bh / (sh * sw), "lin": max(bw, bh) / fw})
    kl.sort(key=lambda d: -d["a"])
    occ2 = (ndimage.distance_transform_edt(~sub) <= 0.02 * fw).mean()
    sil = ndimage.binary_fill_holes(ndimage.binary_closing(sub, np.ones((3, 3)), iterations=max(1, int(0.004 * fw))))
    daud = (ndimage.distance_transform_edt(~sil) > 0.05 * fw).mean()
    c = max(2, int(round(0.01 * fw)))
    gh, gw = sh // c, sw // c
    grov = ndimage.binary_dilation(sub[:gh * c, :gw * c].reshape(gh, c, gw, c).any((1, 3)), iterations=1)
    a_tom, rekt = storste_tomme(grov)
    band = max(2, int(0.02 * fh))
    y = (t0 + b1) // 2
    prof = 1 - g[y - 20:y + 20, max(0, l0 - 4):l0 + 8].mean(0) / 255
    pt = FW_PT / fw
    return {"fw_px": fw, "pt_px": round(pt, 4), "ramme_pt": round(float(prof.sum()) * pt, 2), "blekk_pct": round(100 * float(sub.mean()), 2),
            "okkupasjon2pct": round(100 * float(occ2), 1), "daud_5pct": round(100 * float(daud), 1),
            "storste_tomme_rekt_pct": round(100 * a_tom / max(1, gh * gw), 1),
            "tomme_rader_pct": round(100 * float(np.mean([not sub[i * band:(i + 1) * band].any() for i in range(sh // band)])), 1),
            "figurar": [{"bbox_px": d["bbox"], "lin_fw": round(d["lin"], 3)} for d in kl if d["a"] > 0.01],
            "_ramme": (l0, t0, r1, b1), "_tom": [v * c for v in rekt] if rekt else None}


def strek(g, maske, pt):
    a = np.where(maske, g, 255.0)
    dark = np.clip((235 - a) / 235, 0, 1)
    ink = a < 150
    if not ink.any():
        return {}
    dt = ndimage.distance_transform_edt(ink)
    blob = ndimage.binary_dilation(dt > 2.5, iterations=4)
    sk = skeletonize(ink & ~blob)
    L = sk.sum() * 1.08
    near = ndimage.binary_dilation(sk, iterations=3) & ~blob
    lok_d = ndimage.uniform_filter(dark * near, 15)
    lok_l = ndimage.uniform_filter(sk.astype(float), 15) * 1.08
    lok = (lok_d / np.maximum(lok_l, 1e-9))[sk & (lok_l > 0.04)]
    ys, xs = np.nonzero(ink)
    bb = max(1, (xs.max() - xs.min()) * (ys.max() - ys.min()))
    return {"vekt_pt": round(float(dark[near].sum() / max(L, 1)) * pt, 3), "vekt_p90_pt": round(float(np.percentile(lok, 90)) * pt, 3) if len(lok) else None,
            "tettleik": round(float(L / (bb * pt)) * 100, 2), "klump": round(float(blob.sum() / max(ink.sum(), 1)), 3)}


def sirklar(g, pt):
    mork = g < 128
    radii = np.arange(12.5 / pt, 15.5 / pt + 0.01, 0.5)
    h = hough_circle(skeletonize(mork), radii)
    _, cx, cy, rr = hough_circle_peaks(h, radii, total_num_peaks=80, min_xdistance=int(radii[0] * 1.2), min_ydistance=int(radii[0] * 1.2))
    H, W = g.shape
    vinkel = np.linspace(0, 2 * np.pi, 180, endpoint=False)
    mork1 = ndimage.binary_dilation(mork, iterations=1)
    lab, _ = ndimage.label(~ndimage.binary_dilation(g < 160, iterations=1))
    st = np.bincount(lab.ravel())
    st[0] = 0
    bg = lab == st.argmax()
    ut = []
    for x, y, r in zip(cx, cy, rr):
        px = np.clip(np.round(x + r * np.cos(vinkel)).astype(int), 0, W - 1)
        py = np.clip(np.round(y + r * np.sin(vinkel)).astype(int), 0, H - 1)
        if mork1[py, px].mean() < 0.95:
            continue
        d = np.arange(r + 2, r + 13)
        sx = np.clip(np.round(x + np.outer(np.cos(vinkel[::2]), d)).astype(int), 0, W - 1)
        sy = np.clip(np.round(y + np.outer(np.sin(vinkel[::2]), d)).astype(int), 0, H - 1)
        stråle = mork1[sy, sx].all(1)
        leiar = int(np.sum(stråle & ~np.roll(stråle, 1))) if not stråle.all() else 0
        yy, xx = np.mgrid[max(0, int(y - r - 11)):min(H, int(y + r + 11)), max(0, int(x - r - 11)):min(W, int(x + r + 11))]
        d2 = (xx - x) ** 2 + (yy - y) ** 2
        ring = (d2 > (r + 3) ** 2) & (d2 < (r + 10) ** 2)
        ut.append((int(x), int(y), float(r), 1 - float(bg[yy[ring], xx[ring]].mean()), leiar))
    p = np.array([q[3] for q in ut])
    return {"n": len(ut), "r_pt": round(float(np.median([q[2] for q in ut])) * pt, 2) if ut else None,
            "ringdel": round(float(np.median(p)), 2) if len(p) else None, "ringdel_over_03": round(float((p > 0.3).mean()), 2) if len(p) else None,
            "leiarar": int(sum(q[4] for q in ut))}


def side(png, sidetype, figurar=None, unntak=()):
    t = time.time()
    g = np.asarray(Image.open(png).convert("L")).astype(np.float32)
    m = mal(g)
    boksar = figurar if figurar is not None else [(x, y, x + w, y + h) for x, y, w, h in (f["bbox_px"] for f in m["figurar"])]
    maske = np.zeros(g.shape, bool)
    for x0, y0, x1, y1 in boksar:
        maske[max(0, int(y0)):int(y1), max(0, int(x0)):int(x1)] = True
    for x0, y0, x1, y1 in unntak:
        maske[max(0, int(y0)):int(y1), max(0, int(x0)):int(x1)] = False
    res = {"type": sidetype, **{k: v for k, v in m.items() if not k.startswith("_")}, "strek": strek(g, maske, m["pt_px"]), "sirklar": sirklar(g, m["pt_px"])}
    res["sekund"] = round(time.time() - t, 2)
    return res


def atvaringar(sider):
    å = []
    for i, s in enumerate(sider):
        n, t = s["side"], s["type"]
        if t not in ("cover", "safety", "warnings") and s["storste_tomme_rekt_pct"] > GRENSER["tomme"]:
            å.append(f"side {n}: største tomme rektangel {s['storste_tomme_rekt_pct']} % (grense {GRENSER['tomme']} %)")
        if t in ("parts", "inventory", "hardware") and s["daud_5pct"] > GRENSER["daud"]:
            å.append(f"side {n}: daud flate {s['daud_5pct']} % (grense {GRENSER['daud']} %)")
        for j, lin in enumerate(s.get("stegfigur_lin_fw", []), 1):
            if not GRENSER["lin"][0] <= lin <= GRENSER["lin"][1]:
                å.append(f"side {n}: stegfigur {j} er {lin} fw (mål {GRENSER['lin'][0]}–{GRENSER['lin'][1]})")
        nf = len(s.get("stegfigur_lin_fw", []))
        neste = sider[i + 1] if i + 1 < len(sider) else None
        if t == "step" and nf < GRENSER["min_figurar"] and neste and neste["type"] == "step" and nf + len(neste.get("stegfigur_lin_fw", [])) <= 6:
            å.append(f"side {n}: {nf} figurar, neste steg kunne fått plass på same side")
        for j, ppi in enumerate(s.get("ppi", []), 1):
            if ppi < GRENSER["ppi"]:
                å.append(f"side {n}: bilete {j} har {ppi} ppi (krav {GRENSER['ppi']})")
        v = s["strek"].get("vekt_pt")
        if s.get("ppi") and v is not None and not GRENSER["vekt"][0] <= v <= GRENSER["vekt"][1]:
            å.append(f"side {n}: effektiv strekvekt {v} pt (mål {GRENSER['vekt'][0]}–{GRENSER['vekt'][1]})")
    return å


if __name__ == "__main__":
    if len(sys.argv) > 1:
        for f in sys.argv[1:]:
            print(os.path.basename(f), json.dumps(side(f, "ukjend"), ensure_ascii=False))
    else:
        ut = {f: side(os.path.join(REF, f), t) for f, t in REF_SIDER.items()}
        json.dump(ut, open(os.path.join(HER, "maal_ref.json"), "w"), indent=1, ensure_ascii=False)
        for f, r in ut.items():
            print(f, r["sekund"], "s", r["okkupasjon2pct"], r["daud_5pct"], r["storste_tomme_rekt_pct"], r["strek"], r["sirklar"])
