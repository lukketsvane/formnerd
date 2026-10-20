import sys, json
import numpy as np, trimesh
from PIL import Image, ImageDraw

stl, out_png = sys.argv[1], sys.argv[2]
m = trimesh.load(stl)
x0, y0, z0 = m.bounds[0]
x1, y1, z1 = m.bounds[1]
s = 0.5
Y, Z = np.meshgrid(np.arange(y0, y1, s), np.arange(z0, z1, s))
o = np.c_[np.full(Y.size, x1 + 5), Y.ravel(), Z.ravel()]
loc, idx, _ = m.ray.intersects_location(o, np.tile([-1.0, 0, 0], (Y.size, 1)), multiple_hits=False)
d = np.full(Y.size, np.nan)
d[idx] = x1 - loc[:, 0]
D = d.reshape(Y.shape)

best = None
for cy in np.arange(y0 + 0.3 * (y1 - y0), y0 + 0.7 * (y1 - y0), 0.5):
    for cz in np.arange(z0 + 0.2 * (z1 - z0), z0 + 0.6 * (z1 - z0), 0.5):
        r = np.hypot(Y - cy, Z - cz)
        sd = np.nanmean([np.nanstd(D[(r >= a) & (r < a + 1)]) for a in range(10, 22)])
        if best is None or sd < best[0]:
            best = (sd, cy, cz)
_, cy, cz = best
r = np.hypot(Y - cy, Z - cz)
profile = [[a, round(float(np.nanmedian(D[(r >= a) & (r < a + 1)])), 1)] for a in range(0, 34)]

img = np.nan_to_num(np.clip(D / 40, 0, 1) * 255, nan=255).astype(np.uint8)
im = Image.fromarray(img[::-1]).convert("RGB").resize((img.shape[1] * 4, img.shape[0] * 4), Image.NEAREST)
dr = ImageDraw.Draw(im)
for mm in range(0, int(y1) + 1, 10):
    x = int((mm - y0) / s * 4)
    dr.line([(x, 0), (x, im.height)], fill=(255, 0, 0))
    dr.text((x + 2, 2), f"y{mm}", fill=(255, 0, 0))
for mm in range(0, int(z1) + 1, 10):
    yy = im.height - int((mm - z0) / s * 4)
    dr.line([(0, yy), (im.width, yy)], fill=(0, 160, 255))
    dr.text((2, yy - 12), f"z{mm}", fill=(0, 160, 255))
im.save(out_png)
print(json.dumps({"extents_mm": [round(float(v), 1) for v in m.extents], "lens_axis_yz_mm": [float(cy), float(cz)], "radial_depth_profile_mm": profile}))
