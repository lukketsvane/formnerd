"""Måler A3-forma frå Tripo-meshen og skriv form_maal.json. CAD-en brukar berre tala herfrå."""
import json, pathlib, sys
import numpy as np, trimesh
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from omriss import glatt, resample

HER = pathlib.Path(__file__).resolve().parent
M = trimesh.load(HER / "../../arkiv/entropi-a3/03-3d/a3-entropi-print-120mm.stl")
AY, AZ = 65.0, 32.0
N_PKT = 96


def snitt(o, n):
    s = M.section(plane_origin=o, plane_normal=n)
    return [] if s is None else [np.asarray(e) for e in s.discrete]


def storste_polygon(z):
    polys = [Polygon(L[:, :2]) for L in snitt([0, 0, z], [0, 0, 1]) if len(L) > 3]
    polys = [p.buffer(0) for p in polys if p.is_valid or True]
    polys = [p for p in polys if p.area > 1500]
    return max(polys, key=lambda p: p.area) if polys else None


def kropp_seksjonar():
    ut = []
    senter = (36.0, 60.0)
    for z in [0.3, 0.6, 1.0, 1.5, 2.0, 2.6, 3.3, 4.1, 5.0, 6.0, 7.2, 8.5, 10, 12, 14.5, 17.5, 21, 25, 29, 33, 37, 41, 44, 46.5, 48.5, 50]:
        p = storste_polygon(z)
        if p is None:
            continue
        w = np.sqrt(max(29.6**2 - (z - AZ) ** 2, 0.0)) + 0.3
        p = p.difference(box(58.0, AY - w, 95.0, AY + w)) if w > 0.5 else p
        p = p.difference(box(-5, 44.0, 18.5, 85.0)) if z > 56 else p
        if p.geom_type != "Polygon":
            p = max(p.geoms, key=lambda q: q.area)
        p = glatt(p).simplify(0.1)
        ut.append({"z": z, "punkt": np.round(resample(p), 3).tolist(), "areal": round(p.area, 1)})
    return ut


def tak_plan():
    gx, gy = np.meshgrid(np.arange(10, 64, 1.0), np.arange(4, 116, 1.0))
    O = np.c_[gx.ravel(), gy.ravel(), np.full(gx.size, 150.0)]
    loc, ir, _ = M.ray.intersects_location(O, np.tile([0, 0, -1.0], (len(O), 1)), multiple_hits=False)
    z = loc[:, 2]
    ok = (z > 48) & (z < 59.5)
    A = np.c_[np.ones(ok.sum()), loc[ok, 0], loc[ok, 1]]
    k, *_ = np.linalg.lstsq(A, z[ok], rcond=None)
    rest = z[ok] - A @ k
    return {"a": round(k[0], 3), "bx": round(k[1], 4), "by": round(k[2], 4), "rms": round(float(np.sqrt((rest**2).mean())), 2), "n": int(ok.sum())}


def tonne_profil():
    ut = []
    th = np.radians(np.arange(200, 341, 5))
    for x in np.arange(66.0, 90.5, 0.5):
        O = np.c_[np.full(len(th), x), AY + 70 * np.cos(th), AZ + 70 * np.sin(th)]
        Dd = -np.c_[np.zeros(len(th)), np.cos(th), np.sin(th)]
        loc, ir, _ = M.ray.intersects_location(O, Dd, multiple_hits=False)
        if len(ir) < 5:
            continue
        r = np.hypot(loc[:, 1] - AY, loc[:, 2] - AZ)
        ut.append([round(float(x), 2), round(float(np.median(r)), 3), round(float(r.min()), 2), round(float(r.max()), 2)])
    return ut


def blokk():
    ut = {}
    for z in (60, 66, 72, 78, 82):
        polys = [Polygon(L[:, :2]).buffer(0) for L in snitt([0, 0, z], [0, 0, 1]) if len(L) > 3]
        polys = [p for p in polys if p.area > 100 and p.bounds[0] < 2.0]
        if polys:
            b = max(polys, key=lambda p: p.area).bounds
            ut[str(z)] = [round(v, 2) for v in b]
    O = np.c_[np.full(40, 9.0), np.linspace(50, 80, 40), np.full(40, 150.0)]
    loc, ir, _ = M.ray.intersects_location(O, np.tile([0, 0, -1.0], (40, 1)), multiple_hits=False)
    ut["topp_z"] = round(float(np.median(loc[:, 2])), 2)
    return ut


def front_x():
    O = np.array([[120.0, AY, AZ + 24.0], [120.0, AY, AZ - 24.0], [120.0, AY + 24, AZ], [120.0, AY - 24, AZ]])
    loc, ir, _ = M.ray.intersects_location(O, np.tile([-1.0, 0, 0], (4, 1)), multiple_hits=False)
    return round(float(loc[:, 0].max()), 2)


