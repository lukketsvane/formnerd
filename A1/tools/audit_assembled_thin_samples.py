import gc
import json
import time
from pathlib import Path

import numpy as np
import trimesh

from mesh_print_audit import geometry_mesh


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / 'verification/mesh-audit.json'
OUTPUT = ROOT / 'verification/assembled-thin-samples.json'


def add_source_precision_contact_diagnostic(report, maximum_position_quantum_mm):
    tolerance = 2 * maximum_position_quantum_mm
    report['source_precision_contact_diagnostic'] = {'authoritative_for_exact_boolean_topology': False, 'position_component_type': 'IEEE754 float32, GLB accessor5126', 'maximum_position_quantum_mm': maximum_position_quantum_mm, 'contact_tolerance_mm': tolerance, 'method': 'Merge only ray-interval gaps no larger than two float32 position quanta. Strict intervals and strict chords remain unchanged. This tests microscopic segment seams without modifying geometry.'}
    for row in report['samples']:
        intervals = sorted(interval for value in row['per_node_ray_intervals_relative_to_face_mm'].values() for interval in value)
        merged, bridged = [], []
        for a, b in intervals:
            if merged and a <= merged[-1][1] + tolerance:
                if a > merged[-1][1]:
                    bridged.append(a - merged[-1][1])
                merged[-1][1] = max(merged[-1][1], b)
            else:
                merged.append([a, b])
        containing = next((interval for interval in merged if interval[0] - tolerance <= report['normal_offset_mm'] <= interval[1] + tolerance), None)
        row['source_precision_contact_intervals_relative_to_face_mm'] = merged
        row['source_precision_contact_bridged_gaps_mm'] = bridged
        row['source_precision_contact_chord_mm'] = containing[1] - containing[0] if containing else None
        row['source_precision_contact_inward_depth_mm'] = containing[1] if containing else None
        row['source_precision_contact_chord_below_1_2_mm'] = bool(containing and containing[1] - containing[0] < 1.2)
    exposed = [row for row in report['samples'] if row['exposure_at_offset'] == 'exposed_assembled_outer_face']
    report['summary']['exposed_samples_below_1_2_mm_source_precision_contact_chord'] = sum(row['source_precision_contact_chord_below_1_2_mm'] for row in exposed)
    report['summary']['minimum_exposed_source_precision_contact_chord_mm'] = min(row['source_precision_contact_chord_mm'] for row in exposed)
    report['limitations'].append('Float32-contact chords are a separate print-scale seam diagnostic, not a claim that distinct exact surfaces have been boolean fused.')


