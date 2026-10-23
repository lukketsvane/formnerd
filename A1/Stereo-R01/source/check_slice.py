"""Inspect the actual G-code archive. Never connects to or starts a printer."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('archive', type=Path)
    args = parser.parse_args()
    path = args.archive.resolve()
    with zipfile.ZipFile(path) as z:
        files = z.namelist()
        codes = [name for name in files if name.endswith('.gcode')]
        if not codes:
            raise RuntimeError('Archive has no generated G-code')
        gcode = '\n'.join(z.read(name).decode('utf-8') for name in codes)
        configs = {name: z.read(name).decode('utf-8', errors='replace') for name in files if name.endswith(('.config', '.json'))}
    movements = re.findall(r'^G[0123]\b[^;\n]*\bE(-?[\d.]+)[^;\n]*', gcode, re.M)
    positive = sum(float(e) > 0 for e in movements)
    if positive < 100 or not re.search(r'^G28\b', gcode, re.M) or not re.search(r'^M10[49]\b', gcode, re.M):
        raise RuntimeError('Missing extrusion, homing or nozzle heating commands')
    layer_tags = re.findall(r'^;\s*(?:layer num/total_layer_count:|LAYER_CHANGE|CHANGE_LAYER|LAYER:).*$', gcode, re.M)
    if not layer_tags:
        raise RuntimeError('No layer markers found in G-code')
    profile = path.parent / 'profiles/machine.json'
    if not profile.exists():
        raise RuntimeError('Missing exact machine profile')
    machine = json.loads(profile.read_text(encoding='utf-8-sig'))
    if 'P1S' not in str(machine.get('printer_model', '')):
        raise RuntimeError('Machine profile is not P1S')
    name = path.name.removesuffix('.gcode.3mf')
    plates = json.loads((ROOT / 'print/plates/plate-manifest.json').read_text())
    plate = next(p for p in plates['plates'] if p['id'] == name)
    config_text = '\n'.join(configs.values())
    missing = [p['id'] for p in plate['objects'] if p['id'] not in config_text]
    if missing:
        raise RuntimeError(f'Part names missing from sliced archive: {missing}')
    support = len(re.findall(r'^;\s*(?:FEATURE:|TYPE:)\s*Support', gcode, re.M | re.I))
    if any(p['id'] in ['P01', 'P02'] for p in plate['objects']) and support == 0:
        raise RuntimeError('Shell slice contains no support features')
    stats = [line for line in gcode.splitlines()[:200] if re.search('estimated|filament.*(?:weight|length|volume)|total.*layer', line, re.I)]
    result = {'plate': name, 'archive_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'source_3mf_sha256': plate['sha256'], 'machine': machine.get('printer_model'), 'status': 'generated G-code inspected; physical printing and fit remain untested', 'part_ids': [p['id'] for p in plate['objects']], 'layer_markers': len(layer_tags), 'positive_extrusion_moves': positive, 'support_feature_sections': support, 'header_statistics': stats, 'profile_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(profile.parent.glob('*.json'))}}
    report = path.with_name(name + '.json')
    report.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
