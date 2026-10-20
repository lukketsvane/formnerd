import functools
import json
import sys

import manifold3d as mf
import numpy as np
import trimesh
from scipy import ndimage
from skimage import measure

import hus

PLA = 1.24e-3
SENG = 256.0


def les(sti):
    P = json.load(open(sti))
    return {g: {k: v["verdi"] for k, v in d.items() if not k.startswith("_")} for g, d in P.items() if not g.startswith("_")}


class Felt:
    def __init__(self, d, lo, p):
        self.d, self.lo, self.p = d, lo, p

    def __call__(self, pts):
        pts = np.asarray(pts, float)
        i = np.clip(np.round((pts - self.lo) / self.p).astype(int), 0, np.array(self.d.shape) - 1)
        return self.d[i[..., 0], i[..., 1], i[..., 2]]

    def kant(self, niva, akse, maks, a, b):
        i = [int(round((v - self.lo[k]) / self.p)) for k, v in zip([x for x in range(3) if x != akse], (a, b))]
        sl = [i[0], i[1]]
        sl.insert(akse, slice(None))
        col = np.flatnonzero(self.d[tuple(sl)] >= niva)
        if not len(col):
            return None
        return self.lo[akse] + (col.max() if maks else col.min()) * self.p

    def minste(self, lo, hi, steg=0.5):
        ax = [np.arange(a, b + 1e-9, steg) for a, b in zip(lo, hi)]
        g = np.stack(np.meshgrid(*ax, indexing="ij"), -1).reshape(-1, 3)
        return float(self(g).min())


def rydd(M, minste=1.0):
    deler = [d for d in M.decompose() if d.volume() > minste]
    ut = deler[0]
    for d in deler[1:]:
        ut = ut + d
    return ut


def storst(M):
    deler = M.decompose()
    return max(deler, key=lambda x: x.volume()) if deler else M


def boks(x0, x1, y0, y1, z0, z1):
    return hus.boks((min(x0, x1), min(y0, y1), min(z0, z1)), (max(x0, x1), max(y0, y1), max(z0, z1)))


def kjegle_x(x0, x1, y, z, r0, r1):
    c = mf.Manifold.cylinder(x1 - x0, r0, r1, 96).rotate((0, 90, 0))
    return c.translate((x0, y, z))


def mn(*a):
    return functools.reduce(np.minimum, a)


def samla(delar):
    return functools.reduce(lambda a, b: a + b, delar)


def lågaste_x(M, d, lo, x0, x1):
    """Lågaste x på M i kvar (y, z)-kolonne av avstandsfeltet (uendeleg der M ikkje finst)."""
    p = hus.PITCH
    tm = hus.til_tm(M ^ hus.halvrom_x(x0, x1))
    t = (tm.vertices[tm.faces] - lo) / p
    ylo, yhi = np.ceil(t[:, :, 1].min(1)).astype(int), np.floor(t[:, :, 1].max(1)).astype(int)
    zlo, zhi = np.ceil(t[:, :, 2].min(1)).astype(int), np.floor(t[:, :, 2].max(1)).astype(int)
    cy, cz = np.clip(yhi - ylo + 1, 0, None), np.clip(zhi - zlo + 1, 0, None)
    k = np.repeat(np.arange(len(t)), cy * cz)
    i = np.arange((cy * cz).sum()) - np.repeat(np.cumsum(cy * cz) - cy * cz, cy * cz)
    yy, zz = ylo[k] + i // np.maximum(cz[k], 1), zlo[k] + i % np.maximum(cz[k], 1)
    a, b, c = t[k, 0], t[k, 1], t[k, 2]
    dd = (b[:, 1] - c[:, 1]) * (a[:, 2] - c[:, 2]) + (c[:, 2] - b[:, 2]) * (a[:, 1] - c[:, 1])
    ok = np.abs(dd) > 1e-12
    dd = np.where(ok, dd, 1)
    w1 = ((b[:, 1] - c[:, 1]) * (zz - c[:, 2]) + (c[:, 2] - b[:, 2]) * (yy - c[:, 1])) / dd
    w2 = ((c[:, 1] - a[:, 1]) * (zz - c[:, 2]) + (a[:, 2] - c[:, 2]) * (yy - c[:, 1])) / dd
    e = 1e-6
    inne = ok & (w1 >= -e) & (w2 >= -e) & (1 - w1 - w2 >= -e) & (yy >= 0) & (zz >= 0) & (yy < d.shape[1]) & (zz < d.shape[2])
    x = lo[0] + (w1 * a[:, 0] + w2 * b[:, 0] + (1 - w1 - w2) * c[:, 0]) * p
    H = np.full(d.shape[1:], np.inf, np.float32)
    np.minimum.at(H, (yy[inne], zz[inne]), x[inne])
    return H


