import argparse
import json
from pathlib import Path

import numpy as np
import trimesh
from numba import njit
from PIL import Image
from scipy import ndimage


@njit(cache=True)
def rasterize(vertices, faces, vertex_normals, face_normals, depth, normals, ids, object_id):
    height, width = depth.shape
    for fi in range(len(faces)):
        ia, ib, ic = faces[fi]
        a, b, c = vertices[ia], vertices[ib], vertices[ic]
        xmin = max(0, int(np.floor(min(a[0], b[0], c[0]))))
        xmax = min(width - 1, int(np.ceil(max(a[0], b[0], c[0]))))
        ymin = max(0, int(np.floor(min(a[1], b[1], c[1]))))
        ymax = min(height - 1, int(np.ceil(max(a[1], b[1], c[1]))))
        denom = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(denom) < 1e-12:
            continue
        na, nb, nc = vertex_normals[ia], vertex_normals[ib], vertex_normals[ic]
        fn = face_normals[fi]
        if np.dot(na, fn) < 0.8660254:
            na = fn
        if np.dot(nb, fn) < 0.8660254:
            nb = fn
        if np.dot(nc, fn) < 0.8660254:
            nc = fn
        for yy in range(ymin, ymax + 1):
            py = yy + 0.5
            for xx in range(xmin, xmax + 1):
                px = xx + 0.5
                wa = ((b[1] - c[1]) * (px - c[0]) + (c[0] - b[0]) * (py - c[1])) / denom
                wb = ((c[1] - a[1]) * (px - c[0]) + (a[0] - c[0]) * (py - c[1])) / denom
                wc = 1.0 - wa - wb
                if wa < -1e-8 or wb < -1e-8 or wc < -1e-8:
                    continue
                zz = wa * a[2] + wb * b[2] + wc * c[2]
                if zz <= depth[yy, xx]:
                    continue
                depth[yy, xx] = zz
                ids[yy, xx] = object_id
                nx = wa * na[0] + wb * nb[0] + wc * nc[0]
                ny = wa * na[1] + wb * nb[1] + wc * nc[1]
                nz = wa * na[2] + wb * nb[2] + wc * nc[2]
                length = np.sqrt(nx * nx + ny * ny + nz * nz)
                if length > 0:
                    normals[yy, xx, 0] = nx / length
                    normals[yy, xx, 1] = ny / length
                    normals[yy, xx, 2] = nz / length


def unit(v):
    a = np.asarray(v, dtype=float)
    return a / np.linalg.norm(a)


def color(value):
    if isinstance(value, str):
        h = value.lstrip('#')
        return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=float) / 255
    a = np.asarray(value, dtype=float)
    return a / 255 if a.max() > 1 else a


def load_objects(scene, base):
    objects = []
    for i, item in enumerate(scene['objects']):
        p = Path(item['path'])
        if not p.is_absolute():
            p = base / p
        mesh = trimesh.load(p, force='mesh', process=True)
        if 'transform' in item:
            mesh.apply_transform(np.asarray(item['transform']))
        if 'translation' in item:
            mesh.apply_translation(item['translation'])
        objects.append((item.get('id', str(i + 1)), mesh, color(item.get('color', '#bfc1c4'))))
    return objects


