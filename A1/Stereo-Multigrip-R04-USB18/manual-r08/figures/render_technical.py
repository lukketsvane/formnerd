import argparse,hashlib,json,math,sys
from pathlib import Path
import bpy
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
p=argparse.ArgumentParser()
p.add_argument('--blend',required=True)
p.add_argument('--output',required=True)
p.add_argument('--r04-source',help='R04 source directory for optional bank/cradle geometry')
p.add_argument('--scene',choices=['exploded','seated','keepers','keepers_rear','yokes','rear_usb','board_stack','pair_front','assembled','cam_only','mb_only','sensor_contact','keepers_locked','bank_placement','bank_locked'],required=True)
p.add_argument('--width',type=int,default=2000)
p.add_argument('--samples',type=int,default=48)
p.add_argument('--no-render',action='store_true')
a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
bpy.ops.wm.open_mainfile(filepath=str(Path(a.blend).resolve()))
s=bpy.context.scene
additional_sources=[]
if a.scene in ['bank_placement','bank_locked']:
 if not a.r04_source:raise ValueError('--r04-source is required for bank illustrations')
 source=Path(a.r04_source).resolve()
 names=['01_bank_cradle','REF_power_bank']
 if a.scene=='bank_locked':names += [f'10_frame_{i}_{kind}' for i in range(1,5) for kind in ['pin','wedge']]
 for name in names:
  path=source/'STL'/f'{name}.stl'
  bpy.ops.wm.stl_import(filepath=str(path),global_scale=.001,use_scene_unit=False)
  obj=bpy.context.object
  obj.name=name
  obj['source_category']='reference' if name=='REF_power_bank' else 'printed'
  obj['source_file']=str(path)
  for face in obj.data.polygons:face.use_smooth=False
  additional_sources.append({'name':name,'file':f'STL/{name}.stl','sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'import_scale':.001})
s.render.engine='CYCLES'
s.cycles.device='CPU'
s.cycles.samples=a.samples
s.cycles.use_denoising=True
s.cycles.adaptive_threshold=.035
s.cycles.adaptive_min_samples=16
s.render.resolution_x=a.width
s.render.resolution_y=round(a.width*.8)
s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG'
s.render.image_settings.color_mode='RGBA'
s.render.film_transparent=True
s.use_nodes=False
s.view_settings.view_transform='AgX'
s.view_settings.look='AgX - Medium High Contrast'
s.view_settings.exposure=0
mat=bpy.data.materials.new('Manual neutral matte polymer')
mat.use_nodes=True
bs=mat.node_tree.nodes.get('Principled BSDF')
bs.inputs['Base Color'].default_value=(.43,.43,.43,1)
bs.inputs['Roughness'].default_value=.7
bs.inputs['Metallic'].default_value=0
moves={}
visible=[]
for o in s.objects:
 if o.type in ('LIGHT','CAMERA'):continue
 n=o.name
 e=n.startswith('DETAILED')
 printed=o.get('source_category')=='printed'
 cable=n.startswith(('USB_','cable_clearance'))
 show=False
 if a.scene=='seated':show=e or n=='02_multigrip_carrier'
 if a.scene in ['keepers','keepers_rear']:show=e or n in ['02_multigrip_carrier','03_MB_keeper_left','04_MB_keeper_right']
 if a.scene=='yokes':show=e or n.startswith('20_keeper') or n in ['02_multigrip_carrier','03_MB_keeper_left','04_MB_keeper_right','05_sensor_yoke_left','06_sensor_yoke_right']
 if a.scene=='rear_usb':show=e or printed or cable
 if a.scene=='assembled':show=e or printed
 if a.scene in ['bank_placement','bank_locked']:show=e or printed or n=='REF_power_bank'
 if a.scene=='cam_only':show=n.startswith('DETAILED_R_') and o.get('source_asset')=='ESP32_CAM_reconstructed.blend'
 if a.scene=='mb_only':show=n.startswith('DETAILED_R_') and o.get('source_asset')=='ESP32_MB_reconstructed.blend'
 if a.scene=='sensor_contact':show=(n.startswith('DETAILED_R_') and o.get('source_asset')=='ESP32_CAM_reconstructed.blend') or n=='06_sensor_yoke_right'
 if a.scene=='keepers_locked':show=e or n.startswith('20_keeper') or n in ['02_multigrip_carrier','03_MB_keeper_left','04_MB_keeper_right']
 if a.scene=='board_stack':show=n.startswith('DETAILED_R_')
 if a.scene=='pair_front':show=e
 if a.scene=='exploded':show=e or printed
 o.hide_render=not show
 o.hide_set(not show)
 if not show:continue
 if printed:
  o.data.materials.clear();o.data.materials.append(mat)
 move=Vector((0,0,0))
 if a.scene=='sensor_contact' and n=='06_sensor_yoke_right':move.z=.004
 if a.scene=='bank_placement' and n in ['01_bank_cradle','REF_power_bank']:move.z=-.042
 if a.scene in ['keepers','keepers_rear'] and n in ['03_MB_keeper_left','04_MB_keeper_right']:move.z=-.050
 if a.scene=='yokes' and n in ['05_sensor_yoke_left','06_sensor_yoke_right']:move.z=.045
 if a.scene=='exploded':
  if e:move.z=.024
  elif n in ['03_MB_keeper_left','04_MB_keeper_right']:move.z=-.050
  elif n in ['05_sensor_yoke_left','06_sensor_yoke_right']:move.z=.060
  elif n.startswith('20_keeper'):
   move.z=-.050
   if n.endswith('pin'):move+=Vector((-.028*math.cos(math.radians(18)),-.028*math.sin(math.radians(18)),0))
   else:move.z+=.022
  elif n.startswith('30_yoke'):
   move.z=.060
   if n.endswith('pin'):move+=Vector((-.028*math.cos(math.radians(18)),-.028*math.sin(math.radians(18)),0))
   else:move.z+=.022
 if move.length:
  o.matrix_world=Matrix.Translation(move)@o.matrix_world
  moves[n]=[round(x*1000,8) for x in move]
 visible.append(o)
bpy.context.view_layer.update()
views={'exploded':(1.2,.85,1.3),'seated':(1,.65,2.5),'keepers':(1.5,.85,1.5),'keepers_rear':(-1.2,.65,-1.8),'yokes':(1.25,.8,2),'rear_usb':(.5,1.15,-2.6),'board_stack':(1.45,.9,1.8),'pair_front':(.12,.08,3),'assembled':(1,.65,2.5),'cam_only':(.8,.55,2.5),'mb_only':(1.3,.8,2.0),'sensor_contact':(-1.8,-.9,1.0),'keepers_locked':(-1.2,.65,-1.8),'bank_placement':(1.35,.75,1.6),'bank_locked':(1,.65,2.5)}
forward=Vector(views[a.scene]).normalized()
right=Vector((0,1,0)).cross(forward).normalized()
up=forward.cross(right).normalized()
points=[]
for o in visible:
 for c in o.bound_box:points.append(o.matrix_world@Vector(c))
projected=[Vector((v.dot(right),v.dot(up),v.dot(forward))) for v in points]
low=Vector([min(v[i] for v in projected) for i in range(3)])
high=Vector([max(v[i] for v in projected) for i in range(3)])
center_coords=(low+high)*.5
center=right*center_coords.x+up*center_coords.y+forward*center_coords.z
cam=s.camera
cam.location=center+forward*.6
cam.rotation_euler=Matrix((right,up,forward)).transposed().to_euler()
cam.data.type='ORTHO'
cam.data.ortho_scale=max(high.x-low.x,(high.y-low.y)*s.render.resolution_x/s.render.resolution_y)*1.16
if a.scene=='sensor_contact':
 center=Vector((.0345,0,.0395))
 cam.location=center+forward*.6
 cam.data.ortho_scale=.032
cam.data.clip_start=.001
cam.data.clip_end=10
for o in s.objects:
 if o.type=='LIGHT':o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
if a.scene in ['rear_usb','keepers_rear']:
 d=bpy.data.lights.new('Rear manual fill','AREA');d.energy=1.4;d.shape='DISK';d.size=.22
 o=bpy.data.objects.new('Rear manual fill',d);s.collection.objects.link(o);o.location=(-.14,.15,-.26);o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
out=Path(a.output).resolve();out.parent.mkdir(parents=True,exist_ok=True)
s.render.filepath=str(out)
bpy.context.view_layer.update()
anchors={}
for o in visible:
 if o.get('source_category')=='printed' or o.name=='REF_power_bank' or o.name.endswith('OV2640_square_camera_body'):
  center=sum((o.matrix_world@Vector(c) for c in o.bound_box),Vector())/8
  original=center-Vector(moves.get(o.name,[0,0,0]))*.001
  pa=world_to_camera_view(s,cam,center)
  pb=world_to_camera_view(s,cam,original)
  anchors[o.name]={'shown_center_uv':[round(pa.x,7),round(pa.y,7)],'assembled_center_uv':[round(pb.x,7),round(pb.y,7)],'shown_center_mm':[round(v*1000,7) for v in center],'assembled_center_mm':[round(v*1000,7) for v in original]}
meta={'scene':a.scene,'render_engine':'Blender Cycles','blender_version':bpy.app.version_string,'input_scene':Path(a.blend).name,'visible_object_count':len(visible),'printed_part_count':sum(o.get('source_category')=='printed' for o in visible),'camera_direction':views[a.scene],'illustration_translations_mm':moves,'resolution':[s.render.resolution_x,s.render.resolution_y],'samples':a.samples,'geometry_changes':'none; object visibility and explanatory translations only','electronics':'Detailed source/photo reconstructed ESP32-CAM and MB; nominal component dimensions','motion_note':'Exploded view separates parts for identification. It does not verify PCB insertion. Seated scene shows final reference position only.','object_names':[o.name for o in visible]}
meta['anchors']=anchors
if a.scene in ['sensor_contact','yokes','assembled']:
 contact_points={}
 for sx in [-1,1]:
  for sy in [-1,1]:
   local=Vector((sx*.00375,sy*.00375,0))
   original=Vector((.038163,0,.0375))+Matrix.Rotation(math.radians(18),3,'Z')@local
   shown=original+Vector(moves.get('06_sensor_yoke_right',[0,0,0]))*.001
   uv=world_to_camera_view(s,cam,shown)
   goal=world_to_camera_view(s,cam,original)
   contact_points[f'right_pad_{sx}_{sy}']={'shown_center_uv':[uv.x,uv.y],'assembled_contact_uv':[goal.x,goal.y],'shown_lower_face_mm':[v*1000 for v in shown],'assembled_lower_face_mm':[v*1000 for v in original]}
 meta['existing_integral_contact_points']=contact_points
 meta['contact_point_provenance']='Existing build_harness.py 1x1mm corner contacts at +/-3.75mm from lens axis, lower faceZ37.5mm, podroll18degrees. Reference coordinates, not measured physical contact.'
meta['anchor_coordinates']='Normalized image UV, origin bottom-left; shown to assembled vectors correspond to object illustration translations only.'
s.view_settings.view_transform='Standard'
s.view_settings.look='None'
s.view_settings.exposure=0
s.view_settings.gamma=1
s.cycles.samples=8
s.cycles.use_denoising=False
s.render.film_transparent=False
s.world.use_nodes=True
s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(1,1,1,1)
s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=1
white=bpy.data.materials.new('Technical white fill')
white.use_nodes=True
nt=white.node_tree
nt.nodes.clear()
em=nt.nodes.new('ShaderNodeEmission')
em.inputs['Color'].default_value=(1,1,1,1)
em.inputs['Strength'].default_value=1
outmat=nt.nodes.new('ShaderNodeOutputMaterial')
nt.links.new(em.outputs[0],outmat.inputs['Surface'])
part_collection=bpy.data.collections.new('Technical printed geometry')
elec_collection=bpy.data.collections.new('Technical detailed electronics')
s.collection.children.link(part_collection)
s.collection.children.link(elec_collection)
for o in visible:
 if o.type!='MESH':
  o.hide_render=True
  continue
 o.data.materials.clear();o.data.materials.append(white)
 if o.get('source_category')=='printed' or o.name=='REF_power_bank' or o.name.startswith(('USB_','cable_clearance')):part_collection.objects.link(o)
 else:elec_collection.objects.link(o)
s.render.use_freestyle=True
f=s.view_layers[0].freestyle_settings
f.mode='EDITOR'
f.crease_angle=math.radians(100)
f.use_smoothness=True
while len(f.linesets):f.linesets.remove(f.linesets[0])
inventory=a.scene in ['cam_only','mb_only','pair_front','board_stack','sensor_contact']
econtour=3.2 if inventory else 1.6
edetail=1.6 if inventory else 1.0
pcontour=3.2
pdetail=1.6
if a.scene=='sensor_contact':
 pcontour*=1.8;pdetail*=1.8;econtour*=1.8;edetail*=1.8
for name,col,thickness,contours,creases in [('Printed contours',part_collection,pcontour,True,False),('Printed detail',part_collection,pdetail,False,True),('Electronics contours',elec_collection,econtour,True,False),('Electronics detail',elec_collection,edetail,False,True)]:
 ls=f.linesets.new(name)
 ls.select_by_visibility=True
 ls.visibility='VISIBLE'
 ls.select_by_edge_types=True
 ls.select_by_collection=True
 ls.collection=col
 ls.collection_negation='INCLUSIVE'
 ls.edge_type_combination='OR'
 for prop in ['select_silhouette','select_border','select_crease','select_contour','select_external_contour','select_edge_mark','select_material_boundary','select_ridge_valley','select_suggestive_contour']:setattr(ls,prop,False)
 ls.select_silhouette=contours
 ls.select_border=contours
 ls.select_crease=creases
 ls.linestyle.color=(0,0,0)
 ls.linestyle.alpha=1
 ls.linestyle.thickness=thickness
 ls.linestyle.caps='ROUND'
 ls.linestyle.use_chaining=True
meta['style']='Freestyle visible silhouettes, borders and crease edges on white fill. Printed geometry has stronger outlines; individual electronics inventory uses the same weight. Text objects hidden, no tessellation or shaded surfaces.'
meta['source_scene_sha256']=hashlib.sha256(Path(a.blend).read_bytes()).hexdigest()
meta['omitted_text_object_count']=sum(o.type!='MESH' for o in visible)
meta['visible_object_count']=sum(o.type=='MESH' and not o.hide_render for o in visible)
meta['object_names']=[o.name for o in visible if o.type=='MESH' and not o.hide_render]
meta['samples']=8
meta['intentional_detail_crop']=a.scene=='sensor_contact'
meta['sensor_contact_note']='Carrier and MB omitted; actual right CAM and right yoke. Yoke translated4mm in+Z for contact-region illustration; cropped to shoulder and flex region, no new contact geometry.' if a.scene=='sensor_contact' else None
meta['line_width_pixels']={'printed_contour':pcontour,'printed_detail':pdetail,'electronics_contour':econtour,'electronics_detail':edetail}
meta['additional_geometry_sources']=additional_sources
if a.scene in ['bank_placement','bank_locked']:
 meta['nominal_bank_note']='Existing source REF_power_bank envelope,94x62x15mm, lowerZ2.8mm, verticalcornerfillet4.1mm; no modeled ports. Not a measurement of user hardware. No USB plug or cable objects.'
 meta['bank_motion_note']='Cradle and nominal bank displaced42mm innegativeZ for illustration; no verified bank insertion sweep.' if a.scene=='bank_placement' else 'Final nominal seated bank and assembled cradle/locks. Detailed camera electronics preserved.'
 meta['source_r04_directory']=str(Path(a.r04_source).resolve())
out.with_suffix('.json').write_text(json.dumps(meta,indent=2))
if not a.no_render:bpy.ops.render.render(write_still=True)
print(json.dumps({'output':str(out),'objects':len(visible),'printed':meta['printed_part_count']}))