def fas_felt(d, lo, x0, x1, f):
    """Område der f(d, X) > 0, rekna berre i skiva x0..x1 av avstandsfeltet."""
    p = hus.PITCH
    i0, i1 = max(int((x0 - lo[0]) / p) - 2, 0), min(int(np.ceil((x1 - lo[0]) / p)) + 3, d.shape[0])
    X = (lo[0] + np.arange(i0, i1) * p)[:, None, None]
    h = np.pad(f(d[i0:i1], X).astype(np.float32), 1, constant_values=-1.0)
    return hus.nivaa(h, lo + np.array([(i0 - 1) * p, -p, -p]), 0.0)


def stabel_modell(S, xb, ly, lz, retning):
    """Forenkla stabel: MB nedst (bak), CAM med kamera framme. retning=+1: USB mot +z."""
    B = S["breidd"]
    yc = ly - S["linse_tverr"]
    z_sd = lz - retning * S["linse_frå_sd_ende"]
    z_usb = z_sd + retning * S["lengd_cam"]
    za, zb = sorted((z_sd, z_usb))
    mza, mzb = sorted((z_usb, z_usb - retning * S["lengd_mb"]))
    y0, y1 = yc - B / 2, yc + B / 2
    xL = xb + S["djupn"]
    xp = xL - S["linsetopp_over_pcb"]
    xsd, xk = xp + S["sd_hogd"], xp + S["kamerakropp_topp_over_pcb"]
    d = {}
    d["mb"] = boks(xb, xb + 1.6, y0, y1, mza, mzb)
    d["usb"] = boks(xb + 1.6, xb + 4.6, yc - 3.75, yc + 3.75, z_usb - retning * 5.5, z_usb + retning * 0.3)
    for yr in (y0 + 0.8, y1 - 3.3):
        d[f"hylse_{yr:.0f}"] = boks(xb + 1.6, xp - 1.25 - 2.5, yr, yr + 2.5, z_sd + retning * 3.3, z_sd + retning * 23.6)
        d[f"list_{yr:.0f}"] = boks(xp - 1.25 - 2.5, xp - 1.25, yr, yr + 2.5, z_sd + retning * 3.3, z_sd + retning * 23.6)
    d["esp32s"] = boks(xp - 1.25 - 3.0, xp - 1.25, yc - 9, yc + 9, z_usb, z_usb - retning * 25.5)
    d["cam"] = boks(xp - 1.25, xp, y0, y1, za, zb)
    sd = S["sd_sokkel"]
    d["sd"] = boks(xp, xsd, yc - sd / 2, yc + sd / 2, z_sd, z_sd + retning * 15.6)
    kk = S["kamerakropp"] / 2
    d["kamera"] = boks(xsd, xk, ly - kk, ly + kk, lz - kk, lz + kk)
    d["linse"] = hus.sylinder(((xk + xL) / 2, ly, lz), S["linseløp"] / 2, xL - xk, "x")
    d["blits"] = boks(xp, xp + 1.0, y1 - 3.5, y1 - 1.0, z_usb - retning * 11.5, z_usb - retning * 9.0)
    return d, dict(za=za, zb=zb, mza=mza, mzb=mzb, y0=y0, y1=y1, yc=yc, xb=xb, xL=xL, xp=xp, z_usb=z_usb, z_sd=z_sd)


