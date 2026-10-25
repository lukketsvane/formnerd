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

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'presentation'
p = argparse.ArgumentParser()
p.add_argument('--view', choices=['hero','front','rear','detail'], default='hero')
p.add_argument('--width', type=int, default=2400)
p.add_argument('--samples', type=int, default=128)
p.add_argument('--output')
a = p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for block in list(bpy.data.materials):
 bpy.data.materials.remove(block)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = a.samples
scene.cycles.use_denoising = True
scene.cycles.adaptive_threshold = .02
scene.cycles.max_bounces = 10
scene.cycles.diffuse_bounces = 4
scene.cycles.glossy_bounces = 6
scene.cycles.transmission_bounces = 8
scene.render.resolution_x = a.width
scene.render.resolution_y = round(a.width*.75)
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.film_transparent = True
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'
scene.view_settings.exposure = -.7
scene.view_settings.gamma = 1
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (1,1,1,1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .25
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
'yellow':material('AMS A3 yellow PLA',(.98,.76,.03),.42,0,.025,True),
'gray':material('Reused gray PLA',(.47,.49,.51),.43,0,.025,True),
'pcb':material('Nominal black PCB',(.035,.055,.047),.42),
'black':material('Black moulded polymer',(.045,.05,.055),.30,0,.07),
'rubber':material('Black USB cable',(.06,.065,.07),.48),
'metal':material('Satin connector metal',(.66,.69,.72),.26,.92),
'gold':material('Pin metal',(.68,.70,.72),.22,.9),
'ivory':material('Ivory flex socket',(.84,.84,.77),.31),
'flex':material('Polyimide flex',(.77,.30,.055),.23,.12,.22),
'lens':material('Optical coating',(.018,.11,.12),.055,.35,.8)
}

source=json.loads((OUT/'scene_A3.json').read_text())
allverts=[]
provenance=[]
for item in source['items']:
 path=Path(item['stl'])
 if not path.is_absolute():path=(OUT/path).resolve()
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
  mat=mats['yellow'] if name in ['02_multigrip_carrier','03_MB_keeper_left','04_MB_keeper_right'] or name.endswith('_wedge') else mats['gray']
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

vertices=np.concatenate(allverts)
lo=vertices.min(0);hi=vertices.max(0);center=Vector((lo+hi)*.5)
view={'hero':(1,.68,1.7),'front':(0,0,1),'rear':(-1,.6,-1.7),'detail':(.8,.5,1.9)}[a.view]
forward=Vector(view).normalized();right=Vector((0,1,0)).cross(forward).normalized();up=forward.cross(right).normalized()
camdata=bpy.data.cameras.new('Orthographic product camera');cam=bpy.data.objects.new('Orthographic product camera',camdata);scene.collection.objects.link(cam)
cam.location=center+forward*.55
cam.rotation_euler=Matrix((right,up,forward)).transposed().to_euler()
camdata.type='ORTHO';camdata.lens=85;camdata.clip_start=.001;camdata.clip_end=10
basis=np.array([tuple(right),tuple(up),tuple(forward)]).T
projected=vertices@basis
size=projected.max(0)-projected.min(0)
aspect=scene.render.resolution_x/scene.render.resolution_y
camdata.ortho_scale=max(size[0],size[1]*aspect)*1.13
if a.view=='detail':
 center=Vector((-.025,.006,.032));cam.location=center+forward*.5;camdata.ortho_scale=.080
scene.camera=cam

def area(name,location,power,size,color=(1,1,1),shape='DISK',size_y=None):
 d=bpy.data.lights.new(name,'AREA');d.energy=power/12;d.shape=shape;d.size=size;d.color=color
 if size_y is not None:d.size_y=size_y
 o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=Vector(location)
 o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
area('Large soft key',(-.19,.24,.28),18,.22,(1,.99,.97),'RECTANGLE',.28)
area('Cool edge',(.21,.08,.14),12,.16,(.90,.95,1),'RECTANGLE',.26)
area('Upper rim',(.04,.22,-.20),22,.15,(1,1,1),'RECTANGLE',.24)
area('Front reflection strip',(-.02,-.12,.32),4,.12,(1,1,1),'RECTANGLE',.025)
if a.view=='rear':area('Rear soft key',(-.14,.15,-.26),16,.22,(1,.97,.93),'RECTANGLE',.28)
scene.render.filepath=str(Path(a.output).resolve() if a.output else OUT/f'R04_actual_{a.view}.png')
scene['render_source']='Existing R04 STL meshes, no generated geometry or AI imagery'
scene['geometry_note']='Electronics, USB bodies and cable service envelopes are nominal CAD references; no invented component detailing'
scene['source_revision']='abc4b921c989caf9e1e14d1babe25940b68502be'
scene['materials_note']='Procedural surface shading only; mesh vertices and triangular connectivity preserved after duplicate-vertex welding'
if a.view=='hero':bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'R04_actual_studio.blend'))
(OUT/f'render-{a.view}.json').write_text(json.dumps({'engine':'Blender Cycles','blender_version':bpy.app.version_string,'view':a.view,'samples':a.samples,'resolution':[scene.render.resolution_x,scene.render.resolution_y],'mesh_count':len(provenance),'triangle_count':sum(i['triangles'] for i in provenance),'objects':provenance,'geometry_changes':'none; duplicate-vertex welding and display normals only','physical_fit':'not verified'},indent=2))
bpy.ops.render.render(write_still=True)
print(json.dumps({'output':scene.render.filepath,'objects':len(provenance),'triangles':sum(i['triangles'] for i in provenance)}))
