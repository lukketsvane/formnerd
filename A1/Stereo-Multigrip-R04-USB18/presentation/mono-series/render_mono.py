import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'presentation' / 'mono-series'
SOURCE = ROOT / 'presentation'
if (OUT/'PAUSED').exists():
 raise SystemExit('Rendering paused pending detailed ESP32 model')
PLAN = json.loads((OUT/'shot-plan.json').read_text())
p = argparse.ArgumentParser()
p.add_argument('--view', choices=['hero','front','rear','high','low','detail'], default='hero')
p.add_argument('--palette', choices=['black','grey','duo'], default='black')
p.add_argument('--width', type=int, default=2400)
p.add_argument('--samples', type=int, default=96)
p.add_argument('--output')
a = p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
SHOT = next(v for v in PLAN['shots'] if v['palette']==a.palette and v['view']==a.view)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for block in list(bpy.data.materials):
 bpy.data.materials.remove(block)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = a.samples
scene.cycles.use_denoising = True
scene.cycles.adaptive_threshold = .025
scene.cycles.adaptive_min_samples = 24
scene.cycles.max_bounces = 8
scene.cycles.diffuse_bounces = 3
scene.cycles.glossy_bounces = 4
scene.cycles.transmission_bounces = 6
scene.render.resolution_x = a.width
scene.render.resolution_y = round(a.width*.75)
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.film_transparent = True
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'
scene.view_settings.exposure = -.35
scene.view_settings.gamma = 1
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (1,1,1,1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .40
scene.use_nodes = False

def linear(x):
 return x/12.92 if x <= .04045 else ((x+.055)/1.055)**2.4

def material(name,color,rough=.35,metal=0,coat=0,printed=False):
 m=bpy.data.materials.new(name)
 m.use_nodes=True
 nt=m.node_tree
 bs=nt.nodes.get('Principled BSDF')
 bs.inputs['Base Color'].default_value=tuple(linear(c) for c in color)+(1,)
 bs.inputs['Roughness'].default_value=rough
 bs.inputs['Metallic'].default_value=metal
 bs.inputs['Coat Weight'].default_value=coat
 bs.inputs['Coat Roughness'].default_value=.12
 bs.inputs['IOR'].default_value=1.46
 if printed:
  tex=nt.nodes.new('ShaderNodeTexCoord')
  separate=nt.nodes.new('ShaderNodeSeparateXYZ')
  multiply=nt.nodes.new('ShaderNodeMath');multiply.operation='MULTIPLY';multiply.inputs[1].default_value=2*math.pi/.00012
  sine=nt.nodes.new('ShaderNodeMath');sine.operation='SINE'
  bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.25;bump.inputs['Distance'].default_value=.000006
  nt.links.new(tex.outputs['Object'],separate.inputs[0]);nt.links.new(separate.outputs['Z'],multiply.inputs[0]);nt.links.new(multiply.outputs[0],sine.inputs[0]);nt.links.new(sine.outputs[0],bump.inputs['Height']);nt.links.new(bump.outputs['Normal'],bs.inputs['Normal'])
 return m
mats={
'matte_black':material('Matte black printed polymer',(.085,.09,.095),.62,0,0,True),
'matte_grey':material('Neutral grey printed polymer',(.48,.48,.48),.62,0,0,True),
'pcb':material('Nominal black PCB',(.035,.055,.047),.42),
'black':material('Black moulded polymer',(.045,.05,.055),.30,0,.07),
'rubber':material('Black USB cable',(.06,.065,.07),.48),
'metal':material('Satin connector metal',(.66,.69,.72),.26,.92),
'gold':material('Pin metal',(.68,.70,.72),.22,.9),
'ivory':material('Ivory flex socket',(.84,.84,.77),.31),
'flex':material('Polyimide flex',(.77,.30,.055),.23,.12,.22),
'lens':material('Optical coating',(.018,.11,.12),.055,.35,.8)
}

source=json.loads((SOURCE/'scene_A3.json').read_text())
allverts=[]
provenance=[]
for item in source['items']:
 if item['name'].startswith(('REF_L_','REF_R_')):continue
 path=Path(item['stl'])
 if not path.is_absolute():path=(SOURCE/path).resolve()
 if not path.exists():
  matches=list(ROOT.rglob(path.name))
  if len(matches)!=1:raise RuntimeError(str(path))
  path=matches[0]
 data=path.read_bytes();n=struct.unpack_from('<I',data,80)[0]
 dt=np.dtype([('normal','<f4',(3,)),('v','<f4',(3,3)),('attr','<u2')])
 tris=np.frombuffer(data,dtype=dt,count=n,offset=84)['v'].astype(np.float64)
 if 'transform' in item:
  t=np.array(item['transform']).reshape(4,4)
  tris=(np.c_[tris.reshape(-1,3),np.ones(tris.size//3)]@t.T)[:,:3].reshape(-1,3,3)
 tris+=np.array(item.get('translation',[0,0,0]))
 verts,indices=np.unique(tris.reshape(-1,3),axis=0,return_inverse=True)
 verts=verts*.001
 mesh=bpy.data.meshes.new(item['name'])
 mesh.from_pydata(verts.tolist(),[],indices.reshape(-1,3).tolist());mesh.update()
 obj=bpy.data.objects.new(item['name'],mesh);scene.collection.objects.link(obj)
 for face in mesh.polygons:face.use_smooth=True
 mesh.set_sharp_from_angle(angle=math.radians(36))
 name=item['name']
 if item['category']=='printed':
  mat=mats['matte_black'] if a.palette=='black' or (a.palette=='duo' and name=='02_multigrip_carrier') else mats['matte_grey']
 elif 'lens_glass' in name:mat=mats['lens']
 elif 'flex_socket' in name:mat=mats['ivory']
 elif name.endswith('_flex'):mat=mats['flex']
 elif '_pin_' in name:mat=mats['gold']
 elif '_USB_socket' in name or '_SD_cage' in name:mat=mats['metal']
 elif name.endswith('_CAM') or name.endswith('_MB'):mat=mats['pcb']
 elif name.startswith('cable_clearance'):mat=mats['rubber']
 else:mat=mats['black']
 mesh.materials.append(mat)
 obj['source_stl']=str(path.relative_to(ROOT))
 obj['source_sha256']=hashlib.sha256(data).hexdigest()
 obj['source_category']=item['category']
 allverts.append(verts)
 provenance.append({'name':name,'source_stl':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(data).hexdigest(),'triangles':n,'material':mat.name})

electronics_assets=[]
for filename in ['ESP32_CAM_reconstructed.blend','ESP32_MB_reconstructed.blend']:
 asset=SOURCE/'electronics'/filename
 if not asset.exists():raise FileNotFoundError(asset)
 digest=hashlib.sha256(asset.read_bytes()).hexdigest()
 with bpy.data.libraries.load(str(asset),link=False) as (data_from,data_to):
  data_to.objects=list(data_from.objects)
 originals=[o for o in data_to.objects if o is not None and o.type in ('MESH','FONT','CURVE')]
 for side,label in [(-1,'L'),(1,'R')]:
  transform=Matrix.Translation((side*.038163,0,.0321))@Matrix.Rotation(math.radians(18),4,'Z')@Matrix.Translation((-side*.01167,0,0))@Matrix.Rotation(math.pi if side<0 else 0,4,'Z')
  for original in originals:
   obj=original.copy();obj.name=f'DETAILED_{label}_{original.name}'
   assert original.parent is None
   scene.collection.objects.link(obj);obj.matrix_world=transform@original.matrix_basis
   obj['source_asset']=filename;obj['source_asset_sha256']=digest;obj['board_side']=label
   obj['canonical_to_world']=list(v for row in transform for v in row)
   if obj.type=='MESH':
    coords=np.array([tuple(obj.matrix_world@v.co) for v in obj.data.vertices]);allverts.append(coords)
    triangle_count=sum(len(f.vertices)-2 for f in obj.data.polygons)
   else:triangle_count=0
   provenance.append({'name':obj.name,'source_asset':str(asset.relative_to(ROOT)),'sha256':digest,'triangles':triangle_count,'category':'detailed_electronics','board_side':label})
 electronics_assets.append({'filename':filename,'sha256':digest,'object_count_per_board':len(originals),'license_note':'CAM includes external dependency; not for public mesh redistribution' if filename.startswith('ESP32_CAM_') else 'Original photo-based reconstruction'})
 for original in originals:
  if not original.users_collection:bpy.data.objects.remove(original)

bpy.context.view_layer.update()
for side,label in [(-1,'L'),(1,'R')]:
 body=bpy.data.objects[f'DETAILED_{label}_OV2640_square_camera_body']
 assert (body.matrix_world.translation-Vector((side*.038163,0,.03663))).length<.00000001
allverts=[np.array([tuple(o.matrix_world@v.co) for v in o.data.vertices]) for o in scene.objects if o.type=='MESH']
vertices=np.concatenate(allverts)
lo=vertices.min(0);hi=vertices.max(0);center=Vector((lo+hi)*.5)
view=SHOT['camera_direction']
forward=Vector(view).normalized();right=Vector((0,1,0)).cross(forward).normalized();up=forward.cross(right).normalized()
camdata=bpy.data.cameras.new('Orthographic product camera');cam=bpy.data.objects.new('Orthographic product camera',camdata);scene.collection.objects.link(cam)
cam.location=center+forward*.55
cam.rotation_euler=Matrix((right,up,forward)).transposed().to_euler()
camdata.type='ORTHO';camdata.lens=85;camdata.clip_start=.001;camdata.clip_end=10
basis=np.array([tuple(right),tuple(up),tuple(forward)]).T
projected=vertices@basis
size=projected.max(0)-projected.min(0)
aspect=scene.render.resolution_x/scene.render.resolution_y
camera_center=projected.min(0)*.5+projected.max(0)*.5
center=Vector(camera_center@basis.T)
cam.location=center+forward*.55
camdata.ortho_scale=max(size[0],size[1]*aspect)*1.16
if a.view=='detail':
 center=Vector((-.039,.026,.034));cam.location=center+forward*.5;camdata.ortho_scale=.052
scene.camera=cam

def area(name,location,power,size,color=(1,1,1),shape='DISK',size_y=None):
 d=bpy.data.lights.new(name,'AREA');d.energy=power/12;d.shape=shape;d.size=size;d.color=color
 if size_y is not None:d.size_y=size_y
 o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=Vector(location)
 o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
area('Large soft key',(-.19,.24,.28),18,.22,(1,1,1),'RECTANGLE',.28)
area('Cool edge',(.21,.08,.14),12,.16,(1,1,1),'RECTANGLE',.26)
area('Upper rim',(.04,.22,-.20),22,.15,(1,1,1),'RECTANGLE',.24)
area('Front reflection strip',(-.02,-.12,.32),5,.15,(1,1,1),'RECTANGLE',.06)
area('Broad lower fill',(-.12,-.20,.08),7,.20,(1,1,1),'RECTANGLE',.28)
if a.view=='rear':area('Rear soft key',(-.14,.15,-.26),16,.22,(1,1,1),'RECTANGLE',.28)
scene.render.filepath=str(Path(a.output).resolve() if a.output else OUT/SHOT['filename'])
scene['render_source']='Unchanged R04 printed STL meshes with detailed ESP32-CAM and MB reconstruction; actual Cycles render; no AI imagery'
scene['geometry_note']='Detailed electronics reconstructed from sourced meshes and photographs; component heights nominal. USB bodies and cable service envelopes remain unmeasured references.'
scene['source_revision']='abc4b921c989caf9e1e14d1babe25940b68502be'
scene['materials_note']='Matte colour study only. No physical-print filament or mesh geometry changes.'
scene['palette']=a.palette
scene['shot_id']=SHOT['id']
for screen in bpy.data.screens:
 for viewport in screen.areas:
  if viewport.type=='VIEW_3D':
   viewport.spaces.active.region_3d.view_location=center
   viewport.spaces.active.region_3d.view_distance=.3
   viewport.spaces.active.region_3d.view_perspective='CAMERA'
   viewport.spaces.active.overlay.show_overlays=False
   viewport.spaces.active.shading.type='MATERIAL'
if a.view=='hero':bpy.ops.wm.save_as_mainfile(filepath=str(OUT/f'R04_matte_{a.palette}.blend'))
(OUT/f'render-{SHOT["id"]}.json').write_text(json.dumps({'engine':'Blender Cycles','blender_version':bpy.app.version_string,'view':a.view,'palette':a.palette,'shot_id':SHOT['id'],'intentional_detail_crop':SHOT['intentional_detail_crop'],'samples':a.samples,'resolution':[scene.render.resolution_x,scene.render.resolution_y],'mesh_count':len(provenance),'triangle_count':sum(i['triangles'] for i in provenance),'objects':provenance,'geometry_changes':'Housing unchanged; nominal electronics replaced with detailed photo-based models','electronics_assets':electronics_assets,'left_board_transform':'180degree Z rotation, not reflection','physical_fit':'not verified'},indent=2))
bpy.ops.render.render(write_still=True)
print(json.dumps({'output':scene.render.filepath,'objects':len(provenance),'triangles':sum(i['triangles'] for i in provenance)}))