def sveip_fram(F, x0, x1, klaring, pitch=0.2):
    """Alt som ligg framfor (+x) eller i same kolonne som fremre skal: må vere tomt for at skalet kan skyvast på langs -x."""
    tm = hus.til_tm(F)
    occ, lo = hus.fyll(tm, pitch=pitch)
    har = occ.any(0)
    minx = np.where(har, np.argmax(occ, axis=0), occ.shape[0])
    i0, i1 = max(int((x0 - lo[0]) / pitch), 0), min(int((x1 - lo[0]) / pitch), occ.shape[0])
    ix = np.arange(i0, i1)[:, None, None]
    S = ix >= minx[None]
    r = int(np.ceil(klaring / pitch))
    S = ndimage.binary_dilation(S, structure=np.ones((1, 2 * r + 1, 2 * r + 1), bool))
    S = np.pad(S, 1)
    v, f, _, _ = measure.marching_cubes(S.astype(np.float32), level=0.5, spacing=(pitch,) * 3)
    m = trimesh.Trimesh(v + lo + np.array([(i0 - 1) * pitch + 0.00291, -pitch + 0.00313, -pitch + 0.00271]), f[:, ::-1], process=True)
    if m.volume < 0:
        m.invert()
    return hus.til_mf(m).simplify(0.02)


