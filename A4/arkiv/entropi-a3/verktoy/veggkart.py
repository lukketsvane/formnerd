import sys, numpy as np, trimesh
from scipy import ndimage

def inne_maske(mesh, s=0.5):
    b = mesh.bounds
    xs = np.arange(b[0][0] + s / 2, b[1][0], s); ys = np.arange(b[0][1] + s / 2, b[1][1], s); zs = np.arange(b[0][2] + s / 2, b[1][2], s)
    X, Y = np.meshgrid(xs, ys, indexing='ij')
    o = np.c_[X.ravel(), Y.ravel(), np.full(X.size, b[0][2] - 1)]
    loc, idx, _ = mesh.ray.intersects_location(o, np.tile([0, 0, 1.0], (len(o), 1)), multiple_hits=True)
    M = np.zeros((len(xs), len(ys), len(zs)), bool)
    order = np.lexsort((loc[:, 2], idx))
    loc, idx = loc[order], idx[order]
    starts = np.r_[0, np.nonzero(np.diff(idx))[0] + 1]
    for a, e in zip(starts, np.r_[starts[1:], len(idx)]):
        zz = np.unique(np.round(loc[a:e, 2], 4))
        i, j = np.unravel_index(idx[a], X.shape)
        for z0, z1 in zip(zz[0::2], zz[1::2]):
            M[i, j, (zs > z0) & (zs < z1)] = True
    return M, (xs, ys, zs)

if __name__ == '__main__':
    m = trimesh.load(sys.argv[1]); s = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
    M, ax = inne_maske(m, s)
    D = ndimage.distance_transform_edt(M) * s
    np.savez_compressed(sys.argv[3], D=D.astype(np.float32), xs=ax[0], ys=ax[1], zs=ax[2])
    print('voxels', M.shape, 'inne', int(M.sum()), 'vol cm3', round(M.sum() * s**3 / 1000, 1))
