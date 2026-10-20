import hashlib
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, '/tmp/entropi-mesh-deps')
import numpy as np
import trimesh
import manifold3d as md
import cadquery as cq
import shutter_module
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT.parent if (ROOT.parent / 'mesh/03-quick-capped.glb').exists() else ROOT.parent / 'Entropi-Tripo-Selected'
P = json.loads((ROOT / 'cad/parameters.json').read_text())
OUT = ROOT / 'parts'
OUT.mkdir(exist_ok=True)
CX, CZ = P['optical_axis_xz']
CAD = {}
FRAGMENTS = {}


def box(size, centre):
    return cq.Workplane('XY').box(*size).translate(centre).val()


def cylinder(radius, y0, y1, x=0, z=0):
    return cq.Solid.makeCylinder(radius, y1 - y0, cq.Vector(x, y0, z), cq.Vector(0, 1, 0))


def rounded_bay(width, height, rear, front, x, z, radius=3):
    return cq.Workplane('XY').box(width, front - rear, height).edges('|Y').fillet(radius).translate((x, (front + rear) / 2, z)).val()


def manifold(shape):
    vertices, triangles = shape.tessellate(0.025, 0.07)
    vertices = np.asarray([v.toTuple() for v in vertices], dtype=np.float64)
    unique, inverse = np.unique(vertices, axis=0, return_inverse=True)
    faces = inverse[np.asarray(triangles)]
    result = md.Manifold(md.Mesh64(np.ascontiguousarray(unique), np.ascontiguousarray(faces, dtype=np.uint64)))
    if result.status() != md.Error.NoError:
        raise ValueError(str(result.status()))
    return result


def as_mesh(solid):
    result = solid.to_mesh64()
    return trimesh.Trimesh(np.asarray(result.vert_properties)[:, :3], np.asarray(result.tri_verts), process=False)


def connectivity(mesh):
    vertices, inverse = np.unique(mesh.vertices, axis=0, return_inverse=True)
    faces = inverse[mesh.faces]
    a, b = faces.ravel(), faces[:, [1, 2, 0]].ravel()
    graph = coo_matrix((np.ones(len(a), dtype=bool), (a, b)), shape=(len(vertices), len(vertices))).tocsr()
    count, labels = connected_components(graph, directed=False)
    return count, vertices, faces, labels[faces[:, 0]]


def clean_fragments(solid, name):
    mesh = as_mesh(solid)
    count, vertices, faces, labels = connectivity(mesh)
    if count == 1:
        return solid
    triangles = vertices[faces]
    volumes = np.bincount(labels, weights=np.einsum('ij,ij->i', triangles[:, 0], np.cross(triangles[:, 1], triangles[:, 2])) / 6, minlength=count)
    largest = int(np.argmax(volumes))
    removed = float(np.abs(np.delete(volumes, largest)).sum())
    fragments = []
    for label in range(count):
        if label == largest:
            continue
        points = vertices[np.unique(faces[labels == label])]
        fragments.append({'signed_volume_mm3': float(volumes[label]), 'bounds_mm': [points.min(axis=0).tolist(), points.max(axis=0).tolist()], 'maximum_extent_mm': float(np.ptp(points, axis=0).max())})
    FRAGMENTS[name] = {'detached_cut_fragments_removed': count - 1, 'sum_absolute_signed_volume_mm3': removed, 'maximum_permitted_removal_mm3': 0.01, 'fragments': fragments}
    if removed > 0.01 or any(item['maximum_extent_mm'] > 5 for item in fragments):
        raise ValueError((name, 'Real disconnected geometry', FRAGMENTS[name]))
    faces = faces[labels == largest]
    used = np.unique(faces)
    mapping = np.full(len(vertices), -1, dtype=np.int64)
    mapping[used] = np.arange(len(used))
    return md.Manifold(md.Mesh64(np.ascontiguousarray(vertices[used]), np.ascontiguousarray(mapping[faces], dtype=np.uint64)))


