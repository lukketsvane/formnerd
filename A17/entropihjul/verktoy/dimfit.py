import numpy as np, json, sys
from scipy.optimize import least_squares
from camfit import project

TH = np.linspace(0, 2 * np.pi, 721)


def cam(el, dist, tz, lens=180.0):
    return dict(elev=el, azim=-90.0, roll=0.0, dist=dist, target=[0.0, 0.0, tz], lens=lens)


def ypt(c, r, z, side):
    return project(np.array([[0.0, (-r if side == 'near' else r), z]]), c)[0, 1]


def width(c, r, z):
    q = project(np.stack([r * np.cos(TH), r * np.sin(TH), np.full_like(TH, z)], 1), c)
    return q[:, 0].max() - q[:, 0].min()


def solve(names, x0, meas, lo=None, hi=None):
    def res(x):
        P = dict(zip(names, x))
        c = cam(P['el'], P['dist'], P['tz'])
        out = []
        for m in meas:
            if m[0] == 'y':
                _, rf, zf, side, val, w = m
                out.append((ypt(c, rf(P), zf(P), side) - val) * w)
            else:
                _, rf, zf, val, w = m
                out.append((width(c, rf(P), zf(P)) - val) * w)
        return np.array(out)
    r = least_squares(res, x0, bounds=(lo if lo is not None else -np.inf, hi if hi is not None else np.inf))
    P = dict(zip(names, r.x))
    print('residuals px:', np.round(res(r.x), 1))
    for k, v in P.items():
        print(f'  {k} = {v:.3f}')
    return P
