import argparse
import hashlib
import json
import math
import os
import re
import struct
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape, quoteattr

sys.path.insert(0, '/tmp/entropi-mesh-deps')
import numpy as np
import trimesh


ROOT = Path(__file__).resolve().parents[1]
NAME = 'Entropi Tripo assembled form'
PROFILE = '''printer_technology = FFF
bed_shape = 0x0,256x0,256x256,0x256
max_print_height = 256
nozzle_diameter = 0.4
filament_type = PLA
filament_diameter = 1.75
filament_density = 1.24
filament_colour = #8A8C8F
layer_height = 0.2
first_layer_height = 0.2
perimeters = 3
top_solid_layers = 5
bottom_solid_layers = 5
fill_density = 15%
fill_pattern = gyroid
extrusion_width = 0.45
first_layer_extrusion_width = 0.45
perimeter_extrusion_width = 0.45
external_perimeter_extrusion_width = 0.45
infill_extrusion_width = 0.45
solid_infill_extrusion_width = 0.45
top_infill_extrusion_width = 0.45
perimeter_generator = arachne
resolution = 0
support_material = 1
support_material_auto = 1
support_material_buildplate_only = 0
dont_support_bridges = 0
support_material_threshold = 0
support_material_contact_distance = 0.2
support_material_interface_layers = 2
support_material_xy_spacing = 0.35
support_material_spacing = 2.5
raft_layers = 0
brim_width = 0
skirts = 0
complete_objects = 0
gcode_label_objects = octoprint
gcode_comments = 1
binary_gcode = 0
arc_fitting = disabled
perimeter_speed = 40
external_perimeter_speed = 25
small_perimeter_speed = 20
infill_speed = 60
solid_infill_speed = 40
top_solid_infill_speed = 30
bridge_speed = 25
first_layer_speed = 20
travel_speed = 150
filament_max_volumetric_speed = 10
temperature = 210
first_layer_temperature = 210
bed_temperature = 60
first_layer_bed_temperature = 60
cooling = 1
fan_always_on = 1
min_fan_speed = 100
max_fan_speed = 100
bridge_fan_speed = 100
retract_length = 0.8
retract_speed = 35
use_relative_e_distances = 1
layer_gcode = G92 E0
gcode_flavor = marlin2
start_gcode =
end_gcode =
'''


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(vertices, faces):
    finite = bool(np.isfinite(vertices).all())
    unique, inverse = np.unique(vertices, axis=0, return_inverse=True)
    indexed = inverse[faces]
    triangles = vertices[faces]
    cross = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    zero = int(np.count_nonzero(np.all(cross == 0, axis=1)))
    edges = np.concatenate([indexed[:, [0, 1]], indexed[:, [1, 2]], indexed[:, [2, 0]]])
    direction = np.where(edges[:, 0] < edges[:, 1], 1, -1)
    canonical = np.sort(edges, axis=1)
    _, edge_inverse, counts = np.unique(canonical, axis=0, return_inverse=True, return_counts=True)
    sums = np.bincount(edge_inverse, weights=direction)
    _, face_counts = np.unique(np.sort(indexed, axis=1), axis=0, return_counts=True)
    duplicate = int(np.sum(face_counts - 1))
    open_edges = int(np.count_nonzero(counts == 1))
    nonmanifold = int(np.count_nonzero(counts > 2))
    inconsistent = int(np.count_nonzero((counts == 2) & (sums != 0)))
    volume = float(np.einsum('ij,ij->i', triangles[:, 0], np.cross(triangles[:, 1], triangles[:, 2])).sum() / 6)
    return {'valid': finite and zero == 0 and duplicate == 0 and open_edges == 0 and nonmanifold == 0 and inconsistent == 0 and volume > 0, 'finite_coordinates': finite, 'vertices': len(vertices), 'exact_unique_vertices': len(unique), 'triangles': len(faces), 'zero_area_triangles': zero, 'duplicate_faces': duplicate, 'open_edges': open_edges, 'nonmanifold_edges': nonmanifold, 'inconsistent_winding_edges': inconsistent, 'signed_volume_mm3': volume, 'topology_weld': 'exact coordinate equality only; no tolerance weld'}