def save(name, solid, cad=None):
    if solid.status() != md.Error.NoError or solid.is_empty():
        raise ValueError((name, str(solid.status())))
    mesh = as_mesh(solid)
    faces = np.asarray(mesh.faces, dtype=np.int64)
    graph = coo_matrix((np.ones(faces.size, dtype=bool), (faces.ravel(), faces[:, [1, 2, 0]].ravel())), shape=(len(mesh.vertices), len(mesh.vertices))).tocsr()
    count, labels = connected_components(graph, directed=False)
    if count > 1:
        face_labels = labels[faces[:, 0]]
        triangles = mesh.vertices[faces]
        volumes = np.bincount(face_labels, weights=np.einsum('ij,ij->i', triangles[:, 0], np.cross(triangles[:, 1], triangles[:, 2])) / 6, minlength=count)
        largest = int(np.argmax(volumes))
        removed = float(np.abs(np.delete(volumes, largest)).sum())
        if removed > 0.01:
            raise ValueError((name, 'Non-numerical disconnected export components', removed))
        FRAGMENTS[name + '_export'] = {'closed_numerical_components_removed': count - 1, 'sum_absolute_signed_volume_mm3': removed, 'maximum_permitted_removal_mm3': 0.01}
        selected = faces[face_labels == largest]
        used = np.unique(selected)
        mapping = np.full(len(mesh.vertices), -1, dtype=np.int64)
        mapping[used] = np.arange(len(used))
        mesh = trimesh.Trimesh(mesh.vertices[used], mapping[selected], process=False)
    np.savez_compressed(OUT / (name + '.npz'), vertices=mesh.vertices, faces=mesh.faces)
    if cad is not None:
        if not cad.isValid() or len(cad.Solids()) != 1:
            raise ValueError((name, 'invalid analytic CAD', len(cad.Solids())))
        cq.exporters.export(cad, str(OUT / (name + '.step')))
        reread = cq.importers.importStep(str(OUT / (name + '.step'))).val()
        if not reread.isValid() or len(reread.Solids()) != 1:
            raise ValueError((name, 'STEP roundtrip'))
        CAD[name] = cad
    report = {'triangles': len(mesh.faces), 'components': connectivity(mesh)[0], 'volume_mm3': solid.volume(), 'bounds_mm': list(solid.bounding_box()), 'closed': mesh.is_watertight, 'winding_consistent': mesh.is_winding_consistent, 'cad_step': cad is not None}
    print(name, json.dumps(report), flush=True)
    return report


def lock_shape(x, z):
    head = cylinder(4.0, -33.5, -31.5, x, z)
    shaft = cylinder(2.0, -31.5, -18.5, x, z)
    lugs = box((9.0, 1.4, 1.8), (x, -19.4, z))
    slot = box((5.6, 1.2, 1.8), (x, -33.2, z))
    return head.fuse(shaft).fuse(lugs).cut(slot).clean()


def lock_cut(x, z):
    shaft = cylinder(2.3, -50, -17.5, x, z)
    head = cylinder(4.35, -50, -31.5, x, z)
    entry = box((9.6, 34.0, 2.4), (x, -33.0, z))
    channel = cylinder(5.15, -20.5, -18.2, x, z)
    return shaft.fuse(head).fuse(entry).fuse(channel).clean()


def rotate_y(shape, angle, x=0, z=0):
    return shape.rotate((x, 0, z), (x, 1, z), angle)


cache = np.load(ROOT / 'cad/source-largest.npz')
outer = md.Manifold(md.Mesh64(np.ascontiguousarray(cache['vertices']), np.ascontiguousarray(cache['faces'], dtype=np.uint64)))
print('Source union loaded', outer.num_tri(), str(outer.status()), flush=True)
c = P['cavity']
bay = rounded_bay(c['width'], c['height'], c['rear'], c['front'], *c['centre_xz'], c['corner_radius'])
optics = cylinder(21.2, 2.5, 26.1, CX, CZ).fuse(cylinder(17.3, 2.5, 50, CX, CZ))
optics = optics.fuse(cylinder(19.3, 28, 50, CX, CZ))
for sign in [-1, 1]:
    optics = optics.fuse(box((4.7, 24, 6.2), (CX + sign * 18.8, 38, CZ)))
clearances = bay.fuse(optics)
for x, z in P['lock_centres_xz']:
    clearances = clearances.fuse(lock_cut(x, z))