def royr_fit(start, steg=2.0, rundar=5, n_str=36):
    """Strålar ut frå ei gissa senterlinje i normalplanet; nytt senter og radius frå dei nære treffa."""
    p = np.asarray(start, float)
    th = np.linspace(0, 2 * np.pi, n_str, endpoint=False)
    for _ in range(rundar):
        d = np.diff(p, axis=0)
        L = np.r_[0, np.cumsum(np.linalg.norm(d, axis=1))]
        t = np.arange(0, L[-1] + 1e-6, steg)
        q = np.c_[np.interp(t, L, p[:, 0]), np.interp(t, L, p[:, 1]), np.interp(t, L, p[:, 2])]
        tan = np.gradient(q, axis=0)
        tan /= np.linalg.norm(tan, axis=1, keepdims=True)
        ny, rad, fri, akse = [], [], [], []
        for o, n in zip(q, tan):
            u = np.cross(n, [0, 0, 1.0])
            u = np.cross(n, [1.0, 0, 0]) if np.linalg.norm(u) < 1e-6 else u
            u /= np.linalg.norm(u)
            v = np.cross(n, u)
            Dd = np.outer(np.cos(th), u) + np.outer(np.sin(th), v)
            loc, ir, _ = M.ray.intersects_location(np.tile(o, (n_str, 1)), Dd, multiple_hits=False)
            dist = np.full(n_str, np.nan)
            dist[ir] = np.linalg.norm(loc - o, axis=1)
            ok = np.isfinite(dist)
            if ok.sum() < n_str * 0.6:
                ny.append(o); rad.append(np.nan); fri.append(0.0); akse.append([np.nan, np.nan]); continue
            med = np.nanmedian(dist)
            naer = ok & (dist < 1.6 * med)
            c = o + (loc[np.isin(ir, np.nonzero(naer)[0])] - o).mean(0) if naer.sum() > 6 else o
            r = float(np.nanmedian(dist[naer]))
            a = float(np.nanmedian(np.abs(dist[naer & (np.abs(np.cos(th)) > 0.7)]))) if (naer & (np.abs(np.cos(th)) > 0.7)).any() else r
            b = float(np.nanmedian(np.abs(dist[naer & (np.abs(np.sin(th)) > 0.7)]))) if (naer & (np.abs(np.sin(th)) > 0.7)).any() else r
            ny.append(c); rad.append(r); fri.append(float(naer.mean())); akse.append([a, b])
        ny = np.asarray(ny)
        p = ny.copy()
        for i in range(1, len(p) - 1):
            p[i] = 0.25 * ny[i - 1] + 0.5 * ny[i] + 0.25 * ny[i + 1]
    return p, np.asarray(rad), np.asarray(fri), np.asarray(akse)


ROYR_START = {
    "royr1": [[8, 54, 72], [26, 52, 71], [40, 45, 66], [50, 38, 58], [52, 34, 46]],
    "royr2": [[8, 66, 72], [28, 65, 71], [44, 59, 66], [55, 52, 58], [57, 50, 46]],
    "royr3": [[8, 78, 72], [28, 78, 71], [45, 76, 66], [58, 76, 58], [63, 78, 48]],
    "hjulgrein": [[31, 104, 62], [42, 95, 63], [52, 87, 57], [60, 83, 48], [63, 82, 40]],
    "gripryggen": [[10, 50, 66], [22, 40, 65], [32, 28, 60], [40, 19, 53], [44, 15, 44]],
}

if __name__ == "__main__":
    ut = {"kropp": kropp_seksjonar(), "tak": tak_plan(), "tonne": tonne_profil(), "front_x": front_x(), "blokk": blokk(), "royr": {}}
    for n, s in (ROYR_START.items() if "--royr" in sys.argv else []):
        p, r, fri, ak = royr_fit(s)
        print(n, "punkt", len(p), "r median", np.round(np.nanmedian(r), 2))
        for q, rr, ff, aa in zip(p, r, fri, ak):
            print("   ", np.round(q, 1), round(float(rr), 2) if np.isfinite(rr) else "-", round(float(ff), 2), np.round(aa, 1))
        ut["royr"][n] = {"punkt": np.round(p, 2).tolist(), "r": [None if not np.isfinite(v) else round(float(v), 2) for v in r], "fri": np.round(fri, 2).tolist(), "akse": [[None if not np.isfinite(v) else round(float(v), 2) for v in a] for a in ak]}
    print("tak", ut["tak"], "front_x", ut["front_x"], "blokk", ut["blokk"])
    print("tonne", ut["tonne"])
    print("seksjonar", [(s["z"], s["areal"]) for s in ut["kropp"]])
    (HER / "form_maal.json").write_text(json.dumps(ut))
