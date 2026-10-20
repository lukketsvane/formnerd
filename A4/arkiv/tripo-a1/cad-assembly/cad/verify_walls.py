import hashlib
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, '/tmp/entropi-mesh-deps')

import manifold3d as md
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
CX, CZ = -31.7, -8.4


def load(name):
    path = ROOT / 'parts' / (name + '.npz')
    data = np.load(path)
    solid = md.Manifold(md.Mesh64(np.ascontiguousarray(data['vertices'], dtype=np.float64), np.ascontiguousarray(data['faces'], dtype=np.uint64)))
    if str(solid.status()) != 'Error.NoError':
        raise ValueError((name, str(solid.status())))
    return solid, hashlib.sha256(path.read_bytes()).hexdigest()


def intervals(solid, origin, endpoint):
    origin, endpoint = np.asarray(origin, dtype=float), np.asarray(endpoint, dtype=float)
    length = float(np.linalg.norm(endpoint - origin))
    hits = solid.ray_cast(origin, endpoint)
    distances = []
    for hit in hits:
        value = float(hit.distance) * length
        if not distances or abs(value - distances[-1]) > 1e-7:
            distances.append(value)
    if len(distances) % 2:
        distances.append(length)
    return [[distances[i], distances[i + 1]] for i in range(0, len(distances), 2)]


def merge_contacts(occupied, tolerance=1e-5):
    merged = []
    for start, end in occupied:
        if merged and start - merged[-1][1] <= tolerance:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged


