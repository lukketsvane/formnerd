import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.sax.saxutils import quoteattr

sys.path.insert(0, '/tmp/entropi-vtk')
sys.path.insert(0, '/tmp/entropi-mesh-deps')

import numpy as np
import trimesh
import vtk
from scipy.spatial import cKDTree
from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray


ROOT = Path(__file__).resolve().parents[1]
PRINT = ROOT / 'print'
REVIEW = ROOT / 'review'
VERIFY = ROOT / 'verification'
NS = 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
CONTENT_TYPES = '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>'
RELATIONSHIPS = '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>'
NATIVE_COLOUR_DATA = None
NATIVE_COLOUR_LOADED = False
NATIVE_COLOUR_REPORT = {}
FACE_COLOUR_CACHE = {}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def part_role(name):
    if name.startswith('test_'):
        return 'test_coupon'
    if name.startswith('06_'):
        return 'assembly_tool'
    return 'product_part'


def native_colour_data():
    global NATIVE_COLOUR_DATA, NATIVE_COLOUR_LOADED
    if NATIVE_COLOUR_LOADED:
        return NATIVE_COLOUR_DATA
    NATIVE_COLOUR_LOADED = True
    candidates = [ROOT.parent / 'Entropi-Tripo-Selected/mesh/03-quick-capped.glb', ROOT.parent / 'mesh/03-quick-capped.glb']
    source = next((path for path in candidates if path.is_file()), None)
    if source is None:
        NATIVE_COLOUR_REPORT.update({'method': 'uniform_colour_fallback', 'reason': 'Native selected source GLB unavailable at both supported paths', 'geometry_changed': False})
        return None
    scene = trimesh.load(source, force='scene', process=False)
    centroids, colours = [], []
    grey = {0, 3, 4, 6, 8}
    dark = {1, 2, 5, 7, 9, 10}
    for name in sorted(scene.graph.nodes_geometry):
        transform, geometry = scene.graph[name]
        mesh = scene.geometry[geometry]
        part_id = int(str(name).rsplit('_', 1)[-1])
        if part_id not in grey | dark:
            raise ValueError('Unrecognised native colour region: ' + str(name))
        vertices = trimesh.transform_points(mesh.vertices, transform)[:, [2, 0, 1]] * 140.0
        centroids.append(vertices[np.asarray(mesh.faces)].mean(axis=1))
        colour = [179, 184, 181] if part_id in grey else [56, 61, 64]
        colours.append(np.broadcast_to(np.asarray(colour, dtype=np.uint8), (len(mesh.faces), 3)))
    centroid_array = np.concatenate(centroids)
    colour_array = np.concatenate(colours)
    NATIVE_COLOUR_DATA = (cKDTree(centroid_array), colour_array)
    NATIVE_COLOUR_REPORT.update({'method': 'nearest_native_triangle_centroid_per_main_shell_face', 'source_path': str(source), 'source_sha256': digest(source), 'native_triangles': len(centroid_array), 'native_to_assembly_axes': ['source_Z', 'source_X', 'source_Y'], 'native_to_assembly_scale': 140.0, 'grey_native_ids': sorted(grey), 'dark_native_ids': sorted(dark), 'grey_rgb': [179, 184, 181], 'dark_rgb': [56, 61, 64], 'geometry_changed': False, 'new_cut_faces_receive_nearest_source_region_colour': True})
    return NATIVE_COLOUR_DATA


def face_colours(part):
    if part['name'] != '01_outer_shell':
        return None
    key = (part['name'], part.get('source_sha256', id(part['vertices'])))
    if key in FACE_COLOUR_CACHE:
        return FACE_COLOUR_CACHE[key]
    native = native_colour_data()
    if native is None:
        return None
    tree, colours = native
    faces, vertices = part['faces'], part['vertices']
    result = np.empty((len(faces), 3), dtype=np.uint8)
    for start in range(0, len(faces), 100000):
        centroids = vertices[faces[start:start + 100000]].mean(axis=1)
        _, nearest = tree.query(centroids, workers=2)
        result[start:start + len(centroids)] = colours[nearest]
    FACE_COLOUR_CACHE[key] = result
    return result


