import json
import sys

import manifold3d as mf
import numpy as np
import trimesh

import hus

PARAM = "A2/print/parametrar.json"
UT = "A2/print"
PLA = 1.24e-3
SENG = 256.0


def les(sti=PARAM):
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


def stabel_modell(S, xb, ly, lz, retning):
    """Forenkla stabel: MB nedst (bak), CAM med kamera framme. retning=+1: USB mot +z."""
    L, B = S["lengd"], S["breidd"]
    z_sd = lz - retning * S["linse_frå_sd_ende"]
    z_usb = z_sd + retning * L
    za, zb = sorted((z_sd, z_usb))
    y0, y1 = ly - B / 2, ly + B / 2
    xL = xb + S["djupn"]
    xp = xL - S["linsetopp_over_pcb"]
    d = {}
    d["mb"] = boks(xb, xb + 1.6, y0, y1, za + (0.5 if retning > 0 else 0), zb - (0 if retning > 0 else 0.5))
    d["usb"] = boks(xb + 1.6, xb + 4.6, ly - 3.75, ly + 3.75, z_usb - retning * 5.5, z_usb + retning * 0.3)
    for yr in (y0 + 0.8, y1 - 3.3):
        d[f"hylse_{yr:.0f}"] = boks(xb + 1.6, xp - 1.25 - 2.5, yr, yr + 2.5, z_sd + retning * 3.3, z_sd + retning * 23.6)
        d[f"list_{yr:.0f}"] = boks(xp - 1.25 - 2.5, xp - 1.25, yr, yr + 2.5, z_sd + retning * 3.3, z_sd + retning * 23.6)
    d["esp32s"] = boks(xp - 1.25 - 3.0, xp - 1.25, ly - 9, ly + 9, z_usb, z_usb - retning * 25.5)
    d["cam"] = boks(xp - 1.25, xp, y0, y1, za, zb)
    sd = S["sd_sokkel"]
    d["sd"] = boks(xp, xp + 2.3, ly - sd / 2, ly + sd / 2, z_sd, z_sd + retning * 15.6)
    kk = S["kamerakropp"] / 2
    d["kamera"] = boks(xp + 2.3, xp + 4.5, ly - kk, ly + kk, lz - kk, lz + kk)
    d["linse"] = hus.sylinder(((xp + 4.5 + xL) / 2, ly, lz), S["linseløp"] / 2, xL - xp - 4.5, "x")
    d["blits"] = boks(xp, xp + 1.0, y1 - 3.5, y1 - 1.0, z_usb - retning * 11.5, z_usb - retning * 9.0)
    return d, dict(za=za, zb=zb, y0=y0, y1=y1, xb=xb, xL=xL, xp=xp, z_usb=z_usb, z_sd=z_sd)


