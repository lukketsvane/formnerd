import json
import hashlib
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


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



def run_plate(path):
    binary = Path('/tmp/entropi-prusa/root/usr/bin/prusa-slicer')
    if not binary.exists():
        located = shutil.which('prusa-slicer')
        if not located:
            raise RuntimeError('PrusaSlicer is not installed')
        binary = Path(located)
    environment = os.environ.copy()
    bundled = Path('/tmp/entropi-prusa/root/usr/lib/x86_64-linux-gnu')
    if bundled.exists():
        environment['LD_LIBRARY_PATH'] = str(bundled)
    expected_report = json.loads((ROOT / 'verification/exports.json').read_text())
    plate = next(item for item in expected_report['plates'] if item['path'] == str(path.relative_to(ROOT)))
    expected = {item['name'] for item in plate['parts']}
    folder = Path(tempfile.gettempdir()) / 'a1-assembly-slicing-r01' / path.stem
    folder.mkdir(parents=True, exist_ok=True)
    gcode = Path(folder) / 'validation-only.gcode'
    signature = hashlib.sha256(path.read_bytes() + (ROOT / 'print/generic-test-PLA-0.4mm-0.2mm.ini').read_bytes()).hexdigest()
    signature_path = Path(folder) / 'input-sha256.txt'
    args = [str(binary), '--threads', '2', '--dont-arrange', '--no-ensure-on-bed', '--load', str(ROOT / 'print/generic-test-PLA-0.4mm-0.2mm.ini'), '--export-gcode', '--output', str(gcode), str(path)]
    log_path = ROOT / 'verification' / (path.stem + '-slicer.log')
    if gcode.exists() and signature_path.exists() and signature_path.read_text() == signature:
        log = log_path.read_text()
    else:
        result = subprocess.run(args, env=environment, text=True, capture_output=True)
        log = result.stdout + '\n' + result.stderr
        log_path.write_text(log)
        if result.returncode != 0 or not gcode.exists():
            raise RuntimeError(path.name + ' slicing failed: ' + log[-2000:])
        signature_path.write_text(signature)
    report = toolpaths(gcode)
    found = set()
    with gcode.open() as stream:
        for line in stream:
            match = re.search(r'; printing object (.*?) id:', line)
            if match:
                found.add(match.group(1))
    warnings = [line for line in log.splitlines() if re.search(r'\bwarning\b|\berror\b', line, re.I)]
    report.update({'plate': str(path.relative_to(ROOT)), 'expected_object_names': sorted(expected), 'gcode_object_names': sorted(found), 'all_expected_objects_in_gcode': expected <= found, 'warnings': warnings, 'slicer': 'PrusaSlicer 2.7.2', 'physical_print_tested': False, 'actual_Bambu_P1S_profile_verified': False, 'gcode_delivered': False})
    report['valid'] = report['valid'] and expected <= found and not warnings
    return report


if __name__ == '__main__':
    plates = sorted((ROOT / 'print').glob('A1-plate-*.3mf'))
    with ThreadPoolExecutor(max_workers=2) as pool:
        reports = list(pool.map(run_plate, plates))
    result = {'valid': bool(reports) and all(item['valid'] for item in reports), 'profile': 'generic-test-PLA-0.4mm-0.2mm.ini', 'physical_print_tested': False, 'actual_Bambu_P1S_profile_verified': False, 'plates': reports}
    destination = ROOT / 'verification/slicing.json'
    destination.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)
    raise SystemExit(0 if result['valid'] else 1)
