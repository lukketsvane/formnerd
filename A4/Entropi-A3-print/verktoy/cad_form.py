"""Ytre form til Entropi som rein B-rep (build123d/OCCT), bygd av måla i form_maal.json."""
import json, pathlib, time
import numpy as np
from shapely.geometry import Polygon as ShPolygon
from omriss import glatt, resample
from build123d import *

HER = pathlib.Path(__file__).resolve().parent
K = json.loads((HER / "delar_konfig.json").read_text())
F = K["form"]
MAAL = json.loads((HER / "form_maal.json").read_text())
T0 = time.time()
N_PKT = 96
SENTER = (36.0, 60.0)


def tid(n):
    print(f"{n:<28}{time.time() - T0:7.1f} s", flush=True)


def seksjonsflate(punkt, z):
    return make_face(Wire([Spline(*[(float(x), float(y), z) for x, y in punkt], periodic=True)]))


def forskove(punkt, d):
    p = ShPolygon(punkt).buffer(d, join_style=1)
    if p.geom_type != "Polygon":
        p = max(p.geoms, key=lambda q: q.area)
    return resample(glatt(p, 2.0), front=(58.0, K["akse"]["y"]))


def seksjonar_kropp(full=False):
    return {s["z"]: np.asarray(s["punkt_full" if full else "punkt"]) for s in MAAL["kropp"]}


def kappe(topp, z0, z1, d0, R, steg=12):
    """Avrunda tak: snitt langs ein kvartsirkel med radius R frå z0 (forskyving d0) mot z1, flatt tak frå 75°."""
    ut = []
    for i in range(1, steg):
        th = np.pi / 2 * i / steg
        ut.append((z0 + (z1 - z0) * np.sin(th), d0 - R * (1 - np.cos(th))))
    return ut


def tonnekutt(punkt, z):
    """Tek bort tonneregionen (løpsradius + spalte frå x 66) frå eit fullt snitt."""
    import tonnespalte
    p = tonnespalte.kutt(ShPolygon(punkt), z)
    if p.geom_type != "Polygon":
        p = max(p.geoms, key=lambda q: q.area)
    return resample(glatt(p, 2.0), front=(58.0, K["akse"]["y"]))


def vegg_y(S, z, x):
    """y til grepsida (minste y) ved (x, z), lineært mellom dei målte snitta."""
    from shapely.geometry import LineString
    zs = sorted(S)
    z1 = max([q for q in zs if q <= z] or [zs[0]]); z2 = min([q for q in zs if q >= z] or [zs[-1]])
    ut = []
    for zz in (z1, z2):
        kryss = ShPolygon(S[zz]).exterior.intersection(LineString([(x, -20), (x, 60)]))
        ys = [c[1] for g in getattr(kryss, "geoms", [kryss]) if not g.is_empty for c in g.coords]
        ut.append(min(ys) if ys else None)
    if None in ut:
        return None
    t = 0.0 if z2 == z1 else (z - z1) / (z2 - z1)
    return ut[0] + t * (ut[1] - ut[0])


def kutt_alle(k, verktoy, namn):
    for i, v in enumerate(verktoy):
        ny = k - v
        if ny is not None and ny.is_valid and len(ny.solids()) == 1:
            k = ny
        else:
            print(f"  {namn} {i}: kutt hoppa over")
    return k