def bygg(P):
    K, R, S, Li, U = (P[k] for k in ("kropp", "ramme", "stabel", "linser", "usb_plugg"))
    W, t, to, c, L = K["breidd"], K["vegg"], K["lepp_ytre"], K["lepp_klaring"], K["lepp_lengd"]
    m = hus.last_ytre(breidd=W)
    O = hus.til_mf(m)
    occ, lo = hus.fyll(m)
    d = hus.avstand(occ)
    F = Felt(d, lo, hus.PITCH)
    niv = lambda x: hus.nivaa(d, lo, x).simplify(0.05)
    I_t, I_o, I_oc, I_tk = niv(t), niv(to), niv(to + c), niv(t + R["klaring"])
    kontroll = {}
    ly = Li["y"]

    def visirplan(z, r0=6.0, r1=9.0):
        v = [F.kant(0, 0, True, ly + r * np.sin(a), z + r * np.cos(a)) for r in np.arange(r0, r1, 0.5) for a in np.linspace(0, 2 * np.pi, 36, endpoint=False)]
        return float(np.median([x for x in v if x is not None]))

    fyll = []
    for zf in Li["fyll_søkk_z"]:
        xv = visirplan(zf)
        fyll.append(hus.sylinder((xv - 4, ly, zf), 5.5, 8, "x"))
        kontroll.setdefault("fylte_søkk", []).append({"z": zf, "visirplan_x": round(xv, 2)})
    Oy = O
    for f in fyll:
        Oy = Oy + (f ^ hus.halvrom_x(-1e3, 1e3))

    stablar, innmat = [], {}
    for i, (lz, retning) in enumerate(zip(Li["z"], (+1, -1))):
        xv = visirplan(lz, Li["hol"] / 2 + 0.5, Li["hol"] / 2 + 3.0)
        kk = S["kamerakropp"] / 2 + 0.5
        fot = [(yy, zz) for yy in np.arange(ly - kk, ly + kk + 0.01, 0.25) for zz in np.arange(lz - kk, lz + kk + 0.01, 0.25) if (yy - ly) ** 2 + (zz - lz) ** 2 >= (Li["hol"] / 2) ** 2]
        x_kropp = min(F.kant(t, 0, True, yy, zz) for yy, zz in fot) - R["klaring"]
        xL = min(x_kropp + 4.5, xv - t + Li["inn_i_hol"])
        deler, info = stabel_modell(S, xL - S["djupn"], ly, lz, retning)
        info.update(lz=lz, retning=retning, visir_x=xv)
        stablar.append(info)
        for k, v in deler.items():
            innmat[f"stabel_{i + 1}_{k}"] = v
    x_s = min(s["xb"] for s in stablar) - R["loddeklaring"]
    P_ = R["plate"]

    front = (Oy - I_t) ^ hus.halvrom_x(x_s, 1e3)
    front = front + ((Oy - I_o) ^ hus.halvrom_x(x_s - L, x_s))
    bak = (Oy - I_t) ^ hus.halvrom_x(-1e3, x_s - L - c)
    bak = bak + ((I_oc - I_t) ^ hus.halvrom_x(x_s - L - c, x_s - P_ - c))
    ramme = storst(I_oc ^ hus.halvrom_x(x_s - P_, x_s - 0.05))

    cl, sv, sh = R["klaring"], R["styrevegg"], R["styrehogd"]
    hol = []
    for s in stablar:
        ya, yb, za, zb = s["y0"] - cl, s["y1"] + cl, s["za"] - cl, s["zb"] + cl
        xt = s["xb"] + sh
        for yc, dy in ((ya, 1), (yb, -1)):
            for zc, dz in ((za, 1), (zb, -1)):
                usb_ende = (dz == -1) == (s["retning"] > 0)
                lz_ben = 5.0 if usb_ende else 8.0
                ben = boks(x_s - 0.5, xt, yc, yc - dy * sv, zc, zc + dz * lz_ben) + boks(x_s - 0.5, xt, yc, yc + dy * 7, zc, zc - dz * sv)
                hylle = boks(x_s - 0.5, s["xb"], yc, yc + dy * 3.5, zc, zc + dz * 3.5)
                ramme = ramme + ((ben + hylle) ^ I_tk)
        ux = s["xb"] + S["usb_over_mb_underside"]
        z_inn = s["z_usb"] - s["retning"] * 0.5
        hol.append(boks(ux - U["hogd"] / 2, ux + U["hogd"] / 2, ly - U["breidd"] / 2, ly + U["breidd"] / 2, z_inn, z_inn + s["retning"] * 40))
        hol.append(hus.sylinder((s["xL"], ly, s["lz"]), Li["hol"] / 2, 30, "x"))
        hol.append(kjegle_x(s["visir_x"] - t - 0.01, s["visir_x"] + 3, ly, s["lz"], Li["hol"] / 2, Li["fas_ytre"] / 2 + 1.2))

    for h in hol:
        front, bak, ramme = front - h, bak - h, ramme - h

    xm = x_s - L / 2 - c
    sentrum = np.array([ly, W / 2])
    for vinkel in np.radians([90, 270, 15, 165, 195, 345]):
        retn = np.array([np.sin(vinkel), np.cos(vinkel)])
        flate = None
        for r in np.arange(5, 80, 0.1):
            yz = sentrum + r * retn
            if F((xm, yz[0], yz[1])) < to + c:
                flate = sentrum + (r - 0.1) * retn
                break
        if flate is None:
            continue
        sx = np.array([xm, *(flate - retn * (R["knast_r"] - R["knast_ut"]))])
        bak = bak + (mf.Manifold.sphere(R["knast_r"], 48).translate(sx) ^ hus.halvrom_x(x_s - L - c, x_s - P_ - c))
        front = front - mf.Manifold.sphere(R["knast_r"] + 0.15, 48).translate(sx)
        kontroll.setdefault("knastar", []).append([round(float(v), 1) for v in sx])
    front, bak, ramme = rydd(front), rydd(bak), rydd(ramme)

    deler = {"fremre_skal": front, "bakre_skal": bak, "innmatsramme": ramme}

    kontroll["x_skøyt"] = round(x_s, 2)
    kontroll["stereobasis_mm"] = round(abs(Li["z"][0] - Li["z"][1]), 2)
    kontroll["stablar"] = []
    for i, s in enumerate(stablar):
        k = {key: round(float(v), 2) for key, v in s.items()}
        sjekk = [innmat[n] for n in innmat if n.startswith(f"stabel_{i + 1}_") and not n.endswith("linse")]
        nærast = min(F.minste(*(np.array(M.bounding_box()[:3]), np.array(M.bounding_box()[3:]))) for M in sjekk) - t
        k["minste_avstand_til_innervegg_mm"] = round(nærast, 2)
        ytter = F.kant(0, 2, s["retning"] > 0, s["xb"] + S["usb_over_mb_underside"], ly)
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
            if v > 0.5:
                kontroll["kollisjonar_mm3"][f"{namn[a]} / {namn[b]}"] = round(v, 1)
    return deler, innmat, kontroll


