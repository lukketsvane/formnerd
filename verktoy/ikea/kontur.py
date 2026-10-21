"""Konturar frå synleg CAD-geometri, utan tesselleringsnett.

The input is the renderer's normal/depth/object-id buffers. No geometry is
invented: all strokes lie on visible boundaries or measured surface features.
``konturlag`` keeps the line families separate for physical page line weights.
``kantar`` is a drop-in alternative to the original builder's kantar function.

Optional depth-valley strokes are conservative and disabled by default. Enable
them for organic parts only with ``organic_ids`` (object IDs in this render),
and inspect the resulting views before release.
"""

from dataclasses import dataclass
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi


_QUANTUM = 1.0 / (255.0 * 255.0)
_CROSS = ndi.generate_binary_structure(2, 1)
_FULL = np.ones((3, 3), dtype=bool)


@dataclass
class ContourLayers:
    silhouette: np.ndarray
    seams: np.ndarray
    features: np.ndarray
    valleys: np.ndarray
    depth: np.ndarray
    ids: np.ndarray

    @property
    def edges(self):
        return self.silhouette | self.seams | self.features | self.valleys


def _thin(mask, max_passes=12):
    """Zhang-Suen thinning with an explicit empty border, never wrapped pixels."""
    a = np.pad(np.asarray(mask, bool), 1)
    for _ in range(max_passes):
        changed = False
        for second in (False, True):
            p = [a[:-2, 1:-1], a[:-2, 2:], a[1:-1, 2:], a[2:, 2:],
                 a[2:, 1:-1], a[2:, :-2], a[1:-1, :-2], a[:-2, :-2]]
            count = np.zeros(mask.shape, dtype=np.uint8)
            transitions = np.zeros(mask.shape, dtype=np.uint8)
            for i in range(8):
                count += p[i]
                transitions += ~p[i] & p[(i + 1) % 8]
            if second:
                corner = ~(p[0] & p[2] & p[6]) & ~(p[0] & p[4] & p[6])
            else:
                corner = ~(p[0] & p[2] & p[4]) & ~(p[2] & p[4] & p[6])
            remove = a[1:-1, 1:-1] & (count >= 2) & (count <= 6) & (transitions == 1) & corner
            if np.any(remove):
                a[1:-1, 1:-1][remove] = False
                changed = True
        if not changed:
            break
    return a[1:-1, 1:-1].copy()


def _prune(mask, ids, thresholds):
    labels, count = ndi.label(mask, _FULL)
    if not count:
        return mask
    size = np.bincount(labels.ravel(), minlength=count + 1)
    # Each same-part feature should be independent of the numbering of a
    # neighbouring component. Use the minimum applicable size threshold.
    required = np.full(count + 1, np.inf)
    np.minimum.at(required, labels[mask], thresholds[ids[mask]])
    keep = size >= required
    keep[0] = False
    return keep[labels]


def _normalise(n):
    return n / np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-7)


def _suppress_parallel(features, boundary, radius):
    """Remove a nearby duplicate line while retaining lines crossing a seam.

    Distance alone would cut every real junction. The local covariance of
    the feature pixels supplies its tangent; only a tangent running along
    the boundary is suppressed. This changes the stroke selection, never
    the foreground mask or the visible part boundary.
    """
    if not features.any() or not boundary.any() or radius <= 0:
        return features
    distance = ndi.distance_transform_edt(~boundary).astype(np.float32)
    dy, dx = np.gradient(distance)
    a = features.astype(np.float32)
    x = np.arange(-4, 5, dtype=np.float32)
    ones = np.ones(9, dtype=np.float32)
    rows = [ndi.convolve1d(a, k, axis=0, mode="constant")
            for k in (ones, x, x * x)]
    count = np.maximum(ndi.convolve1d(rows[0], ones, axis=1, mode="constant"), 1)
    mx = ndi.convolve1d(rows[0], x, axis=1, mode="constant") / count
    my = ndi.convolve1d(rows[1], ones, axis=1, mode="constant") / count
    xx = ndi.convolve1d(rows[0], x * x, axis=1, mode="constant") / count - mx * mx
    yy = ndi.convolve1d(rows[2], ones, axis=1, mode="constant") / count - my * my
    xy = ndi.convolve1d(rows[1], x, axis=1, mode="constant") / count - mx * my
    angle = .5 * np.arctan2(2 * xy, xx - yy)
    across = abs(np.cos(angle) * dx + np.sin(angle) * dy)
    anisotropy = np.hypot(xx - yy, 2 * xy)
    parallel = (distance > 1.5) & (distance <= radius) & (across < .4) & (anisotropy > .45 * (xx + yy))
    return features & ~parallel


