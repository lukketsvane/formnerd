import hashlib
import json
import zipfile
from pathlib import Path
import numpy as np
from PIL import Image

P=Path(__file__).resolve().parents[2]
REPO=P.parents[2]
E=P/'electronics'
M=P/'mono-series'
manifest_file=E/'delivery-manifest.json'
manifest=json.loads(manifest_file.read_text())
qa=json.loads((E/'visual-qa.json').read_text())
checks=[]
for item in manifest['ordered_images']:
 file=Path(item['path'])
 digest=hashlib.sha256(file.read_bytes()).hexdigest()
 assert qa[item['id']]['status']=='passed',item['id']
 assert qa[item['id']]['sha256']==digest,item['id']
 im=Image.open(file)
 assert im.size==(2400,1800) and im.mode=='RGB',(file.name,im.size,im.mode)
 pixels=np.asarray(im)
 white=np.all(pixels==255,axis=2)
 assert white.any(),file.name
 edge_nonwhite=int(sum(np.any(edge!=255,axis=-1).sum() for edge in [pixels[0],pixels[-1],pixels[:,0],pixels[:,-1]]))
 assert item.get('intentional_detail_crop',False) or edge_nonwhite==0,file.name
 check={'id':item['id'],'filename':file.name,'repo_path':str(file.relative_to(REPO)),'sha256':digest,'bytes':file.stat().st_size,'dimensions':list(im.size),'mode':im.mode,'white_pixels':int(white.sum()),'edge_nonwhite':edge_nonwhite,'intentional_detail_crop':item.get('intentional_detail_crop',False),'visual_qa':qa[item['id']]}
 checks.append(check)
 item.update({'sha256':digest,'bytes':file.stat().st_size,'qa_status':'passed'})

assert len(checks)==21
for i in range(1,19):
 metadata=json.loads((M/f'render-{i:02}.json').read_text())
 assert len(metadata['electronics_assets'])==2
 assert metadata['samples']==96 and metadata['resolution']==[2400,1800]
assert json.loads((E/'assembly-verification.json').read_text())['status']=='passed'
(E/'image-checks.json').write_text(json.dumps({'status':'passed','count':21,'engine':'Blender4.3.2 Cycles CPU','samples':96,'images':checks},indent=2))

archive=Path(manifest['final_image_zip'])
archive_manifest=[{'id':i['id'],'filename':Path(i['path']).name,'label':i['label'],'sha256':i['sha256'],'intentional_detail_crop':i.get('intentional_detail_crop',False)} for i in manifest['ordered_images']]
readme='21 actual Blender Cycles renders, 2400×1800 RGB, 96 samples, white background.\n\nESP32-CAM front/back and MB programmer board, followed by six views each in matte black, neutral grey, and black/grey. Detail views are intentional close crops.\n\nElectronics are detailed reference reconstructions from sourced connector geometry and photographs. Package heights and photo-derived positions are nominal, not vendor-certified. Original R04 printed geometry is unchanged.\n\nNo AI-generated images are included. See the repository electronics/README.md and model provenance for source attribution and reproducibility.\n'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for item in manifest['ordered_images']:
  file=Path(item['path']);z.write(file,file.name)
 z.writestr('README.txt',readme)
 z.writestr('render-manifest.json',json.dumps(archive_manifest,indent=2))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None

public_files=[E/'.gitignore',E/'README.md',E/'PRIVATE_MODEL_README.md',E/'model-provenance.json',E/'mb-model-provenance.json',E/'assembly-verification.json',E/'visual-qa.json',E/'image-checks.json',E/'ESP32_MB_reconstructed.blend',M/'.gitignore',M/'README.md',M/'shot-plan.json',M/'render_mono.py',M/'run_batch.py',M/'batch-progress.json']
public_files.extend(sorted((E/'source').glob('*.py')))
public_files.extend(M/f'render-{i:02}.json' for i in range(1,19))
public_files.extend(Path(i['path']) for i in manifest['ordered_images'])
public_records=[]
for file in public_files:
 assert file.exists(),file
 public_records.append({'path':str(file.relative_to(REPO)),'bytes':file.stat().st_size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
public_manifest=E/'public-manifest.json'
public_manifest.write_text(json.dumps({'status':'verified','image_count':21,'render_engine':'Blender4.3.2 Cycles CPU','housing_geometry':'Unchanged R04 printed meshes','external_mesh_handling':'CAM source and derived .blend files omitted from public repository; explicit external dependency in build script','files':public_records},indent=2))
file_list=E/'public-file-list.json'
file_list.write_text(json.dumps([r['path'] for r in public_records]+[str(public_manifest.relative_to(REPO)),str(file_list.relative_to(REPO))],indent=2))
manifest['status']='complete;21images individually visually approved and verified'
manifest['archive_sha256']=hashlib.sha256(archive.read_bytes()).hexdigest()
manifest['archive_bytes']=archive.stat().st_size
manifest_file.write_text(json.dumps(manifest,indent=2))
print(json.dumps({'images':len(checks),'archive':str(archive),'archive_bytes':archive.stat().st_size,'public_files':len(public_records)+2,'status':'passed'}))