def load_parts():
    parts = []
    for path in sorted((ROOT / 'parts').glob('*.npz')):
        with np.load(path) as data:
            vertices = np.asarray(data['vertices'], dtype=np.float64)
            faces = np.asarray(data['faces'], dtype=np.int64)
        if vertices.ndim != 2 or vertices.shape[1] != 3 or faces.ndim != 2 or faces.shape[1] != 3:
            raise ValueError('Malformed mesh arrays: ' + path.name)
        if not np.isfinite(vertices).all() or faces.min() < 0 or faces.max() >= len(vertices):
            raise ValueError('Invalid mesh values: ' + path.name)
        parts.append({'name': path.stem, 'vertices': vertices, 'faces': faces, 'source_sha256': digest(path)})
    if not parts:
        raise ValueError('No parts/*.npz files exist yet')
    return parts


def export_3mf(path, parts, purpose):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        archive.writestr('[Content_Types].xml', CONTENT_TYPES)
        archive.writestr('_rels/.rels', RELATIONSHIPS)
        archive.writestr('Metadata/assembly-purpose.json', json.dumps({'purpose': purpose, 'units': 'mm', 'coordinate_significant_digits': 17, 'physical_print_fit_verified': False, 'printer_profile_embedded': False, 'source_geometry_simplified': False}, indent=2))
        with archive.open('3D/3dmodel.model', 'w') as stream:
            stream.write(('<?xml version="1.0" encoding="UTF-8"?><model unit="millimeter" xml:lang="en-US" xmlns="' + NS + '"><metadata name="Title">A1 Assembly R01</metadata><resources>').encode())
            for object_id, part in enumerate(parts, 1):
                stream.write(('<object id="%d" type="model" name=%s><mesh><vertices>' % (object_id, quoteattr(part['name']))).encode())
                vertices, faces = part['vertices'], part['faces']
                for start in range(0, len(vertices), 10000):
                    stream.write(''.join('<vertex x="%.17g" y="%.17g" z="%.17g"/>' % tuple(v) for v in vertices[start:start + 10000]).encode())
                stream.write(b'</vertices><triangles>')
                for start in range(0, len(faces), 10000):
                    stream.write(''.join('<triangle v1="%d" v2="%d" v3="%d"/>' % tuple(f) for f in faces[start:start + 10000]).encode())
                stream.write(b'</triangles></mesh></object>')
            stream.write(b'</resources><build>')
            for object_id in range(1, len(parts) + 1):
                stream.write(('<item objectid="%d"/>' % object_id).encode())
            stream.write(b'</build></model>')
    readback = []
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError('3MF ZIP integrity failure: ' + str(path))
        with archive.open('3D/3dmodel.model') as stream:
            part_index = -1
            vertex_index = 0
            face_index = 0
            builds = 0
            for event, node in ET.iterparse(stream, events=('start', 'end')):
                local = node.tag.rsplit('}', 1)[-1]
                if event == 'start' and local == 'object':
                    part_index += 1
                    vertex_index = 0
                    face_index = 0
                    if node.attrib.get('name') != parts[part_index]['name']:
                        raise ValueError('3MF part name mismatch')
                elif event == 'end' and local == 'vertex':
                    original = parts[part_index]['vertices'][vertex_index]
                    parsed = [float(node.attrib[k]) for k in ('x', 'y', 'z')]
                    if not np.array_equal(original, parsed):
                        raise ValueError('3MF float64 coordinate mismatch')
                    vertex_index += 1
                    node.clear()
                elif event == 'end' and local == 'triangle':
                    original = parts[part_index]['faces'][face_index]
                    parsed = [int(node.attrib[k]) for k in ('v1', 'v2', 'v3')]
                    if not np.array_equal(original, parsed):
                        raise ValueError('3MF face index mismatch')
                    face_index += 1
                    node.clear()
                elif event == 'end' and local == 'object':
                    part = parts[part_index]
                    if vertex_index != len(part['vertices']) or face_index != len(part['faces']):
                        raise ValueError('3MF vertex/triangle count mismatch')
                    readback.append({'name': part['name'], 'role': part_role(part['name']), 'vertices': vertex_index, 'triangles': face_index})
                    node.clear()
                elif event == 'end' and local == 'item':
                    builds += 1
                    node.clear()
    if len(readback) != len(parts) or builds != len(parts):
        raise ValueError('3MF object/build count mismatch')
    return {'path': str(path.relative_to(ROOT)), 'bytes': path.stat().st_size, 'sha256': digest(path), 'objects': len(readback), 'build_items': builds, 'parts': readback, 'exact_float64_coordinates_and_indices_roundtrip': True, 'coordinate_significant_digits': 17, 'purpose': purpose}