def bygg(P):
    K, R, S, Li, U = (P[k] for k in ("kropp", "ramme", "stabel", "linser", "usb_plugg"))
    W, t, to, c, L = K["breidd"], K["vegg"], K["lepp_ytre"], K["lepp_klaring"], K["lepp_lengd"]
    m = hus.last_ytre(K["kjelde_mesh"], W)
    O = hus.til_mf(m)
    occ, lo = hus.fyll(m)
    d = hus.avstand(occ)
    F = Felt(d, lo, hus.PITCH)
    niv = lambda x: hus.nivaa(d, lo, x).simplify(0.05)
    I_t, I_o, I_oc, I_tk = niv(t), niv(to), niv(to + c), niv(t + R["klaring"])
    kontroll = {}
    ly = Li["y"]
    def ringkant(z, r0, r1, niva=0.0, f=np.median):
        v = [F.kant(niva, 0, True, ly + r * np.sin(a), z + r * np.cos(a)) for r in np.arange(r0, r1, 0.5) for a in np.linspace(0, 2 * np.pi, 36, endpoint=False)]
        return float(f([x for x in v if x is not None]))

    fyll = []
    for zf in Li["fyll_søkk_z"]:
        xv = ringkant(zf, 6.0, 9.0)
        fyll.append(hus.sylinder((xv - 4, ly, zf), 5.5, 8, "x"))
        kontroll.setdefault("fylte_søkk", []).append({"z": zf, "visirplan_x": round(xv, 2)})
    Oy = O
    for f in fyll:
        Oy = Oy + (f ^ hus.halvrom_x(-1e3, 1e3))
    skal = Oy - I_t
    r_hol = Li["hol"] / 2

    def plasser(lz, retning, x_lins):
        rom = skal - hus.sylinder((x_lins, ly, lz), r_hol, 80, "x")

        def gap(xb):
            deler, _ = stabel_modell(S, xb, ly, lz, retning)
            return samla([v for k, v in deler.items() if k != "linse"]).min_gap(rom, 5.0)

        hi = x_lins - S["djupn"]
        if gap(hi) >= S["frigang"]:
            return hi
        lo_ = hi - 12.0
        if gap(lo_) < S["frigang"]:
            raise RuntimeError(f"stabelen ved z={lz} får ikkje {S['frigang']} mm frigang")
        for _ in range(16):
            m = (lo_ + hi) / 2
            lo_, hi = (m, hi) if gap(m) >= S["frigang"] else (lo_, m)
        return lo_

    stablar, innmat = [], {}
    for i, (lz, retning) in enumerate(zip(Li["z"], (+1, -1))):
        xv = ringkant(lz, r_hol + 0.5, r_hol + 3.0)
        x_lins = xv - t + Li["inn_i_hol"]
        deler, info = stabel_modell(S, plasser(lz, retning, x_lins), ly, lz, retning)
        info.update(lz=lz, retning=retning, visir_x=xv, linse_under_maks=x_lins - info["xL"])
        info["ytre_min_x"] = ringkant(lz, r_hol, r_hol + Li["fres_inne"] + 0.5, f=np.min)
        stablar.append(info)
        for k, v in deler.items():
            innmat[f"stabel_{i + 1}_{k}"] = v
    x_s = min(min(s["xb"] - R["loddeklaring"], s["xb"] + S["usb_over_mb_underside"] - U["hogd"] / 2 - U["vegg_under"]) for s in stablar)
    P_, a_p, oc = R["plate"], R["plate_klaring"], to + c
    x0 = x_s - L - c

    front = (Oy - I_t) ^ hus.halvrom_x(x_s, 1e3)
    front = front + ((Oy - I_o) ^ hus.halvrom_x(x_s - L, x_s))
    front = front - fas_felt(d, lo, x_s - 1, x_s + t - to + 1, lambda D, X: mn(D - to - 0.05, x_s + D - to - X, X - x_s + 1, t + 0.5 - D))
    bak = (Oy - I_t) ^ hus.halvrom_x(-1e3, x0)
    bak = bak + ((I_oc - niv(t + K["lepp_inn_tillegg"])) ^ hus.halvrom_x(x0, x_s - P_ - c))
    bak = bak - (fas_felt(d, lo, x0 - oc - 1, x0 + 1, lambda D, X: mn(D + 0.5, oc + 0.1 - D - (x0 - X), X - (x0 - oc - 0.5), x0 + 0.5 - X)) ^ hus.halvrom_x(-1e3, x0))
    ramme = storst(I_oc ^ hus.halvrom_x(x_s - P_, x_s - a_p))

    cl, sv, sh, hy = R["klaring"], R["styrevegg"], R["styrehogd"], R["hylle"]
    hol = []
    for s in stablar:
        ya, yb, za, zb = s["y0"] - cl, s["y1"] + cl, s["mza"] - cl, s["mzb"] + cl
        xt = s["xb"] + sh
        for yc, dy in ((ya, 1), (yb, -1)):
            for zc, dz in ((za, 1), (zb, -1)):
                usb_ende = (dz == -1) == (s["retning"] > 0)
                lz_ben = 5.0 if usb_ende else 8.0
                ben = boks(x_s - 0.5, xt, yc, yc - dy * sv, zc - dz * sv, zc + dz * lz_ben) + boks(x_s - 0.5, xt, yc, yc + dy * 7, zc, zc - dz * sv)
                hylle = boks(x_s - 0.5, s["xb"], yc, yc + dy * hy, zc, zc + dz * hy)
                ramme = ramme + ((ben + hylle) ^ I_tk)
        ux = s["xb"] + S["usb_over_mb_underside"]
        z_inn = s["z_usb"] - s["retning"] * 0.5
        hol.append(boks(ux - U["hogd"] / 2, ux + U["hogd"] / 2, s["yc"] - U["breidd"] / 2, s["yc"] + U["breidd"] / 2, z_inn, z_inn + s["retning"] * 40))
        hol.append(hus.sylinder((s["xL"], ly, s["lz"]), r_hol, 30, "x"))
        x_inn = ringkant(s["lz"], r_hol + 0.5, r_hol + 3.0, niva=t)
        hol.append(kjegle_x(x_inn - 0.01, x_inn + Li["fas_inne"], ly, s["lz"], r_hol + Li["fas_inne"], r_hol))
        x_fres = s["ytre_min_x"] - 1.6
        if x_fres > s["xL"] - 4:
            hol.append(kjegle_x(s["xL"] - 4, x_fres, ly, s["lz"], r_hol + Li["fres_inne"], r_hol + Li["fres_inne"]))
        hol.append(kjegle_x(s["xL"], s["xL"] + 25, ly, s["lz"], r_hol, r_hol + 25 * np.tan(np.radians(Li["synsfelt_halvvinkel"]))))
        hol.append(kjegle_x(s["visir_x"] - t - 0.01, s["visir_x"] + 3, ly, s["lz"], r_hol, Li["fas_ytre"] / 2 + 1.2))

    for h in hol:
        front, bak, ramme = front - h, bak - h, ramme - h

    sveip = sveip_fram(front, x0 - 1.0, x_s + sh + 20.0, c)
    v0 = bak.volume(), ramme.volume()
    bak, ramme = bak - sveip, ramme - sveip
    kontroll["sveip_trimma_mm3"] = {"bakre_skal": round(v0[0] - bak.volume(), 1), "innmatsramme": round(v0[1] - ramme.volume(), 1)}
    H = lågaste_x(front, d, lo, x_s - L - 1, x_s + t - to + 2)[None]
    platekant = fas_felt(d, lo, x_s - P_, x_s + t - to, lambda D, X: mn(D - oc - 0.05, t - D, x_s - a_p + D - to - X, X - (x_s - P_ + 0.5), H - a_p - X))
    for h in hol:
        platekant = platekant - h
    ramme = ramme + platekant
    bak_utan_knast = bak

    xm = x_s - c - (L + P_) / 2
    sentrum = np.array([ly, W / 2])
    for vinkel in np.radians([90, 270, 15, 165, 195, 345]):
        retn = np.array([np.sin(vinkel), np.cos(vinkel)])
        flate = None
        for r in np.arange(5, 80, 0.1):
            yz = sentrum + r * retn
            if F((xm, yz[0], yz[1])) < oc:
                flate = sentrum + (r - 0.1) * retn
                break
        if flate is None:
            continue
        sx = np.array([xm, *(flate - retn * (R["knast_r"] - R["knast_ut"]))])
        bak = bak + (mf.Manifold.sphere(R["knast_r"], 48).translate(sx) ^ hus.halvrom_x(x0, x_s - P_ - c))
        front = front - mf.Manifold.sphere(R["knast_r"] + 0.15, 48).translate(sx)
        kontroll.setdefault("knastar", []).append([round(float(v), 1) for v in sx])
    front, bak, ramme = rydd(front), rydd(bak), rydd(ramme)

    deler = {"fremre_skal": front, "bakre_skal": bak, "innmatsramme": ramme}

    kontroll["x_skøyt"] = round(x_s, 2)
    kontroll["stereobasis_mm"] = round(abs(Li["z"][0] - Li["z"][1]), 2)
    kontroll["stablar"] = []
    for i, s in enumerate(stablar):
        k = {key: round(float(v), 2) for key, v in s.items()}
        gap = {n[9:]: M.min_gap(front, 5.0) for n, M in innmat.items() if n.startswith(f"stabel_{i + 1}_")}
        linse = gap.pop("linse")
        trong = min(gap, key=gap.get)
        k["klaring_til_fremre_skal_mm"] = round(gap[trong], 2)
        k["trongaste_del"] = trong
        k["linseløp_til_holkant_mm"] = round(linse, 2)
        ytter = F.kant(0, 2, s["retning"] > 0, s["xb"] + S["usb_over_mb_underside"], s["yc"])
        k["usb_kontakt_til_ytterflate_mm"] = round(abs(ytter - s["z_usb"]), 2)
        kontroll["stablar"].append(k)
    kontroll["kollisjonar_mm3"] = {}
    alle = {**deler, **innmat}
    namn = list(alle)
    for a in range(len(namn)):
        for b in range(a + 1, len(namn)):
            if namn[a].startswith("stabel") and namn[b].startswith(namn[a][:8]):
                continue
            v = (alle[namn[a]] ^ alle[namn[b]]).volume()
            if v > 0.01:
                kontroll["kollisjonar_mm3"][f"{namn[a]} / {namn[b]}"] = round(v, 2)
    andre = samla([bak_utan_knast, ramme] + list(innmat.values()))
    kontroll["påskyving_mm3"] = {str(dx): round((front.translate((dx, 0, 0)) ^ andre).volume(), 2) for dx in (0.0, 0.1, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 8.0, 12.0, 20.0, 30.0)}
    return deler, innmat, kontroll


