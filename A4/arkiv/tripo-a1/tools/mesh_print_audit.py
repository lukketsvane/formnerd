import argparse
import importlib.util
import json
import math
import sys
import time
from itertools import combinations
from pathlib import Path

import numpy as np
import trimesh


def signed_volume(vertices, faces):
    triangles = vertices[faces]
    return float(np.einsum('ij,ij->i', triangles[:, 0], np.cross(triangles[:, 1], triangles[:, 2])).sum() / 6)


def geometry_mesh(mesh):
    _, first, inverse = np.unique(mesh.vertices, axis=0, return_index=True, return_inverse=True)
    return trimesh.Trimesh(vertices=mesh.vertices[first], faces=inverse[mesh.faces], process=False)


def topology(mesh, tolerance):
    vertices = np.asarray(mesh.vertices)
    faces = np.asarray(mesh.faces)
    triangles = vertices[faces]
    twice_area = np.linalg.norm(np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0]), axis=1)
    collapsed = np.any(np.sort(faces, axis=1)[:, 1:] == np.sort(faces, axis=1)[:, :-1], axis=1)
    edges = np.concatenate((faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]))
    _, first_edge, inverse, counts = np.unique(np.sort(edges, axis=1), axis=0, return_index=True, return_inverse=True, return_counts=True)
    directions = np.bincount(inverse, weights=np.where(edges[:, 0] < edges[:, 1], 1, -1), minlength=len(counts))
    _, duplicate_counts = np.unique(np.sort(faces, axis=1), axis=0, return_counts=True)
    last_edge = np.zeros(len(counts), dtype=np.int64)
    np.maximum.at(last_edge, inverse, np.arange(len(edges)))
    shared = counts >= 2
    adjacency = np.column_stack((first_edge[shared] % len(faces), last_edge[shared] % len(faces)))
    groups = trimesh.graph.connected_components(adjacency, nodes=np.arange(len(faces)), min_len=1, engine='scipy')
    components = []
    for ids in sorted(groups, key=len, reverse=True):
        used = np.unique(faces[ids])
        components.append({'faces': int(len(ids)), 'vertices': int(len(used)), 'bounds': np.asarray([vertices[used].min(axis=0), vertices[used].max(axis=0)]).tolist(), 'signed_volume': signed_volume(vertices, faces[ids])})
    report = {
        'vertices': int(len(vertices)), 'faces': int(len(faces)),
        'collapsed_faces': int(collapsed.sum()),
        'zero_area_faces': int((twice_area == 0).sum()),
        'near_zero_area_faces': int(((twice_area > 0) & (twice_area <= tolerance * tolerance)).sum()),
        'duplicate_faces': int(np.maximum(duplicate_counts - 1, 0).sum()),
        'boundary_edges': int((counts == 1).sum()),
        'nonmanifold_edges': int((counts > 2).sum()),
        'same_direction_paired_edges': int(((counts == 2) & (directions != 0)).sum()),
        'connected_surface_components': int(len(components)),
        'single_connected_print_part': len(components) == 1,
        'components': components,
        'signed_volume': signed_volume(vertices, faces),
        'bounds': np.asarray(mesh.bounds).tolist(),
    }
    report['closed_manifold'] = report['boundary_edges'] == 0 and report['nonmanifold_edges'] == 0 and report['collapsed_faces'] == 0 and report['zero_area_faces'] == 0
    report['consistent_winding'] = report['same_direction_paired_edges'] == 0
    report['all_closed_components_outward'] = report['closed_manifold'] and report['consistent_winding'] and all(q['signed_volume'] > 0 for q in components)
    report['topology_passed'] = report['closed_manifold'] and report['consistent_winding'] and report['duplicate_faces'] == 0 and report['all_closed_components_outward']
    return report


