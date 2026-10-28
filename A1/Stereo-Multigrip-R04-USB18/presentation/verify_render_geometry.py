import hashlib
import json
import struct
from pathlib import Path
import bpy
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'presentation'
source=json.loads((P/'scene_A3.json').read_text())
checks=[]
for item in source['items']:
 path=(P/item['stl']).resolve()
 data=path.read_bytes()
 n=struct.unpack_from('<I',data,80)[0]
 dt=np.dtype([('normal','<f4',(3,)),('v','<f4',(3,3)),('attr','<u2')])
 reference=np.frombuffer(data,dtype=dt,count=n,offset=84)['v'].astype(np.float64)
 obj=bpy.data.objects[item['name']]
 v=np.array([tuple(p.co) for p in obj.data.vertices],dtype=np.float64)
 f=np.array([tuple(p.vertices) for p in obj.data.polygons])
 actual=v[f]*1000
 error=float(np.abs(actual-reference).max())
 assert actual.shape==reference.shape
 assert error<.00001,(item['name'],error)
 assert len(obj.modifiers)==0,item['name']
 assert np.max(np.abs(np.array(obj.matrix_world)-np.eye(4)))<1e-9
 assert obj['source_sha256']==hashlib.sha256(data).hexdigest()
 checks.append({'name':item['name'],'triangles':n,'max_coordinate_error_mm':error,'modifiers':0})
objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
assert len(objects)==len(checks)
result={'status':'passed','source_revision':'abc4b921c989caf9e1e14d1babe25940b68502be','mesh_objects':len(checks),'triangles':sum(c['triangles'] for c in checks),'max_coordinate_error_mm':max(c['max_coordinate_error_mm'] for c in checks),'coordinate_precision_note':'STL millimetres converted to Blender float32 metres; sub-0.00001 mm quantisation only','extra_meshes':0,'geometry_modifiers':0,'checks':checks}
(P/'actual-render-verification.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:v for k,v in result.items() if k!='checks'}))
