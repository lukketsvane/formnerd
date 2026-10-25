import argparse
import json
import math
import sys
from pathlib import Path
import bpy
from mathutils import Vector

p=argparse.ArgumentParser()
p.add_argument('--output',required=True)
p.add_argument('--preview')
p.add_argument('--width',type=int,default=1600)
p.add_argument('--samples',type=int,default=24)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
out=Path(a.output).resolve()
out.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
collection=bpy.data.collections.new('ESP32_CAM_MB')
bpy.context.scene.collection.children.link(collection)
records=[]

def linear(x):
 return x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4

def material(name,rgb,roughness=.4,metallic=0):
 m=bpy.data.materials.new(name);m.use_nodes=True
 b=m.node_tree.nodes.get('Principled BSDF')
 b.inputs['Base Color'].default_value=tuple(linear(x) for x in rgb)+(1,)
 b.inputs['Roughness'].default_value=roughness;b.inputs['Metallic'].default_value=metallic
 return m

mats={
 'pcb':material('MB black soldermask',(.047,.054,.052),.47),
 'edge':material('MB FR4 edge',(.22,.19,.12),.62),
 'black':material('MB moulded polymer',(.045,.048,.052),.42),
 'cavity':material('MB dark socket interior',(.012,.014,.016),.65),
 'metal':material('MB tin and steel',(.68,.70,.72),.27,.88),
 'gold':material('MB contact plating',(.75,.60,.29),.28,.86),
 'ceramic':material('MB tan ceramic',(.38,.29,.17),.55),
 'white':material('MB white silkscreen',(.80,.82,.80),.64),
 'trace':material('MB masked copper traces',(.070,.078,.074),.44),
 'amber':material('MB amber tactile actuator',(.66,.44,.09),.44),
 'red':material('MB red indicator resin',(.49,.025,.015),.25)
}

def register(obj,name,mat,origin='Photo-based reconstruction; component dimensions and placement nominal'):
 obj.name=name
 for c in list(obj.users_collection):c.objects.unlink(obj)
 collection.objects.link(obj)
 obj.data.materials.clear();obj.data.materials.append(mats[mat])
 obj['provenance']=origin
 records.append({'name':name,'material':mat,'origin':origin})
 return obj

def cube(name,loc,size,mat,bevel=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=tuple(v*.001 for v in loc))
 obj=bpy.context.object;obj.dimensions=tuple(v*.001 for v in size)
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if bevel:
  m=obj.modifiers.new('Edge radius','BEVEL');m.width=bevel*.001;m.segments=3
  bpy.ops.object.modifier_apply(modifier=m.name)
 return register(obj,name,mat)

def mesh(name,verts,faces,mat):
 data=bpy.data.meshes.new(name);data.from_pydata([tuple(v*.001 for v in p) for p in verts],[],faces);data.update()
 obj=bpy.data.objects.new(name,data);collection.objects.link(obj)
 return register(obj,name,mat)

def cylinder(name,loc,r,depth,mat,n=32):
 bpy.ops.mesh.primitive_cylinder_add(vertices=n,radius=r*.001,depth=depth*.001,location=tuple(v*.001 for v in loc))
 obj=bpy.context.object
 for face in obj.data.polygons:face.use_smooth=len(face.vertices)==4
 return register(obj,name,mat)

def board(name,w,h,bottom,thickness,r,mat):
 xy=[]
 for cx,cy,start in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
  for j in range(9):
   angle=math.radians(start+j*90/8)
   xy.append((cx+r*math.cos(angle),cy+r*math.sin(angle)))
 n=len(xy);verts=[(x,y,z) for z in (bottom,bottom+thickness) for x,y in xy]
 faces=[tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]
 faces.extend([(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)])
 return mesh(name,verts,faces,mat)

def text(name,body,loc,size,rotation=0):
 data=bpy.data.curves.new(name,'FONT');data.body=body;data.size=size*.001;data.extrude=.000001;data.resolution_u=4
 obj=bpy.data.objects.new(name,data);collection.objects.link(obj);obj.location=tuple(v*.001 for v in loc)
 obj.rotation_euler.z=math.radians(rotation);data.materials.append(mats['white'])
 obj['provenance']='Visible product marking reconstructed from Prusa programmer-board photograph'
 records.append({'name':name,'material':'white','origin':obj['provenance']})
 return obj

