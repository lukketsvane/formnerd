import json, pathlib
import numpy as np
from shapely.geometry import Polygon, box

HER = pathlib.Path(__file__).resolve().parent
K = json.loads((HER / "delar_konfig.json").read_text())
AY, AZ = K["akse"]["y"], K["akse"]["z"]


def loep_r(x):
    L, ef = K["form"]["linse"], K["form"]["ef"]
    pr = L["profil"] + [[ef["flens_x"][0], L["profil"][-1][1]], [ef["flens_x"][0] + 0.01, ef["flens_r"]], [ef["flens_x"][1], ef["flens_r"]]]
    xs, rs = zip(*pr)
    return np.interp(x, xs, rs)


def kutt(p, z, x0=66.0, x1=95.0):
    """Tek bort tonneregionen frå snittet p ved høgda z: innanfor r 28 under spalte_fraa_z (foten går inn i løpet), elles løpsradius + spalte."""
    L = K["form"]["linse"]
    if z <= L["spalte_fraa_z"]:
        w = float(np.sqrt(max(28.0**2 - (z - AZ) ** 2, 0.0)))
        return p.difference(box(x0, AY - w, x1, AY + w)) if w > 0.5 else p
    xs = np.arange(x0, x1 + 0.01, 0.5)
    w = np.sqrt(np.maximum((loep_r(xs) + L["spalte"]) ** 2 - (z - AZ) ** 2, 0.0))
    m = w > 0.3
    if not m.any():
        return p
    xs, w = xs[m], w[m]
    nedre = [(float(x), AY - float(v)) for x, v in zip(xs, w)]
    ovre = [(float(x), AY + float(v)) for x, v in zip(xs, w)]
    pts = [(x0 - 0.01, nedre[0][1])] + nedre + [(xs[-1] + 0.5, nedre[-1][1]), (xs[-1] + 0.5, ovre[-1][1])] + ovre[::-1] + [(x0 - 0.01, ovre[0][1])]
    return p.difference(Polygon(pts).buffer(0))