def orient_for_print(part):
    rotation = np.array([[-1., 0., 0.], [0., 0., 1.], [0., 1., 0.]])
    if part['name'].startswith(('02_', '04_')):
        rotation = np.array([[1., 0., 0.], [0., 0., 1.], [0., -1., 0.]])
    if part['name'].startswith(('07', '08')):
        rotation = np.eye(3)
    vertices = part['vertices'] @ rotation.T
    low, high = vertices.min(axis=0), vertices.max(axis=0)
    shift = np.array([128 - (low[0] + high[0]) / 2, 128 - (low[1] + high[1]) / 2, -low[2]])
    vertices += shift
    matrix = np.eye(4)
    matrix[:3, :3] = rotation
    matrix[:3, 3] = shift
    return {**part, 'vertices': vertices}, {'rotation_determinant': float(np.linalg.det(rotation)), 'assembly_to_print_matrix': matrix.tolist(), 'bounds_mm': [vertices.min(axis=0).tolist(), vertices.max(axis=0).tolist()], 'orientation_is_a_starting_point': True, 'supports_and_actual_printer_profile_verified': False}


def layout_print_parts(parts):
    oriented = [orient_for_print(part)[0] for part in parts]
    plates = []
    current = []
    x, y, row_height = 10.0, 10.0, 0.0
    for part in oriented:
        low, high = part['vertices'].min(axis=0), part['vertices'].max(axis=0)
        size = high - low
        if size[0] > 236 or size[1] > 236 or size[2] > 256:
            raise ValueError('Part exceeds conservative 256 mm plate area: ' + part['name'])
        if x + size[0] > 246:
            x = 10.0
            y += row_height + 10.0
            row_height = 0.0
        if y + size[1] > 246:
            plates.append(current)
            current = []
            x, y, row_height = 10.0, 10.0, 0.0
        translation = np.array([x - low[0], y - low[1], -low[2]])
        moved = {**part, 'vertices': part['vertices'] + translation}
        current.append(moved)
        x += size[0] + 10.0
        row_height = max(row_height, size[1])
    if current:
        plates.append(current)
    reports = []
    for index, plate in enumerate(plates, 1):
        rectangles = []
        for part in plate:
            low, high = part['vertices'].min(axis=0), part['vertices'].max(axis=0)
            if (low < -1e-8).any() or (high > 256 + 1e-8).any():
                raise ValueError('Plate bounds failure')
            rectangles.append({'name': part['name'], 'role': part_role(part['name']), 'min': low.tolist(), 'max': high.tolist()})
        for i, a in enumerate(rectangles):
            for b in rectangles[i + 1:]:
                if all(min(a['max'][axis], b['max'][axis]) > max(a['min'][axis], b['min'][axis]) for axis in [0, 1]):
                    raise ValueError('Print layout footprint overlap')
        report = export_3mf(PRINT / ('A1-plate-%02d.3mf' % index), plate, 'Separate print parts arranged on a 256 mm plate. Supports and actual P1S profile must be checked.')
        report['nonoverlapping_xy_bounding_rectangles'] = True
        report['bounds'] = rectangles
        reports.append(report)
    return reports