usb = box((15, 40, 12), (CX, -40, -17.0))
wire = cylinder(2, -10, 8.4, 45, 25)
wire = wire.fuse(cq.Solid.makeCylinder(2, 76.7, cq.Vector(-31.7, -10, 25), cq.Vector(1, 0, 0)))
clearances = clearances.fuse(wire)
print('Analytic cavity and ports ready', flush=True)
hollow = outer - manifold(clearances)
main, rear = hollow.split_by_plane((0, 1, 0), -28.85)
_, rear = rear.split_by_plane((0, 1, 0), -29.15)
rear = rear - manifold(usb)
male_outer = rounded_bay(39.4, 55.4, -32.8, -25.8, CX, -4, 2.7)
male_inner = rounded_bay(36.2, 52.2, -34, -24, CX, -4, 1.2)
male = male_outer.cut(male_inner)
male_foot = rounded_bay(43.6, 59.6, -33.0, -30.8, CX, -4, 4.8).cut(male_inner)
male = male.fuse(male_foot).cut(usb).clean()
rear = rear + md.Manifold.batch_boolean([manifold(male), outer], md.OpType.Intersect)
print('Rear tongue added', flush=True)
shutter = shutter_module.build()
cap_clearance = cq.Solid.makeCylinder(7.8, 20, cq.Vector(45, 8.4, 35.1))
cassette_roof_clearance = box((15.0, 55.1, 0.3), (45.0, -14.45, 35.55))
main = main - manifold(shutter['body_cut'].fuse(cap_clearance).fuse(cassette_roof_clearance))
stop = box((12, 7.0, 9.0), (45, -29.5, 28.5))
rear = rear + md.Manifold.batch_boolean([manifold(stop), outer], md.OpType.Intersect)
source_scene = trimesh.load(SOURCE_ROOT / 'mesh/03-quick-capped.glb', force='scene', process=False)
native_transform, native_geometry = source_scene.graph['tripo_part_10']
native_mesh = source_scene.geometry[native_geometry]
native_vertices = trimesh.transform_points(native_mesh.vertices, native_transform)[:, [2, 0, 1]] * 140.0
native_unique, native_inverse = np.unique(native_vertices, axis=0, return_inverse=True)
native_cap = md.Manifold(md.Mesh64(np.ascontiguousarray(native_unique), np.ascontiguousarray(native_inverse[native_mesh.faces], dtype=np.uint64)))
native_cap, _ = native_cap.split_by_plane((0, 0, 1), 36.6)
stem = shutter['stem'].fuse(cq.Solid.makeCylinder(2.25, 1.0, cq.Vector(45, 8.4, 36.0))).clean()
shutter_part = native_cap + manifold(stem)
shutter['metadata']['root_native_cap_attachment'].update({'native_cap_cut_z_mm': 36.6, 'stem_top_z_mm': 37.0, 'nominal_overlap_mm': 0.4})
shutter['metadata']['retainer']['upper_channel_front_y_mm'] = 13.1
shutter['metadata']['retainer']['root_roof_clearance_top_z_mm'] = 35.7
(ROOT / 'verification/shutter-interface.json').write_text(json.dumps(shutter['metadata'], indent=2) + '\n')
print('Native shutter and cassette ready', flush=True)
main = clean_fragments(main, 'outer_shell')
rear = clean_fragments(rear, 'rear_cover')

carrier = rounded_bay(35.6, 51.6, -23.6, 2.4, CX, -4, 2.2)
carrier = carrier.cut(rounded_bay(29.2, 48.4, -25, 4, CX, -4, 0.5))
carrier = carrier.cut(box((25, 40, 44), (CX, -9, -4)))
carrier = carrier.fuse(box((35.6, 2.0, 2.8), (CX, -22.6, 20.4)))
carrier = carrier.fuse(box((35.6, 2.0, 2.8), (CX, -22.6, -28.4)))
carrier = carrier.fuse(box((2.0, 6, 51.6), (CX - 16.8, -19.6, -4)))
carrier = carrier.fuse(box((2.0, 6, 51.6), (CX + 16.8, -19.6, -4)))
carrier = carrier.cut(box((16, 9, 13), (CX, -24, -17)))
camera_seat = box((16, 1.6, 16), (CX, 24.0, CZ)).cut(cylinder(4.4, 22, 26, CX, CZ))
camera_seat = camera_seat.cut(box((10.0, 0.8, 10.0), (CX, 23.25, CZ)))
for sign in [-1, 1]:
    start = cq.Vector(CX + sign * 16.0, 1.2, CZ)
    end = cq.Vector(CX + sign * 6.5, 23.7, CZ)
    vector = end - start
    arm = cq.Solid.makeCylinder(1.5, vector.Length, start, vector.normalized())
    carrier = carrier.fuse(arm)
    camera_seat = camera_seat.cut(cylinder(1.15, 22, 26, CX, CZ + sign * 6.2))