def main():
    started = time.monotonic()
    source = json.loads(AUDIT.read_text())
    scale = source['millimetres_per_unit']
    scene = trimesh.load_scene(source['input'], process=False, maintain_order=True)
    rows = []
    for name in ['tripo_part_6', 'tripo_part_7']:
        transform, geometry = scene.graph[name]
        mesh = scene.geometry[geometry].copy()
        mesh.apply_transform(transform)
        for sample in source['parts'][name]['sampled_wall_chords']['thin_samples']:
            triangle = np.asarray(mesh.vertices)[np.asarray(mesh.faces)[sample['face']]]
            normal = np.cross(triangle[1] - triangle[0], triangle[2] - triangle[0])
            normal /= np.linalg.norm(normal)
            centre = np.asarray(sample['position_mm']) / scale
            rows.append({'source_node': name, 'face': sample['face'], 'position_mm': sample['position_mm'], 'outward_normal': normal.tolist(), 'original_segment_chord_mm': sample['chord_mm'], 'recorded_centroid_error_mm': float(np.linalg.norm(centre - triangle.mean(axis=0)) * scale), 'inside_plus_normal_nodes': [], 'inside_minus_normal_nodes': [], 'per_node_ray_intervals_relative_to_face_mm': {}})
        del mesh
    assert len(rows) == 10
    points = np.asarray([q['position_mm'] for q in rows]) / scale
    normals = np.asarray([q['outward_normal'] for q in rows])
    offset_mm = 0.01
    offset = offset_mm / scale
    distance = 2 * float(np.linalg.norm(np.asarray(source['source_extents'])))
    origins = points + normals * distance
    directions = -normals
    probes = np.concatenate((points + normals * offset, points - normals * offset))
    epsilon = max(float(np.linalg.norm(np.asarray(source['source_extents']))) * 1e-9, 1e-12)
    report = {'scope': 'Only the ten pre-existing flagged samples from capped nodes6 and7; no new broad sampling.', 'input': source['input'], 'input_modified': False, 'physical_scale_basis': source['physical_scale_basis'], 'millimetres_per_unit': scale, 'normal_offset_mm': offset_mm, 'method': 'One node at a time: exact-coordinate welding, normal-offset containment, all ray-surface hits, interval midpoint containment, and interval union across all eleven closed volumes.', 'complete': False, 'processed_nodes': [], 'samples': rows, 'limitations': ['This is a directional chord check at ten fixed points, not a global minimum-wall or print-strength certification.', 'No boolean union, remesh, smoothing, or mechanical modification is performed.']}
    for name in sorted(scene.graph.nodes_geometry):
        transform, geometry = scene.graph[name]
        raw = scene.geometry[geometry].copy()
        raw.apply_transform(transform)
        mesh = geometry_mesh(raw)
        del raw
        containment = mesh.contains(probes)
        for i, row in enumerate(rows):
            if containment[i]:
                row['inside_plus_normal_nodes'].append(name)
            if containment[i + len(rows)]:
                row['inside_minus_normal_nodes'].append(name)
        locations, ray_ids, _ = mesh.ray.intersects_location(origins, directions, multiple_hits=True)
        distances = np.einsum('ij,ij->i', locations - origins[ray_ids], directions[ray_ids]) if len(locations) else np.array([])
        interval_pairs, midpoints = [], []
        for i in range(len(rows)):
            hits = np.sort(distances[ray_ids == i])
            if len(hits):
                hits = hits[np.r_[True, np.diff(hits) > epsilon]]
            for a, b in zip(hits[:-1], hits[1:]):
                if b - a <= epsilon:
                    continue
                interval_pairs.append((i, float(a), float(b)))
                midpoints.append(origins[i] + directions[i] * ((a + b) / 2))
        inside_intervals = mesh.contains(np.asarray(midpoints)) if midpoints else []
        for (i, a, b), inside in zip(interval_pairs, inside_intervals):
            if inside:
                rows[i]['per_node_ray_intervals_relative_to_face_mm'].setdefault(name, []).append([(a - distance) * scale, (b - distance) * scale])
        report['processed_nodes'].append(name)
        report['elapsed_seconds'] = time.monotonic() - started
        OUTPUT.write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({'processed': name, 'nodes_done': len(report['processed_nodes']), 'elapsed_seconds': report['elapsed_seconds']}), flush=True)
        del mesh, locations, ray_ids, distances
        gc.collect()
    for row in rows:
        own = row['source_node']
        plus_other = [name for name in row['inside_plus_normal_nodes'] if name != own]
        minus_other = [name for name in row['inside_minus_normal_nodes'] if name != own]
        row['other_nodes_at_plus_normal'] = plus_other
        row['other_nodes_at_minus_normal'] = minus_other
        row['exposure_at_offset'] = 'buried_or_internal_assembled_face' if row['inside_plus_normal_nodes'] else ('exposed_assembled_outer_face' if row['inside_minus_normal_nodes'] else 'ambiguous_no_inside_minus_probe')
        intervals = sorted(interval for value in row['per_node_ray_intervals_relative_to_face_mm'].values() for interval in value)
        merged = []
        for a, b in intervals:
            if merged and a <= merged[-1][1] + epsilon * scale:
                merged[-1][1] = max(merged[-1][1], b)
            else:
                merged.append([a, b])
        row['assembled_union_intervals_relative_to_face_mm'] = merged
        containing = next((interval for interval in merged if interval[0] - epsilon * scale <= offset_mm <= interval[1] + epsilon * scale), None)
        row['assembled_union_chord_mm'] = containing[1] - containing[0] if containing else None
        row['assembled_inward_depth_from_face_mm'] = containing[1] if containing else None
        row['assembled_chord_below_1_2_mm'] = bool(containing and containing[1] - containing[0] < 1.2)
    report['complete'] = len(report['processed_nodes']) == source['node_count']
    report['summary'] = {'sample_count': len(rows), 'exposed_at_offset': sum(row['exposure_at_offset'] == 'exposed_assembled_outer_face' for row in rows), 'buried_or_internal_at_offset': sum(row['exposure_at_offset'] == 'buried_or_internal_assembled_face' for row in rows), 'ambiguous': sum(row['exposure_at_offset'].startswith('ambiguous') for row in rows), 'exposed_samples_below_1_2_mm_assembled_chord': sum(row['exposure_at_offset'] == 'exposed_assembled_outer_face' and row['assembled_chord_below_1_2_mm'] for row in rows)}
    quantum_mm = float(np.max(np.abs(np.spacing(np.asarray(scene.bounds, dtype=np.float32))))) * scale
    add_source_precision_contact_diagnostic(report, quantum_mm)
    report['elapsed_seconds'] = time.monotonic() - started
    OUTPUT.write_text(json.dumps(report, indent=2) + '\n')
    for row in rows:
        print(json.dumps({k: row[k] for k in ['source_node', 'face', 'exposure_at_offset', 'original_segment_chord_mm', 'assembled_union_chord_mm', 'other_nodes_at_plus_normal']}), flush=True)
    print(json.dumps(report['summary']), flush=True)


if __name__ == '__main__':
    main()
