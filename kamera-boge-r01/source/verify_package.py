import hashlib
import json
from pathlib import Path


root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / 'package-manifest.json').read_text(encoding='utf-8'))
failures = []
for entry in manifest['files']:
    path = (root / entry['path']).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        failures.append({'path': entry['path'], 'reason': 'missing or invalid path'})
        continue
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if path.stat().st_size != entry['bytes'] or digest != entry['sha256']:
        failures.append({'path': entry['path'], 'reason': 'size or hash mismatch'})
large_files = []
for entry in json.loads((root / 'large-files.json').read_text(encoding='utf-8'))['files']:
    path = root / entry['path']
    if not path.exists():
        large_files.append({'path': entry['path'], 'status': 'not assembled yet'})
        continue
    valid = path.stat().st_size == entry['bytes'] and hashlib.sha256(path.read_bytes()).hexdigest() == entry['sha256']
    large_files.append({'path': entry['path'], 'status': 'valid' if valid else 'invalid'})
    if not valid:
        failures.append({'path': entry['path'], 'reason': 'assembled size or hash mismatch'})
print(json.dumps({'passed': not failures, 'checked': len(manifest['files']), 'large_files': large_files, 'failures': failures}, indent=2))
raise SystemExit(1 if failures else 0)
