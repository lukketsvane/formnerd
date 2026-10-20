import json
from pathlib import Path

import cadquery as cq


def box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))


def cylinder(radius, z0, z1, x=45.0, y=8.4):
    return cq.Solid.makeCylinder(radius, z1 - z0, cq.Vector(x, y, z0))


def build():
    stem = cylinder(2.25, 30.3, 36.6).fuse(cylinder(3.8, 31.6, 32.8)).clean()
    floor = box(37.8, 52.2, -25.7, 16.8, 24.0, 25.8)
    left = box(37.8, 40.0, -1.0, 12.8, 25.8, 35.2)
    right = box(50.0, 52.2, -1.0, 12.8, 25.8, 35.2)
    rear = box(40.0, 50.0, -1.0, 1.4, 25.8, 35.2)
    fork = box(37.8, 52.2, -1.0, 12.8, 33.2, 35.2)
    notch = box(42.4, 47.6, 8.4, 18.0, 32.9, 35.5).fuse(cylinder(2.6, 32.9, 35.5))
    fork = fork.cut(notch)
    pieces = [floor, left, right, rear, fork]
    pieces.extend([
        box(35.7, 37.8, -25.7, 16.8, 26.0, 27.5),
        box(52.2, 54.3, -25.7, 16.8, 26.0, 27.5),
        box(40.7, 41.7, 2.5, 12.8, 25.8, 30.4),
        box(48.3, 49.3, 2.5, 12.8, 25.8, 30.4),
        box(40.4, 41.8, 5.1, 11.7, 25.8, 27.0),
        box(48.2, 49.6, 5.1, 11.7, 25.8, 27.0),
        box(41.8, 48.2, 3.8, 5.1, 25.8, 27.0),
    ])
    retainer = pieces[0]
    for part in pieces[1:]:
        retainer = retainer.fuse(part)
    retainer = retainer.cut(box(40.8, 42.2, 5.2, 11.6, 23.8, 25.8))
    retainer = retainer.cut(box(47.8, 49.2, 5.2, 11.6, 23.8, 25.8)).clean()
    body_cut = box(37.5, 52.5, -42.0, 17.1, 23.7, 28.0)
    body_cut = body_cut.fuse(box(37.5, 52.5, -42.0, 13.1, 28.0, 35.5))
    body_cut = body_cut.fuse(box(35.4, 37.5, -42.0, 17.1, 25.7, 27.8))
    body_cut = body_cut.fuse(box(52.5, 54.6, -42.0, 17.1, 25.7, 27.8))
    body_cut = body_cut.fuse(cylinder(2.65, 29.0, 37.0))
    body_cut = body_cut.fuse(cylinder(4.15, 30.1, 33.1)).clean()
    positions = [0.0, 0.3, 0.6, 0.9, 1.2]
    movement = []
    for travel in positions:
        overlap = stem.translate((0.0, 0.0, -travel)).intersect(retainer).Volume()
        movement.append({'travel_mm': travel, 'overlap_mm3': overlap})
    insertion = []
    for offset in [-45.0, -40.0, -30.0, -20.0, -10.0, -5.0, 0.0]:
        overlap = stem.intersect(retainer.translate((0.0, offset, 0.0))).Volume()
        insertion.append({'retainer_y_offset_mm': offset, 'overlap_mm3': overlap})
    clearance_solid = body_cut.intersect(retainer)
    cassette_outside_cut = retainer.cut(body_cut).Volume()
    metadata = {
        'units': 'mm',
        'button_centre_xy': [45.0, 8.4],
        'root_native_cap_attachment': {
            'stem_top_z_mm': 36.6,
            'native_cap_cut_z_mm': 36.0,
            'nominal_overlap_mm': 0.6,
            'native_cap_not_included': True,
            'native_cap_swept_clearance_must_be_cut_by_root': True,
        },
        'stem': {
            'diameter_mm': 4.5,
            'flange_diameter_mm': 7.6,
            'flange_z_mm': [31.6, 32.8],
            'tip_z_mm_at_rest': 30.3,
            'maximum_downward_travel_mm': 1.2,
            'tip_z_mm_at_full_travel': 29.1,
            'capture_fork_bottom_z_mm': 33.2,
            'upward_flange_gap_mm': 0.4,
            'hard_stop_top_z_mm': 30.4,
            'hard_stop_contacts_flange_at_full_travel': True,
        },
        'retainer': {
            'insertion_axis': '+Y from rear -Y',
            'fork_open_direction': '+Y',
            'bounds_mm': [35.7, -25.7, 24.0, 54.3, 16.8, 35.2],
            'central_channel_mm': [37.5, -42.0, 23.7, 52.5, 17.1, 35.5],
            'side_rail_grooves_mm': [
                [35.4, -42.0, 25.7, 37.5, 17.1, 27.8],
                [52.5, -42.0, 25.7, 54.6, 17.1, 27.8],
            ],
            'nominal_clearance_each_side_mm': 0.3,
            'retention': 'Root rear cover needs an internal stop near Y=-26.0; the module is not independently latched.',
            'body_cut_application': 'Subtract from the main body after the native rear cap is split. Do not subtract this entry channel from the removable rear cap.',
            'lead_slot_width_mm': 1.4,
        },
        'switch_interface': {
            'status': 'UNCONFIRMED nominal 6x6 tactile switch only',
            'nominal_switch_body_xy_mm': [6.0, 6.0],
            'pocket_xy_mm': [6.4, 6.6],
            'pocket_xy_bounds_mm': [41.8, 5.1, 48.2, 11.7],
            'support_floor_z_mm': 25.8,
            'actual_switch_height_pinout_and_travel_verified': False,
            'actuation_and_overtravel_verified': False,
            'return_mechanism_verified': False,
            'return_note': 'A measured return mechanism or verified switch-return interface remains required. No spring is assumed owned.',
        },
        'verification': {
            'stem_valid': stem.isValid(),
            'stem_solids': len(stem.Solids()),
            'retainer_valid': retainer.isValid(),
            'retainer_solids': len(retainer.Solids()),
            'body_cut_valid': body_cut.isValid(),
            'body_cut_solids': len(body_cut.Solids()),
            'movement_checks': movement,
            'rear_insertion_checks': insertion,
            'cassette_outside_cut_mm3': cassette_outside_cut,
            'cassette_inside_cut_mm3': clearance_solid.Volume(),
            'physical_print_tested': False,
        },
    }
    assert stem.isValid() and len(stem.Solids()) == 1
    assert retainer.isValid() and len(retainer.Solids()) == 1
    assert body_cut.isValid() and len(body_cut.Solids()) == 1
    assert max(item['overlap_mm3'] for item in movement) < 1e-7
    assert max(item['overlap_mm3'] for item in insertion) < 1e-7
    assert cassette_outside_cut < 1e-7
    return {'stem': stem, 'retainer': retainer, 'body_cut': body_cut, 'metadata': metadata}


if __name__ == '__main__':
    result = build()
    path = Path(__file__).with_name('shutter_module_diagnostic.json')
    path.write_text(json.dumps(result['metadata'], indent=2) + '\n')
    print(json.dumps(result['metadata']['verification'], indent=2))
