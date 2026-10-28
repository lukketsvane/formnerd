"""Restore byte-identical large files from Git-friendly chunks, if present."""
from pathlib import Path
import hashlib
import json
import os
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    manifest = ROOT / 'large-files.json'
    if not manifest.exists():
        print('No split assets to restore.')
        return
    for entry in json.loads(manifest.read_text())['files']:
        target = ROOT / entry['path']
        if target.exists():
            if hashlib.sha256(target.read_bytes()).hexdigest() != entry['sha256']:
                raise RuntimeError(f'Existing file differs; preserve and resolve manually: {target}')
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=target.name + '.', dir=target.parent)
        try:
            h = hashlib.sha256()
            with os.fdopen(fd, 'wb') as out:
                for part in entry['chunks']:
                    data = (ROOT / part['path']).read_bytes()
                    if hashlib.sha256(data).hexdigest() != part['sha256']:
                        raise RuntimeError(f'Chunk hash mismatch: {part["path"]}')
                    h.update(data)
                    out.write(data)
            if h.hexdigest() != entry['sha256'] or Path(temporary).stat().st_size != entry['bytes']:
                raise RuntimeError(f'Restored file mismatch: {entry["path"]}')
            os.replace(temporary, target)
            print('Restored:', entry['path'])
        finally:
            if Path(temporary).exists():
                Path(temporary).unlink()


if __name__ == '__main__':
    main()