def riller(k):
    """Riller i grepsida og eit spor langs delinga, skorne i det reine loftet (plane boksar)."""
    D, ri, dz, df = K["detalj"], K["detalj"]["riller"], K["skal"]["deling_z"], K["detalj"]["delingsfas"]
    S = seksjonar_kropp()
    MN = (Align.MIN, Align.MIN, Align.MIN)
    verktoy = []
    for z in np.arange(ri["z"][0], ri["z"][1] + 0.01, ri["deling"]):
        if abs(z - dz) <= ri["unngaa_deling"]:
            continue
        boksar = []
        for x0 in np.arange(ri["x"][0], ri["x"][1], ri["steg"]):
            ys = [vegg_y(S, z, x) for x in (x0, x0 + ri["steg"] / 2, x0 + ri["steg"])]
            if any(y is None for y in ys):
                continue
            boksar.append(Pos(x0, min(ys) - 3.0, z - ri["breidd"] / 2) * Box(ri["steg"], max(ys) + ri["djupn"] - min(ys) + 3.0, ri["breidd"], align=MN))
        u = boksar[0]
        for b in boksar[1:]:
            u = u + b
        verktoy.append(u)
    k = kutt_alle(k, verktoy, "rille")
    zs = sorted(S)
    naer = min(zs, key=lambda q: abs(q - dz))
    p = np.asarray(S[naer])
    seg = []
    for a, b in zip(p, np.roll(p, -1, axis=0)):
        d = b - a
        L = float(np.hypot(*d))
        v = float(np.degrees(np.arctan2(d[1], d[0])))
        m = (a + b) / 2
        if m[0] > 65.9 and np.hypot(m[1] - K["akse"]["y"], dz - K["akse"]["z"]) < 33.5:
            continue
        seg.append(Pos(m[0], m[1], dz) * Rot(0, 0, v) * Box(L + 0.3, 2.0 + df["djupn"], 2 * df["breidd"], align=(Align.CENTER, Align.MAX, Align.CENTER)).moved(Pos(0, df["djupn"], 0)))
    u = seg[0]
    for b in seg[1:]:
        u = u + b
    return kutt_alle(k, [u], "delingsspor")


def kropp_loft():
    b = F["kropp"]
    S = seksjonar_kropp()
    zs = sorted(S)
    flater = [seksjonsflate(S[z], z) for z in zs]
    topp_full = seksjonar_kropp(full=True)[zs[-1]]
    for z, d in kappe(topp_full, zs[-1], b["topp_z"], 0.0, b["topp_r"]):
        flater.append(seksjonsflate(tonnekutt(forskove(topp_full, d), z), z))
    return riller(loft(flater, ruled=True))


def konservativt(S, z, v):
    """Det minste av kroppsnitta ved z-v, z og z+v, så veggen held v òg der flata hallar."""
    zs = sorted(S)
    p = None
    for zz in (z - v, z, z + v):
        naer = min(zs, key=lambda q: abs(q - zz))
        q = ShPolygon(S[naer])
        p = q if p is None else p.intersection(q)
    if p.geom_type != "Polygon":
        p = max(p.geoms, key=lambda q: q.area)
    return np.asarray(p.exterior.coords)[:-1]


def holrom_loft():
    h = F["holrom"]
    S = seksjonar_kropp(full=True)
    v = K["skal"]["vegg"]
    zs = [z for z in sorted(S) if z >= h["golv_z"]]
    flater = [seksjonsflate(forskove(konservativt(S, z, v), -v), z) for z in zs]
    topp = S[zs[-1]]
    for z, d in kappe(topp, zs[-1], h["tak_z"], -v, h["tak_r"]):
        flater.append(seksjonsflate(forskove(topp, d), z))
    return loft(flater, ruled=True)


def linsetonne():
    L, ef = F["linse"], F["ef"]
    ay, az = K["akse"]["y"], K["akse"]["z"]
    pr = L["profil"] + [[ef["flens_x"][0], pr_r] for pr_r in [L["profil"][-1][1]]] + [[ef["flens_x"][0], ef["flens_r"]], [ef["flens_x"][1], ef["flens_r"]]]
    prof = Polyline((pr[0][0], 0), *[(x, r) for x, r in pr], (pr[-1][0], 0), close=True)
    k = revolve(make_face(prof), Axis.X)
    k = Pos(0, ay, az) * k
    return chamfer(k.edges().group_by(Axis.X)[-1], ef["flens_fas"])


def royr(p, r, b=None):
    sti = Spline(*[tuple(float(v) for v in q) for q in p])
    pl = Plane(origin=sti @ 0, z_dir=sti % 0)
    sek = pl * (Ellipse(r, b) if b else Circle(r))
    return sweep(sek, sti, transition=Transition.ROUND)