ROT = {"fremre_skal": (0, -90, 0), "bakre_skal": (0, 90, 0), "innmatsramme": (0, -90, 0)}


def print_retning(namn, M):
    M = M.rotate(ROT[namn])
    lo = M.bounding_box()[:3]
    return M.translate((-lo[0], -lo[1], -lo[2]))


def printsjekk(M, stl=None):
    tm = hus.til_tm(M)
    lag1 = M.slice(0.1)
    opna = lag1.offset(-0.42, mf.JoinType.Round).offset(0.42, mf.JoinType.Round)
    n, a = tm.face_normals, tm.area_faces
    lo, hi = tm.bounds
    paa_seng = tm.triangles_center[:, 2] < 0.05
    heng = (n[:, 2] < -np.cos(np.radians(45))) & ~paa_seng
    return {
        "volum_cm3": round(M.volume() / 1000, 1),
        "masse_g_massiv": round(M.volume() * PLA, 1),
        "mål_mm": [round(float(x), 1) for x in hi - lo],
        "får_plass_på_P1S": bool((hi - lo <= SENG).all()),
        "vasstett": bool(tm.is_watertight),
        "komponentar": len(M.decompose()),
        "trekantar": int(len(tm.faces)),
        "flate_på_seng_mm2": round(float(a[paa_seng].sum()), 0),
        "overheng_over_45_mm2": round(float(a[heng].sum()), 0),
        "lag1_mm2": round(lag1.area(), 0),
        "lag1_bitar": len(lag1.decompose()),
        "lag1_smalare_enn_2_liner_mm2": round(lag1.area() - opna.area(), 1),
        **({} if stl is None else stl_sjekk(stl)),
    }


