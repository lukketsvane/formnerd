import numpy as np, cv2, json, sys, os, glob
from scipy.optimize import minimize
from scipy import ndimage

D = '.'
variants = sys.argv[1].split(',')
names = sorted(os.path.basename(p)[:-4] for p in glob.glob(f'{D}/out/basis/*.npy'))
IDC = {'blast': (1, 0, 0), 'polish': (0, 1, 0), 'spun': (0, 0, 1), 'brushz': (1, 1, 0)}


def lin(x):
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def tiles(mask, n=6):
    ys, xs = np.where(mask)
    if len(ys) == 0:
        return []
    out = []
    qy = np.quantile(ys, np.linspace(0, 1, n + 1)); qx = np.quantile(xs, np.linspace(0, 1, n + 1))
    for i in range(n):
        for j in range(n):
            m = mask & (np.arange(mask.shape[0])[:, None] >= qy[i]) & (np.arange(mask.shape[0])[:, None] <= qy[i + 1]) & \
                (np.arange(mask.shape[1])[None, :] >= qx[j]) & (np.arange(mask.shape[1])[None, :] <= qx[j + 1])
            if m.sum() > 25:
                out.append(m)
    return out


regs = []
HPR = []
for v in variants:
    B = []
    A = None
    for n in names:
        im = cv2.imread(f"{D}/out/{os.environ.get('BAS', 'bas_')}{v}/{n}.png", cv2.IMREAD_UNCHANGED).astype(float) / 65535.0
        B.append(im[:, :, :3].mean(2))
        A = im[:, :, 3] if A is None else np.minimum(A, im[:, :, 3])
    B = np.stack(B, 0)
    h, w = A.shape
    ref = cv2.imread(f'{D}/ref/{v}.png')[:, :, ::-1].astype(float) / 255.0
    ref = cv2.resize(lin(ref).mean(2), (w, h), interpolation=cv2.INTER_AREA)
    idp = cv2.imread(f"{D}/out/{os.environ.get('IDD', 'id')}/{v}.png", cv2.IMREAD_UNCHANGED)
    ida = cv2.resize(idp[:, :, 3], (w, h), interpolation=cv2.INTER_NEAREST) / 65535.0
    idc = cv2.resize(idp[:, :, 2::-1], (w, h), interpolation=cv2.INTER_NEAREST) / 65535.0
    for fin, col in IDC.items():
        m = (np.abs(idc - np.array(col)).max(2) < 0.2) & (ida > 0.99) & (A > 0.99)
        m = ndimage.binary_erosion(m, iterations=1)
        if m.sum() < 60:
            continue
        for t in tiles(m, 5 if fin in ('blast', 'spun') else 3):
            regs.append((v, fin, B[:, t].mean(1), ref[t].mean(), t.sum()))
        if fin in ('blast', 'spun'):
            hp = lambda x: x - ndimage.gaussian_filter(x, 2.5)
            HB = np.stack([hp(b)[m] for b in B], 1)
            hr = hp(ref)[m]
            HPR.append((v, fin, HB, hr.std()))
X = np.array([r[2] for r in regs]); y = np.array([r[3] for r in regs])
wt = np.array([1.0 if r[1] in ('blast', 'spun') else 0.5 for r in regs])
lam = float(sys.argv[2]) if len(sys.argv) > 2 else 0.002


HPW = float(os.environ.get('HPW', '0'))


def loss(z):
    wv = z ** 2
    p = X @ wv
    L = np.sum(wt * (np.log(p + 1e-3) - np.log(y + 1e-3)) ** 2) + lam * np.sum(wv)
    for v, fin, HB, sr in HPR:
        sf = (HB @ wv).std()
        L += HPW * (np.log(sf + 1e-4) - np.log(sr + 1e-4)) ** 2
    return L


z0 = np.full(len(names), 0.5)
r = minimize(loss, z0, method='L-BFGS-B')
wv = r.x ** 2
print('weights', {n: round(float(c), 3) for n, c in zip(names, wv) if c > 1e-3})
p = X @ wv
for v in variants:
    for fin in IDC:
        s = [i for i, rr in enumerate(regs) if rr[0] == v and rr[1] == fin]
        if s:
            print(f'  {v} {fin:7s} tiles {len(s):3d}  ref {y[s].mean():.3f}  fit {p[s].mean():.3f}  corr {np.corrcoef(p[s], y[s])[0, 1] if len(s) > 2 else 0:.3f}')
for v, fin, HB, sr in HPR:
    print(f'  hp {v} {fin}: ref std {sr:.4f}  fit std {(HB @ wv).std():.4f}')
json.dump({n: float(c) for n, c in zip(names, wv)}, open(f"{D}/out/{os.environ.get('OUTW', 'env_weights3.json')}", 'w'), indent=1)