def source_parts(path):
    scene = trimesh.load(path, force='scene', process=False)
    parts = []
    for node in sorted(scene.graph.nodes_geometry):
        transform, geometry = scene.graph[node]
        mesh = scene.geometry[geometry]
        vertices = trimesh.transform_points(np.asarray(mesh.vertices, dtype=np.float64), transform)
        faces = np.asarray(mesh.faces, dtype=np.int64).copy()
        if np.linalg.det(transform[:3, :3]) < 0:
            faces = faces[:, [0, 2, 1]]
        parts.append({'name': str(node), 'vertices': vertices, 'faces': faces, 'source_world_transform': transform.tolist()})
    if not parts:
        raise ValueError('No mesh nodes found in the GLB')
    return parts


def orient(parts, width):
    all_vertices = np.concatenate([part['vertices'] for part in parts])
    bounds = np.array([all_vertices.min(axis=0), all_vertices.max(axis=0)])
    scale = width / (bounds[1, 2] - bounds[0, 2])
    rotation = np.array([[0., 0., -1.], [0., 1., 0.], [1., 0., 0.]])
    transformed = all_vertices @ rotation.T * scale
    lo, hi = transformed.min(axis=0), transformed.max(axis=0)
    translation = np.array([128 - (lo[0] + hi[0]) / 2, 128 - (lo[1] + hi[1]) / 2, -lo[2]])
    matrix = np.eye(4)
    matrix[:3, :3] = rotation * scale
    matrix[:3, 3] = translation
    ranges = []
    offset = 0
    for part in parts:
        part['vertices'] = part['vertices'] @ rotation.T * scale + translation
        part['audit'] = audit(part['vertices'], part['faces'])
        ranges.append({'name': part['name'], 'first_triangle': offset, 'last_triangle': offset + len(part['faces']) - 1})
        offset += len(part['faces'])
    print_bounds = np.array([transformed.min(axis=0) + translation, transformed.max(axis=0) + translation])
    fits = bool((print_bounds[0] >= -1e-8).all() and (print_bounds[1] <= 256 + 1e-8).all())
    return {'assumed_width_mm': width, 'dimensional_accuracy_verified': False, 'scale_basis': 'original world scene Z extent; 140 mm is an assumed display/form size', 'source_world_bounds': bounds.tolist(), 'scale_mm_per_source_unit': scale, 'world_to_printer_matrix': matrix.tolist(), 'axis_mapping': {'printer_X': '-source_Z', 'printer_Y': '+source_Y', 'printer_Z': '+source_X'}, 'rotation_determinant': float(np.linalg.det(rotation)), 'print_bounds_mm': print_bounds.tolist(), 'print_dimensions_mm': (print_bounds[1] - print_bounds[0]).tolist(), 'bed_mm': [256, 256], 'fits_256mm_build_volume': fits, 'bed_min_z_mm': float(print_bounds[0, 2]), 'build_objects': 1, 'volumes': ranges, 'geometry_modified': False, 'mesh_simplified': False, 'topology_modified': False, 'logical_part_separation_verified': False, 'purpose': 'assembled form, not a screw-fit kit'}


def concatenated(parts):
    vertices, faces = [], []
    offset = 0
    for part in parts:
        vertices.append(part['vertices'])
        faces.append(part['faces'] + offset)
        offset += len(part['vertices'])
    return np.concatenate(vertices), np.concatenate(faces)


