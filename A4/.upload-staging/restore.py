import hashlib
import json
import os
from pathlib import Path
import shutil

root=Path(__file__).resolve().parents[2]
staging=root/'A4/.upload-staging'
manifest=json.loads((staging/'import.json').read_text())

def location(name):
    path=(root/name).resolve()
    if not path.is_relative_to(root/'A4') and path!=root/'README.md':
        raise ValueError('Invalid design path')
    return path

for item in manifest['files']:
    destination=location(item['file'])
    destination.parent.mkdir(parents=True,exist_ok=True)
    temporary=destination.with_name(destination.name+'.assembling')
    digest=hashlib.sha256()
    total=0
    with temporary.open('wb') as output:
        for part in item['parts']:
            source=location(part['file'])
            if not source.is_relative_to(staging/'chunks'):
                raise ValueError('Invalid chunk path')
            data=source.read_bytes()
            if len(data)!=part['bytes'] or hashlib.sha256(data).hexdigest()!=part['sha256']:
                raise ValueError('Chunk verification failed: '+part['file'])
            output.write(data)
            digest.update(data)
            total+=len(data)
        output.flush()
        os.fsync(output.fileno())
    if total!=item['bytes'] or digest.hexdigest()!=item['sha256']:
        raise ValueError('Restored file verification failed: '+item['file'])
    temporary.replace(destination)
    print('Restored '+item['file'],flush=True)

verified=[]
for item in manifest['verify_files']:
    path=location(item['file'])
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if path.stat().st_size!=item['bytes'] or digest!=item['sha256']:
        raise ValueError('Final verification failed: '+item['file'])
    verified.append(item)
report={'all_files_verified':True,'file_count':len(verified),'restored_large_files':len(manifest['files']),'source_commit':manifest['source_commit'],'staging_commit':os.environ.get('GITHUB_SHA'),'verification':'Exact original size and SHA256 for every new or updated file','files':verified}
(root/'A4/import_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
shutil.rmtree(staging)
print('All '+str(len(verified))+' design files verified',flush=True)