carrier = carrier.fuse(camera_seat)
carrier = carrier.clean()
print('Carrier ready', flush=True)

flange = cylinder(19.0, 28, 29.8, CX, CZ)
barrel = cylinder(17.0, 24, 28.1, CX, CZ)
bezel = flange.fuse(barrel)
for sign in [-1, 1]:
    bezel = bezel.fuse(box((4.0, 1.4, 5.6), (CX + sign * 18.4, 24.9, CZ)))
bezel = bezel.cut(cylinder(15.0, 23, 32, CX, CZ)).clean()
bezel_locked = rotate_y(bezel, 45, CX, CZ)

locks = {}
for i, (x, z) in enumerate(P['lock_centres_xz']):
    locks[f'05_lock_{i+1}'] = rotate_y(lock_shape(x, z), 90, x, z)
tool = box((5.1, 1.5, 5), (0, 0, 0)).fuse(box((14, 3.5, 3.5), (0, 0, 4.0))).clean()
camera_keeper = box((16, 1.0, 16), (CX, 22.1, CZ)).cut(box((8.2, 4, 8.2), (CX, 22.1, CZ)))
for sign in [-1, 1]:
    camera_keeper = camera_keeper.fuse(cylinder(1.0, 22.3, 24.8, CX, CZ + sign * 6.2))
    camera_keeper = camera_keeper.cut(cylinder(2.4, 20, 25, CX + sign * 7.5, CZ))
camera_keeper = camera_keeper.clean()
coupon = box((18, 20, 18), (0, -25, 0)).cut(lock_cut(0, 0)).clean()

report = {'revision': P['revision'], 'parts': {}, 'mechanical_hardware_fit_measured': False, 'source_geometry': 'Boolean-machined native detailed Tripo outer geometry; not reconstructed by hand', 'units': 'mm', 'axes': P['axes']}
report['source_sha256'] = hashlib.sha256((SOURCE_ROOT / 'mesh/03-quick-capped.glb').read_bytes()).hexdigest()
report['numerical_fragments_removed'] = FRAGMENTS
SOLIDS = {'01_outer_shell': main, '02_native_rear_cover': rear, '03_esp32_carrier': manifold(carrier), '04_optical_bezel': manifold(bezel_locked)}
report['parts']['01_outer_shell'] = save('01_outer_shell', main)
report['parts']['02_native_rear_cover'] = save('02_native_rear_cover', rear)
report['parts']['03_esp32_carrier'] = save('03_esp32_carrier', SOLIDS['03_esp32_carrier'], carrier)
report['parts']['04_optical_bezel'] = save('04_optical_bezel', SOLIDS['04_optical_bezel'], bezel_locked)
for name, shape in locks.items():
    SOLIDS[name] = manifold(shape)
    report['parts'][name] = save(name, SOLIDS[name], shape)
report['parts']['06_lock_tool'] = save('06_lock_tool', manifold(tool), tool)
SOLIDS['07_shutter'] = shutter_part
SOLIDS['08_shutter_retainer'] = manifold(shutter['retainer'])
SOLIDS['09_camera_keeper'] = manifold(camera_keeper)
report['parts']['07_shutter'] = save('07_shutter', shutter_part)
report['parts']['08_shutter_retainer'] = save('08_shutter_retainer', SOLIDS['08_shutter_retainer'], shutter['retainer'])
report['parts']['09_camera_keeper'] = save('09_camera_keeper', SOLIDS['09_camera_keeper'], camera_keeper)
report['parts']['test_lock_socket'] = save('test_lock_socket', manifold(coupon), coupon)
assembly = cq.Assembly(name='A1_Analytic_Mechanism')
for name, shape in CAD.items():
    if name != '06_lock_tool' and not name.startswith('test_'):
        assembly.add(shape, name=name)
cq.exporters.export(stem, str(OUT / '07_shutter_stem.step'))
assembly.add(stem, name='07_shutter_stem_without_native_mesh_cap')
assembly.export(str(ROOT / 'A1_Analytic_Mechanism.step'))
(ROOT / 'verification/build.json').write_text(json.dumps(report, indent=2) + '\n')
print('Build exported', flush=True)
