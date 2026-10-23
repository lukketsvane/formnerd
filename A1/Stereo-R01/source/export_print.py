import hashlib
import json
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
manifest_path = ROOT / 'cad/assembly-manifest.json'
manifest = json.loads(manifest_path.read_text())
destination = ROOT / 'print'
destination.mkdir(exist_ok=True)
results = []
for part in manifest['parts']:
    pid = part['id']
    angle = 0 if pid in ['P06', 'P10'] else (np.pi / 2 if pid == 'P02' else -np.pi / 2)
    transform = trimesh.transformations.rotation_matrix(angle, [1, 0, 0])
    mesh = trimesh.load(ROOT / part['stl'], force='mesh')
    original = mesh.copy()
    mesh.apply_transform(transform)
    delta = -np.r_[mesh.bounds.mean(axis=0)[:2], mesh.bounds[0, 2]]
    mesh.apply_translation(delta)
    transform[:3, 3] += delta
    file = destination / f'{pid}.stl'
    mesh.export(file)
    reloaded = trimesh.load(file, force='mesh')
    roundtrip = mesh.copy()
    roundtrip.apply_transform(np.linalg.inv(transform))
    error = float(np.max(np.abs(roundtrip.vertices - original.vertices)))
    results.append({'id': pid, 'path': str(file.relative_to(ROOT)), 'sha256': hashlib.sha256(file.read_bytes()).hexdigest(), 'assembly_to_print_transform': transform.tolist(), 'print_to_assembly_transform': np.linalg.inv(transform).tolist(), 'transform_roundtrip_max_error_mm': error, 'size_mm': reloaded.extents.tolist(), 'minimum_build_z_mm': float(reloaded.bounds[0, 2]), 'watertight': bool(reloaded.is_watertight), 'components': len(reloaded.split(only_watertight=False)), 'note': part['print_orientation']})
(destination / 'print-manifest.json').write_text(json.dumps({'units': 'mm', 'source_manifest_sha256': hashlib.sha256(manifest_path.read_bytes()).hexdigest(), 'status': 'unsliced candidates; support, bed contact and all layers require Bambu Studio inspection', 'profiles_embedded': False, 'parts': results}, indent=2))
print(json.dumps({'parts': len(results), 'watertight': all(x['watertight'] for x in results), 'max_transform_error_mm': max(x['transform_roundtrip_max_error_mm'] for x in results)}))