def sokarblokk():
    b = F["sokar"]
    k = Box(b["x"][1] - b["x"][0], b["y"][1] - b["y"][0], b["z"][1] - b["z"][0], align=(Align.MIN, Align.MIN, Align.MIN)).moved(Pos(b["x"][0], b["y"][0], b["z"][0]))
    k = fillet([e for e in k.edges() if e.center().Z > b["z"][0] + 1], b["fillet"])
    pl = b["plint"]
    u = pl["utvid"]
    plint = Box(pl.get("x_til", b["x"][1] + u) - b["x"][0], b["y"][1] - b["y"][0] + 2 * u, pl["z"][1] - pl["z"][0], align=(Align.MIN, Align.MIN, Align.MIN)).moved(Pos(b["x"][0], b["y"][0] - u, pl["z"][0]))
    plint = fillet([e for e in plint.edges() if e.center().Z > pl["z"][1] - 0.1 or abs(e.center().Z - (pl["z"][0] + pl["z"][1]) / 2) < 0.5], 1.0)
    return k + plint


def syl(cx, cy, r, z0, z1):
    return Pos(cx, cy, z0) * Cylinder(r, z1 - z0, align=(Align.CENTER, Align.CENTER, Align.MIN))


def hjulboss():
    b = F["hjulboss"]
    c = syl(b["senter"][0], b["senter"][1], b["r"], b["z"][0], b["z"][1])
    c = fillet(c.edges().group_by(Axis.Z)[-1], b["fillet"])
    kr = b["krage"]
    return c + Pos(b["senter"][0], b["senter"][1], kr["z"][0]) * Cone(kr["r"], b["r"], kr["z"][1] - kr["z"][0], align=(Align.CENTER, Align.CENTER, Align.MIN))


def knappboss():
    b = F["knappboss"]
    c = syl(K["utloysar"]["senter"][0], K["utloysar"]["senter"][1], b["r"], b["z"][0], b["z"][1])
    return fillet(c.edges().group_by(Axis.Z)[-1], b["fillet"])


def bygg_form():
    import hashlib
    nokkel = hashlib.sha1(("v9" + json.dumps(K["detalj"]["riller"]) + json.dumps(K["detalj"]["delingsfas"]) + json.dumps(F, sort_keys=True) + json.dumps(MAAL["kropp"]) + json.dumps(K["akse"]) + json.dumps(K["utloysar"])).encode()).hexdigest()[:12]
    cache = HER.parent / "print" / "cad" / f"form_{nokkel}"
    if (cache / "union.brep").exists():
        delar = {p.stem: import_brep(p) for p in sorted(cache.glob("*.brep")) if p.stem != "union"}
        u = import_brep(cache / "union.brep")
        tid("form frå cache")
        return u, delar
    u, delar = _bygg_form()
    cache.mkdir(parents=True, exist_ok=True)
    for n, d in delar.items():
        export_brep(d, cache / f"{n}.brep")
    export_brep(u, cache / "union.brep")
    return u, delar


def _bygg_form():
    k = kropp_loft()
    tid("kropp-loft")
    delar = {"kropp": k, "linse": linsetonne()}
    delar.update({p["namn"]: royr(p["punkt"], p["r"], p.get("b")) for p in F["royr"]})
    delar.update({q["namn"]: Pos(*q["senter"]) * Sphere(q["r"]) for q in F.get("kular", [])})
    delar.update({"sokar": sokarblokk(), "hjulboss": hjulboss(), "knappboss": knappboss()})
    tid("delar")
    u = k
    for n, d in delar.items():
        if n == "kropp":
            continue
        u2 = u + d
        if not u2.is_valid or len(u2.solids()) != 1:
            u2 = u2.fix()
            print("  fix etter", n, "gyldig", u2.is_valid, "solidar", len(u2.solids()))
            if not u2.is_valid or len(u2.solids()) != 1:
                raise RuntimeError(f"union feila ved {n}")
        u = u2
    tid("union")
    return u, delar


if __name__ == "__main__":
    k, delar = bygg_form()
    print("gyldig", k.is_valid, "volum", round(k.volume / 1000, 1), "cm3", "flater", len(k.faces()), "solidar", len(k.solids()))
    ut = HER.parent / "print" / "cad"
    ut.mkdir(exist_ok=True)
    export_stl(k, ut / "form.stl", tolerance=0.02, angular_tolerance=0.15)
    tid("stl")
