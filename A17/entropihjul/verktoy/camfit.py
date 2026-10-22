import sys, json
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from scipy.optimize import minimize
from scipy.spatial import ConvexHull

W, H = 1448, 1086
D = '.'


def ref_mask(path, thr=246):
    g = np.asarray(Image.open(path).convert('L')).astype(float)
    m = g < thr
    m = ndimage.binary_fill_holes(ndimage.binary_closing(m, iterations=3))
    lab, n = ndimage.label(m)
    sizes = ndimage.sum(m, lab, range(1, n + 1))
    return lab == (1 + int(np.argmax(sizes)))


def cam_basis(p):
    el, az, roll = np.radians(p['elev']), np.radians(p['azim']), np.radians(p['roll'])
    tgt = np.array(p['target'], float)
    loc = tgt + p['dist'] * np.array([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)])
    f = tgt - loc; f /= np.linalg.norm(f)
    right = np.cross(f, [0, 0, 1.0]); right /= np.linalg.norm(right)
    up = np.cross(right, f)
    c, s = np.cos(roll), np.sin(roll)
    return loc, f, c * right + s * up, -s * right + c * up


def project(P, p):
    loc, f, r, u = cam_basis(p)
    d = P - loc
    zc = d @ f
    k = p['lens'] / 36.0 * W
    return np.stack([W / 2 + (d @ r) / zc * k, H / 2 - (d @ u) / zc * k], 1)


def sil(P, p):
    q = project(P, p)
    hl = ConvexHull(q)
    im = Image.new('L', (W, H), 0)
    ImageDraw.Draw(im).polygon([tuple(q[i]) for i in hl.vertices], fill=255)
    return np.asarray(im) > 127


def unpack(x, lens):
    return dict(elev=float(x[0]), azim=float(x[1]), roll=float(x[2]), dist=float(x[3]), target=[float(x[4]), float(x[5]), float(x[6])], lens=lens)


def fit(P, mask, x0, lens=180.0):
    az = x0[1]
    full = lambda y: np.r_[y[0], az, y[1:]]
    def loss(y):
        s = sil(P, unpack(full(y), lens))
        return 1.0 - np.logical_and(s, mask).sum() / np.logical_or(s, mask).sum()
    y0 = np.r_[x0[0], x0[2:]]
    r = minimize(loss, y0, method='Nelder-Mead', options=dict(maxiter=900, xatol=1e-3, fatol=1e-7))
    return unpack(full(r.x), lens), 1 - r.fun


def blender_cam(p):
    loc, f, r, u = cam_basis(p)
    return dict(loc=loc.tolist(), rot=np.stack([r, u, -f], 1).tolist(), lens=p['lens'])


if __name__ == '__main__':
    var, npz, ref = sys.argv[1], sys.argv[2], sys.argv[3]
    x0 = json.loads(sys.argv[4]) if len(sys.argv) > 4 else [33.0, -95.0, -1.4, 190.0, 0.2, 0.0, 3.6]
    d = np.load(npz, allow_pickle=True)
    P = np.vstack([d[str(n) + '_v'][::7] for n in d['names']]).astype(float)
    hull = ConvexHull(P); P = P[hull.vertices]
    mask = ref_mask(ref)
    p, iou = fit(P, mask, np.array(x0, float))
    print(var, 'IoU', round(iou, 5), json.dumps(p))
    json.dump(dict(fit=p, iou=iou, blender=blender_cam(p)), open(f'{D}/cam_{var}.json', 'w'), indent=1)
