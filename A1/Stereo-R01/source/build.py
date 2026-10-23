import json
from pathlib import Path

import cadquery as cq
import manifold3d as mf
import numpy as np
import trimesh
from scipy.ndimage import gaussian_filter

from mesh_fields import boks, nivaa, sylinder, til_mf, til_tm

ROOT = Path(__file__).resolve().parents[1]
CAD = ROOT / 'cad'
CAD.mkdir(exist_ok=True)
PARTS = {}
SOLIDS = {}
BREPS = {}
HARDWARE = []
FRONT_CUTS = []
REAR_CUTS = []
REMOVED = []


def box(a, b):
    d = np.subtract(b, a)
    return cq.Workplane('XY').box(*d, centered=False).translate(a).val()


def cyl(center, radius, length, axis='y'):
    direction = {'x': (1, 0, 0), 'y': (0, 1, 0), 'z': (0, 0, 1)}[axis]
    p = np.asarray(center) - np.asarray(direction) * length / 2
    return cq.Solid.makeCylinder(radius, length, cq.Vector(*p), cq.Vector(*direction))


def hex_m(center, af, length, axis='y', angle=0):
    c = mf.Manifold.cylinder(length, af / np.sqrt(3), af / np.sqrt(3), 6)
    if axis == 'y':
        c = c.rotate((-90, 0, 0))
        c = c.rotate((0, angle, 0))
    return c.translate(np.asarray(center) - np.asarray((0, length / 2, 0) if axis == 'y' else (0, 0, length / 2)))


def cq_m(shape):
    vertices, faces = shape.tessellate(0.06, 0.12)
    tm = trimesh.Trimesh([v.toTuple() for v in vertices], faces, process=True)
    return til_mf(tm)


def add(pid, name, solid, kind='analytic', color='#c7c9cc', explode=(0, 0, 0), print_note='', quantity=1):
    if kind == 'analytic':
        BREPS[pid] = solid
        cq.exporters.export(solid, str(CAD / f'{pid}.step'))
        m = cq_m(solid)
    else:
        m = solid
        pieces = m.decompose()
        keep = [q for q in pieces if q.volume() > 0.5]
        removed = [q for q in pieces if q.volume() <= 0.5]
        if removed:
            REMOVED.append({'part': pid, 'count': len(removed), 'volume_mm3': sum(q.volume() for q in removed)})
            m = mf.Manifold.batch_boolean(keep, mf.OpType.Add)
    m = m.simplify(0.0001)
    mesh = til_tm(m)
    mesh.export(CAD / f'{pid}.stl')
    roundtrip = trimesh.load(CAD / f'{pid}.stl', force='mesh', process=True)
    weld = None
    if not roundtrip.is_watertight:
        before_faces, before_volume = len(roundtrip.faces), roundtrip.volume
        roundtrip.merge_vertices(digits_vertex=4)
        roundtrip.process(validate=True)
        weld = {'precision_mm': 0.0001, 'faces_removed': before_faces - len(roundtrip.faces), 'volume_delta_mm3': float(roundtrip.volume - before_volume)}
        if abs(weld['volume_delta_mm3']) > 0.1:
            raise RuntimeError(f'{pid} export welding exceeds volume tolerance')
        roundtrip.export(CAD / f'{pid}.stl')
        roundtrip = trimesh.load(CAD / f'{pid}.stl', force='mesh', process=True)
    if not roundtrip.is_watertight or len(roundtrip.split(only_watertight=False)) != 1:
        raise RuntimeError(f'{pid} STL roundtrip topology failed')
    mesh = roundtrip
    m = til_mf(mesh)
    SOLIDS[pid] = m
    PARTS[pid] = {'id': pid, 'name': name, 'quantity': quantity, 'geometry_type': kind,
                  'stl': f'cad/{pid}.stl', 'step': f'cad/{pid}.step' if kind == 'analytic' else None,
                  'color': color, 'assembly_transform': np.eye(4).tolist(), 'exploded_translation': list(explode),
                  'print_orientation': print_note, 'bounds_mm': mesh.bounds.tolist(), 'volume_mm3': float(mesh.volume),
                  'watertight': bool(mesh.is_watertight), 'connected_components': len(mesh.split(only_watertight=False)),
                  'stl_roundtrip_watertight': bool(roundtrip.is_watertight), 'stl_roundtrip_components': len(roundtrip.split(only_watertight=False)),
                  'export_vertex_weld': weld,
                  'brep_valid': bool(solid.isValid()) if kind == 'analytic' else None}
    print(pid, name, len(mesh.faces), mesh.volume, flush=True)
    return m


