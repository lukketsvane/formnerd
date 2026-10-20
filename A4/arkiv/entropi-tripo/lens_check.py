import sys, json
import numpy as np, trimesh
from PIL import Image

m = trimesh.load(sys.argv[1])
x0, y0, z0 = m.bounds[0]; x1, y1, z1 = m.bounds[1]
step = 0.5
ys, zs = np.arange(y0, y1, step), np.arange(z0, z1, step)
Y, Z = np.meshgrid(ys, zs)
origins = np.c_[np.full(Y.size, x1 + 5), Y.ravel(), Z.ravel()]
dirs = np.tile([-1.0, 0, 0], (Y.size, 1))
loc, idx, _ = m.ray.intersects_location(origins, dirs, multiple_hits=False)
depth = np.full(Y.size, np.nan)
depth[idx] = x1 - loc[:, 0]
D = depth.reshape(Y.shape)
img = np.nan_to_num((D - np.nanmin(D)) / (np.nanmax(D) - np.nanmin(D)) * 255, nan=255).astype(np.uint8)
Image.fromarray(img[::-1, ::-1]).save(sys.argv[2])
low = (Z > z0 + 0.1 * (z1 - z0)) & (Z < z0 + 0.7 * (z1 - z0)) & (Y > y0 + 0.2 * (y1 - y0)) & (Y < y0 + 0.8 * (y1 - y0))
deep = low & (D > np.nanpercentile(D[low], 99))
cy, cz = Y[deep].mean(), Z[deep].mean()
r = np.hypot(Y - cy, Z - cz)
prof = [(round(float(rr), 1), round(float(np.nanmedian(D[(r >= rr) & (r < rr + 1)])), 1)) for rr in np.arange(0, 45, 1.0)]
print(json.dumps({"lens_axis_center_mm": [round(float(cy), 1), round(float(cz), 1)], "radial_depth_profile_mm": prof}))
