import numpy as np
from shapely.geometry import Polygon

N_PKT = 140


def glatt(poly, r=3.0):
    p = poly.buffer(r, join_style=1).buffer(-2 * r, join_style=1).buffer(r, join_style=1)
    if p.geom_type != "Polygon":
        p = max(p.geoms, key=lambda q: q.area)
    return p


def resample(poly, senter=(36.0, 60.0), n=N_PKT):
    """n punkt jamt etter bogelengd langs omrisset, start rett bak senteret (-x)."""
    ring = np.asarray(poly.exterior.coords)
    if Polygon(ring).exterior.is_ccw is False:
        ring = ring[::-1]
    ring = ring[:-1]
    v = np.arctan2(ring[:, 1] - senter[1], ring[:, 0] - senter[0])
    i0 = int(np.argmin(np.abs(np.abs(v) - np.pi)))
    ring = np.roll(ring, -i0, axis=0)
    lukka = np.vstack([ring, ring[:1]])
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(lukka, axis=0), axis=1))]
    ss = np.linspace(0, s[-1], n, endpoint=False)
    return np.c_[np.interp(ss, s, lukka[:, 0]), np.interp(ss, s, lukka[:, 1])]