def screw(pid, x, z, head_y, length, name):
    shaft = cyl((x, head_y - length / 2, z), 1.5, length)
    head = cyl((x, head_y + 1.5, z), 2.75, 3)
    cut = cyl((x, head_y + 2.5, z), 1.2, 1.1)
    shape = shaft.fuse(head).cut(cut)
    path = CAD / f'{pid}.stl'
    cq.exporters.export(shape, str(path))
    HARDWARE.append({'id': pid, 'name': name, 'type': 'purchased', 'stl': f'cad/{pid}.stl', 'quantity': 1,
                     'color': '#74787d', 'assembly_transform': np.eye(4).tolist(),
                     'exploded_translation': [0, 65, 0], 'thread_geometry': 'nominal smooth envelope, not modelled thread'})


def nut(pid, x, z, middle_y, angle=0):
    m = hex_m((x, middle_y, z), 5.5, 2.4, angle=angle) - sylinder((x, middle_y, z), 1.25, 3, 'y')
    til_tm(m).export(CAD / f'{pid}.stl')
    HARDWARE.append({'id': pid, 'name': 'M3 hex nut', 'type': 'purchased', 'stl': f'cad/{pid}.stl', 'quantity': 1,
                     'color': '#74787d', 'assembly_transform': np.eye(4).tolist(), 'exploded_translation': [0, -4, 0]})


data = np.load(ROOT / 'reference/shape-field.npz')
field = gaussian_filter(data['field'], sigma=1.5)
outer = nivaa(field, data['origin'], 0, pitch=float(data['pitch'])).simplify(0.025)
outer_mesh = til_tm(outer)
outer_mesh.export(CAD / 'outer-smoothed.glb')
inner = nivaa(field, data['origin'], 2.6, pitch=float(data['pitch'])).simplify(0.025)
skin = outer - inner
front = skin ^ boks((-100, -100, -10), (100, 12, 120))
rear = skin ^ boks((-100, 12.3, -10), (100, 100, 120))
closure = [(-58, 8), (57, 8), (-60, 50), (50, 74)]

for i, (x, z) in enumerate(closure, 1):
    post = sylinder((x, 7.5, z), 7, 9, 'y') ^ outer
    front = front + post
    slot_z = (z, z + 15) if z < 40 else (z - 15, z)
    slot = boks((x - 2.95, 7.1, slot_z[0]), (x + 2.95, 9.9, slot_z[1]))
    FRONT_CUTS.extend([sylinder((x, 7, z), 1.75, 12, 'y'), hex_m((x, 8.5, z), 5.9, 2.8, angle=30), slot])
    tail = sylinder((x, 23.65, z), 7, 22.7, 'y') ^ outer
    tail = tail - sylinder((x, 23, z), 1.75, 30, 'y') - sylinder((x, 39, z), 3.25, 23.4, 'y')
    rear = rear + tail
    REAR_CUTS.extend([sylinder((x, 23, z), 1.75, 30, 'y'), sylinder((x, 39, z), 3.25, 23.4, 'y')])
    screw(f'H{i:02}', x, z, 27.3, 25, 'M3 × 25 socket screw')
    nut(f'N{i:02}', x, z, 8.5, angle=30)

lens_x = [-6.0, 48.0]
for x in lens_x:
    socket = sylinder((x, -22, 48), 15, 16, 'y') ^ outer
    socket = socket - sylinder((x, -30, 48), 10.95, 30, 'y') - sylinder((x, -8.7, 48), 13.35, 20, 'y')
    front = (front + socket) - sylinder((x, -40, 48), 10.95, 44, 'y')
    FRONT_CUTS.extend([sylinder((x, -40, 48), 10.95, 44, 'y'), sylinder((x, -8.7, 48), 13.35, 20, 'y')])
    collar = cyl((x, -26.35, 48), 10.6, 15.9).fuse(cyl((x, -17.2, 48), 13, 2.4))
    collar = collar.cut(cyl((x, -25, 48), 5, 24))
    add('P04' if x < 0 else 'P05', 'Lens collar left' if x < 0 else 'Lens collar right', collar,
        color='#34383c', explode=(0, -25, 0), print_note='Optical axis vertical; flange on plate. Bore is a provisional Ø10 opening, not a verified camera mount.')