def _refine_organic(features, ids, eligible, boundary, minimum, style):
    """Unify unresolved bevel pairs on long organic-shell contours.

    A two-pixel closing can join tiny raster gaps and narrow parallel bevel
    edges. Thinning then restores a single stroke. Small disconnected
    symbols and other parts (in particular knurled hardware) are untouched.
    Both the joining distance and minimum contour extent are configurable.
    """
    result = features.copy()
    radius = max(0, int(style.get("organic_join_px", 2)))
    extent = int(style.get("organic_join_extent", 96))
    organic = np.isin(ids, eligible)
    if radius:
        for ident in eligible:
            labels, count = ndi.label(result & (ids == ident), _FULL)
            keep = np.zeros(count + 1, dtype=bool)
            for k, box in enumerate(ndi.find_objects(labels), start=1):
                keep[k] = box is not None and max(s.stop - s.start for s in box) >= extent
            long = keep[labels]
            cleaned = _thin(ndi.binary_closing(long, iterations=radius))
            result[long] = False
            result |= cleaned & (ids == ident)
    refined = _suppress_parallel(result & organic, boundary,
                                  float(style.get("organic_duplicate_px", 7)))
    # Removing a parallel duplicate can leave a few raster specks. Do not
    # reapply the large original feature threshold to the useful fragments
    # ending at real T-junctions.
    refined = _prune(refined, ids, np.minimum(minimum, 24))
    return (result & ~organic) | refined


def _valley_lines(z, ids, eligible, style):
    """Thin depth ridges reveal visible valleys between convex organic forms."""
    output = np.zeros(ids.shape, bool)
    sigma = float(style.get("valley_sigma", 3.0))
    strength = float(style.get("valley_strength", 4.0e-6))
    minimum = int(style.get("valley_min_px", 100))
    for ident in eligible:
        yy, xx = np.nonzero(ids == ident)
        if not len(xx):
            continue
        pad = int(np.ceil(4 * sigma)) + 2
        y0, y1 = max(0, yy.min() - pad), min(ids.shape[0], yy.max() + pad + 1)
        x0, x1 = max(0, xx.min() - pad), min(ids.shape[1], xx.max() + pad + 1)
        mask = ids[y0:y1, x0:x1] == ident
        den = ndi.gaussian_filter(mask.astype(np.float32), sigma)
        depth = ndi.gaussian_filter(np.where(mask, z[y0:y1, x0:x1], 0), sigma) / np.maximum(den, 1e-8)
        # Derivatives of the already smoothed depth. The mask removes the
        # silhouette and inter-part zones where normalized convolution bends.
        dy, dx = np.gradient(depth)
        dyy, dxy = np.gradient(dy)
        _, dxx = np.gradient(dx)
        delta = np.sqrt(np.maximum((dxx - dyy) ** 2 + 4 * dxy ** 2, 0))
        lo = (dxx + dyy - delta) * .5
        hi = (dxx + dyy + delta) * .5
        vx, vy = dxy, lo - dxx
        length = np.hypot(vx, vy)
        # Axis-aligned Hessians need an explicit eigenvector.
        fallback = length < 1e-12
        vx = np.where(fallback, (dxx <= dyy).astype(float), vx)
        vy = np.where(fallback, (dxx > dyy).astype(float), vy)
        length = np.maximum(np.hypot(vx, vy), 1e-12)
        vx, vy = vx / length, vy / length
        y, x = np.indices(mask.shape, dtype=float)
        plus = ndi.map_coordinates(depth, [y + vy, x + vx], order=1, mode="nearest")
        minus = ndi.map_coordinates(depth, [y - vy, x - vx], order=1, mode="nearest")
        interior = ndi.distance_transform_edt(mask) > max(4, 3 * sigma)
        ridge = interior & (lo < -strength) & (abs(lo) > 1.8 * abs(hi))
        ridge &= (depth >= plus) & (depth >= minus)
        ridge = _thin(ridge)
        labels, count = ndi.label(ridge, _FULL)
        size = np.bincount(labels.ravel(), minlength=count + 1)
        keep = size >= minimum
        keep[0] = False
        output[y0:y1, x0:x1] |= keep[labels]
    return output