def segment_triangle(a, b, triangle, epsilon):
    direction = b - a
    edge1, edge2 = triangle[1] - triangle[0], triangle[2] - triangle[0]
    p = np.cross(direction, edge2)
    determinant = float(edge1 @ p)
    threshold = epsilon * max(np.linalg.norm(direction) * np.linalg.norm(edge1) * np.linalg.norm(edge2), 1e-30)
    if abs(determinant) <= threshold:
        return False
    delta = a - triangle[0]
    u = float(delta @ p) / determinant
    q = np.cross(delta, edge1)
    v = float(direction @ q) / determinant
    t = float(edge2 @ q) / determinant
    return u >= -epsilon and v >= -epsilon and u + v <= 1 + epsilon and -epsilon <= t <= 1 + epsilon


def polygon_area(points):
    if len(points) < 3:
        return 0.0
    p = np.asarray(points)
    return float(np.abs(np.sum(p[:, 0] * np.roll(p[:, 1], -1) - p[:, 1] * np.roll(p[:, 0], -1))) / 2)


def coplanar_overlap(a, b, normal, tolerance):
    axis = int(np.argmax(np.abs(normal)))
    a, b = np.delete(a, axis, axis=1), np.delete(b, axis, axis=1)
    if np.cross(b[1] - b[0], b[2] - b[0]) < 0:
        b = b[::-1]
    output = list(a)
    for c, d in zip(b, np.roll(b, -1, axis=0)):
        side_tolerance = tolerance * np.linalg.norm(d - c)
        source, output = output, []
        if not source:
            break
        previous = source[-1]
        previous_side = float(np.cross(d - c, previous - c))
        for current in source:
            current_side = float(np.cross(d - c, current - c))
            if (current_side >= -side_tolerance) != (previous_side >= -side_tolerance):
                denominator = previous_side - current_side
                if abs(denominator) > 1e-30:
                    output.append(previous + (current - previous) * (previous_side / denominator))
            if current_side >= -side_tolerance:
                output.append(current)
            previous, previous_side = current, current_side
    return polygon_area(output) > tolerance * tolerance


def triangle_contact(a, b, tolerance):
    na = np.cross(a[1] - a[0], a[2] - a[0])
    nb = np.cross(b[1] - b[0], b[2] - b[0])
    la, lb = np.linalg.norm(na), np.linalg.norm(nb)
    if min(la, lb) <= tolerance * tolerance:
        return False
    na, nb = na / la, nb / lb
    if abs(float(na @ nb)) > 1 - 1e-8 and np.max(np.abs((b - a[0]) @ na)) <= tolerance:
        return coplanar_overlap(a, b, na, tolerance)
    return any(segment_triangle(t[i], t[(i + 1) % 3], other, 1e-9) for t, other in [(a, b), (b, a)] for i in range(3))


def self_contacts(mesh, tolerance, max_pairs, deadline):
    if importlib.util.find_spec('rtree') is None:
        return {'checked': False, 'reason': 'rtree unavailable'}
    triangles = np.asarray(mesh.triangles)
    bounds = np.hstack((triangles.min(axis=1), triangles.max(axis=1)))
    tree = mesh.triangles_tree
    checked, found = 0, []
    complete = True
    for i, box in enumerate(bounds):
        if time.monotonic() > deadline:
            complete = False
            break
        for j in tree.intersection(np.r_[box[:3] - tolerance, box[3:] + tolerance]):
            if j <= i or np.intersect1d(mesh.faces[i], mesh.faces[j]).size:
                continue
            if checked >= max_pairs or len(found) >= 100:
                complete = False
                break
            checked += 1
            if triangle_contact(triangles[i], triangles[j], tolerance):
                found.append([int(i), int(j)])
        if not complete:
            break
    return {'checked': True, 'complete_within_nonadjacent_face_method': complete, 'candidate_pairs_checked': checked, 'nonadjacent_contacts_found': len(found), 'face_pairs': found, 'limitations': 'Faces sharing a welded vertex are excluded; this does not certify absence of folded intersections between adjacent faces.'}


