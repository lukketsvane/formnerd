import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, '/tmp/entropi-mesh-deps')

import manifold3d as md
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components


ROOT = Path(__file__).resolve().parents[1]
P = json.loads((ROOT / 'cad/parameters.json').read_text())
LIMIT = 0.01


def topology(vertices, faces):
    finite = bool(np.isfinite(vertices).all())
    in_range = bool(len(vertices) and vertices.ndim == 2 and vertices.shape[1] == 3 and len(faces) and faces.ndim == 2 and faces.shape[1] == 3 and faces.min() >= 0 and faces.max() < len(vertices))
    if not finite or not in_range:
        return {'valid': False, 'finite_coordinates': finite, 'indices_in_range': in_range}
    a = np.concatenate([faces[:, 0], faces[:, 1], faces[:, 2]])
    b = np.concatenate([faces[:, 1], faces[:, 2], faces[:, 0]])
    keys = np.minimum(a, b).astype(np.uint64) * np.uint64(len(vertices)) + np.maximum(a, b).astype(np.uint64)
    unique_keys, inverse, counts = np.unique(keys, return_inverse=True, return_counts=True)
    directions = np.where(a < b, 1.0, -1.0)
    sums = np.bincount(inverse, weights=directions)
    open_edges = int(np.count_nonzero(counts == 1))
    nonmanifold = int(np.count_nonzero(counts > 2))
    inconsistent = int(np.count_nonzero((counts == 2) & (sums != 0)))
    del a, b, keys, inverse, counts, directions, sums
    rows = (unique_keys // np.uint64(len(vertices))).astype(np.int64)
    columns = (unique_keys % np.uint64(len(vertices))).astype(np.int64)
    graph = coo_matrix((np.ones(len(unique_keys), dtype=np.uint8), (rows, columns)), shape=(len(vertices), len(vertices))).tocsr()
    components = int(connected_components(graph, directed=False, return_labels=False))
    del unique_keys, rows, columns, graph
    triangles = vertices[faces]
    cross = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    degenerate = int(np.count_nonzero(np.all(cross == 0, axis=1)))
    signed_volume = float(np.einsum('ij,ij->i', triangles[:, 0], np.cross(triangles[:, 1], triangles[:, 2])).sum(dtype=np.float64) / 6)
    return {
        'valid': finite and in_range and open_edges == 0 and nonmanifold == 0 and inconsistent == 0 and degenerate == 0 and signed_volume > 0,
        'finite_coordinates': finite,
        'indices_in_range': in_range,
        'open_edges': open_edges,
        'nonmanifold_edges': nonmanifold,
        'inconsistent_winding_edges': inconsistent,
        'zero_area_triangles': degenerate,
        'signed_volume_mm3': signed_volume,
        'connected_components': components,
        'connectivity_basis': 'scipy.sparse.csgraph vertex connectivity on exact triangle indices',
        'topology_basis': 'Exact triangle indices and float64 coordinates; no tolerance welding',
    }


def load(path):
    with np.load(path) as data:
        vertices = np.ascontiguousarray(data['vertices'], dtype=np.float64)
        faces = np.ascontiguousarray(data['faces'], dtype=np.uint64)
    check = topology(vertices, faces)
    if not check.get('indices_in_range') or not check.get('finite_coordinates'):
        return None, check
    solid = md.Manifold(md.Mesh64(vertices, faces))
    status = str(solid.status())
    volume = float(solid.volume())
    components = check['connected_components']
    check.update({
        'vertices': len(vertices),
        'triangles': len(faces),
        'manifold_status': status,
        'manifold_volume_mm3': volume,
        'connected_components': components,
        'bounds_mm': list(solid.bounding_box()),
    })
    check['valid'] = bool(check['valid'] and solid.status() == md.Error.NoError and math.isfinite(volume) and volume > 0 and components == 1)
    return solid, check


def bounds_overlap(a, b):
    aa = np.asarray(a.bounding_box())
    bb = np.asarray(b.bounding_box())
    return bool(np.all(np.minimum(aa[3:], bb[3:]) - np.maximum(aa[:3], bb[:3]) > 1e-9))


def intersection(a, b):
    if not bounds_overlap(a, b):
        return {'tested': False, 'volume_mm3': 0.0, 'status': 'bounds_disjoint'}
    result = a ^ b
    volume = float(result.volume())
    return {'tested': True, 'volume_mm3': volume, 'status': str(result.status()), 'valid': result.status() == md.Error.NoError and math.isfinite(volume)}


def rotate_y(solid, angle, centre):
    x, z = centre
    return solid.translate((-x, 0, -z)).rotate((0, angle, 0)).translate((x, 0, z))


def collisions(moving, stationary, original=False):
    tests, skipped, overlaps, errors = 0, 0, [], []
    for moving_name, candidate in moving.items():
        for fixed_name in stationary:
            if original:
                result = STATIC[tuple(sorted((moving_name, fixed_name)))]
            else:
                result = intersection(candidate, SOLIDS[fixed_name])
            tests += int(result['tested'])
            skipped += int(not result['tested'])
            if result.get('valid') is False:
                errors.append({'moving': moving_name, 'stationary': fixed_name, **result})
            if result['volume_mm3'] > LIMIT:
                overlaps.append({'moving': moving_name, 'stationary': fixed_name, 'volume_mm3': result['volume_mm3']})
    return {'boolean_tests': tests, 'bounds_skipped': skipped, 'interferences': overlaps, 'errors': errors, 'valid': not overlaps and not errors}


def extract(label, moving_names, removed, direction, angle=0, centre=(0, 0)):
    fixed = [name for name in ASSEMBLY if name not in set(moving_names) | set(removed)]
    original = {name: SOLIDS[name] for name in moving_names}
    samples = []
    if angle:
        for value in [angle / 2, angle]:
            posed = {name: rotate_y(solid, value, centre) for name, solid in original.items()}
            samples.append({'phase': 'unlock_rotation', 'angle_deg': value, **collisions(posed, fixed)})
        base = {name: rotate_y(solid, angle, centre) for name, solid in original.items()}
    else:
        base = original
    if fixed:
        fixed_bounds = np.array([SOLIDS[name].bounding_box() for name in fixed])
        moving_bounds = np.array([solid.bounding_box() for solid in base.values()])
        if direction < 0:
            free = float(moving_bounds[:, 4].max() - fixed_bounds[:, 1].min() + 2.0)
        else:
            free = float(fixed_bounds[:, 4].max() - moving_bounds[:, 1].min() + 2.0)
    else:
        free = 0.0
    distances = sorted(set([0.0, 2.0, 8.0, 40.0, max(40.0, free)]))
    for distance in distances:
        posed = {name: solid.translate((0, direction * distance, 0)) for name, solid in base.items()}
        samples.append({'phase': 'extraction', 'translation_mm': [0.0, direction * distance, 0.0], **collisions(posed, fixed, original=not angle and distance == 0)})
    clear = not any(bounds_overlap(candidate, SOLIDS[name]) for candidate in posed.values() for name in fixed)
    return {
        'label': label,
        'moving_parts': moving_names,
        'prerequisites_removed': removed,
        'rotation_axis': '+Y' if angle else None,
        'rotation_centre_xz_mm': list(centre) if angle else None,
        'samples': samples,
        'final_bounds_clear': clear,
        'valid': all(sample['valid'] for sample in samples) and clear,
        'scope': 'Discrete collision samples only; continuous swept collision, deformation, friction and physical fit are not certified',
    }


REPORT = {
    'revision': P['revision'],
    'units': 'mm',
    'interference_limit_mm3': LIMIT,
    'parts': {},
    'static_pairs': [],
    'motions': [],
    'excluded_from_assembly': [],
    'hardware_fit_verified': False,
    'physical_print_tested': False,
    'continuous_swept_motion_verified': False,
}
SOLIDS = {}
ASSEMBLY = []
for path in sorted((ROOT / 'parts').glob('*.npz')):
    if not re.match(r'^\d\d_', path.stem):
        REPORT['excluded_from_assembly'].append({'part': path.stem, 'reason': 'Separate test or coupon artifact'})
        continue
    solid, check = load(path)
    REPORT['parts'][path.stem] = check
    if solid is not None and solid.status() == md.Error.NoError:
        SOLIDS[path.stem] = solid
        if path.stem == '06_lock_tool' or 'coupon' in path.stem:
            REPORT['excluded_from_assembly'].append({'part': path.stem, 'reason': 'Assembly tool or fit coupon'})
        else:
            ASSEMBLY.append(path.stem)
required = ['01_outer_shell', '02_native_rear_cover', '03_esp32_carrier', '04_optical_bezel', '07_shutter', '08_shutter_retainer']
required.extend(f'05_lock_{index + 1}' for index in range(len(P['lock_centres_xz'])))
REPORT['missing_required_parts'] = [name for name in required if name not in SOLIDS]
print(json.dumps({'stage': 'topology', 'parts': len(REPORT['parts']), 'invalid': [name for name, value in REPORT['parts'].items() if not value['valid']], 'missing': REPORT['missing_required_parts']}), flush=True)

STATIC = {}
for i, a in enumerate(ASSEMBLY):
    for b in ASSEMBLY[i + 1:]:
        result = intersection(SOLIDS[a], SOLIDS[b])
        STATIC[tuple(sorted((a, b)))] = result
        REPORT['static_pairs'].append({'a': a, 'b': b, **result})
REPORT['static_interferences'] = [pair for pair in REPORT['static_pairs'] if pair['volume_mm3'] > LIMIT]
REPORT['static_errors'] = [pair for pair in REPORT['static_pairs'] if pair.get('valid') is False]
print(json.dumps({'stage': 'static', 'pairs': len(STATIC), 'interferences': REPORT['static_interferences'], 'errors': REPORT['static_errors']}), flush=True)

locks = [name for name in ASSEMBLY if name.startswith('05_lock_')]
if '02_native_rear_cover' in SOLIDS:
    REPORT['motions'].append(extract('Remove rear cover after unlocking and removing locks', ['02_native_rear_cover'], locks, -1))
if '03_esp32_carrier' in SOLIDS:
    moving = ['03_esp32_carrier'] + [name for name in ASSEMBLY if name.startswith('09_camera_keeper')]
    removed = [name for name in locks + ['02_native_rear_cover', '04_optical_bezel'] if name in SOLIDS]
    REPORT['motions'].append(extract('Extract carrier with attached camera keeper after rear cover and bezel removal', moving, removed, -1))
if '04_optical_bezel' in SOLIDS:
    REPORT['motions'].append(extract('Unlock bezel then extract through front', ['04_optical_bezel'], [], 1, -float(P['bezel']['locked_rotation_deg']), P['optical_axis_xz']))
for name in locks:
    index = int(name.rsplit('_', 1)[1]) - 1
    REPORT['motions'].append(extract('Quarter-turn unlock then remove ' + name, [name], [], -1, -90.0, P['lock_centres_xz'][index]))
if '07_shutter' in SOLIDS:
    stationary = [name for name in ASSEMBLY if name != '07_shutter']
    samples = []
    for distance in [0.0, 0.6, 1.2]:
        moved = {'07_shutter': SOLIDS['07_shutter'].translate((0, 0, -distance))}
        samples.append({'travel_mm': distance, **collisions(moved, stationary, original=distance == 0)})
    REPORT['motions'].append({'label': 'Shutter downward travel', 'moving_parts': ['07_shutter'], 'samples': samples, 'valid': all(item['valid'] for item in samples), 'scope': 'Discrete rigid-part samples only; switch actuation, return force and physical fit remain unverified'})
if '08_shutter_retainer' in SOLIDS:
    removed = [name for name in locks + ['02_native_rear_cover'] if name in SOLIDS]
    REPORT['motions'].append(extract('Remove shutter retainer through rear access', ['08_shutter_retainer'], removed, -1))
REPORT['valid'] = bool(REPORT['parts']) and not REPORT['missing_required_parts'] and all(value['valid'] for value in REPORT['parts'].values()) and not REPORT['static_interferences'] and not REPORT['static_errors'] and all(motion['valid'] for motion in REPORT['motions'])
REPORT['scope'] = 'Independent float64 mesh topology and sampled rigid assembly checks. Passing these checks is not physical print approval, measured hardware fit, working electronics, optical validation or a complete tolerance certificate.'
destination = ROOT / 'verification/assembly-independent.json'
destination.parent.mkdir(exist_ok=True)
destination.write_text(json.dumps(REPORT, indent=2) + '\n')
print(json.dumps({'valid': REPORT['valid'], 'parts': len(REPORT['parts']), 'static_interferences': len(REPORT['static_interferences']), 'failed_motions': [motion['label'] for motion in REPORT['motions'] if not motion['valid']], 'report': str(destination)}), flush=True)
raise SystemExit(0 if REPORT['valid'] else 1)