def polydata(vertices, faces):
    points = vtk.vtkPoints()
    points.SetData(numpy_to_vtk(vertices, deep=True))
    packed = np.column_stack((np.full(len(faces), 3, dtype=np.int64), faces)).ravel()
    cells = vtk.vtkCellArray()
    cells.SetCells(len(faces), numpy_to_vtkIdTypeArray(packed, deep=True))
    data = vtk.vtkPolyData()
    data.SetPoints(points)
    data.SetPolys(cells)
    normals = vtk.vtkPolyDataNormals()
    normals.SetInputData(data)
    normals.SplittingOff()
    normals.ConsistencyOff()
    normals.AutoOrientNormalsOff()
    normals.Update()
    return normals.GetOutput()


def offset_for(name):
    if name.startswith('02_'):
        return np.array([0., -105., 0.])
    if name.startswith('03_'):
        return np.array([0., -54., 0.])
    if name.startswith('09_'):
        return np.array([0., -112., 0.])
    if name.startswith('04_'):
        return np.array([0., 48., 0.])
    if name.startswith('05_'):
        return np.array([0., -155., 0.])
    if name.startswith('06_'):
        return np.array([88., -110., -10.])
    if name.startswith('07'):
        return np.array([0., 0., 33.])
    if name.startswith('08'):
        return np.array([0., -55., 0.])
    return np.zeros(3)


def colour_for(name):
    if name.startswith('01_'):
        return (0.78, 0.80, 0.79)
    if name.startswith('02_'):
        return (0.24, 0.26, 0.27)
    if name.startswith(('04_', '05_', '07')):
        return (0.24, 0.26, 0.27)
    return (0.56, 0.58, 0.58)


