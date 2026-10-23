import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT.parent / 'deliverables'
DEST.mkdir(exist_ok=True)
audit = json.loads((ROOT / 'verification/independent-audit.json').read_text())
if audit['status'] != 'digital_checks_pass_for_tested_nominal_geometry':
    raise RuntimeError('Independent digital checks have unresolved blockers')
for path, digest in audit['source_hashes'].items():
    if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != digest:
        raise RuntimeError(f'Audited source changed: {path}')
prints = json.loads((ROOT / 'print/print-manifest.json').read_text())
if not all(p['watertight'] and p['components'] == 1 for p in prints['parts']):
    raise RuntimeError('Print export topology check failed')
if prints['source_manifest_sha256'] != hashlib.sha256((ROOT / 'cad/assembly-manifest.json').read_bytes()).hexdigest():
    raise RuntimeError('Print export is from a different CAD revision')
for part in prints['parts']:
    if part['sha256'] != hashlib.sha256((ROOT / part['path']).read_bytes()).hexdigest():
        raise RuntimeError(f"Print file changed: {part['path']}")
manual = json.loads((ROOT / 'manual/render-audit.json').read_text())
if manual['pdf_sha256'] != hashlib.sha256((ROOT / 'manual/FormNerd-Stereo-R01-montering.pdf').read_bytes()).hexdigest():
    raise RuntimeError('Manual PDF changed after render audit')
for path, digest in manual['source_geometry_sha256'].items():
    if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != digest:
        raise RuntimeError(f'Manual geometry changed: {path}')
files = []
for path in ROOT.rglob('*'):
    if not path.is_file() or '__pycache__' in path.parts or path.suffix == '.pyc':
        continue
    rel = path.relative_to(ROOT)
    if str(rel).startswith('manual/figures/') and str(rel) not in manual['figure_files']:
        continue
    if rel.parts[0] == 'review' and path.name not in ['hero.png', 'hero-scene.json', 'hero.anchors.json'] and not path.name.startswith('Plate-'):
        continue
    if path.name == 'release-manifest.json':
        continue
    files.append(path)
release = {'revision': 'Stereo R01', 'digital_status': audit['status'], 'physical_fit_tested': False, 'slicer_validated': False, 'functional_camera_validated': False, 'files': [{'path': str(p.relative_to(ROOT)), 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(files)]}
(ROOT / 'release-manifest.json').write_text(json.dumps(release, indent=2))
files.append(ROOT / 'release-manifest.json')
full = DEST / 'FormNerd-Stereo-R01-CAD.zip'
with zipfile.ZipFile(full, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
    for path in sorted(files):
        archive.write(path, Path('FormNerd-Stereo-R01') / path.relative_to(ROOT))
small = DEST / 'FormNerd-Stereo-R01-print.zip'
with zipfile.ZipFile(small, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
    for path in sorted(files):
        rel = path.relative_to(ROOT)
        if rel.parts[0] == 'print' or str(rel) in ['README.md', 'LOCAL-AGENT.txt', 'Open-Print.ps1', 'source/restore_payloads.py', 'cad/assembly-manifest.json', 'verification/independent-audit.json', 'manual/FormNerd-Stereo-R01-montering.pdf']:
            archive.write(path, Path('FormNerd-Stereo-R01-print') / rel)
for path in [full, small]:
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise RuntimeError(f'Archive CRC validation failed: {path}')
print(json.dumps([{'path': str(p), 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in [full, small]], indent=2))