def render(scene, output, base=Path('.')):
    objects = load_objects(scene, base)
    camera = scene.get('camera', {})
    direction = unit(camera.get('direction', scene.get('direction', [-1, -2, 1])))
    up = unit(camera.get('up', scene.get('up', [0, 0, 1])))
    right = unit(np.cross(up, direction))
    up = unit(np.cross(direction, right))
    basis = np.column_stack([right, up, direction])
    projected = [np.asarray(mesh.vertices @ basis, dtype=np.float32) for _, mesh, _ in objects]
    lo = np.min([v.min(axis=0) for v in projected], axis=0)
    hi = np.max([v.max(axis=0) for v in projected], axis=0)
    size = scene.get('size', [1800, 1400])
    if isinstance(size, int):
        size = [size, size]
    ss = float(scene.get('supersample', 1.5))
    width, height = [int(x * ss) for x in size]
    margin = float(scene.get('margin', 0.085))
    scale = min(width * (1 - 2 * margin) / max(hi[0] - lo[0], 1e-6), height * (1 - 2 * margin) / max(hi[1] - lo[1], 1e-6))
    scale *= float(camera.get('zoom', 1))
    center = (lo + hi) / 2
    depth = np.full((height, width), -1e20, dtype=np.float32)
    normals = np.zeros((height, width, 3), dtype=np.float32)
    ids = np.zeros((height, width), dtype=np.uint16)
    anchors = {}
    for i, ((name, mesh, _), p) in enumerate(zip(objects, projected), 1):
        p[:, 0] = (p[:, 0] - center[0]) * scale + width / 2
        p[:, 1] = height / 2 - (p[:, 1] - center[1]) * scale
        vn = np.asarray(mesh.vertex_normals @ basis, dtype=np.float32)
        fn = np.asarray(mesh.face_normals @ basis, dtype=np.float32)
        rasterize(p, np.asarray(mesh.faces, dtype=np.int32), vn, fn, depth, normals, ids, i)
        anchors[name] = {'center': (p[:, :2].mean(axis=0) / ss).tolist(), 'bounds': [(p[:, :2].min(axis=0) / ss).tolist(), (p[:, :2].max(axis=0) / ss).tolist()]}
    mask = ids > 0
    mode = scene.get('mode', 'product')
    if mode == 'line':
        edge = np.zeros(mask.shape, dtype=bool)
        for axis in (0, 1):
            for shift in (-1, 1):
                neighbor_ids = np.roll(ids, shift, axis)
                both = mask & (neighbor_ids > 0)
                neighbor_normals = np.roll(normals, shift, axis)
                edge |= ids != neighbor_ids
                edge |= both & ((normals * neighbor_normals).sum(axis=2) < np.cos(np.deg2rad(42)))
                edge |= both & (np.abs(depth - np.roll(depth, shift, axis)) > max(0.7, float(np.linalg.norm(hi - lo)) * 0.004))
        width_px = float(scene.get('line_width', 1.1)) * ss
        if width_px > 1.5:
            edge = ndimage.binary_dilation(edge, iterations=max(1, int(width_px / 2)))
        rgb = np.full((height, width, 3), 255, dtype=np.uint8)
        rgb[edge] = 12
    else:
        base_colors = np.vstack([np.ones(3)] + [c for _, _, c in objects])
        rgb = base_colors[ids].astype(np.float32)
        lighting = np.full(ids.shape, 0.38, dtype=np.float32)
        specular = np.zeros(ids.shape, dtype=np.float32)
        for light, strength, shine in [([-0.6, 0.8, 1.2], 0.48, 0.38), ([1, 0.3, 0.4], 0.20, 0.14), ([-0.2, 0.8, -0.8], 0.18, 0.08)]:
            light = unit(light)
            lighting += np.maximum(0, (normals * light).sum(axis=2)) * strength
            half = unit(light + np.array([0, 0, 1]))
            specular += np.maximum(0, (normals * half).sum(axis=2)) ** 48 * shine
        rgb *= lighting[..., None]
        rgb += specular[..., None]
        rgb[~mask] = 1
        rgb = (np.clip(rgb, 0, 1) * 255).astype(np.uint8)
    image = Image.fromarray(rgb).resize(tuple(size), Image.Resampling.LANCZOS)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)
    metadata = {'size': size, 'mode': mode, 'direction': direction.tolist(), 'up': up.tolist(), 'pixels_per_mm': float(scale / ss), 'anchors': anchors, 'triangles': sum(len(m.faces) for _, m, _ in objects)}
    output.with_suffix('.anchors.json').write_text(json.dumps(metadata, indent=2))
    return metadata


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('scene')
    parser.add_argument('output', nargs='?')
    parser.add_argument('--base', type=Path, default=Path(__file__).resolve().parents[1], help='Root for relative object paths; defaults to this project root')
    args = parser.parse_args()
    path = Path(args.scene)
    scene = json.loads(path.read_text())
    output = args.output or scene.get('output')
    if not output:
        parser.error('Output path is required as argument or scene.output')
    result = render(scene, output, args.base)
    print(json.dumps({'output': str(output), 'triangles': result['triangles'], 'mode': result['mode']}))