def render(parts, filename, exploded=False, technical=False):
    renderer = vtk.vtkRenderer()
    renderer.SetBackground(1, 1, 1)
    renderer.SetAutomaticLightCreation(False)
    window = vtk.vtkRenderWindow()
    window.SetOffScreenRendering(True)
    window.SetMultiSamples(8)
    size = (2400, 1800) if exploded else (2000, 1600)
    window.SetSize(*size)
    window.AddRenderer(renderer)
    bounds = []
    offsets = {}
    labels = []
    technical_points = []
    camera = renderer.GetActiveCamera()
    camera.ParallelProjectionOn()
    for part in parts:
        offset = offset_for(part['name']) if exploded else np.zeros(3)
        offsets[part['name']] = offset.tolist()
        points = part['vertices'] + offset
        if technical:
            technical_points.append(points)
        bounds.extend([points.min(axis=0), points.max(axis=0)])
        data = polydata(part['vertices'], part['faces'])
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(data)
        per_face = None if technical else face_colours(part)
        if per_face is None:
            mapper.ScalarVisibilityOff()
        else:
            if data.GetNumberOfCells() != len(per_face):
                raise ValueError('VTK face colour count mismatch')
            data.GetCellData().SetScalars(numpy_to_vtk(per_face, deep=True, array_type=vtk.VTK_UNSIGNED_CHAR))
            mapper.SetScalarModeToUseCellData()
            mapper.SetColorModeToDirectScalars()
            mapper.ScalarVisibilityOn()
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.SetPosition(*offset)
        material = actor.GetProperty()
        material.SetColor(*colour_for(part['name']))
        material.SetAmbient(0.65)
        material.SetDiffuse(0.35)
        material.SetSpecular(0.08)
        material.SetSpecularPower(28)
        material.SetInterpolationToPhong()
        if technical:
            material.SetColor(1, 1, 1)
            material.SetAmbient(1)
            material.SetDiffuse(0)
            material.SetSpecular(0)
        renderer.AddActor(actor)
        if technical:
            silhouette = vtk.vtkPolyDataSilhouette()
            silhouette.SetInputData(data)
            silhouette.SetCamera(camera)
            silhouette.SetEnableFeatureAngle(False)
            silhouette.BorderEdgesOff()
            edges = vtk.vtkPolyDataMapper()
            edges.SetInputConnection(silhouette.GetOutputPort())
            edges.SetResolveCoincidentTopologyToPolygonOffset()
            outline = vtk.vtkActor()
            outline.SetMapper(edges)
            outline.SetPosition(*offset)
            outline.GetProperty().SetColor(0, 0, 0)
            outline.GetProperty().SetLineWidth(2.8)
            renderer.AddActor(outline)
            top = points.mean(axis=0)
            top[2] = points[:, 2].max() + 4
            labels.append((part['name'][:2], top))
    bounds = np.asarray(bounds)
    low, high = bounds.min(axis=0), bounds.max(axis=0)
    centre = (low + high) / 2
    direction = np.array([1., 1., 1.]) if not exploded else np.array([1., -1., 1.])
    direction /= np.linalg.norm(direction)
    up = np.array([0., 0., 1.])
    camera.SetPosition(*(centre + 900 * direction))
    camera.SetFocalPoint(*centre)
    camera.SetViewUp(*up)
    right = np.cross(up, direction)
    right /= np.linalg.norm(right)
    real_up = np.cross(direction, right)
    corners = np.array([[x, y, z] for x in [low[0], high[0]] for y in [low[1], high[1]] for z in [low[2], high[2]]])
    projected = np.column_stack(((corners - centre) @ right, (corners - centre) @ real_up))
    extent = np.ptp(projected, axis=0)
    if technical:
        limits = np.array([[float((points @ right).min()), float((points @ right).max()), float((points @ real_up).min()), float((points @ real_up).max())] for points in technical_points])
        low_projected = limits[:, [0, 2]].min(axis=0)
        high_projected = limits[:, [1, 3]].max(axis=0)
        focus = (low_projected + high_projected) / 2
        centre = centre + right * (focus[0] - centre @ right) + real_up * (focus[1] - centre @ real_up)
        camera.SetPosition(*(centre + 900 * direction))
        camera.SetFocalPoint(*centre)
        extent = high_projected - low_projected
    camera.SetParallelScale(max(extent[1] / 2, extent[0] / 2 * size[1] / size[0]) / 0.9)
    for position, intensity in [([250, 200, 400], 0.8), ([-200, -100, 200], 0.35)]:
        light = vtk.vtkLight()
        light.SetLightTypeToSceneLight()
        light.SetPosition(*(centre + position))
        light.SetFocalPoint(*centre)
        light.SetIntensity(intensity)
        renderer.AddLight(light)
    renderer.ResetCameraClippingRange()
    window.Render()
    if technical:
        for label, point in labels:
            renderer.SetWorldPoint(*point, 1)
            renderer.WorldToDisplay()
            x, y, _ = renderer.GetDisplayPoint()
            caption = vtk.vtkTextActor()
            caption.SetInput(label)
            caption.SetDisplayPosition(round(x), round(y))
            caption.GetTextProperty().SetFontSize(32)
            caption.GetTextProperty().SetBold(True)
            caption.GetTextProperty().SetColor(0, 0, 0)
            caption.GetTextProperty().SetBackgroundColor(1, 1, 1)
            caption.GetTextProperty().SetBackgroundOpacity(1)
            renderer.AddActor2D(caption)
        window.Render()
    pixels = vtk.vtkWindowToImageFilter()
    pixels.SetInput(window)
    pixels.SetInputBufferTypeToRGB()
    pixels.ReadFrontBufferOff()
    pixels.Update()
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(str(REVIEW / filename))
    writer.SetInputConnection(pixels.GetOutputPort())
    writer.Write()
    window.Finalize()
    return {'path': 'review/' + filename, 'camera_direction': direction.tolist(), 'camera_up': up.tolist(), 'orthographic': True, 'part_translation_offsets_mm': offsets, 'offsets_are_illustration_only_not_insertion_path_certification': True, 'geometry_simplified': False, 'ground_or_environment': False, 'technical_linework': technical, 'appearance_mapping': dict(NATIVE_COLOUR_REPORT), 'sha256': digest(REVIEW / filename)}


