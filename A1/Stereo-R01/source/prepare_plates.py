"""Write three named, geometry-only 3MF plates from the verified print STLs."""
from pathlib import Path
import hashlib
import json
import zipfile
import xml.etree.ElementTree as ET

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
NS = 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
ET.register_namespace('', NS)
LAYOUT = [
    ('Plate-00-prove', [('P10', 100, 110), ('P04', 80, 165), ('P05', 125, 165), ('P06', 160, 110)]),
    ('Plate-01-front', [('P01', 128, 128)]),
    ('Plate-02-bak-og-berar', [('P02', 128, 70), ('P03', 128, 170), ('P08', 78, 225), ('P09', 170, 225)]),
]


def tag(name):
    return '{' + NS + '}' + name


def make():
    source = json.loads((ROOT / 'print/print-manifest.json').read_text())
    records = {p['id']: p for p in source['parts']}
    output = ROOT / 'print/plates'
    output.mkdir(exist_ok=True)
    plates = []
    seen = []
    for name, positions in LAYOUT:
        model = ET.Element(tag('model'), {'unit': 'millimeter', 'xml:lang': 'nn-NO'})
        ET.SubElement(model, tag('metadata'), {'name': 'Title'}).text = 'FormNerd Stereo R01 ' + name
        resources = ET.SubElement(model, tag('resources'))
        build = ET.SubElement(model, tag('build'))
        entries, boxes = [], []
        scene = {'objects': [], 'camera': {'direction': [0, 0, 1], 'up': [0, 1, 0]}, 'mode': 'line', 'size': [1800, 1800], 'margin': .09, 'line_width': 1.8}
        for index, (pid, x, y) in enumerate(positions, 1):
            p = records[pid]
            path = ROOT / p['path']
            if hashlib.sha256(path.read_bytes()).hexdigest() != p['sha256']:
                raise RuntimeError(f'Source STL changed: {pid}')
            mesh = trimesh.load(path, force='mesh')
            if not mesh.is_watertight or not mesh.is_winding_consistent or mesh.volume <= 0:
                raise RuntimeError(f'Invalid source: {pid}')
            vertices = mesh.vertices + [x, y, 0]
            bounds = np.array([vertices.min(0), vertices.max(0)])
            if np.any(bounds[0, :2] < 8) or np.any(bounds[1, :2] > 248) or abs(bounds[0, 2]) > .001:
                raise RuntimeError(f'Outside P1S bed or above plate: {pid}')
            for old_pid, box in boxes:
                gap = np.maximum(bounds[0, :2] - box[1, :2], box[0, :2] - bounds[1, :2]).max()
                if gap < 8:
                    raise RuntimeError(f'Insufficient plate spacing: {old_pid}, {pid}')
            boxes.append((pid, bounds))
            obj = ET.SubElement(resources, tag('object'), {'id': str(index), 'name': pid, 'type': 'model'})
            xmlmesh = ET.SubElement(obj, tag('mesh'))
            vs = ET.SubElement(xmlmesh, tag('vertices'))
            for v in vertices:
                ET.SubElement(vs, tag('vertex'), dict(zip('xyz', [format(float(c), '.10g') for c in v])))
            ts = ET.SubElement(xmlmesh, tag('triangles'))
            for f in mesh.faces:
                ET.SubElement(ts, tag('triangle'), dict(zip(['v1', 'v2', 'v3'], [str(int(c)) for c in f])))
            ET.SubElement(build, tag('item'), {'objectid': str(index)})
            entries.append({'id': pid, 'source': p['path'], 'source_sha256': p['sha256'], 'translation_mm': [x, y, 0], 'bounds_mm': bounds.tolist(), 'triangles': len(mesh.faces)})
            scene['objects'].append({'id': pid, 'path': p['path'], 'translation': [x, y, 0], 'color': '#62676c'})
            seen.append(pid)
        path = output / (name + '.3mf')
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr('[Content_Types].xml', '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
            z.writestr('_rels/.rels', '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
            z.writestr('3D/3dmodel.model', ET.tostring(model, encoding='utf-8', xml_declaration=True))
        with zipfile.ZipFile(path) as z:
            check = ET.fromstring(z.read('3D/3dmodel.model'))
            for obj, entry in zip(check.find(tag('resources')), entries):
                raw = obj.find(tag('mesh'))
                v = np.array([[float(q.get(c)) for c in 'xyz'] for q in raw.find(tag('vertices'))])
                f = np.array([[int(q.get(c)) for c in ['v1', 'v2', 'v3']] for q in raw.find(tag('triangles'))])
                loaded = trimesh.Trimesh(v, f, process=True)
                if not loaded.is_watertight or len(loaded.split(only_watertight=False)) != 1:
                    raise RuntimeError(f'3MF roundtrip failed: {entry["id"]}')
                original = trimesh.load(ROOT / entry['source'], force='mesh')
                if abs(loaded.volume - original.volume) > .01:
                    raise RuntimeError(f'3MF volume changed: {entry["id"]}')
        scene_path = ROOT / 'review' / (name + '.json')
        scene_path.write_text(json.dumps(scene, indent=2))
        plates.append({'id': name, 'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'objects': entries, 'geometry_roundtrip_passed': True})
    if sorted(seen) != sorted(records):
        raise RuntimeError('Missing or duplicated print parts')
    result = {'units': 'mm', 'bed_mm': [256, 256], 'status': 'geometry-only; slicing pending', 'source_manifest_sha256': source['source_manifest_sha256'], 'plates': plates}
    (output / 'plate-manifest.json').write_text(json.dumps(result, indent=2))
    print(json.dumps({'plates': len(plates), 'unique_parts': len(seen), 'roundtrip': 'passed'}))


if __name__ == '__main__':
    make()