def sampled_wall_chords(mesh, tolerance, millimetres_per_unit, sample_count, minimum_wall_mm):
    if millimetres_per_unit is None:
        return {'checked': False, 'reason': 'Physical print scale not supplied'}
    if importlib.util.find_spec('rtree') is None:
        return {'checked': False, 'reason': 'rtree unavailable'}
    if not mesh.is_volume:
        return {'checked': False, 'reason': 'Mesh is not a closed, outward-wound volume'}
    count = min(sample_count, len(mesh.faces))
    ids = np.random.default_rng(617).choice(len(mesh.faces), count, replace=False, p=mesh.area_faces / mesh.area_faces.sum())
    normals = mesh.face_normals[ids]
    origins = mesh.triangles_center[ids] - normals * tolerance * 10
    locations, ray_ids, _ = mesh.ray.intersects_location(origins, -normals, multiple_hits=True)
    distances = np.full(count, np.inf)
    if len(locations):
        chord = np.linalg.norm(locations - origins[ray_ids], axis=1)
        keep = chord > tolerance * 2
        np.minimum.at(distances, ray_ids[keep], chord[keep] + tolerance * 10)
    good = np.isfinite(distances)
    mm = distances[good] * millimetres_per_unit
    thin_ids = np.flatnonzero(good & (distances * millimetres_per_unit < minimum_wall_mm))
    return {'checked': True, 'method': 'sampled inward surface-normal chords', 'samples': count, 'rays_with_opposite_hits': int(good.sum()), 'minimum_chord_mm': float(mm.min()) if len(mm) else None, 'fifth_percentile_chord_mm': float(np.percentile(mm, 5)) if len(mm) else None, 'median_chord_mm': float(np.median(mm)) if len(mm) else None, 'threshold_mm': minimum_wall_mm, 'below_threshold_samples': int(len(thin_ids)), 'thin_samples': [{'face': int(ids[i]), 'position_mm': (mesh.triangles_center[ids[i]] * millimetres_per_unit).tolist(), 'chord_mm': float(distances[i] * millimetres_per_unit)} for i in thin_ids[:30]], 'limitations': 'Sampled chords are a local thickness indicator, not an exhaustive minimum-wall certification.'}