ROT = {"fremre_skal": (0, -90, 0), "bakre_skal": (0, 90, 0), "innmatsramme": (0, -90, 0)}


def print_retning(namn, M):
    M = M.rotate(ROT[namn])
    lo = M.bounding_box()[:3]
    return M.translate((-lo[0], -lo[1], -lo[2]))


def printsjekk(M):
    tm = hus.til_tm(M)
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
    }


def prøvebitar(P, deler, kontroll):
    L = P["kropp"]["lepp_lengd"]
    xs = kontroll["x_skøyt"]
    s1 = kontroll["stablar"][0]
    return {
        "prove_skoyt_framme": ("fremre_skal", deler["fremre_skal"] ^ boks(xs - L - 1, xs + 6, -1e3, 1e3, -1, 38)),
        "prove_skoyt_bak": ("bakre_skal", deler["bakre_skal"] ^ boks(xs - L - 8, xs, -1e3, 1e3, -1, 38)),
        "prove_holdar": ("innmatsramme", deler["innmatsramme"] ^ boks(-1e3, 1e3, s1["y0"] - 6, s1["y1"] + 6, s1["za"] - 6, s1["zb"] + 6)),
        "prove_linse_usb": ("fremre_skal", deler["fremre_skal"] ^ boks(s1["xb"] - 2, 1e3, s1["y0"] - 6, s1["y1"] + 6, s1["za"] - 4, 1e3)),
    }


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
    P = les()
    deler, innmat, kontroll = bygg(P)
    kontroll["delar"] = {}
    utskrift = []
    for namn, M in deler.items():
        Mp = print_retning(namn, M)
        hus.til_tm(Mp).export(f"{UT}/{namn}.stl")
        hus.til_tm(M).export(f"{UT}/montert/{namn}.glb")
        kontroll["delar"][namn] = printsjekk(Mp)
        utskrift.append((namn, Mp))
    lagre_3mf(f"{UT}/A2-hus-alle-delar.3mf", utskrift)
    prøve = []
    for namn, (rot, M) in prøvebitar(P, deler, kontroll).items():
        Mp = print_retning(rot, storst(M))
        hus.til_tm(Mp).export(f"{UT}/provebitar/{namn}.stl")
        kontroll["delar"][namn] = printsjekk(Mp)
        prøve.append((namn, Mp))
    lagre_3mf(f"{UT}/provebitar/A2-provebitar.3mf", prøve)
    for namn, M in innmat.items():
        hus.til_tm(M).export(f"{UT}/montert/{namn}.glb")
    json.dump(kontroll, open(f"{UT}/kontroll.json", "w"), indent=2, ensure_ascii=False)
    print(json.dumps(kontroll, indent=2, ensure_ascii=False))