carrier = None
for ix, x in enumerate([-6.0, 44.0]):
    frame = box((x - 17, 7, 18), (x - 13, 14, 64))
    frame = frame.fuse(box((x + 13, 7, 18), (x + 17, 14, 64)))
    frame = frame.fuse(box((x - 17, 7, 18), (x + 17, 14, 21)))
    frame = frame.cut(box((x - 13.8, 10.4, 20.8), (x + 13.8, 12.6, 68)))
    for xx in [x - 15, x + 15]:
        frame = frame.fuse(cyl((xx, 10.5, 64), 4, 7))
        frame = frame.cut(cyl((xx, 10.5, 64), 1.75, 12))
        shape_n = cq.Workplane('XZ', origin=(xx, 7, 64)).polygon(6, 5.9 / np.cos(np.pi / 6)).extrude(-2.8).val()
        frame = frame.cut(shape_n)
    lx = lens_x[ix]
    ring = cyl((lx, -4.2, 48), 14.5, 23).cut(cyl((lx, -4.2, 48), 10, 25))
    ring = ring.fuse(box((x - 17, 5, 34), (x - 12, 7.3, 62)))
    ring = ring.fuse(box((x + 12, 5, 34), (x + 17, 7.3, 62)))
    frame = frame.fuse(ring)
    carrier = frame if carrier is None else carrier.fuse(frame)
    cap = box((x - 19, 14.3, 61.5), (x + 19, 17.3, 66.5))
    cap = cap.fuse(box((x - 13.5, 10.1, 61.5), (x + 13.5, 14.5, 62.8)))
    for xx in [x - 15, x + 15]:
        cap = cap.cut(cyl((xx, 15.8, 64), 1.75, 5))
        hi = 7 + ix * 2 + ([x - 15, x + 15].index(xx))
        screw(f'H{hi:02}', xx, 64, 17.3, 12, 'M3 × 12 socket screw')
        nut(f'N{hi:02}', xx, 64, 8.4)
    add('P08' if x < 0 else 'P09', 'PCB top keeper left' if x < 0 else 'PCB top keeper right', cap,
        color='#b7bbc0', explode=(0, 32, 20), print_note='Flat face on plate. Keeper retains nominal PCB top edge; check populated-board clearance before fitting.')

carrier = carrier.fuse(box((8, 7, 19), (35, 10.2, 24)))
carrier = carrier.fuse(box((8, 7, 58), (35, 10.2, 63)))
for i, z in enumerate([16, 66], 5):
    x = 21
    post = sylinder((x, -11.5, z), 5.5, 37, 'y') ^ outer
    nutp = hex_m((x, 3.8, z), 5.9, 2.8)
    slot = boks((x, 2.4, z - 3), (x + 9, 5.2, z + 3))
    front = front + post
    FRONT_CUTS.extend([sylinder((x, 2.5, z), 1.75, 10, 'y'), nutp, slot])
    carrier = carrier.fuse(cyl((x, 8.6, z), 5.5, 3.2)).cut(cyl((x, 8.6, z), 1.75, 8))
    screw(f'H{i:02}', x, z, 10.2, 12, 'M3 × 12 socket screw')
    nut(f'N{i:02}', x, z, 3.8)

for x in [-6.0, 44.0]:
    for xx in [x - 15, x + 15]:
        carrier = carrier.cut(cyl((xx, 10.5, 64), 1.75, 12))
        carrier = carrier.cut(cq.Workplane('XZ', origin=(xx, 4.5, 64)).polygon(6, 5.9 / np.cos(np.pi / 6)).extrude(-5.3).val())
    carrier = carrier.cut(box((x - 13.8, 10.4, 20.8), (x + 13.8, 12.6, 80)))
for pid in ['P08', 'P09']:
    carrier = carrier.cut(BREPS[pid])

button_x, button_y = -49.5, -6.6
front = front - sylinder((button_x, button_y, 83.75), 8.3, 32.5, 'z')
front = front - boks((button_x - 10, button_y - 5.8, 65), (button_x + 10, button_y + 5.8, 70))
cap_mesh = outer ^ sylinder((button_x, button_y, 82.15), 7.8, 25.7, 'z')
cap_mesh = cap_mesh + boks((button_x - 9.7, button_y - 5.5, 67.8), (button_x + 9.7, button_y + 5.5, 69.6))
cap_mesh = cap_mesh + sylinder((button_x, button_y, 70.5), 7.8, 2.4, 'z')
cap_mesh = cap_mesh ^ (boks((-100, -100, -10), (100, 100, 69.6)) + sylinder((button_x, button_y, 70), 7, 60, 'z'))
guard = nivaa(field, data['origin'], 1.6, pitch=float(data['pitch'])).simplify(0.025)
for dy in np.arange(0, 28.01, 0.25):
    front = front - (cap_mesh.translate((0, dy, -2.8)) ^ guard)
