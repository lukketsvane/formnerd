import argparse
import ast
import json
from pathlib import Path
import sys

import cadquery as cq


def bounds(shape):
    b = shape.BoundingBox()
    return [b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax]


def common_volume(a, b, bounds_a, bounds_b):
    if any(min(bounds_a[i + 1], bounds_b[i + 1]) - max(bounds_a[i], bounds_b[i]) <= 1e-7 for i in (0, 2, 4)):
        return 0.0
    return float(sum(s.Volume() for s in a.intersect(b).Solids()))


def mount_positions(source):
    names = {'front_mounts', 'rear_mounts', 'cassette_mounts'}
    positions = {}
    for node in ast.walk(ast.parse(source.read_text())):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in names:
                    positions[target.id] = ast.literal_eval(node.value)
    if set(positions) != names:
        raise ValueError('Mount positions unavailable in builder')
    return positions


def fasteners(root, p):
    mounts = mount_positions(root / 'cad/build_assembly.py')
    rows = []
    def add(name, seat, outward, length, receiver):
        rows.append({'name': name, 'seat_mm': list(seat), 'head_direction': list(outward), 'shaft_length_mm': length, 'pilot_receiver': receiver})
    for index, (x, z) in enumerate(mounts['front_mounts'], 1):
        add(f'cage_{index}', (x, p['body_front_y'] + p['wall'], z), (0, 1, 0), 10, '01_rib_cage')
    for index, (x, z) in enumerate(mounts['rear_mounts'], 1):
        add(f'cover_{index}', (x, 26.9, z), (0, 1, 0), 8, '02_chassis')
    for index, (x, z) in enumerate(mounts['cassette_mounts'], 1):
        add(f'carrier_{index}', (x, 2, z), (0, 1, 0), 10, '02_chassis')
    clamp_top = 43 + (p['esp32_board_length_nominal'] + 1.2) / 2 + 2.4
    for index, x in enumerate((16, 46), 1):
        add(f'board_clamp_{index}', (x, -4, clamp_top), (0, 0, 1), 6, '04_esp32_carrier')
    for index, x in enumerate((14, 48), 1):
        add(f'baffle_{index}', (x, -9, 43), (0, 1, 0), 8, '06_optical_baffle')
    for index, y in enumerate((p['usb_axis_y']-p['io_mount_pitch']/2,p['usb_axis_y']+p['io_mount_pitch']/2), 1):
        add(f'io_{index}', (-59.2, y, 37), (1, 0, 0), 6, '02_chassis')
    add('dial_retainer', (47, 10, 79), (0, 0, -1), 6, '09_rear_dial')
    add('optional_lens_blank', (31, -27.8, 43), (0, 1, 0), 4, '12_lens_blank')
    add('service_cover', (-70.5, 21.4, 78), (0, 1, 0), 6, '01_rib_cage')
    lens_x = p.get('optical_axis_x', 31.0)
    lens_z = p.get('optical_axis_z', 43.0)
    collar_y = p.get('camera_collar_y', -26.0)
    collar_depth = p.get('camera_collar_depth', 6.2)
    collar_radius = max(7.5, p.get('camera_barrel_diameter_assumed', 8.0) / 2 + 3.0)
    split_gap = p.get('camera_collar_split_gap', 0.6)
    base_top = lens_z - collar_radius + 0.5
    for index, side in enumerate((-1, 1), 1):
        add(f'camera_base_{index}', (lens_x + side * 10, collar_y + collar_depth + 3.1, base_top), (0, 0, 1), 6, '06_optical_baffle')
        add(f'camera_cap_{index}', (lens_x + side * 9.5, collar_y + collar_depth / 2, lens_z + split_gap / 2 + 5.0), (0, 0, 1), 8, '17_camera_saddle')
    seat_z = p.get('usb_pcb_seat_z_assumed', 33.4)
    pcb_width = p.get('usb_pcb_width_assumed', 14.0)
    pcb_thickness = p.get('usb_pcb_thickness_assumed', 1.6)
    clamp_x = -59.4 + p.get('usb_pcb_length_assumed', 16.0) + 1.8 - 3.8
    usb_y = p.get('usb_axis_y', 7.0)
    clamp_top = seat_z + pcb_thickness + 0.4 + 0.3 + 2.4
    for index, side in enumerate((-1, 1), 1):
        add(f'usb_retainer_{index}', (clamp_x, usb_y + side * (pcb_width / 2 + 2.8), clamp_top), (0, 0, 1), 6, '10_io_plate')
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--shaft-radius', type=float, default=1.0)
    parser.add_argument('--head-radius', type=float, default=1.9)
    parser.add_argument('--head-height', type=float, default=2.0)
    parser.add_argument('--volume-tolerance', type=float, default=1e-4)
    args = parser.parse_args()
    root = args.root.resolve()
    p = json.loads((root / 'cad/parameters.json').read_text())
    manifest = json.loads((root / 'cad/assembly_manifest.json').read_text())
    items = manifest['parts'] if isinstance(manifest, dict) else manifest
    parts = {item['name']: cq.importers.importStep(str(root / Path(item['file']).with_suffix('.step'))).val() for item in items}
    part_bounds = {name: bounds(shape) for name, shape in parts.items()}
    report = {
        'units': 'mm',
        'assembly_part_count': len(parts),
        'assembly_part_names': list(parts),
        'shaft_radius_mm': args.shaft_radius,
        'head_radius_mm': args.head_radius,
        'head_height_mm': args.head_height,
        'volume_tolerance_mm3': args.volume_tolerance,
        'scope': 'Static native BRep clearance of simplified M2 shaft and cylindrical head envelopes. Pilot receiver shaft interference is expected for direct plastic threading and is recorded, not counted as a collision. Heads are checked against every part. This is not a tool-access, thread-strength, screw-to-screw or physical-fit certificate.',
        'fasteners': [],
        'errors': [],
    }
    for row in fasteners(root, p):
        outward = cq.Vector(*row['head_direction'])
        seat = cq.Vector(*row['seat_mm'])
        shaft = cq.Solid.makeCylinder(args.shaft_radius, row['shaft_length_mm'], seat, outward.multiply(-1))
        head = cq.Solid.makeCylinder(args.head_radius, args.head_height, seat, outward)
        sb, hb = bounds(shaft), bounds(head)
        row['head_collisions'] = []
        row['shaft_collisions'] = []
        row['receiver_shaft_intersection_mm3'] = None
        for name, part in parts.items():
            head_volume = common_volume(head, part, hb, part_bounds[name])
            if head_volume > args.volume_tolerance:
                row['head_collisions'].append({'part': name, 'volume_mm3': head_volume})
            shaft_volume = common_volume(shaft, part, sb, part_bounds[name])
            if name == row['pilot_receiver']:
                row['receiver_shaft_intersection_mm3'] = shaft_volume
            elif shaft_volume > args.volume_tolerance:
                row['shaft_collisions'].append({'part': name, 'volume_mm3': shaft_volume})
        row['pilot_receiver_present'] = row['pilot_receiver'] in parts
        row['clearance_pass'] = not row['head_collisions'] and not row['shaft_collisions'] and row['pilot_receiver_present']
        if not row['clearance_pass']:
            report['errors'].append({'fastener': row['name'], 'head_collisions': row['head_collisions'], 'shaft_collisions': row['shaft_collisions'], 'pilot_receiver_present': row['pilot_receiver_present']})
        report['fasteners'].append(row)
        print(json.dumps(row), flush=True)
    report['fastener_count'] = len(report['fasteners'])
    report['geometry_pass'] = not report['errors']
    report['physical_fit_verified'] = False
    output = root / 'cad/fastener_verification.json'
    output.write_text(json.dumps(report, indent=2))
    print(json.dumps({'geometry_pass': report['geometry_pass'], 'errors': len(report['errors']), 'fasteners': report['fastener_count'], 'report': str(output)}), flush=True)
    return 0 if report['geometry_pass'] else 1


if __name__ == '__main__':
    sys.exit(main())