def trace(name,points,width=.11,z=-8.478):
 for j,(a,b) in enumerate(zip(points,points[1:])):
  dx=b[0]-a[0];dy=b[1]-a[1];length=math.hypot(dx,dy)
  obj=cube(name+f'_{j}',((a[0]+b[0])/2,(a[1]+b[1])/2,z),(length,width,.008),'trace')
  obj.rotation_euler.z=math.atan2(dy,dx)

def outline(name,x,y,w,h,z=-8.465):
 for sign in (-1,1):
  cube(name+f'_x{sign}',(x+sign*w/2,y,z),(.065,h,.008),'white')
  cube(name+f'_y{sign}',(x,y+sign*h/2,z),(w,.065,.008),'white')

def smd(name,x,y,w,h,kind='black'):
 cube(name+'_body',(x,y,-8.20),(w*.66,h,.43),kind,.04)
 for sign in (-1,1):
  cube(name+f'_terminal{sign}',(x+sign*w*.39,y,-8.22),(w*.25,h,.32),'metal',.025)
  cube(name+f'_pad{sign}',(x+sign*w*.43,y,-8.46),(w*.38,h+.18,.07),'metal',.02)

board('MB_PCB_core',40.5,27,-10.1,1.6,.65,'edge')
board('MB_top_soldermask',40.43,26.93,-8.502,.014,.62,'pcb')
board('MB_bottom_soldermask',40.43,26.93,-10.112,.014,.62,'pcb')