def export_glb(parts):
    scene = trimesh.Scene()
    colour_seam_splits = {}
    for part in parts:
        per_face = face_colours(part)
        if per_face is None:
            mesh = trimesh.Trimesh(part['vertices'] / 1000.0, part['faces'], process=False)
            rgb = [round(value * 255) for value in colour_for(part['name'])]
            mesh.visual = trimesh.visual.ColorVisuals(mesh=mesh, vertex_colors=rgb + [255])
        else:
            palette, face_ids = np.unique(per_face, axis=0, return_inverse=True)
            key = (part['faces'] * len(palette) + face_ids[:, None]).ravel()
            unique_key, inverse = np.unique(key, return_inverse=True)
            preview_vertices = part['vertices'][unique_key // len(palette)] / 1000.0
            preview_faces = inverse.reshape(-1, 3)
            rgb = palette[unique_key % len(palette)]
            rgba = np.column_stack((rgb, np.full(len(rgb), 255, dtype=np.uint8)))
            mesh = trimesh.Trimesh(preview_vertices, preview_faces, process=False)
            mesh.visual = trimesh.visual.ColorVisuals(mesh=mesh, vertex_colors=rgba)
            colour_seam_splits[part['name']] = {'source_vertices': len(part['vertices']), 'preview_vertices': len(preview_vertices), 'triangle_positions_unchanged_before_float32_export': True}
        scene.add_geometry(mesh, node_name=part['name'], geom_name=part['name'])
    path = REVIEW / 'A1-assembled.glb'
    path.write_bytes(scene.export(file_type='glb'))
    readback = trimesh.load(path, force='scene', process=False)
    exported_triangles = sum(len(mesh.faces) for mesh in readback.geometry.values())
    triangles = sum(len(part['faces']) for part in parts)
    if exported_triangles != triangles or len(readback.geometry) != len(parts):
        raise ValueError('GLB part/triangle count mismatch')
    return {'path': str(path.relative_to(ROOT)), 'bytes': path.stat().st_size, 'sha256': digest(path), 'triangles': triangles, 'parts': len(parts), 'coordinates': 'GLB float32 in meters, source mm divided by 1000; preview only. High-precision 3MF is the manufacturing export.', 'appearance_mapping': dict(NATIVE_COLOUR_REPORT), 'preview_vertices_split_only_at_colour_boundaries': colour_seam_splits, 'triangle_count_roundtrip': True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-render', action='store_true')
    parser.add_argument('--render-only', action='store_true')
    args = parser.parse_args()
    for folder in [PRINT, REVIEW, VERIFY]:
        folder.mkdir(exist_ok=True)
    parts = load_parts()
    product = [part for part in parts if part_role(part['name']) == 'product_part']
    report = {'physical_print_fit_verified': False, 'source_npz': {part['name']: part['source_sha256'] for part in parts}, 'part_roles': {part['name']: part_role(part['name']) for part in parts}}
    if not args.render_only:
        report['assembled_3mf'] = export_3mf(REVIEW / 'A1-assembled.3mf', product, 'Assembly inspection pose. Separate mechanical objects in their designed positions. Do not print this assembled pose as one solid.')
        report['parts_3mf'] = []
        report['print_poses'] = {}
        for part in parts:
            oriented, pose = orient_for_print(part)
            purpose = 'Individual print part. Starting orientation only; inspect supports and actual P1S profile before printing.'
            if part_role(part['name']) == 'test_coupon':
                purpose = 'Fit-test coupon only, excluded from the product assembly. Print and physically check this coupon before final parts.'
            elif part_role(part['name']) == 'assembly_tool':
                purpose = 'Separate printed assembly tool, excluded from the product assembly.'
            report['parts_3mf'].append(export_3mf(PRINT / (part['name'] + '.3mf'), [oriented], purpose))
            report['print_poses'][part['name']] = pose
            print('3MF verified ' + part['name'], flush=True)
        report['plates'] = layout_print_parts(parts)
        report['glb'] = export_glb(product)
    if not args.no_render:
        report['renders'] = [render(product, 'A1-assembled.png'), render(product, 'A1-exploded.png', True)]
    report['appearance_mapping'] = dict(NATIVE_COLOUR_REPORT)
    path = VERIFY / ('review-renders.json' if args.render_only else 'exports.json')
    path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'report': str(path), 'parts': len(parts), 'product_parts': len(product)}), flush=True)


if __name__ == '__main__':
    main()