def from_arrays(normal, depth, ids, style=None, crease=None, min_px=None,
                depth_per_pixel=None, organic_ids=()):
    """Extract separately weighted lines from RGB normals and decoded depth.

    normal: uint8 RGB camera-space normals; depth: normalized float HxW;
    ids: integer HxW, 0 is background. depth_per_pixel, when known, is one
    orthographic pixel in normalized depth units (span / (pixels * B)).
    This permits distinguishing steep continuous faces from self-occlusion.
    """
    style = {"crease": 38., "depth_eps": .004, "min_px": 30, **(style or {})}
    ids = np.asarray(ids, dtype=np.int32)
    z = np.asarray(depth, dtype=np.float32)
    n = np.asarray(normal, dtype=np.float32)[..., :3] / 127.5 - 1
    if z.shape != ids.shape or n.shape[:2] != ids.shape:
        raise ValueError("Normal-, djupne- og ID-buffer må ha same storleik")
    if np.any(ids < 0) or not np.all(np.isfinite(z)):
        raise ValueError("Ugyldige ID-ar eller djupneverdiar")
    n = _normalise(n)
    fg = ids > 0
    silhouette = fg & ~ndi.binary_erosion(fg, structure=_CROSS, border_value=0)
    seams = np.zeros(ids.shape, bool)
    features = np.zeros(ids.shape, bool)
    count = max([int(ids.max(initial=0)), *(crease or {}), *(min_px or {})]) + 1
    angles = np.full(count, float(style["crease"]), dtype=np.float32)
    minimum = np.full(count, float(style["min_px"]), dtype=np.float32)
    for k, v in (crease or {}).items():
        angles[int(k)] = float(v)
    for k, v in (min_px or {}).items():
        minimum[int(k)] = float(v)
    cosine = np.cos(np.deg2rad(angles))

    for axis in (0, 1):
        a = (slice(None, -1), slice(None)) if axis == 0 else (slice(None), slice(None, -1))
        b = (slice(1, None), slice(None)) if axis == 0 else (slice(None), slice(1, None))
        visible = fg[a] & fg[b]
        same = visible & (ids[a] == ids[b])
        seam = visible & (ids[a] != ids[b])
        seams[a] |= seam
        # Keep real hard edges; unlike a triangle-edge renderer this never
        # draws the edges of nearly coplanar tessellation triangles.
        angular = (n[a] * n[b]).sum(-1) < np.minimum(cosine[ids[a]], cosine[ids[b]])
        dz = abs(z[a] - z[b])
        if depth_per_pixel is not None:
            component = 1 if axis == 0 else 0
            slope_a = abs(n[a][..., component]) / np.maximum(abs(n[a][..., 2]), .04)
            slope_b = abs(n[b][..., component]) / np.maximum(abs(n[b][..., 2]), .04)
            expected = .5 * (slope_a + slope_b) * float(depth_per_pixel)
            epsilon = float(style.get("occlusion_eps", 8 * _QUANTUM))
            jump = dz > (expected * 2.2 + epsilon)
        else:
            jump = dz > float(style["depth_eps"])
        features[a] |= same & (angular | jump)

    # Surface-feature cleanup must not remove small but necessary holes or
    # silhouettes. Those remain in separate, unpruned families.
    features &= ~ndi.binary_dilation(silhouette | seams, structure=_CROSS)
    features = _prune(features, ids, minimum)
    if organic_ids:
        features = _refine_organic(features, ids, organic_ids,
                                   silhouette | seams, minimum, style)
    valleys = _valley_lines(z, ids, organic_ids, style) if organic_ids else np.zeros_like(fg)
    # A weak ridge following an already drawn contour does not describe a
    # second geometric boundary. Cull it, then prune after culling so that
    # isolated remnants cannot become unexplained floating marks.
    if valleys.any():
        valley_gap = max(1, int(style.get("valley_edge_gap", 18)))
        valleys &= ~ndi.binary_dilation(silhouette | seams | features, iterations=valley_gap)
        valleys = _prune(valleys, ids, np.full(count, float(style.get("valley_min_px", 100))))
    return ContourLayers(silhouette, seams, features, valleys, z, ids)