pins=[-2.36+j*2.54 for j in range(8)]
for side in (-1,1):
 y=side*11.43
 block=cube(f'MB_header_{side}',(6.53,y,-4.25),(20.52,2.62,8.5),'black',.09)
 for j,x in enumerate(pins):
  bpy.ops.mesh.primitive_cube_add(size=1,location=(x*.001,y*.001,-3.95*.001))
  cut=bpy.context.object;cut.dimensions=(.00162,.00162,.0081)
  bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
  bpy.context.view_layer.objects.active=block
  mod=block.modifiers.new('Socket opening','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cut
  bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
  cube(f'MB_socket_floor_{side}_{j}',(x,y,-8.0),(1.58,1.58,.10),'cavity')
  for q in (-1,1):cube(f'MB_socket_contact_{side}_{j}_{q}',(x+q*.48,y,-2.9),(.16,.58,4.85),'gold',.035)
  cylinder(f'MB_solder_pad_bottom_{side}_{j}',(x,y,-10.14),.77,.07,'metal')
  cube(f'MB_header_pin_tail_{side}_{j}',(x,y,-10.43),(.64,.64,.65),'gold',.045)

outer=[(-3.85,-8.45),(3.85,-8.45),(3.85,-6.70),(3.02,-6.00),(-3.02,-6.00),(-3.85,-6.70)]
inner=[(-3.45,-8.16),(3.45,-8.16),(3.45,-6.87),(2.87,-6.32),(-2.87,-6.32),(-3.45,-6.87)]
verts=[]
for x in (-22.1,-16.55):
 for contour in (outer,inner):verts.extend([(x,y,z) for y,z in contour])
faces=[]
for i in range(6):
 j=(i+1)%6
 faces.extend([(i,j,6+j,6+i),(12+i,18+i,18+j,12+j),(i,12+i,12+j,j),(6+i,6+j,18+j,18+i)])
shell=mesh('MB_microUSB_open_metal_shell',verts,faces,'metal')
bevel=shell.modifiers.new('Rolled shell edges','BEVEL');bevel.width=.000055;bevel.segments=2
bpy.context.view_layer.objects.active=shell;bpy.ops.object.modifier_apply(modifier=bevel.name)
cube('MB_microUSB_rear_insulator',(-16.7,0,-7.27),(.36,6.7,1.85),'cavity',.10)
cube('MB_microUSB_inner_tongue',(-19.1,0,-7.62),(4.6,5.55,.43),'black',.10)
for j in range(5):
 y=(j-2)*.65
 cube(f'MB_USB_contact_{j}',(-19.65,y,-7.365),(3.2,.30,.055),'gold',.025)
 cube(f'MB_USB_solder_lead_{j}',(-15.92,y,-8.32),(1.2,.32,.16),'metal',.025)
 cube(f'MB_USB_signal_pad_{j}',(-15.55,y,-8.46),(1.15,.43,.07),'metal',.025)
for side in (-1,1):
 cube(f'MB_USB_anchor_{side}',(-17.4,side*3.95,-8.30),(1.5,.95,.32),'metal',.1)
 cube(f'MB_USB_roof_slot_{side}',(-19.7,side*1.95,-6.004),(1.45,.46,.018),'cavity',.13)

for side,label in [(1,'IO0'),(-1,'RST')]:
 x=-17.1;y=side*9.4
 cube(f'MB_{label}_switch_base',(x,y,-8.13),(3.8,4.1,.65),'black',.18)
 cube(f'MB_{label}_switch_shell',(x,y,-7.72),(3.9,3.8,.38),'metal',.15)
 cube(f'MB_{label}_switch_amber_top',(x,y,-7.48),(3.12,2.95,.16),'amber',.2)
 cube(f'MB_{label}_switch_recess',(x,y,-7.37),(1.97,1.97,.10),'black',.18)
 cube(f'MB_{label}_actuator',(x,y,-7.10),(1.55,1.55,.48),'amber',.18)
 for sx in (-1,1):
  for sy in (-1,1):cube(f'MB_{label}_switch_leg_{sx}_{sy}',(x+sx*1.82,y+sy*1.88,-8.37),(.65,.76,.2),'metal',.05)
 text(f'MB_{label}_mark',label,(-19.75,y+1.2,-8.46),.85,-90)

cx=-7.3
cube('MB_CH340_body',(cx,0,-7.48),(4.05,10.05,1.62),'black',.15)
lead_profile=[(2.0,-7.19),(2.4,-7.19),(2.94,-8.21),(3.55,-8.21),(3.55,-8.40),(2.82,-8.40),(2.25,-7.38),(2.0,-7.38)]
for side in (-1,1):
 for j in range(8):
  y=(j-3.5)*1.27
  points=[(cx+side*x,y+dy,z) for dy in (-.21,.21) for x,z in lead_profile]
  n=len(lead_profile);faces=[tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]
  faces.extend([(k,(k+1)%n,(k+1)%n+n,k+n) for k in range(n)])
  mesh(f'MB_CH340_gullwing_{side}_{j}',points,faces,'metal')
  cube(f'MB_CH340_pad_{side}_{j}',(cx+side*3.25,y,-8.46),(1.45,.65,.08),'metal',.035)
cylinder('MB_CH340_orientation_dot',(cx-1.2,3.9,-6.662),.25,.012,'trace')
text('MB_CH340_mark','CH340',(cx+.8,2.65,-6.656),.82,-90)

cube('MB_regulator_package',(7.5,2.3,-7.85),(2.25,3.35,1.0),'black',.12)
for j in range(3):cube(f'MB_regulator_lead_{j}',(5.9,2.3+(j-1)*.95,-8.28),(1.2,.43,.26),'metal',.035)
cube('MB_regulator_tab',(9.1,2.3,-8.28),(1.2,2.35,.26),'metal',.035)
for name,x,y,w,h,kind in [
 ('C1',11.5,3.3,2.0,1.25,'ceramic'),('C2',3.8,2.3,2.0,1.25,'ceramic'),
 ('R1',5.5,-1.5,1.6,.8,'black'),('R2',1.9,-1.6,1.6,.8,'black'),
 ('C3',.6,4.5,2.0,1.25,'ceramic'),('R3',-.7,7.7,1.6,.8,'black'),
 ('R4',-12.2,-4.4,1.6,.8,'black'),('R5',-13.9,5.0,1.6,.8,'black'),
 ('C4',-13.8,7.6,1.6,.8,'ceramic'),('R6',10.4,-4.7,1.6,.8,'black')]:
 smd('MB_'+name,x,y,w,h,kind);outline('MB_'+name+'_outline',x,y,w+.6,h+.5)
smd('MB_status_LED',13.6,-4.7,1.75,1.05,'red')
outline('MB_status_LED_outline',13.6,-4.7,2.35,1.55)
text('MB_board_model','ESP32-CAM-MB',(15.7,8.8,-8.455),1.19,-90)
text('MB_power_mark','5V',(-14.7,-3.65,-8.455),.67,-90)
outline('MB_USB_test_mark',-.6,-7.0,2.4,2.4)
for dx in (-.55,.55):
 for dy in (-.55,.55):cube(f'MB_test_pad_{dx}_{dy}',(-.6+dx,-7.0+dy,-8.45),(.44,.44,.08),'metal',.04)
for i,points in enumerate([
 [(-15.4,-1.3),(-13.3,-1.3),(-11.4,-3.2),(-10.5,-3.2)],
 [(-15.4,-.65),(-13,-.65),(-11.7,-1.95),(-10.5,-1.95)],
 [(-15.4,0),(-12.5,0),(-11.8,1.45),(-10.5,1.45)],
 [(-15.4,.65),(-12.3,.65),(-11.5,2.7),(-10.5,2.7)],
 [(-15.4,1.3),(-13.3,1.3),(-11.2,5.8),(-3,5.8),(1.8,10.1)],
 [(-3.7,-3.2),(-1.8,-3.2),(0,-5.0),(6,-5.0),(9,-9.8)],
 [(-3.7,-1.9),(-1.5,-1.9),(.7,-4),(8,-4),(11.7,-9.8)],
 [(-3.7,.6),(-.5,.6),(1.2,2.3),(5.8,2.3)],
 [(9.9,2.3),(11.4,2.3),(11.5,3.3)],
 [(13.6,-4.7),(15,-4.7),(16.7,-6.4),(16.7,-10.2)]
 ]):trace(f'MB_visible_trace_{i}',points)
for i,(x,y) in enumerate([(-13,-4),(-12,4),(-1,-6),(0,7),(2,-6.5),(4,6.2),(7,-6),(12,7),(16,-7.4)]):
 cylinder(f'MB_via_annulus_{i}',(x,y,-8.457),.22,.04,'metal',24)
 cylinder(f'MB_via_hole_{i}',(x,y,-8.429),.10,.013,'cavity',24)

scene=bpy.context.scene
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene['model']='Photo-reconstructed ESP32-CAM-MB programmer base'
scene['canonical_axes']='Blender meters; CAM PCB bottomZ0; MB PCB bottomZ−10.1mm; USBnegativeX'
scene['physical_dimensions']='Nominal40.5×27×1.6mm PCB and8.5mm headers; package heights and layout approximated from photograph'
scene['source_photo']='https://github.com/prusa3d/Prusa-Firmware-ESP32-Cam/blob/master/doc/AI_Thinker-ESP32-cam/esp32_and_prog.jpg'
scene['geometry_origin']='Own primitive and mesh reconstruction; no external mesh asset included'
scene['housing_modified']=False
bpy.ops.wm.save_as_mainfile(filepath=str(out))
provenance={'model':'ESP32-CAM-MB','collection':'ESP32_CAM_MB','unit':'meter','canonical_cam_bottom_z_mm':0,'mb_bottom_z_mm':-10.1,'pcb_size_mm':[40.5,27,1.6],'header_height_mm':8.5,'header_pin_x_mm':pins,'header_pin_y_mm':[-11.43,11.43],'usb_open_front_x_mm':-22.1,'source_photo':scene['source_photo'],'reference_note':'Appearance reconstructed from the Prusa programmer photo; exact manufacturer revision and package dimensions not measured. Markings are product identification, not a serial number.','geometry_origin':scene['geometry_origin'],'objects':records,'object_count':len(collection.objects)}
(out.parent/'mb-model-provenance.json').write_text(json.dumps(provenance,indent=2))
if a.preview:
 scene.render.engine='CYCLES';scene.cycles.samples=a.samples;scene.cycles.use_denoising=True
 scene.cycles.adaptive_threshold=.025;scene.cycles.adaptive_min_samples=24
 scene.render.resolution_x=a.width;scene.render.resolution_y=round(a.width*.75);scene.render.resolution_percentage=100
 scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
 scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.35
 scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
 target=Vector((0,0,-.004))
 bpy.ops.object.camera_add(location=(-.075,-.065,.085));cam=bpy.context.object;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=.061;scene.camera=cam
 for pos,energy,size in [((-.06,.08,.10),.50,.13),((.08,-.02,.07),.28,.11),((0,.03,-.08),.15,.10)]:
  bpy.ops.object.light_add(type='AREA',location=pos);light=bpy.context.object;light.data.energy=energy;light.data.shape='DISK';light.data.size=size;light.rotation_euler=(target-light.location).to_track_quat('-Z','Y').to_euler()
 scene.render.filepath=str(Path(a.preview).resolve());bpy.ops.render.render(write_still=True)
print(json.dumps({'model':str(out),'collection':'ESP32_CAM_MB','objects':len(collection.objects)}))