def export_stl(path, parts):
    count = sum(len(part['faces']) for part in parts)
    record_type = np.dtype([('normal', '<f4', (3,)), ('vertices', '<f4', (3, 3)), ('attribute', '<u2')])
    with path.open('wb') as stream:
        stream.write(b'Entropi native high-detail assembled Tripo form'.ljust(80, b'\0'))
        stream.write(struct.pack('<I', count))
        for part in parts:
            triangles = part['vertices'][part['faces']]
            normals = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
            norms = np.linalg.norm(normals, axis=1)
            normals = np.divide(normals, norms[:, None], out=np.zeros_like(normals), where=norms[:, None] != 0)
            records = np.zeros(len(triangles), dtype=record_type)
            records['normal'] = normals
            records['vertices'] = triangles
            stream.write(records.tobytes())
    records = np.fromfile(path, dtype=record_type, offset=84)
    checks = {}
    offset = 0
    maximum_error = 0.
    for part in parts:
        size = len(part['faces'])
        triangles = records['vertices'][offset:offset + size].astype(np.float64)
        original = part['vertices'][part['faces']]
        maximum_error = max(maximum_error, float(np.linalg.norm(triangles - original, axis=2).max()))
        vertices = triangles.reshape(-1, 3)
        faces = np.arange(len(vertices)).reshape(-1, 3)
        checks[part['name']] = audit(vertices, faces)
        offset += size
    return {'valid': all(item['valid'] for item in checks.values()), 'format': 'binary STL float32', 'triangles_written': count, 'triangles_read_back': len(records), 'maximum_vertex_rounding_displacement_mm': maximum_error, 'native_triangle_count_preserved': len(records) == count, 'parts': checks, 'sha256': digest(path), 'bytes': path.stat().st_size}


def export_3mf(path, parts, profile, poses):
    content_types = '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>'
    relationships = '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>'
    config = ET.Element('config')
    obj = ET.SubElement(config, 'object', {'id': '1', 'instances_count': '1'})
    ET.SubElement(obj, 'metadata', {'type': 'object', 'key': 'name', 'value': NAME})
    for part in poses['volumes']:
        volume = ET.SubElement(obj, 'volume', {'firstid': str(part['first_triangle']), 'lastid': str(part['last_triangle'])})
        ET.SubElement(volume, 'metadata', {'type': 'volume', 'key': 'name', 'value': part['name']})
        ET.SubElement(volume, 'metadata', {'type': 'volume', 'key': 'volume_type', 'value': 'ModelPart'})
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        archive.writestr('[Content_Types].xml', content_types)
        archive.writestr('_rels/.rels', relationships)
        archive.writestr('Metadata/Slic3r_PE.config', '; generated by PrusaSlicer 2.7.2\n\n' + '\n'.join('; ' + line for line in profile.splitlines()) + '\n')
        archive.writestr('Metadata/Slic3r_PE_model.config', ET.tostring(config, encoding='utf-8', xml_declaration=True))
        archive.writestr('Metadata/print-settings.json', json.dumps({'profile': 'generic PLA; 0.4 mm nozzle; 0.2 mm layers; 256 mm bed; actual P1S firmware/profile not verified', 'support': 'automatic everywhere, including bridges', 'assumed_width_mm': poses['assumed_width_mm'], 'gcode_delivered': False, 'purpose': poses['purpose']}, indent=2))
        with archive.open('3D/3dmodel.model', 'w') as stream:
            stream.write(('<?xml version="1.0" encoding="UTF-8"?><model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><metadata name="Title">' + escape(NAME) + '</metadata><resources><object id="1" type="model" name=' + quoteattr(NAME) + '><mesh><vertices>').encode())
            for part in parts:
                for start in range(0, len(part['vertices']), 10000):
                    lines = ['<vertex x="%.17g" y="%.17g" z="%.17g"/>' % tuple(vertex) for vertex in part['vertices'][start:start + 10000]]
                    stream.write(''.join(lines).encode())
            stream.write(b'</vertices><triangles>')
            offset = 0
            for part in parts:
                for start in range(0, len(part['faces']), 10000):
                    lines = ['<triangle v1="%d" v2="%d" v3="%d"/>' % tuple(face + offset) for face in part['faces'][start:start + 10000]]
                    stream.write(''.join(lines).encode())
                offset += len(part['vertices'])
            stream.write(b'</triangles></mesh></object></resources><build><item objectid="1"/></build></model>')
    vertices, faces = concatenated(parts)
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError('3MF archive failed ZIP integrity check')
        model = ET.fromstring(archive.read('3D/3dmodel.model'))
        mesh = model.find('{*}resources/{*}object/{*}mesh')
        read_vertices = np.array([[float(vertex.attrib[key]) for key in ['x', 'y', 'z']] for vertex in mesh.find('{*}vertices')])
        read_faces = np.array([[int(face.attrib[key]) for key in ['v1', 'v2', 'v3']] for face in mesh.find('{*}triangles')])
        exact = np.array_equal(vertices, read_vertices) and np.array_equal(faces, read_faces)
        volumes = len(ET.fromstring(archive.read('Metadata/Slic3r_PE_model.config')).findall('object/volume'))
        objects = len(model.findall('{*}resources/{*}object'))
        build_items = len(model.findall('{*}build/{*}item'))
    return {'valid': exact and objects == 1 and build_items == 1 and volumes == len(parts), 'coordinate_significant_digits': 17, 'exact_float64_coordinates_and_indices_roundtrip': exact, 'triangles': len(read_faces), 'core_objects': objects, 'build_items': build_items, 'named_volumes': volumes, 'sha256': digest(path), 'bytes': path.stat().st_size}