def konturlag(mappe, stil, crease=None, min_px=None, organic_ids=None):
    """Read the existing renderer buffers and return separately weighted masks."""
    p = Path(mappe)
    normals = np.asarray(Image.open(p / "normal.png").convert("RGB"))
    raw_z = np.asarray(Image.open(p / "djupn.png").convert("RGB"), dtype=np.float32)
    ids = np.asarray(Image.open(p / "id.png").convert("RGB"))[..., 0].astype(np.int32)
    z = raw_z[..., 0] / 255 + raw_z[..., 1] / (255 * 255)
    depth_per_pixel = None
    scene_path = p / "scene.json"
    if scene_path.exists():
        scene = json.loads(scene_path.read_text())
        if "boks" in scene and "span" in scene:
            b = np.asarray(scene["boks"], dtype=float)
            diagonal = np.linalg.norm(b[1] - b[0])
            if diagonal > 0:
                depth_per_pixel = scene["span"] / (ids.shape[1] * diagonal)
    return from_arrays(normals, z, ids, stil, crease, min_px,
                       depth_per_pixel=depth_per_pixel,
                       organic_ids=organic_ids if organic_ids is not None else stil.get("organic_ids", ()))


def kantar(mappe, stil, crease=None, min_px=None):
    """Drop-in API: (combined edges, decoded depth, object IDs)."""
    layers = konturlag(mappe, stil, crease, min_px)
    return layers.edges, layers.depth, layers.ids


def self_test():
    """Four semantic checks, independent of any particular camera mesh."""
    size = 160
    ids = np.ones((size, size), np.int32)
    normals = np.full((size, size, 3), [128, 128, 255], np.uint8)
    z = np.full((size, size), .5, np.float32)
    plane = from_arrays(normals, z, ids, {"min_px": 5})
    assert not plane.features.any() and not plane.seams.any()
    assert plane.silhouette[0].all() and plane.silhouette[-1].all()
    split = ids.copy()
    split[:, size // 2:] = 2
    seam = from_arrays(normals, z, split, {"min_px": 5})
    assert seam.seams[:, size // 2 - 1].all() and not seam.features.any()
    step = z.copy()
    step[:, size // 2:] += .02
    occlusion = from_arrays(normals, step, ids, {"min_px": 5}, depth_per_pixel=.001)
    assert occlusion.features[5:-5, size // 2 - 1].all()
    assert not occlusion.features[:, -1].any(), "No wrap-around edge at the opposite boundary"
    slope = np.tile(.2 + np.arange(size) * .005, (size, 1)).astype(np.float32)
    n = np.array([5., 0., 1.]); n /= np.linalg.norm(n)
    slope_normals = np.full((size, size, 3), np.rint((n + 1) * 127.5), dtype=np.uint8)
    continuous = from_arrays(slope_normals, slope, ids, {"min_px": 5}, depth_per_pixel=.001)
    assert not continuous.features.any(), "A steep continuous plane is not an occluding edge"
    boundary = np.zeros((size, size), bool)
    boundary[80, 5:-5] = True
    lines = np.zeros_like(boundary)
    lines[85, 10:-10] = True
    lines[10:-10, 80] = True
    reduced = _suppress_parallel(lines, boundary, 7)
    assert not reduced[85, 15:65].any(), "Nearby parallel seam must be deduplicated"
    assert reduced[75:85, 80].all(), "A real crossing must remain attached"
    return {"plane": "ok", "seam": "ok", "self_occlusion": "ok",
            "steep_plane": "ok", "parallel_cleanup": "ok", "junction": "ok"}


if __name__ == "__main__":
    print(json.dumps(self_test()))