def stl_sjekk(sti):
    tm = trimesh.load(sti)
    kantar = np.unique(tm.edges_sorted, axis=0, return_counts=True)[1]
    return {"stl_vasstett": bool(tm.is_watertight), "stl_kantar_med_fleire_enn_2_flater": int((kantar > 2).sum())}


def prøvebitar(P, deler, kontroll):
    L, P_ = P["kropp"]["lepp_lengd"], P["ramme"]["plate"]
    xs = kontroll["x_skøyt"]
    ut = {
        "prove_skoyt_framme": ("fremre_skal", deler["fremre_skal"] ^ boks(xs - L - 1, xs + 6, -1e3, 1e3, -1, 38)),
        "prove_skoyt_bak": ("bakre_skal", deler["bakre_skal"] ^ boks(xs - L - 8, xs, -1e3, 1e3, -1, 38)),
        "prove_skoyt_ramme": ("innmatsramme", deler["innmatsramme"] ^ boks(xs - P_ - 1, xs + 2, -1e3, 1e3, -1, 38)),
    }
    for i, s in enumerate(kontroll["stablar"], 1):
        z = (s["za"] - 4, 1e3) if s["retning"] > 0 else (-1e3, s["zb"] + 4)
        ut[f"prove_holdar_{i}"] = ("innmatsramme", deler["innmatsramme"] ^ boks(-1e3, 1e3, s["y0"] - 6, s["y1"] + 6, s["za"] - 6, s["zb"] + 6))
        ut[f"prove_linse_usb_{i}"] = ("fremre_skal", deler["fremre_skal"] ^ boks(s["xb"] - 2, 1e3, s["y0"] - 6, s["y1"] + 6, *z))
    return ut


def lagre_3mf(sti, delar, mellomrom=8.0):
    scene, x, y, rad = trimesh.Scene(), 0.0, 0.0, 0.0
    for namn, M in delar:
        tm = hus.til_tm(M)
        e = tm.extents
        if x + e[0] > SENG:
            x, y, rad = 0.0, y + rad + mellomrom, 0.0
        tm.apply_translation((x, y, 0))
        scene.add_geometry(tm, node_name=namn, geom_name=namn)
        x, rad = x + e[0] + mellomrom, max(rad, e[1])
    open(sti, "wb").write(trimesh.exchange.threemf.export_3MF(scene))


if __name__ == "__main__":
    UT = f"{sys.argv[1]}/print"
    P = les(f"{UT}/parametrar.json")
    deler, innmat, kontroll = bygg(P)
    kontroll["delar"] = {}
    utskrift = []
    for namn, M in deler.items():
        Mp = print_retning(namn, M)
        hus.til_tm(Mp).export(f"{UT}/{namn}.stl")
        hus.til_tm(M).export(f"{UT}/montert/{namn}.glb")
        kontroll["delar"][namn] = printsjekk(Mp, f"{UT}/{namn}.stl")
        utskrift.append((namn, Mp))
    lagre_3mf(f"{UT}/{sys.argv[1]}-hus-alle-delar.3mf", utskrift)
    prøve = []
    for namn, (rot, M) in prøvebitar(P, deler, kontroll).items():
        Mp = print_retning(rot, storst(M))
        hus.til_tm(Mp).export(f"{UT}/provebitar/{namn}.stl")
        kontroll["delar"][namn] = printsjekk(Mp, f"{UT}/provebitar/{namn}.stl")
        prøve.append((namn, Mp))
    lagre_3mf(f"{UT}/provebitar/{sys.argv[1]}-provebitar.3mf", prøve)
    for namn, M in innmat.items():
        hus.til_tm(M).export(f"{UT}/montert/{namn}.glb")
    json.dump(kontroll, open(f"{UT}/kontroll.json", "w"), indent=2, ensure_ascii=False)
    print(json.dumps(kontroll, indent=2, ensure_ascii=False))
