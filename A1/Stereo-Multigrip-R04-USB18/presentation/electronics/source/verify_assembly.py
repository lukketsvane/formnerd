import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Matrix

p=argparse.ArgumentParser();p.add_argument('--output',required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
root=Path(__file__).resolve().parents[3]
presentation=root/'presentation'
source=json.loads((presentation/'scene_A3.json').read_text())
checks=[]
for item in source['items']:
 if item['name'].startswith(('REF_L_','REF_R_')):continue
 path=(presentation/item['stl']).resolve();data=path.read_bytes();n=struct.unpack_from('<I',data,80)[0]
 dt=np.dtype([('normal','<f4',(3,)),('v','<f4',(3,3)),('attr','<u2')])
 reference=np.frombuffer(data,dtype=dt,count=n,offset=84)['v'].astype(np.float64)
 obj=bpy.data.objects[item['name']]
 vertices=np.array([tuple(v.co) for v in obj.data.vertices],dtype=np.float64)
 faces=np.array([tuple(f.vertices) for f in obj.data.polygons]);actual=vertices[faces]*1000
 assert actual.shape==reference.shape
 error=float(np.abs(actual-reference).max());assert error<.00001
 assert len(obj.modifiers)==0
 assert np.max(np.abs(np.array(obj.matrix_world)-np.eye(4)))<1e-9
 assert obj['source_sha256']==hashlib.sha256(data).hexdigest()
 checks.append({'name':item['name'],'category':item['category'],'triangles':n,'max_coordinate_error_mm':error,'modifiers':0})

side_checks=[]
for side,label in [(-1,'L'),(1,'R')]:
 expected=Matrix.Translation((side*.038163,0,.0321))@Matrix.Rotation(math.radians(18),4,'Z')@Matrix.Translation((-side*.01167,0,0))@Matrix.Rotation(math.pi if side<0 else 0,4,'Z')
 objects=[o for o in bpy.context.scene.objects if o.name.startswith(f'DETAILED_{label}_')]
 assert objects
 for obj in objects:
  matrix=np.array(obj['canonical_to_world']).reshape(4,4)
  assert np.max(np.abs(matrix-np.array(expected)))<1e-7
  assert abs(np.linalg.det(matrix[:3,:3])-1)<1e-6
  assert obj.matrix_world.to_3x3().determinant()>0
 body=bpy.data.objects[f'DETAILED_{label}_OV2640_square_camera_body']
 lens_xy=np.array(body.matrix_world.translation)[:2]*1000
 assert np.linalg.norm(lens_xy-np.array([side*38.163,0]))<.00001
 side_checks.append({'side':label,'objects':len(objects),'rotation_is_reflection':False,'camera_center_xy_mm':lens_xy.tolist(),'canonical_to_world':np.array(expected).tolist()})

assert len(side_checks)==2 and side_checks[0]['objects']==side_checks[1]['objects']
result={'status':'passed','scope':'Unchanged original housing and cable-envelope meshes, plus electronics placement and rotation parity','source_revision':'abc4b921c989caf9e1e14d1babe25940b68502be','unchanged_source_objects':len(checks),'unchanged_printed_objects':sum(c['category']=='printed' for c in checks),'max_coordinate_error_mm':max(c['max_coordinate_error_mm'] for c in checks),'electronics_placement':side_checks,'physical_fit':'Not validated; component heights and cable envelopes nominal','checks':checks}
Path(a.output).write_text(json.dumps(result,indent=2))
print(json.dumps({k:v for k,v in result.items() if k!='checks'}))