for dz in np.arange(-2.8, 0.01, 0.1):
    front = front - (cap_mesh.translate((0, 0, dz)) ^ guard)
retainer = box((-61, -13.6, 65.3), (-38, 0.4, 67.5))
retainer = retainer.fuse(box((-61, 0.4, 65.3), (-56, 36, 67.5)))
retainer = retainer.fuse(box((-43, 0.4, 65.3), (-38, 36, 67.5)))
retainer_m = cq_m(retainer)
rear = rear + (retainer_m ^ outer)
front = front - (retainer_m.translate((0, 0, -0.3)) + retainer_m.translate((0, 0, 0.3)))
add('P06', 'Captured shutter cap', cap_mesh, kind='hybrid_mesh', color='#34383c', explode=(0, 0, 20),
    print_note='Flange down. Rear-shell fork captures cap; no spring or switch fitted. This is a retained mechanical demonstrator only.')

usb_brep = cq.Workplane(obj=box((19.4, -45, 5.3), (30.4, 15, 10.5))).edges('|Y').fillet(2.4).val()
usbcut = cq_m(usb_brep)
front = front - usbcut
carrier_m = cq_m(carrier)
front = front - carrier_m
rear = rear - carrier_m
for dy in np.arange(0, 61, 2):
    front = front - carrier_m.translate((0, dy, 0))
    front = front - retainer_m.translate((0, dy, -0.3)) - retainer_m.translate((0, dy, 0.3))
for m in FRONT_CUTS:
    front = front - m
for m in REAR_CUTS:
    rear = rear - m
for pid in ['P08', 'P09']:
    front = front - SOLIDS[pid]
    rear = rear - SOLIDS[pid]
add('P01', 'Front shell', front, kind='hybrid_mesh', color='#62676c', explode=(0, -6, 0),
    print_note='Split plane y=12 on plate; front outward. Supports may be needed inside bosses and lens sockets. Inspect slice first.')
add('P02', 'Rear shell with shutter capture fork', rear, kind='hybrid_mesh', color='#62676c', explode=(0, 58, 0),
    print_note='Orientation must accommodate projecting capture fork; split-plane-down needs support under shell. Inspect slice and support contact before printing.')
add('P03', 'Shared camera carrier', carrier, explode=(0, 26, 0), color='#9fa4a9',
    print_note='Rear planar rail faces on plate; optical axis vertical. PCB edge channels and collars require fit-coupon approval.')

coupon = box((0, 0, 0), (56, 24, 3))
coupon = coupon.fuse(cyl((13, 12, 6), 13.35, 6, 'z')).cut(cyl((13, 12, 6), 10.95, 15, 'z'))
coupon = coupon.fuse(box((30, 0, 3), (56, 12, 8)))
coupon = coupon.cut(cyl((38, 6, 6), 1.75, 12, 'z'))
coupon = coupon.cut(cq.Workplane('XY', origin=(48, 6, 5.2)).polygon(6, 5.9 / np.cos(np.pi / 6)).extrude(3).val())
coupon = coupon.cut(box((32, 16, 0), (55, 18.2, 3.5)))
add('P10', 'Critical fit coupon', coupon, color='#b7bbc0', print_note='Base on plate. Tests Ø21.9 collar receiver, Ø3.5 screw clearance, 5.9 AF nut pocket and 2.2 PCB channel; not part of assembly.')

scene = trimesh.Scene()
for pid, p in PARTS.items():
    if pid == 'P10':
        continue
    tm = til_tm(SOLIDS[pid])
    tm.visual.face_colors = trimesh.visual.color.hex_to_rgba(p['color'])
    scene.add_geometry(tm, node_name=pid, geom_name=pid)
for h in HARDWARE:
    tm = trimesh.load(ROOT / h['stl'], force='mesh')
    tm.visual.face_colors = trimesh.visual.color.hex_to_rgba(h['color'])
    scene.add_geometry(tm, node_name=h['id'], geom_name=h['id'])