def main():
    shell, shell_sha = load('01_outer_shell')
    bezel, bezel_sha = load('04_optical_bezel')
    rear, rear_sha = load('02_native_rear_cover')
    ring = []
    for y in [18.0, 24.7, 26.8, 28.7]:
        row = {'y_mm': y, 'probes': []}
        for degrees in range(0, 360, 10):
            radians = math.radians(degrees)
            endpoint = [CX + 55 * math.cos(radians), y, CZ + 55 * math.sin(radians)]
            origin = [CX, y, CZ]
            native = intervals(shell, origin, endpoint)
            insert = intervals(bezel, origin, endpoint)
            near_native = [pair for pair in native if pair[0] < 32 and pair[1] > 14]
            near_insert = [pair for pair in insert if pair[0] < 32 and pair[1] > 14]
            native_contact = merge_contacts(near_native)
            excluded = y > 26 and min(degrees, abs(180 - degrees), 360 - degrees) <= 12
            row['probes'].append({
                'azimuth_deg': degrees,
                'excluded_native_wall_entry_slot_sector': excluded,
                'native_radial_intervals_mm': near_native,
                'native_contact_merged_radial_intervals_mm': native_contact,
                'bezel_radial_intervals_mm': near_insert,
                'native_first_chord_mm': near_native[0][1] - near_native[0][0] if near_native else None,
                'native_first_contact_merged_chord_mm': native_contact[0][1] - native_contact[0][0] if native_contact else None,
                'bezel_first_chord_mm': near_insert[0][1] - near_insert[0][0] if near_insert else None,
            })
        expected = [item for item in row['probes'] if not item['excluded_native_wall_entry_slot_sector']]
        positive = [item['native_first_chord_mm'] for item in expected if item['native_first_chord_mm'] is not None]
        row['native_min_first_radial_chord_mm_excluding_entry_slots'] = min(positive) if positive else None
        contact_values = [item['native_first_contact_merged_chord_mm'] for item in expected if item['native_first_contact_merged_chord_mm'] is not None]
        row['native_min_first_contact_merged_radial_chord_mm_excluding_entry_slots'] = min(contact_values) if contact_values else None
        row['native_zero_material_azimuths_deg_excluding_entry_slots'] = [item['azimuth_deg'] for item in expected if item['native_first_chord_mm'] is None]
        bezel_values = [item['bezel_first_chord_mm'] for item in row['probes'] if item['bezel_first_chord_mm'] is not None]
        row['bezel_min_first_radial_chord_mm_when_present'] = min(bezel_values) if bezel_values else None
        ring.append(row)
        print(json.dumps({key: value for key, value in row.items() if key != 'probes'}), flush=True)
    optical = []
    origin = np.array([CX, 28.0, CZ])
    for half_angle in [0, 35, 40]:
        azimuths = [0] if half_angle == 0 else list(range(0, 360, 10))
        samples = []
        for degrees in azimuths:
            r = math.tan(math.radians(half_angle)) * 12.0
            angle = math.radians(degrees)
            endpoint = origin + np.array([r * math.cos(angle), 12.0, r * math.sin(angle)])
            shell_hits = shell.ray_cast(origin, endpoint)
            bezel_hits = bezel.ray_cast(origin, endpoint)
            hits = [
                {'part': label, 'position_mm': list(hit.position), 'normal': list(hit.normal)}
                for label, collection in [('01_outer_shell', shell_hits), ('04_optical_bezel', bezel_hits)]
                for hit in collection if hit.distance > 1e-8
            ]
            samples.append({'azimuth_deg': degrees, 'blocked': bool(hits), 'hits': hits})
        optical.append({'half_angle_deg': half_angle, 'rays': len(samples), 'blocked_rays': sum(item['blocked'] for item in samples), 'samples': samples})
        print(json.dumps({key: value for key, value in optical[-1].items() if key != 'samples'}), flush=True)
    rear_samples = []
    excluded_count = 0
    for x in np.linspace(-51.0, -12.0, 14):
        for z in np.linspace(-31.0, 23.0, 19):
            if -39.2 <= x <= -24.2 and -23.0 <= z <= -11.0:
                excluded_count += 1
                continue
            occupied = intervals(rear, [x, -50.0, z], [x, -29.0, z])
            rear_samples.append({'x_mm': float(x), 'z_mm': float(z), 'occupied_y_intervals_mm': [[pair[0] - 50.0, pair[1] - 50.0] for pair in occupied], 'total_material_chord_mm': sum(pair[1] - pair[0] for pair in occupied)})
    positive_rear = [item['total_material_chord_mm'] for item in rear_samples if item['total_material_chord_mm'] > 1e-7]
    rear_report = {
        'grid_shape_before_exclusion': [14, 19],
        'grid_extent_xz_mm': [[-51.0, -31.0], [-12.0, 23.0]],
        'ray_y_start_end_mm': [-50.0, -29.0],
        'usb_rectangle_excluded_xz_mm': [[-39.2, -23.0], [-24.2, -11.0]],
        'excluded_usb_samples': excluded_count,
        'sample_count': len(rear_samples),
        'minimum_positive_total_material_chord_mm': min(positive_rear) if positive_rear else None,
        'zero_material_samples': [item for item in rear_samples if item['total_material_chord_mm'] <= 1e-7],
        'samples': rear_samples,
    }
    report = {
        'revision': 'A1-Assembly-R01',
        'method': 'Independent Manifold64 finite ray casts on exported part meshes; 36 radial directions per station and 73 ideal optical rays',
        'source_part_npz_sha256': {'01_outer_shell': shell_sha, '04_optical_bezel': bezel_sha, '02_native_rear_cover': rear_sha},
        'optical_axis_xz_mm': [CX, CZ],
        'source_seam_contact_diagnostic': {'merge_gap_tolerance_mm': 1e-5, 'strict_intervals_preserved': True, 'interpretation': 'Contact-merged chords treat micron source seams as backing material. They do not alter the delivered mesh or replace the strict measurements.'},
        'radial_stations': ring,
        'optics_assumptions': {'lens_tip_y_mm': 28.0, 'front_test_plane_y_mm': 40.0, 'point_lens_model': True, 'actual_camera_module_measured': False, 'actual_optical_field_of_view_verified': False, 'scope': 'Only body and bezel occlusion, for the assumed nominal lens tip. Not an actual optical certificate.'},
        'optical_cones': optical,
        'rear_cover': rear_report,
        'global_minimum_wall_certificate': False,
        'physical_print_verified': False,
    }
    path = ROOT / 'verification/targeted-walls-and-optics.json'
    path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'rear_minimum_material_chord_mm': rear_report['minimum_positive_total_material_chord_mm'], 'rear_zero_material_samples': len(rear_report['zero_material_samples']), 'report': str(path)}), flush=True)


if __name__ == '__main__':
    main()
