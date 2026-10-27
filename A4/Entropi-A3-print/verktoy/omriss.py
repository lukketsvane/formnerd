import numpy as np
from shapely.geometry import Polygon

N_PKT = 140
SENTER = (36.0, 60.0)


def glatt(poly, r=3.0):
    p = poly.buffer(r, join_style=1).buffer(-2 * r, join_style=1).buffer(r, join_style=1)
    if p.geom_type != "Polygon":
        p = max(p.geoms, key=lambda q: q.area)
    return p


def _tett(ring, steg=0.5):
    lukka = np.vstack([ring, ring[:1]])
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(lukka, axis=0), axis=1))]
    ss = np.arange(0, s[-1], steg)
    return np.c_[np.interp(ss, s, lukka[:, 0]), np.interp(ss, s, lukka[:, 1])]


def _anker(ring, front):
    cx, cy = SENTER
    x, y = ring[:, 0], ring[:, 1]
    maal = [(x.min(), cy), (cx, y.min()), front, (cx, y.max())]
    return [int(np.argmin(np.hypot(x - mx, y - my))) for mx, my in maal]


def _boge(p, n):
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
    ss = np.linspace(0, s[-1], n, endpoint=False)
    return np.c_[np.interp(ss, s, p[:, 0]), np.interp(ss, s, p[:, 1])]


def resample(poly, n=N_PKT, front=(58.0, 65.0)):
    """n punkt etter bogelengd, fordelte på fire bogar mellom faste ankerpunkt (bak, grep, front, hjulside)."""
    ring = np.asarray(poly.exterior.coords)
    if not Polygon(ring).exterior.is_ccw:
        ring = ring[::-1]
    ring = ring[:-1]
    ring = _tett(ring)
    bak, grep, front, hjul = _anker(ring, front)
    ring = np.roll(ring, -bak, axis=0)
    m = len(ring)
    idx = sorted(((grep - bak) % m, (front - bak) % m, (hjul - bak) % m))
    grenser = [0] + idx + [m]
    k = n // 4
    ut = []
    for a, b in zip(grenser[:-1], grenser[1:]):
        seg = np.vstack([ring[a:b], ring[b % m][None]])
        ut.append(_boge(seg, k))
    return np.vstack(ut)
