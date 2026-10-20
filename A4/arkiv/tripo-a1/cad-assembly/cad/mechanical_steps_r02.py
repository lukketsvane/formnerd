import argparse
import hashlib
import json
import math
from pathlib import Path

import export_review as base
import numpy as np
import trimesh
import vtk
from PIL import Image, ImageDraw, ImageFont
from vtk.util.numpy_support import vtk_to_numpy


ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'review/steps-r02'
SIZE = (2200, 1600)
PARTS = {part['name']: part for part in base.load_parts()}
PARAMETERS = json.loads((ROOT / 'cad/parameters.json').read_text())
CX, CZ = PARAMETERS['optical_axis_xz']
LOCKS = sorted(name for name in PARTS if name.startswith('05_'))
PRODUCT = [name for name in PARTS if base.part_role(name) == 'product_part']
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
DATA = {}
REFERENCES = {}


def ref_box(name, size, centre):
    mesh = trimesh.creation.box(extents=size)
    mesh.apply_translation(centre)
    REFERENCES[name] = {'name': name, 'vertices': np.asarray(mesh.vertices), 'faces': np.asarray(mesh.faces), 'nominal': True}


def ref_cylinder(name, radius, length, centre):
    mesh = trimesh.creation.cylinder(radius=radius, height=length, sections=64)
    transform = trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0])
    mesh.apply_transform(transform)
    mesh.apply_translation(centre)
    REFERENCES[name] = {'name': name, 'vertices': np.asarray(mesh.vertices), 'faces': np.asarray(mesh.faces), 'nominal': True}


ref_box('E1', (27, 4.5, 40.5), (CX, -2.0, -4.0))
ref_box('E2', (28, 4.0, 48), (CX, -19.6, -4.0))
ref_box('E0', (28, 22, 48), (CX, -10.6, -4.0))
ref_box('E4', (9, 0.5, 9), (CX, 23.1, CZ))
ref_cylinder('L3', 4.0, 4.65, (CX, 25.675, CZ))
ref_box('FPC', (6, 15, 0.25), (CX, -0.4, CZ - 4.5))
ref_box('SW', (6, 6, 4.3), (45, 8.4, 27.95))
switch_actuator = trimesh.creation.cylinder(radius=1.4, height=1.2, sections=48)
switch_actuator.apply_translation((45, 8.4, 30.7))
REFERENCES['SW-A'] = {'name': 'SW-A', 'vertices': np.asarray(switch_actuator.vertices), 'faces': np.asarray(switch_actuator.faces), 'nominal': True}


def rotation(axis, degrees):
    return trimesh.transformations.rotation_matrix(math.radians(degrees), axis)[:3, :3]


def instance(name, offset=(0, 0, 0), moving=False, angle=0, pivot=(0, 0, 0), axis=(0, 1, 0), wire=False, opacity=1, clip=None):
    return {'name': name, 'offset': np.asarray(offset, dtype=float), 'moving': moving, 'angle': angle, 'pivot': np.asarray(pivot, dtype=float), 'axis': axis, 'wire': wire, 'opacity': opacity, 'clip': clip}


def transformed(item):
    part = PARTS.get(item['name'], REFERENCES.get(item['name']))
    vertices = part['vertices']
    if item['angle']:
        r = rotation(item['axis'], item['angle'])
        vertices = (vertices - item['pivot']) @ r.T + item['pivot']
    return part, vertices


def geometry(item):
    key = (item['name'], item['angle'], tuple(item['pivot']), tuple(item['axis']), str(item['clip']))
    if key not in DATA:
        part, vertices = transformed(item)
        DATA[key] = base.polydata(vertices, part['faces'])
        if item['clip']:
            plane = vtk.vtkPlane()
            plane.SetNormal(*item['clip']['normal'])
            plane.SetOrigin(*item['clip']['origin'])
            cut = vtk.vtkClipPolyData()
            cut.SetInputData(DATA[key])
            cut.SetClipFunction(plane)
            cut.Update()
            DATA[key] = cut.GetOutput()
    return DATA[key]