def part_intersections(parts, tolerance, max_pairs, deadline):
    candidates = []
    for (an, a), (bn, b) in combinations(parts.items(), 2):
        overlap = np.minimum(a.bounds[1], b.bounds[1]) - np.maximum(a.bounds[0], b.bounds[0])
        if np.all(overlap > tolerance):
            candidates.append((an, a, bn, b))
    if importlib.util.find_spec('manifold3d') is None:
        return {'checked': False, 'reason': 'manifold3d unavailable', 'aabb_overlap_candidate_pairs': [[a, b] for a, _, b, _ in candidates]}
    results = []
    for an, a, bn, b in candidates:
        if len(results) >= max_pairs or time.monotonic() > deadline:
            break
        if not a.is_volume or not b.is_volume:
            results.append({'a': an, 'b': bn, 'checked': False, 'reason': 'At least one part is not a valid closed outward volume'})
            continue
        try:
            overlap = trimesh.boolean.intersection([a, b], engine='manifold', check_volume=True)
            value = abs(float(overlap.volume)) if overlap is not None else 0.0
            threshold = float(max(min(abs(a.volume), abs(b.volume)) * 1e-6, tolerance ** 3 * 100))
            results.append({'a': an, 'b': bn, 'checked': True, 'overlap_volume_source_units_cubed': value, 'numerical_threshold_source_units_cubed': threshold, 'interpenetration_detected': bool(value > threshold)})
        except Exception as error:
            results.append({'a': an, 'b': bn, 'checked': False, 'error': str(error)})
    return {'checked': True, 'complete': len(results) == len(candidates) and all(q.get('checked') for q in results), 'aabb_overlap_candidate_count': len(candidates), 'pairs': results}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--millimetres-per-unit', type=float)
    parser.add_argument('--target-width-mm', type=float)
    parser.add_argument('--width-axis', choices=['x', 'y', 'z'], default='x')
    parser.add_argument('--minimum-wall-mm', type=float, default=1.2)
    parser.add_argument('--wall-samples', type=int, default=256)
    parser.add_argument('--max-self-pairs', type=int, default=100000)
    parser.add_argument('--max-part-pairs', type=int, default=128)
    parser.add_argument('--time-budget-seconds', type=float, default=120)
    args = parser.parse_args()
    if args.millimetres_per_unit and args.target_width_mm:
        raise SystemExit('Supply one scale mechanism, not both.')
    started = time.monotonic()
    deadline = started + args.time_budget_seconds
    scene = trimesh.load_scene(str(args.input), process=False, maintain_order=True)
    objects = {}
    for node in sorted(scene.graph.nodes_geometry):
        matrix, geometry = scene.graph[node]
        mesh = scene.geometry[geometry].copy()
        if not isinstance(mesh, trimesh.Trimesh) or not len(mesh.faces):
            continue
        mesh.apply_transform(matrix)
        objects[str(node)] = mesh
    if not objects:
        raise SystemExit('No triangle-mesh nodes were found.')
    low = np.min([q.bounds[0] for q in objects.values()], axis=0)
    high = np.max([q.bounds[1] for q in objects.values()], axis=0)
    diagonal = float(np.linalg.norm(high - low))
    tolerance = max(diagonal * 1e-7, 1e-12)
    scale = args.millimetres_per_unit
    if args.target_width_mm:
        width_axis = ['x', 'y', 'z'].index(args.width_axis)
        scale = args.target_width_mm / (high[width_axis] - low[width_axis])
    report = {'input': str(args.input.resolve()), 'input_modified': False, 'trimesh_version': trimesh.__version__, 'node_count': len(objects), 'source_units_metadata': scene.units, 'source_bounds': [low.tolist(), high.tolist()], 'source_extents': (high - low).tolist(), 'millimetres_per_unit': scale, 'target_width_mm': args.target_width_mm, 'target_width_axis': args.width_axis if args.target_width_mm else None, 'print_extents_mm': ((high - low) * scale).tolist() if scale else None, 'weld_tolerance_source_units': 0.0, 'geometric_query_tolerance_source_units': tolerance, 'welding_method': 'read-only exact-coordinate welding for geometric topology and UV seam duplicates', 'parts': {}, 'supports_and_mechanical_fit_verified': False}
    welded = {}
    for name, mesh in objects.items():
        q = geometry_mesh(mesh)
        welded[name] = q
        result = topology(q, tolerance)
        result['original_vertex_count'] = len(mesh.vertices)
        report['parts'][name] = result
        print(json.dumps({'part': name, 'faces': len(q.faces), 'topology_passed': result['topology_passed'], 'boundary_edges': result['boundary_edges'], 'components': result['connected_surface_components']}), flush=True)
    report['part_intersections'] = part_intersections(welded, tolerance, args.max_part_pairs, deadline)
    for name, mesh in welded.items():
        if not report['parts'][name]['topology_passed']:
            report['parts'][name]['sampled_wall_chords'] = {'checked': False, 'reason': 'Topology must be corrected before thickness sampling'}
        elif time.monotonic() < deadline:
            report['parts'][name]['sampled_wall_chords'] = sampled_wall_chords(mesh, tolerance, scale, args.wall_samples, args.minimum_wall_mm)
        else:
            report['parts'][name]['sampled_wall_chords'] = {'checked': False, 'reason': 'Audit time budget reached'}
    for name, mesh in welded.items():
        report['parts'][name]['self_contacts'] = self_contacts(mesh, tolerance, args.max_self_pairs, deadline)
    report['all_part_topology_checks_passed'] = all(q['topology_passed'] for q in report['parts'].values())
    report['all_nodes_single_component'] = all(q['single_connected_print_part'] for q in report['parts'].values())
    report['elapsed_seconds'] = time.monotonic() - started
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(str(args.output.resolve()), flush=True)


if __name__ == '__main__':
    main()
