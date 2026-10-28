import argparse
import json
import math
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Matrix,Vector

p=argparse.ArgumentParser()
p.add_argument('--model',required=True)
p.add_argument('--output',required=True)
p.add_argument('--view',choices=['front','back','mb'],default='front')
p.add_argument('--width',type=int,default=2400)
p.add_argument('--samples',type=int,default=96)
p.add_argument('--scene-output')
p.add_argument('--skip-render',action='store_true')
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
bpy.ops.wm.open_mainfile(filepath=str(Path(a.model).resolve()))
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=a.samples;scene.cycles.use_denoising=True
scene.cycles.adaptive_threshold=.022;scene.cycles.adaptive_min_samples=16
scene.cycles.max_bounces=8;scene.cycles.diffuse_bounces=3;scene.cycles.glossy_bounces=4
scene.render.resolution_x=a.width;scene.render.resolution_y=round(a.width*.75);scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.film_transparent=True
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=-.35
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(1,1,1,1);scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.40
scene.use_nodes=False
vertices=np.array([tuple(o.matrix_world@v.co) for o in scene.objects if o.type=='MESH' for v in o.data.vertices])
direction={'front':(.6,.5,1.9),'back':(-.6,.5,-1.9),'mb':(-.9,-.8,1.9)}[a.view]
forward=Vector(direction).normalized();right=Vector((0,1,0)).cross(forward).normalized();up=forward.cross(right).normalized()
basis=np.array([tuple(right),tuple(up),tuple(forward)]).T
projected=vertices@basis;size=projected.max(0)-projected.min(0)
center=Vector(((projected.min(0)+projected.max(0))*.5)@basis.T)
data=bpy.data.cameras.new('Board product camera');cam=bpy.data.objects.new('Board product camera',data);scene.collection.objects.link(cam)
cam.location=center+forward*.30;cam.rotation_euler=Matrix((right,up,forward)).transposed().to_euler();data.type='ORTHO'
data.ortho_scale=max(size[0],size[1]*4/3)*1.18;data.clip_start=.0001;data.clip_end=10;scene.camera=cam
for name,location,power,size in [('Soft key',(-.08,.10,.14),.7,.13),('Right fill',(.10,.03,.10),.45,.10),('Back rim',(.02,.10,-.12),.9,.11),('Lower fill',(-.05,-.10,.04),.3,.13)]:
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
 obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=location;obj.rotation_euler=(center-obj.location).to_track_quat('-Z','Y').to_euler()
if a.view=='back':
 data=bpy.data.lights.new('Rear broad key','AREA');data.energy=.6;data.size=.15
 obj=bpy.data.objects.new('Rear broad key',data);scene.collection.objects.link(obj);obj.location=(-.08,.07,-.13);obj.rotation_euler=(center-obj.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=str(Path(a.output).resolve())
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   area.spaces.active.region_3d.view_location=center
   area.spaces.active.region_3d.view_distance=.08
   area.spaces.active.region_3d.view_perspective='CAMERA'
   area.spaces.active.overlay.show_overlays=False
   area.spaces.active.shading.type='MATERIAL'
if a.scene_output:bpy.ops.wm.save_as_mainfile(filepath=str(Path(a.scene_output).resolve()))
if not a.skip_render:bpy.ops.render.render(write_still=True)
print(json.dumps({'output':scene.render.filepath,'view':a.view,'width':a.width,'samples':a.samples}))