def parse_profile(text):
    return {line.split(' = ', 1)[0]: line.split(' = ', 1)[1] for line in text.splitlines() if ' = ' in line and not line.startswith(('#', ';'))}


def slicer_run(binary, args):
    env = os.environ.copy()
    env['LD_LIBRARY_PATH'] = '/tmp/entropi-prusa/root/usr/lib/x86_64-linux-gnu' + (':' + env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
    result = subprocess.run([str(binary)] + [str(arg) for arg in args], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors='replace', env=env)
    if result.returncode:
        raise RuntimeError('PrusaSlicer failed:\n' + result.stdout[-12000:])
    return result.stdout


def toolpaths(path):
    xy = np.array([0., 0.])
    absolute_e = 0.
    relative_e = False
    relative_xyz = False
    role = ''
    counts = {'xy_extrusion_moves': 0, 'model_xy_extrusion_moves': 0, 'support_xy_extrusion_moves': 0, 'perimeter_xy_extrusion_moves': 0, 'layers': 0}
    support_filament = 0.
    lo = np.array([math.inf, math.inf])
    hi = np.array([-math.inf, -math.inf])
    stats = {}
    with path.open() as stream:
        for raw in stream:
            line = raw.strip()
            if line == ';LAYER_CHANGE':
                counts['layers'] += 1
            if line.startswith(';TYPE:'):
                role = line[6:].lower()
            if line.startswith('; ') and ' = ' in line:
                key, value = line[2:].split(' = ', 1)
                if key in ['filament used [mm]', 'filament used [g]', 'estimated printing time (normal mode)']:
                    stats[key] = value
            command = line.split(';', 1)[0].strip()
            if command == 'M83':
                relative_e = True
            elif command == 'M82':
                relative_e = False
            elif command == 'G90':
                relative_xyz = False
            elif command == 'G91':
                relative_xyz = True
            tokens = {key: float(value) for key, value in re.findall(r'\b([XYE])([-+]?(?:\d*\.\d+|\d+\.?\d*))', command)}
            if command.startswith('G92 '):
                absolute_e = tokens.get('E', absolute_e)
                for axis, key in enumerate(['X', 'Y']):
                    xy[axis] = tokens.get(key, xy[axis])
            if command.split(' ', 1)[0] not in ['G0', 'G1']:
                continue
            new_xy = xy.copy()
            for axis, key in enumerate(['X', 'Y']):
                if key in tokens:
                    new_xy[axis] = xy[axis] + tokens[key] if relative_xyz else tokens[key]
            delta_e = tokens.get('E', 0.) if relative_e else tokens.get('E', absolute_e) - absolute_e
            if 'E' in tokens:
                absolute_e = absolute_e + tokens['E'] if relative_e else tokens['E']
            if delta_e > 1e-10 and np.linalg.norm(new_xy - xy) > 1e-8:
                counts['xy_extrusion_moves'] += 1
                lo = np.minimum(lo, np.minimum(xy, new_xy))
                hi = np.maximum(hi, np.maximum(xy, new_xy))
                if role.startswith('support material'):
                    counts['support_xy_extrusion_moves'] += 1
                    support_filament += delta_e
                elif role and 'skirt' not in role and 'wipe tower' not in role:
                    counts['model_xy_extrusion_moves'] += 1
                    if 'perimeter' in role:
                        counts['perimeter_xy_extrusion_moves'] += 1
            xy = new_xy
    finite = bool(np.isfinite(lo).all() and np.isfinite(hi).all())
    counts.update({'extrusion_xy_bounds_mm': [lo.tolist(), hi.tolist()], 'extrusion_within_256mm_bed': finite and bool((lo >= 0).all() and (hi <= 256).all()), 'support_filament_mm': support_filament, 'statistics': stats})
    counts['valid'] = counts['layers'] > 0 and counts['model_xy_extrusion_moves'] > 0 and counts['support_xy_extrusion_moves'] > 0 and counts['perimeter_xy_extrusion_moves'] > 0 and counts['extrusion_within_256mm_bed']
    return counts


def validate_slice(binary, path, profile_path, directory, expected_volumes, expected_triangles):
    effective = directory / 'effective.ini'
    slicer_run(binary, ['--load', profile_path, '--save', effective])
    expected = parse_profile(effective.read_text())
    reloaded = directory / 'reloaded.ini'
    slicer_run(binary, ['--save', reloaded, path])
    actual = parse_profile(reloaded.read_text())
    keys = ['bed_shape', 'max_print_height', 'nozzle_diameter', 'filament_type', 'layer_height', 'perimeters', 'fill_density', 'fill_pattern', 'support_material', 'support_material_auto', 'support_material_buildplate_only', 'dont_support_bridges']
    matches = all(actual.get(key) == expected.get(key) for key in keys)
    roundtrip = directory / 'roundtrip.3mf'
    info = slicer_run(binary, ['--dont-arrange', '--no-ensure-on-bed', '--info', path])
    export_log = slicer_run(binary, ['--dont-arrange', '--no-ensure-on-bed', '--export-3mf', '--output', roundtrip, path])
    with zipfile.ZipFile(roundtrip) as archive:
        model = ET.fromstring(archive.read('3D/3dmodel.model'))
        model_config = ET.fromstring(archive.read('Metadata/Slic3r_PE_model.config'))
        objects = len(model_config.findall('object'))
        volumes = len(model_config.findall('object/volume'))
        build_items = len(model.findall('{*}build/{*}item'))
        triangle_count = len(model.findall('{*}resources/{*}object/{*}mesh/{*}triangles/{*}triangle'))
    gcode = directory / 'validation-only.gcode'
    log = slicer_run(binary, ['--dont-arrange', '--no-ensure-on-bed', '--load', profile_path, '--export-gcode', '--output', gcode, path])
    result = toolpaths(gcode)
    combined_log = info + '\n' + export_log + '\n' + log
    (ROOT / 'verification/slicer-log.txt').write_text(combined_log)
    warnings = [line for line in combined_log.splitlines() if re.search(r'\bwarning\b|\berror\b', line, re.IGNORECASE)]
    result.update({'slicer': 'PrusaSlicer 2.7.2', 'embedded_generic_profile_reloaded_correctly': matches, 'profile_keys_verified': keys, 'reloaded_profile_values': {key: actual.get(key) for key in keys}, 'slicer_object_count': objects, 'slicer_volume_count': volumes, 'slicer_build_items': build_items, 'triangles_after_slicer_import_export': triangle_count, 'native_triangle_count_preserved_by_slicer': triangle_count == expected_triangles, 'warnings': warnings, 'physical_print_tested': False, 'actual_Bambu_P1S_profile_verified': False, 'gcode_delivered': False, 'scale_is_assumed': True, 'profile_portability': 'Standard 3MF geometry is portable; generic Prusa settings are verified only in PrusaSlicer. Select the actual P1S printer and PLA profile in Bambu Studio.'})
    result['valid'] = result['valid'] and matches and objects == 1 and build_items == 1 and volumes == expected_volumes and triangle_count == expected_triangles and not warnings
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=Path)
    parser.add_argument('--width-mm', type=float, default=140.)
    parser.add_argument('--slicer', type=Path, default=Path('/tmp/entropi-prusa/root/usr/bin/prusa-slicer'))
    args = parser.parse_args()
    (ROOT / 'print').mkdir(exist_ok=True)
    (ROOT / 'verification').mkdir(exist_ok=True)
    parts = source_parts(args.input)
    poses = orient(parts, args.width_mm)
    poses['input_file'] = str(args.input.resolve())
    poses['input_sha256'] = digest(args.input)
    write_json(ROOT / 'print/poses.json', poses)
    audits = {part['name']: part['audit'] for part in parts}
    if not all(item['valid'] for item in audits.values()) or not poses['fits_256mm_build_volume']:
        write_json(ROOT / 'verification/print-export.json', {'valid': False, 'parts': audits, 'pose': poses})
        raise ValueError('Exact-coordinate source topology or build volume check failed')
    profile = ROOT / 'print/generic-PLA-0.4mm-0.2mm.ini'
    profile.write_text(PROFILE)
    stl = export_stl(ROOT / 'print/Entropi-140mm.stl', parts)
    print('STL exported and read back:', stl['triangles_read_back'], 'triangles; valid =', stl['valid'], flush=True)
    stl['deliverable'] = stl['valid']
    if not stl['valid']:
        diagnostic = Path(tempfile.gettempdir()) / ('entropi-tripo-float32-diagnostic-' + poses['input_sha256'][:12] + '.stl')
        (ROOT / 'print/Entropi-140mm.stl').replace(diagnostic)
        stl['diagnostic_path'] = str(diagnostic)
        stl['exclusion_reason'] = 'Float32 precision creates microscopic topology defects; binary STL excluded from print deliverables. Exact 17-digit 3MF is primary.'
    with tempfile.TemporaryDirectory(prefix='entropi-tripo-slice-') as temporary:
        directory = Path(temporary)
        effective = directory / 'effective.ini'
        slicer_run(args.slicer, ['--load', profile, '--save', effective])
        effective_text = effective.read_text()
        profile.write_text(effective_text)
        three_mf = export_3mf(ROOT / 'print/Entropi-140mm.3mf', parts, effective_text, poses)
        report = {'valid': three_mf['valid'], 'input_sha256': poses['input_sha256'], 'parts': audits, 'native_triangles': sum(len(part['faces']) for part in parts), 'scale_is_assumed': True, 'geometry_simplified': False, 'source_geometry_modified': False, 'primary_print_file': 'print/Entropi-140mm.3mf', 'three_mf': three_mf, 'stl': stl}
        if not stl['valid']:
            report['stl_precision_limitation'] = 'Float32 STL precision changes microscopic sliver topology. Use the exact float64-coordinate 3MF as the primary file; no source repair or simplification was performed.'
        write_json(ROOT / 'verification/print-export.json', report)
        if not three_mf['valid']:
            raise ValueError('3MF readback check failed')
        print('3MF exported: one assembled object,', len(parts), 'volumes. Starting supported slice.', flush=True)
        slice_report = validate_slice(args.slicer, ROOT / 'print/Entropi-140mm.3mf', profile, directory, len(parts), report['native_triangles'])
        write_json(ROOT / 'verification/slicer-checks.json', slice_report)
    print(json.dumps({'print_export_valid': report['valid'], 'stl_valid': stl['valid'], 'slicer_valid': slice_report['valid'], 'objects': slice_report['slicer_object_count'], 'volumes': slice_report['slicer_volume_count'], 'layers': slice_report['layers'], 'model_xy_extrusion_moves': slice_report['model_xy_extrusion_moves'], 'support_xy_extrusion_moves': slice_report['support_xy_extrusion_moves'], 'warnings': slice_report['warnings']}), flush=True)
    raise SystemExit(0 if report['valid'] and slice_report['valid'] else 1)


if __name__ == '__main__':
    main()
