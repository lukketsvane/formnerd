import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import time

import cadquery as cq


def verify_baffle(shapes, root=None, tolerance=1e-4):
    moving = ['06_optical_baffle', '12_lens_blank', '13_lens_blank_retainer', '17_camera_saddle', '18_camera_clamp']
    removed = ['03_rear_cover', '04_esp32_carrier', '05_board_clamp']
    fixed = [name for name in shapes if name not in set(moving + removed)]
    result = {
        'name': 'baffle_removal',
        'check_scope': 'continuous_baffle_translation_swept_envelope',
        'moving_parts': moving,
        'baffle_parts': moving,
        'previously_removed_parts': removed,
        'fixed_parts': fixed,
        'direction': [0, -1, 0],
        'travel_mm': 50.0,
        'volume_tolerance_mm3': tolerance,
        'containment_records': [],
        'fixed_part_results': [],
        'source_step_files': [],
        'blockers': [],
        'sampled_path_clear': False,
        'continuous_envelope_clear': False,
        'scope': 'Exact native BRep cuts prove initial optical-part containment in a coaxial cylinder extending through the full 50 mm negative-Y translation. Exact native BRep common volumes test this bounding swept cylinder against every remaining fixed part. This certifies continuous positive-volume clearance within the stated tolerance; zero-volume contact is allowed. Input shapes must be valid solids and fasteners must be removed. Physical hardware fit is not verified.',
    }
    if not math.isfinite(tolerance) or tolerance < 0:
        result['blockers'].append({'kind': 'invalid_volume_tolerance', 'value': str(tolerance)})
        return result
    missing = [name for name in moving if name not in shapes]
    if missing:
        result['blockers'].append({'kind': 'missing_optical_parts', 'parts': missing})
        return result
    if root is not None:
        root = Path(root)
        try:
            manifest = json.loads((root / 'cad/assembly_manifest.json').read_text())
            entries = manifest['parts'] if isinstance(manifest, dict) else manifest
            sources = {entry['name']: root / Path(entry['file']).with_suffix('.step') for entry in entries}
            for name in moving + fixed:
                path = sources[name]
                result['source_step_files'].append({'name': name, 'file': str(path.relative_to(root)), 'sha256': sha256(path.read_bytes()).hexdigest()})
        except Exception as error:
            result['blockers'].append({'kind': 'source_hash_record_failed', 'error': str(error)})
    try:
        ymin = min(shapes[name].BoundingBox().ymin for name in moving) - result['travel_mm']
        ymax = -11.0
        if ymin >= ymax:
            raise ValueError('The swept cylinder must have positive Y length')
        envelope = cq.Solid.makeCylinder(20.25, ymax - ymin, cq.Vector(31.0, ymin, 43.0), cq.Vector(0, 1, 0))
        bb = envelope.BoundingBox()
        valid = bool(envelope.isValid())
        result['envelope'] = {'shape': 'coaxial_cylinder', 'axis_point_xz_mm': [31.0, 43.0], 'radius_mm': 20.25, 'y_min_mm': ymin, 'y_max_mm': ymax, 'bounds_mm': [bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax], 'valid': valid}
        if not valid:
            raise ValueError('The swept cylinder is invalid')
    except Exception as error:
        result['blockers'].append({'kind': 'swept_envelope_failed', 'error': str(error)})
        return result
    for name in moving:
        started = time.monotonic()
        row = {'part': name, 'method': 'BRep_cut', 'contained': False}
        try:
            outside = shapes[name].cut(envelope)
            value = float(sum(abs(solid.Volume()) for solid in outside.Solids()))
            row.update({'outside_envelope_volume_mm3': value, 'contained': math.isfinite(value) and value <= tolerance})
            if not row['contained']:
                result['blockers'].append({'kind': 'outside_swept_envelope', 'moving_part': name, 'volume_mm3': value})
        except Exception as error:
            row['error'] = str(error)
            result['blockers'].append({'kind': 'containment_check_failed', 'moving_part': name, 'error': str(error)})
        row['elapsed_seconds'] = time.monotonic() - started
        result['containment_records'].append(row)
        print(json.dumps({'motion': result['name'], 'containment': row}), flush=True)
    for name in fixed:
        started = time.monotonic()
        row = {'fixed_part': name, 'method': 'BRep_common', 'clear': False}
        try:
            common = envelope.intersect(shapes[name])
            value = float(sum(abs(solid.Volume()) for solid in common.Solids()))
            row.update({'intersection_volume_mm3': value, 'clear': math.isfinite(value) and value <= tolerance})
            if not row['clear']:
                result['blockers'].append({'kind': 'swept_envelope_intersection', 'fixed_part': name, 'volume_mm3': value})
        except Exception as error:
            row['error'] = str(error)
            result['blockers'].append({'kind': 'swept_intersection_check_failed', 'fixed_part': name, 'error': str(error)})
        row['elapsed_seconds'] = time.monotonic() - started
        result['fixed_part_results'].append(row)
        print(json.dumps({'motion': result['name'], 'fixed_intersection': row}), flush=True)
    result['pair_checks_completed'] = len(result['containment_records']) + len(result['fixed_part_results'])
    result['proof'] = 'Each initial moving part lies inside the cylinder. Its Y minimum is the minimum initial part Y minus 50 mm, and its Y maximum is -11 mm. Any negative-Y translation from 0 through 50 mm preserves radial containment and remains within these Y limits. Cylinder clearance therefore implies clearance for every translated optical part throughout the continuous path.'
    passed = not result['blockers'] and all(row['contained'] for row in result['containment_records']) and all(row['clear'] for row in result['fixed_part_results'])
    result['sampled_path_clear'] = passed
    result['continuous_envelope_clear'] = passed
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--volume-tolerance', type=float, default=1e-4)
    args = parser.parse_args()
    root = args.root.resolve()
    manifest = json.loads((root / 'cad/assembly_manifest.json').read_text())
    entries = manifest['parts'] if isinstance(manifest, dict) else manifest
    shapes = {}
    inputs = []
    for entry in entries:
        path = root / Path(entry['file']).with_suffix('.step')
        shape = cq.importers.importStep(str(path)).val()
        shapes[entry['name']] = shape
        row = {'name': entry['name'], 'step_valid': bool(shape.isValid()), 'solid_count': len(shape.Solids())}
        inputs.append(row)
        print(json.dumps(row), flush=True)
    result = verify_baffle(shapes, root, args.volume_tolerance)
    result['input_parts'] = inputs
    invalid = [row['name'] for row in inputs if not row['step_valid'] or row['solid_count'] != 1]
    if invalid:
        result['blockers'].append({'kind': 'invalid_input_solids', 'parts': invalid})
        result['sampled_path_clear'] = False
        result['continuous_envelope_clear'] = False
    result['geometry_pass'] = result['continuous_envelope_clear']
    result['physical_hardware_fit_verified'] = False
    result['release_status'] = 'CONTINUOUS_ENVELOPE_GEOMETRY_ONLY' if result['geometry_pass'] else 'DIGITAL_GEOMETRY_CHECKS_FAILED'
    destination = root / 'cad/verification_baffle_removal.json'
    destination.write_text(json.dumps(result, indent=2))
    print(json.dumps({'geometry_pass': result['geometry_pass'], 'report': str(destination)}), flush=True)
    return 0 if result['geometry_pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