scene.export(CAD / 'assembly.glb')
assembly = cq.Assembly(name='analytic_mechanical_parts_only')
for pid, shape in BREPS.items():
    if pid != 'P10':
        assembly.add(shape, name=pid)
assembly.save(str(CAD / 'analytic-parts.step'))

collisions = []
ids = [p for p in SOLIDS if p != 'P10']
for i, a in enumerate(ids):
    for b in ids[i + 1:]:
        v = float((SOLIDS[a] ^ SOLIDS[b]).volume())
        if v > 0.01:
            collisions.append({'a': a, 'b': b, 'intersection_mm3': v})
manifest = {'revision': 'stereo-final-r01', 'units': 'mm', 'front_axis': '-Y', 'up_axis': '+Z',
            'datum': {'reference_width_mm': 140, 'regularized_width_mm': float(outer_mesh.extents[0]), 'lens_centers_mm': [[x, -26, 48] for x in lens_x], 'baseline_mm': 54, 'pcb_centres_mm': [[-6, 11.5, 41.25], [44, 11.5, 41.25]], 'pcb_nominal_envelope_mm': [27, 1.6, 40.5], 'pcb_nominal_z_range_mm': [21, 61.5], 'shell_split_y_mm': [12, 12.3], 'shutter_axis_xy_mm': [button_x, button_y], 'closure_centres_xz_mm': closure, 'closure_nut_y_mm': 8.5, 'shutter_entry_drop_mm': 2.8, 'shutter_insertion_entry_z_mm': -2.8, 'shutter_insertion_path': 'rearward entry at Z offset -2.8 mm, slide forward in -Y, then lift +2.8 mm into guide', 'usb_service_aperture_mm': [11, 5.2], 'usb_service_aperture_centre_xz_mm': [24.9, 7.9]},
            'parts': list(PARTS.values()), 'hardware': HARDWARE,
            'bom': [{'name': 'M3 × 25 socket screw', 'quantity': 4}, {'name': 'M3 × 12 socket screw', 'quantity': 6}, {'name': 'M3 hex nut, 5.5 mm AF × 2.4 mm nominal', 'quantity': 10}],
            'assembly_steps': ['Test P10 fit coupon with actual hardware and PCB edge.', 'Slide four closure nuts into P01 internal vertical slots: lower nuts from above, upper nuts from below. Insert two carrier nuts through side access.', 'Insert P04 and P05 from inside P01 toward front; flanges sit behind socket shoulders.', 'Hold P06 2.8 mm below final height, enter from rear and slide forward, then lift 2.8 mm into guide. Keep cap supported until rear shell is fitted.', 'Outside housing, check populated-board clearance and slide nominal boards into P03 edge channels.', 'Outside housing, install P08/P09 top keepers with four M3×12 screws and nuts.', 'Fit loaded P03 cassette from rear and fasten with H05/H06 and N05/N06. Carrier traps lens collar flanges.', 'Route prototype cabling clear of closure and shutter fork; USB-C electronics are not included.', 'Install P02 from rear; its integral fork captures P06. Tighten four M3×25 screws by hand.'],
            'interfaces_open': ['Exact PCB clone/component and ESP32-CAM-MB stack dimensions', 'Actual lens barrel, optical centre and flex bend clearance', '30 mm true optic requirement is not met by current scale', 'Functional USB-C charging/data electronics and mounting', 'Shutter spring, switch and actuation interface', 'Stereo electrical synchronization and optical calibration', 'Print slicing, physical fit and mechanical load validation'],
            'status': 'mechanical prototype, not production validated', 'unintended_collisions': collisions,
            'surface_derivation': {'field_voxel_pitch_mm': 0.4, 'gaussian_sigma_voxels': 1.5, 'outer_iso_mm': 0, 'inner_iso_mm': 2.6, 'mesh_simplification_mm': 0.025, 'final_export_simplification_mm': 0.0001, 'shutter_access_guard_iso_mm': 1.6, 'raw_tripo_surface_exact': False}, 'removed_small_components': REMOVED}
(CAD / 'assembly-manifest.json').write_text(json.dumps(manifest, indent=2))
(ROOT / 'verification/geometry.json').write_text(json.dumps({'parts': list(PARTS.values()), 'pair_intersections': collisions, 'printability_status': 'watertight checks only; supports and slicer not validated'}, indent=2))
print(json.dumps({'parts': len(PARTS), 'collisions': collisions}), flush=True)