def arrow(draw, start, end, width=8, dashed=False):
    start, end = np.asarray(start, dtype=float), np.asarray(end, dtype=float)
    delta = end - start
    length = np.linalg.norm(delta)
    if length < 20:
        return
    direction = delta / length
    normal = np.array([-direction[1], direction[0]])
    tip = end
    base_point = end - direction * 30
    if dashed:
        for distance in np.arange(0, max(0, length - 25), 28):
            segment_end = min(distance + 17, length - 25)
            draw.line([tuple(start + direction * distance), tuple(start + direction * segment_end)], fill='white', width=width + 7)
            draw.line([tuple(start + direction * distance), tuple(start + direction * segment_end)], fill='black', width=width)
    else:
        draw.line([tuple(start), tuple(base_point)], fill='white', width=width + 7)
        draw.line([tuple(start), tuple(base_point)], fill='black', width=width)
    triangle = [tip, base_point + normal * 14, base_point - normal * 14]
    draw.polygon([tuple(p) for p in triangle], fill='black')


def label(draw, text, point, offset, occupied):
    font = ImageFont.truetype(BOLD, 47)
    bounds = draw.textbbox((0, 0), text, font=font)
    width, height = bounds[2] - bounds[0] + 30, bounds[3] - bounds[1] + 24
    candidates = [offset, (-offset[0], offset[1]), (offset[0], -offset[1]), (150, -120), (-150, -120), (150, 120), (-150, 120), (0, -200), (0, 200)]
    chosen = None
    for dx, dy in candidates:
        centre = np.asarray(point) + [dx, dy]
        left = min(max(35, centre[0] - width / 2), SIZE[0] - width - 35)
        top = min(max(35, centre[1] - height / 2), SIZE[1] - height - 90)
        rect = (left, top, left + width, top + height)
        if all(rect[2] + 8 < r[0] or rect[0] > r[2] + 8 or rect[3] + 8 < r[1] or rect[1] > r[3] + 8 for r in occupied):
            chosen = rect
            break
    if chosen is None:
        chosen = rect
    occupied.append(chosen)
    left, top, right, bottom = chosen
    centre = np.array([(left + right) / 2, (top + bottom) / 2])
    point = np.asarray(point)
    near = np.clip(point, [left, top], [right, bottom])
    draw.line([tuple(point), tuple(near)], fill='white', width=9)
    draw.line([tuple(point), tuple(near)], fill='black', width=3)
    draw.ellipse((point[0] - 4, point[1] - 4, point[0] + 4, point[1] + 4), fill='black')
    draw.rounded_rectangle(chosen, radius=9, fill='white', outline='black', width=3)
    draw.text((left + 15, top + 5 - bounds[1]), text, font=font, fill='black')


def turn_points(centre, radius, degrees, start=25):
    centre = np.asarray(centre)
    angles = np.radians(np.linspace(start, start + degrees, max(30, int(degrees))))
    return np.column_stack((centre[0] + radius * np.cos(angles), np.full(len(angles), centre[1]), centre[2] - radius * np.sin(angles)))


