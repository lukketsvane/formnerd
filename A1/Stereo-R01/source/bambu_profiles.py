"""Flatten installed official Bambu profiles for an explicit P1S trial slice."""
from pathlib import Path
import argparse
import json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('profiles', type=Path, help='Bambu resources/profiles/BBL')
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    index = {}
    for kind in ['machine', 'process', 'filament']:
        for path in (args.profiles / kind).glob('*.json'):
            data = json.loads(path.read_text(encoding='utf-8-sig'))
            index[kind, data.get('name', path.stem)] = data

    def flatten(kind, name, chain=()):
        if name in chain:
            raise ValueError('Profile inheritance cycle')
        data = index[kind, name]
        result = flatten(kind, data['inherits'], chain + (name,)) if data.get('inherits') else {}
        for inc in data.get('include', []):
            result.update({k: v for k, v in flatten(kind, inc, chain + (name,)).items() if k not in ['name', 'setting_id', 'type', 'from', 'instantiation']})
        result.update({k: v for k, v in data.items() if k not in ['inherits', 'include']})
        return result

    choices = [('machine', 'Bambu Lab P1S 0.4 nozzle'), ('process', '0.16mm High Quality @BBL P1P'), ('filament', 'Bambu PLA Basic @BBL P1S 0.4 nozzle')]
    args.output.mkdir(parents=True, exist_ok=True)
    for kind, name in choices:
        data = flatten(kind, name)
        if kind == 'process':
            data.update({'wall_loops': '4', 'wall_generator': 'arachne', 'sparse_infill_density': '20%', 'sparse_infill_pattern': 'gyroid', 'enable_support': '1', 'support_type': 'tree(auto)', 'support_on_build_plate_only': '0', 'brim_type': 'auto_brim', 'brim_width': '6', 'curr_bed_type': 'Textured PEI Plate'})
        data['from'] = 'User'
        data['name'] = name + ' - FormNerd Stereo R01 trial'
        (args.output / (kind + '.json')).write_text(json.dumps(data, indent=2), encoding='utf-8')
        print(kind, name)


if __name__ == '__main__':
    main()