def stage(filename, items, direction, labels, arrows=(), turns=(), focus=None, nominal=False, note=None):
    renderer = vtk.vtkRenderer()
    renderer.SetBackground(1, 1, 1)
    renderer.SetAutomaticLightCreation(False)
    window = vtk.vtkRenderWindow()
    window.SetOffScreenRendering(True)
    window.SetMultiSamples(8)
    window.SetSize(*SIZE)
    window.AddRenderer(renderer)
    camera = renderer.GetActiveCamera()
    camera.ParallelProjectionOn()
    bounds = []
    for item in items:
        part, vertices = transformed(item)
        world = vertices + item['offset']
        bounds.extend([world.min(axis=0), world.max(axis=0)])
        data = geometry(item)
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(data)
        mapper.ScalarVisibilityOff()
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.SetPosition(*item['offset'])
        prop = actor.GetProperty()
        prop.SetColor(*((0.87, 0.63, 0.34) if item['moving'] else (0.83, 0.83, 0.83)))
        prop.SetAmbient(0.73)
        prop.SetDiffuse(0.27)
        prop.SetSpecular(0.0)
        prop.SetOpacity(item['opacity'])
        if item['name'].startswith(('01_', '02_', '07_')):
            prop.SetInterpolationToPhong()
        else:
            prop.SetInterpolationToFlat()
        if item['wire']:
            feature_edges = vtk.vtkFeatureEdges()
            feature_edges.SetInputData(data)
            feature_edges.FeatureEdgesOn()
            feature_edges.SetFeatureAngle(30)
            feature_edges.BoundaryEdgesOn()
            feature_edges.ManifoldEdgesOff()
            feature_edges.NonManifoldEdgesOff()
            mapper.SetInputConnection(feature_edges.GetOutputPort())
            prop.SetRepresentationToWireframe()
            prop.SetColor(0.3, 0.3, 0.3)
            prop.SetLineWidth(2)
        renderer.AddActor(actor)
        if not item['wire']:
            silhouette = vtk.vtkPolyDataSilhouette()
            silhouette.SetInputData(data)
            silhouette.SetCamera(camera)
            silhouette.SetEnableFeatureAngle(False)
            silhouette.BorderEdgesOff()
            edge_mapper = vtk.vtkPolyDataMapper()
            edge_mapper.SetInputConnection(silhouette.GetOutputPort())
            edge_mapper.SetResolveCoincidentTopologyToPolygonOffset()
            edge_actor = vtk.vtkActor()
            edge_actor.SetMapper(edge_mapper)
            edge_actor.SetPosition(*item['offset'])
            edge_actor.GetProperty().SetColor(0.04, 0.04, 0.04)
            edge_actor.GetProperty().SetLineWidth(1.4)
            edge_actor.GetProperty().SetOpacity(item['opacity'])
            renderer.AddActor(edge_actor)
    bounds = np.asarray(bounds)
    low, high = (np.asarray(focus[0]), np.asarray(focus[1])) if focus else (bounds.min(axis=0), bounds.max(axis=0))
    centre = (low + high) / 2
    direction = np.asarray(direction, dtype=float)
    direction /= np.linalg.norm(direction)
    up = np.array([0., 0., 1.])
    camera.SetPosition(*(centre + direction * 1000))
    camera.SetFocalPoint(*centre)
    camera.SetViewUp(*up)
    right = np.cross(up, direction)
    right /= np.linalg.norm(right)
    real_up = np.cross(direction, right)
    corners = np.array([[x, y, z] for x in [low[0], high[0]] for y in [low[1], high[1]] for z in [low[2], high[2]]])
    projected = np.column_stack(((corners - centre) @ right, (corners - centre) @ real_up))
    extent = np.ptp(projected, axis=0)
    camera.SetParallelScale(max(extent[1] / 2, extent[0] / 2 * SIZE[1] / SIZE[0]) / 0.76)
    for position, intensity in [([400, -200, 500], 0.8), ([-300, 300, 250], 0.4)]:
        light = vtk.vtkLight()
        light.SetLightTypeToSceneLight()
        light.SetPosition(*(centre + position))
        light.SetFocalPoint(*centre)
        light.SetIntensity(intensity)
        renderer.AddLight(light)
    renderer.ResetCameraClippingRange()
    window.Render()
    pixels = vtk.vtkWindowToImageFilter()
    pixels.SetInput(window)
    pixels.SetInputBufferTypeToRGB()
    pixels.ReadFrontBufferOff()
    pixels.Update()
    raw = vtk_to_numpy(pixels.GetOutput().GetPointData().GetScalars()).reshape(SIZE[1], SIZE[0], 3)
    image = Image.fromarray(raw[::-1].copy())
    draw = ImageDraw.Draw(image)

    def project(point):
        renderer.SetWorldPoint(*point, 1)
        renderer.WorldToDisplay()
        x, y, depth = renderer.GetDisplayPoint()
        return np.array([x, SIZE[1] - y])

    for start, end, dashed in arrows:
        arrow(draw, project(start), project(end), dashed=dashed)
    for turn in turns:
        centre_point, radius, degrees = turn[:3]
        start_angle = turn[3] if len(turn) > 3 else 25
        points = np.array([project(point) for point in turn_points(centre_point, radius, degrees, start_angle)])
        draw.line([tuple(point) for point in points], fill='white', width=14, joint='curve')
        draw.line([tuple(point) for point in points], fill='black', width=7, joint='curve')
        arrow(draw, points[-5], points[-1], width=7)
        midpoint = points[len(points) // 2]
        font = ImageFont.truetype(BOLD, 49)
        text = str(degrees) + '°'
        text_box = draw.textbbox((0, 0), text, font=font)
        text_width = text_box[2] - text_box[0]
        draw.rounded_rectangle((midpoint[0] - text_width / 2 - 10, midpoint[1] - 75, midpoint[0] + text_width / 2 + 10, midpoint[1] - 12), 8, fill='white')
        draw.text((midpoint[0] - text_width / 2, midpoint[1] - 80), text, font=font, fill='black')
    occupied = []
    for text, point, offset in labels:
        label(draw, text, project(point), offset, occupied)
    if nominal or note:
        text = note or 'NOMINELT · MÅ MÅLAST'
        font = ImageFont.truetype(BOLD, 40)
        text_box = draw.textbbox((0, 0), text, font=font)
        text_width = text_box[2] - text_box[0]
        draw.rectangle((SIZE[0] / 2 - text_width / 2 - 18, SIZE[1] - 88, SIZE[0] / 2 + text_width / 2 + 18, SIZE[1] - 22), fill='white')
        draw.text((SIZE[0] / 2 - text_width / 2, SIZE[1] - 79), text, font=font, fill='black')
    path = DEST / filename
    image.save(path)
    window.Finalize()
    result = {'filename': filename, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'camera_direction': direction.tolist(), 'camera_up': up.tolist(), 'orthographic': True, 'focus_bounds_mm': [low.tolist(), high.tolist()], 'nominal_reference_electronics': nominal, 'physical_fit_verified': False, 'illustrative_offsets_only': True, 'printed_part_geometry_modified': False, 'instances': [{k: v.tolist() if isinstance(v, np.ndarray) else v for k, v in item.items()} for item in items], 'labels': [label[0] for label in labels]}
    print(json.dumps({'rendered': filename, 'bytes': path.stat().st_size}), flush=True)
    return result


def assembled_without(*excluded):
    return [instance(name) for name in PRODUCT if name not in excluded]


def build_stages():
    steps = []
    inventory = []
    for name in PRODUCT:
        offset = base.offset_for(name)
        if name == '09_camera_keeper':
            offset = np.array([-55., -50., 10.])
        elif name == '07_shutter':
            offset = np.array([-100., 0., 63.])
        inventory.append(instance(name, offset))
    inventory.extend([instance('06_lock_tool', (74, -132, -8)), instance('test_lock_socket', (-65, -152, -29))])
    steps.append(('m01-inventory.png', inventory, (1, -1, 1), [
        ('01', (50, 0, -20), (150, 60)), ('02', (35, -138, 0), (100, 110)),
        ('03', (CX, -64, 0), (-160, 60)), ('04', (CX, 77, CZ), (130, -90)),
        ('05 × 4', (20, -183, 27), (100, -100)), ('06', (74, -132, -8), (100, 70)),
        ('07', (-55, 8.4, 102), (-130, -100)), ('08', (45, -60, 28), (130, -65)),
        ('09', (CX - 50, -27.9, CZ + 10), (-140, -90)), ('T1', (-65, -177, -29), (-130, 50)),
    ], (), (), None, False, None))

    x, z = PARAMETERS['lock_centres_xz'][0]
    lock = instance(LOCKS[0], offset=(-x, -21, -z), moving=True, angle=-90, pivot=(x, 0, z))
    steps.append(('m02-lock-test.png', [instance('test_lock_socket'), lock], (1, -1, 1), [
        ('T1', (6, -23, 3), (170, 40)), ('05', (0, -51, 0), (-180, -120)),
    ], [((0, -46, 0), (0, -36, 0), False)], [((0, -34, 0), 13, 90)], None, False, None))

    steps.append(('m03-carrier.png', [instance('03_esp32_carrier', clip={'normal': [-1, 0, 0], 'origin': [CX, 0, 0]}), instance('E1', moving=True), instance('E2', moving=True), instance('E0', wire=True, opacity=0.35)], (1, -1, 1), [
        ('03', (CX - 12, -9, 21.8), (-180, -90)), ('E1 NOM.', (CX + 10, -2, 10), (210, -90)), ('E2 NOM.', (CX + 10, -20, -14), (170, 100)),
    ], (), (), None, True, 'SNITT · NOMINELL PLASSERING · 28 × 48 × 22 mm'))

    steps.append(('m04-camera.png', [instance('03_esp32_carrier', clip={'normal': [0, 1, 0], 'origin': [0, 4, 0]}), instance('E4', (0, -16, 0), True), instance('L3', (0, -16, 0), True), instance('FPC', opacity=0.65), instance('09_camera_keeper', (0, -32, 0), True)], (1, -1, 1), [
        ('03', (CX + 7.5, 22, CZ + 6), (160, -90)), ('E4 NOM.', (CX, 7.1, CZ), (-220, -80)), ('FPC NOM.', (CX, -0.4, CZ - 4.5), (-200, 130)), ('09', (CX + 5, -9.9, CZ), (170, 95)),
    ], [((CX, 11.5, CZ), (CX, 21.0, CZ), False), ((CX, -6, CZ + 6.2), (CX, 0, CZ + 6.2), False)], (), ((-46, -23, -25), (-17, 31, 10)), True, 'UTSNITT AV 03 · KAMERA/FLEKS NOMINELT'))

    steps.append(('m05-button.png', [instance('01_outer_shell'), instance('07_shutter', (0, 0, 22), True)], (1, 1, 1), [
        ('01', (56, 8, 34), (170, 80)), ('07', (45, 8.4, 61), (-170, -80)),
    ], [((45, 8.4, 51), (45, 8.4, 42), False)], (), ((27, -9, 23), (64, 27, 66)), False, 'NÆRBILETE'))

    steps.append(('m06-switch-seat.png', [instance('08_shutter_retainer', clip={'normal': [0, 0, -1], 'origin': [0, 0, 32.8]}), instance('SW', (0, 0, 18), True), instance('SW-A', (0, 0, 18), True)], (1, 1, 1), [
        ('08', (53, -3, 27), (180, 85)), ('SW NOM.', (45, 8.4, 46), (-200, -80)),
    ], [((45, 8.4, 40), (45, 8.4, 33), False)], (), None, True, 'SNITT AV 08 · BRYTAR MÅ MÅLAST'))

    steps.append(('m07-cassette.png', [instance('01_outer_shell'), instance('07_shutter'), instance('08_shutter_retainer', (0, -48, 0), True)], (1, -1, 1), [
        ('01', (58, -17, 30), (150, -50)), ('07', (45, 8.4, 40), (-150, -80)), ('08', (45, -55, 28), (-180, 100)),
    ], [((45, -40, 28), (45, -29, 28), False)], (), ((27, -82, 19), (62, 21, 46)), False, 'INN FRÅ BAKSIDA'))

    steps.append(('m08-carrier-insert.png', [instance('01_outer_shell'), instance('07_shutter'), instance('08_shutter_retainer'), instance('03_esp32_carrier', (0, -64, 0), True), instance('09_camera_keeper', (0, -64, 0), True)], (1, -1, 1), [
        ('01', (-8, -27, 13), (170, -70)), ('03 + 09', (CX, -76, -7), (-190, 105)),
    ], [((CX, -34, CZ), (CX, -25, CZ), False)], (), ((-62, -95, -40), (1, 37, 33)), False, 'INN FRÅ BAKSIDA'))

    bezel_items = assembled_without('02_native_rear_cover', '04_optical_bezel', *LOCKS)
    bezel_items.append(instance('04_optical_bezel', (0, 23, 0), True, angle=-45, pivot=(CX, 0, CZ)))
    steps.append(('m09-bezel.png', bezel_items, (1, 1, 1), [
        ('01', (-7, 26, CZ - 12), (130, 120)), ('04', (CX, 52, CZ - 16), (-160, 80)),
    ], [((CX + 12, 47, CZ), (CX + 12, 33, CZ), False)], [((CX, 54, CZ), 26, 45, -120)], ((-59, 11, -38), (-3, 63, 18)), False, None))

    cover_items = assembled_without('02_native_rear_cover', *LOCKS)
    cover_items.append(instance('02_native_rear_cover', (0, -58, 0), True))
    steps.append(('m10-cover.png', cover_items, (1, -1, 1), [
        ('01', (60, -22, 10), (140, -80)), ('02', (35, -88, -5), (-170, 100)),
    ], [((45, -70, -5), (45, -42, -5), False)], (), None, False, None))

    lock_items = assembled_without(*LOCKS)
    for name, (x, z) in zip(LOCKS, PARAMETERS['lock_centres_xz']):
        lock_items.append(instance(name, (0, -27, 0), True, angle=-90, pivot=(x, 0, z)))
    tool_x, tool_z = PARAMETERS['lock_centres_xz'][2]
    lock_items.append(instance('06_lock_tool', (tool_x, -64.5, tool_z), angle=90, axis=(1, 0, 0)))
    x, z = PARAMETERS['lock_centres_xz'][2]
    steps.append(('m11-locks.png', lock_items, (1, -1, 1), [
        ('05 × 4', (CX, -61, 30), (-190, -90)), ('06', (tool_x, -65, tool_z), (170, -90)), ('02', (52, -34, -4), (150, 110)),
    ], [((px, -51, pz), (px, -38, pz), False) for px, pz in PARAMETERS['lock_centres_xz']], [((x, -51, z), 14, 90)], None, False, None))

    steps.append(('m12-finished.png', [instance(name) for name in PRODUCT], (1, 1, 1), [], (), (), None, False, 'MEKANISK PROTOTYPE · FYSISK PASSFORM IKKJE TESTA'))
    return steps


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--only', nargs='*')
    args = parser.parse_args()
    DEST.mkdir(parents=True, exist_ok=True)
    reports = []
    for definition in build_stages():
        if args.only and definition[0].split('-')[0] not in args.only:
            continue
        reports.append(stage(*definition))
    metadata = {'source_npz_sha256': {name: part['source_sha256'] for name, part in PARTS.items()}, 'printed_part_geometry_modified': False, 'physical_fit_verified': False, 'electronics_measured': False, 'electronics_are_schematic_nominal_reference_only': True, 'illustration_offsets_are_not_path_certification': True, 'stages': reports}
    path = DEST / 'metadata.json'
    if args.only and path.exists():
        previous = json.loads(path.read_text())
        combined = {item['filename']: item for item in previous['stages']}
        combined.update({item['filename']: item for item in reports})
        metadata['stages'] = [combined[name] for name in sorted(combined)]
    path.write_text(json.dumps(metadata, indent=2) + '\n')
    print(json.dumps({'stages': len(reports), 'metadata': str(path)}), flush=True)


if __name__ == '__main__':
    main()
