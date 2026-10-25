import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path
import bpy
import numpy as np

p=argparse.ArgumentParser()
p.add_argument('--source-wrl',required=True)
p.add_argument('--output',required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
out=Path(a.output).resolve()
out.parent.mkdir(parents=True,exist_ok=True)
src=Path(a.source_wrl).resolve()
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for block in list(bpy.data.materials):bpy.data.materials.remove(block)
collection=bpy.data.collections.new('ESP32_CAM')
bpy.context.scene.collection.children.link(collection)
records=[]

def linear(c):
 return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4

def material(name,color,rough=.4,metal=0):
 m=bpy.data.materials.new(name);m.use_nodes=True
 bs=m.node_tree.nodes.get('Principled BSDF')
 bs.inputs['Base Color'].default_value=tuple(linear(c) for c in color)+(1,)
 bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal
 return m

mats={
 'pcb':material('Black PCB solder mask',(.055,.064,.061),.43),
 'edge':material('Dark FR4 board edge',(.20,.18,.12),.62),
 'black':material('Black moulded electronics',(.048,.05,.052),.38),
 'metal':material('Tin and stainless contacts',(.67,.69,.71),.29,.88),
 'gold':material('Gold plated contacts',(.73,.58,.29),.28,.85),
 'ivory':material('Ivory FFC socket',(.83,.82,.75),.38),
 'substrate':material('Module laminate edge',(.35,.30,.18),.59),
 'white':material('White PCB silkscreen',(.80,.82,.79),.65),
 'ceramic':material('Tan ceramic capacitors',(.40,.29,.16),.54),
 'flex':material('Amber polyimide ribbon',(.69,.27,.045),.35,.05),
 'flex_trace':material('Embedded ribbon copper',(.49,.21,.055),.42,.16),
 'flash':material('Pale yellow LED phosphor',(.89,.85,.40),.48),
 'lens':material('Dark optical glass',(.018,.035,.04),.07,.22),
 'sensor':material('Camera package',(.037,.039,.040),.43)
}
mats['lens'].node_tree.nodes.get('Principled BSDF').inputs['Coat Weight'].default_value=.48

def register(obj,name,mat,origin):
 obj.name=name
 for c in list(obj.users_collection):c.objects.unlink(obj)
 collection.objects.link(obj)
 obj.data.materials.clear();obj.data.materials.append(mats[mat])
 obj['provenance']=origin
 records.append({'name':name,'material':mat,'origin':origin})
 return obj

def cube(name,loc,size,mat,bevel=0,origin='Photo-based reconstruction; dimensions nominal'):
 bpy.ops.mesh.primitive_cube_add(size=1,location=tuple(x*.001 for x in loc))
 o=bpy.context.object;o.dimensions=tuple(x*.001 for x in size)
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if bevel:
  mod=o.modifiers.new('Manufactured edge radius','BEVEL');mod.width=bevel*.001;mod.segments=3
  bpy.ops.object.modifier_apply(modifier=mod.name)
 return register(o,name,mat,origin)

def cylinder(name,loc,radius,depth,mat,vertices=64):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius*.001,depth=depth*.001,location=tuple(x*.001 for x in loc))
 o=bpy.context.object
 for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
 return register(o,name,mat,'Photo-based camera detail; dimensions nominal')

def text(name,body,loc,size,rotation=0,flip=False):
 c=bpy.data.curves.new(name,'FONT');c.body=body;c.size=size*.001;c.extrude=.002*.001;c.resolution_u=6
 o=bpy.data.objects.new(name,c);collection.objects.link(o);o.location=tuple(x*.001 for x in loc)
 o.rotation_euler=(math.pi if flip else 0,0,math.radians(rotation));c.materials.append(mats['white'])
 o['provenance']='Visible product marking reconstructed from user photograph'
 records.append({'name':name,'material':'white','origin':o['provenance']})
 return o

def mesh_object(name,verts,faces,mat,origin):
 me=bpy.data.meshes.new(name);me.from_pydata((np.asarray(verts)*.001).tolist(),[],faces);me.update()
 o=bpy.data.objects.new(name,me);collection.objects.link(o)
 me.materials.append(mats[mat]);o['provenance']=origin
 for f in me.polygons:f.use_smooth=True
 me.set_sharp_from_angle(angle=math.radians(35))
 records.append({'name':name,'material':mat,'origin':origin})
 return o

def components(verts,faces):
 v,remap=np.unique(verts.round(5),axis=0,return_inverse=True);f=remap[faces];parent=np.arange(len(v))
 def find(x):
  while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
  return x
 for face in f:
  for index in face[1:]:parent[find(int(index))]=find(int(face[0]))
 roots=np.array([find(i) for i in range(len(v))]);groups={}
 for i,face in enumerate(f):groups.setdefault(int(roots[face[0]]),[]).append(i)
 for indexes in groups.values():
  old=f[indexes];used,new=np.unique(old,return_inverse=True)
  yield v[used],new.reshape(-1,3)

def canonical(v):
 q=np.empty_like(v);q[:,0]=6.515989-v[:,1];q[:,1]=v[:,0]+.002032
 q[:,2]=np.where(v[:,2]<=2.5,v[:,2]-2.5,np.where(v[:,2]>=3.5,v[:,2]-1.9,(v[:,2]-2.5)*1.6))
 return q

source_count=0
for i,shape in enumerate(src.read_text().split('Shape{')[1:]):
 if i==7:continue
 pts=re.search(r'point\s*\[([^\]]+)\]',shape,re.S).group(1)
 verts=np.array([[float(v)*2.54 for v in row.split()] for row in pts.strip(' \n,').split(',')])
 raw=[int(x) for x in re.search(r'coordIndex\s*\[([^\]]+)\]',shape,re.S).group(1).replace(',',' ').split()]
 faces=np.asarray(raw).reshape(-1,4)[:,:3]
 for j,(v,f) in enumerate(components(verts,faces)):
  lo=v.min(0);hi=v.max(0);size=hi-lo
  if i==2 and size[0]>26 and size[1]>39:continue
  if lo[1]>21.5 and 3.49<=lo[2] and hi[2]<=3.51:continue
  mat={0:'metal',1:'gold',2:'black',3:'black',4:'gold',5:'substrate',6:'ivory'}[i]
  mesh_object(f'Sourced_{i:02}_{j:03}',canonical(v),f.tolist(),mat,'External ProtoFlow/FastEDA ESP32-CAM WRL component geometry')
  source_count+=1

outline_shape=src.read_text().split('Shape{')[8]
outline_pts=re.search(r'point\s*\[([^\]]+)\]',outline_shape,re.S).group(1)
outline_native=np.array([[float(v)*2.54 for v in row.split()] for row in outline_pts.strip(' \n,').split(',')])
points=sorted(set(tuple(v) for v in canonical(outline_native)[:,:2].round(6)))
def cross2(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
lower=[]
for q in points:
 while len(lower)>=2 and cross2(lower[-2],lower[-1],q)<=0:lower.pop()
 lower.append(q)
upper=[]
for q in reversed(points):
 while len(upper)>=2 and cross2(upper[-2],upper[-1],q)<=0:upper.pop()
 upper.append(q)
outline=lower[:-1]+upper[:-1];n=len(outline)
board_vertices=[(x,y,z) for z in (0,1.6) for x,y in outline]
board_faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
board=mesh_object('CAM_PCB_core',board_vertices,board_faces,'edge','Exact sourced roundedXYboardoutline; nominal reconstructed1.6mm thickness; black face material replaces logo')
board.data.materials.append(mats['pcb'])
for i,face in enumerate(board.data.polygons):
 face.use_smooth=False
 if i<2:face.material_index=1

camera_body=cube('OV2640_square_camera_body',(11.67,0,4.53),(8.8,8.8,1.74),'sensor',.24)
camera_body.data.materials.append(mats['black'])
for face in camera_body.data.polygons:
 if face.normal.z>.9:face.material_index=1
camera_body['face_treatment']='Black top-face material on existing body surface; no additional raised geometry'
cylinder('Camera_optical_seat',(11.67,0,5.60),2.30,.40,'sensor')
ring_verts=[]
for z,r in [(5.76,2.06),(6.00,2.06),(5.76,1.62),(6.00,1.62)]:
 for i in range(64):
  angle=i*2*math.pi/64;ring_verts.append((11.67+r*math.cos(angle),r*math.sin(angle),z))
ring_faces=[]
for i in range(64):
 j=(i+1)%64
 ring_faces.extend([(i,j,64+j,64+i),(128+i,192+i,192+j,128+j),(64+i,64+j,192+j,192+i),(i,128+i,128+j,j)])
mesh_object('Camera_low_annular_rim',ring_verts,ring_faces,'black','Photo-based low lens rim; dimensions nominal')
cylinder('Camera_recessed_glass',(11.67,0,5.90),1.60,.06,'lens')
cylinder('Camera_inner_aperture',(11.67,0,5.936),.77,.012,'lens')

curve=[(-4.9,3.35),(-3.4,3.42),(-2.1,3.85),(.4,4.06),(3.2,4.10),(5.8,4.12),(7.5,4.13)]
rv=[]
for x,z in curve:rv.extend([(x,-2.35,z),(x,2.35,z),(x,-2.35,z+.13),(x,2.35,z+.13)])
rf=[]
for n in range(len(curve)-1):
 a0=n*4;b0=(n+1)*4
 rf.extend([(a0,a0+1,b0+1,b0),(a0+2,b0+2,b0+3,a0+3),(a0,b0,b0+2,a0+2),(a0+1,a0+3,b0+3,b0+1)])
rf.extend([(0,2,3,1),(len(rv)-4,len(rv)-3,len(rv)-1,len(rv)-2)])
mesh_object('OV2640_orange_flex',rv,rf,'flex','Photo-based ribbon route and width; nominal bend heights')
for j in range(12):
 y=-2.04+j*.37
 for k in range(2,len(curve)-1):
  x0,z0=curve[k];x1,z1=curve[k+1]
  mesh_object(f'Flex_internal_trace_{j:02}_{k}',[(x0,y-.025,z0+.132),(x1,y-.025,z1+.132),(x1,y+.025,z1+.132),(x0,y+.025,z0+.132)],[(0,1,2,3)],'flex_trace','Visible parallel conductor structure; count illustrative')

def photo_front(px,py):
 return 20-(py-64)*40/827,13.5-(px-934)*27/543

flash_x,flash_y=photo_front(1429,670)
cube('Flash_LED_white_package',(flash_x,flash_y,2.06),(3.15,3.15,.90),'ivory',.15)
cylinder('Flash_LED_phosphor',(flash_x,flash_y,2.53),1.18,.06,'flash')
for sign in (-1,1):cube(f'Flash_LED_solder_{sign}',(flash_x+sign*1.65,flash_y,1.69),(.55,1.7,.16),'metal',.06)
label=text('ESP32_CAM_silkscreen','ESP32-CAM',(-18.35,8.1,1.64),2.3,-90)
bpy.context.view_layer.update();label.scale*=.0162/label.dimensions.x
text('Camera_flex_mark','OV2640',(-.5,-.75,4.27),.66)
text('RF_module_mark','ESP32-S',(-5.1,3.2,-2.02),1.1,0,True)

front_components=[('R7',1154,427,1.4,.75,'black'),('R8',1173,427,1.4,.75,'black'),('R9',1195,427,1.4,.75,'black'),('R10',1288,427,1.4,.75,'black'),('R11',1312,427,1.4,.75,'black'),('R2',1367,417,.75,1.4,'black'),('R1',1367,442,.75,1.4,'black'),('R13',1367,463,.75,1.4,'black'),('R12',1367,487,.75,1.4,'black'),('C11',1037,479,1.55,.85,'ceramic'),('C2',1158,483,1.55,.85,'ceramic'),('C3',1184,484,1.4,.75,'ceramic'),('C8',1307,480,1.55,.85,'ceramic'),('C9',1335,481,1.4,.75,'ceramic'),('R15',993,653,.75,1.4,'black'),('R14',993,681,.75,1.4,'black'),('R17',1087,708,1.4,.75,'black'),('R18',1105,708,1.4,.75,'black'),('R16',1127,708,1.4,.75,'black'),('C12',1150,708,1.4,.75,'ceramic'),('C14',1171,708,1.4,.75,'ceramic'),('R3',1194,708,1.4,.75,'black'),('C13',1254,707,1.4,.75,'ceramic')]

def smd(name,x,y,w,h,mat,z=1.6,flip=False):
 sign=-1 if flip else 1
 cube(name+'_body',(x,y,z+sign*.30),(w*.68,h,.48),mat,.04)
 for side in (-1,1):
  cube(f'{name}_terminal_{side}',(x+side*w*.40,y,z+sign*.27),(w*.24,h,.36),'metal',.035)
  cube(f'{name}_pad_{side}',(x+side*w*.43,y,z+sign*.04),(w*.38,h+.16,.06),'metal',.035)

for name,px,py,w,h,mat in front_components:
 x,y=photo_front(px,py);smd(name,x,y,w,h,mat)

for name,px,py in [('U1',1081,491),('U3',1244,492),('Q2',992,602),('Q1',1439,604)]:
 x,y=photo_front(px,py)
 cube(name,(x,y,2.11),(1.4,2.5,.85),'black',.08)
 for side in (-1,1):
  count=2 if side==1 else 1
  for k in range(count):cube(f'{name}_lead_{side}_{k}',(x+side*.97,y+(k-(count-1)/2)*1.65,1.81),(.65,.45,.26),'metal',.025)

for j,(top,bottom) in enumerate(zip(['IO4','IO2','IO14','IO15','IO13','IO12','GND','5V'],['GND','U0T','U0R','VCC','GND','IO0','IO16','3V3'])):
 x=-2.36+j*2.54
 text(f'Front_pin_label_top_{j}',top,(x-.9,12.4,1.64),.60)
 text(f'Front_pin_label_bottom_{j}',bottom,(x+.9,-12.4,1.64),.60,180)

def outline(name,x,y,w,h,z=1.65):
 for sign in (-1,1):
  cube(name+f'_x{sign}',(x+sign*w/2,y,z),(.075,h,.012),'white')
  cube(name+f'_y{sign}',(x,y+sign*h/2,z),(w,.075,.012),'white')

for name,px,py,pw,ph in [('R7_8_9',1175,427,76,51),('R10_11',1300,427,59,51),('R1_2_12_13',1367,452,52,99),('C11',1037,479,44,55),('C2_3',1171,483,67,54),('C8_9',1320,480,67,54),('R14_15',993,667,46,54),('Lower_bank',1140,708,148,51),('C13',1254,707,40,54)]:
 x,y=photo_front(px,py);outline(name+'_outline',x,y,ph*40/827,pw*27/543)

for i,(px,py) in enumerate([(1026,335),(1030,352),(1021,374),(1102,340),(1122,351),(1381,345),(1388,362),(1008,739),(1037,739),(1245,766),(1359,744),(1390,749)]):
 x,y=photo_front(px,py);cylinder(f'Visible_via_{i}',(x,y,1.637),.13,.025,'substrate',20);cylinder(f'Via_drill_{i}',(x,y,1.653),.065,.009,'black',20)

def photo_back(px,py):
 return -20+(py-70)*40/817,13.5-(px-137)*27/561

back_components=[('C1',187,258),('C7',187,304),('R6',187,357),('R4',402,652),('C10',421,685),('C6',484,685),('R19',589,657),('R5',481,785),('C5',300,829)]
for name,px,py in back_components:
 x,y=photo_back(px,py);smd('Rear_'+name,x,y,1.4,.75,'ceramic' if name.startswith('C') else 'black',0,True)

x,y=photo_back(253,683)
cube('Rear_tantalum_C4',(x,y,-1.0),(4.0,2.8,1.8),'flash',.12)
for sign in (-1,1):cube(f'Rear_C4_terminal_{sign}',(x+sign*2.1,y,-.35),(.65,2.7,.5),'metal',.06)
x,y=photo_back(404,800)
cube('Rear_AMS1117_regulator',(x,y,-1.1),(3.4,6.4,1.6),'black',.10)
cube('Rear_AMS1117_tab',(x+2.3,y,-.3),(1.9,5.8,.4),'metal',.08)
for k in range(3):cube(f'Rear_AMS1117_lead_{k}',(x-2.2,y+(k-1)*2.2,-.45),(1.65,.65,.65),'metal',.06)
x,y=photo_back(566,797)
cube('Rear_PSRAM',(x,y,-.9),(4.8,3.8,1.5),'black',.13)
for side in (-1,1):
 for k in range(4):cube(f'Rear_PSRAM_lead_{side}_{k}',(x+side*2.72,y+(k-1.5)*1.15,-.38),(.9,.45,.5),'metal',.045)
x,y=photo_back(246,826)
cube('Rear_reset_switch',(x,y,-.65),(4.2,3.4,1.2),'metal',.12)
cylinder('Rear_reset_button',(x,y,-1.35),1.12,.3,'black')
text('Rear_reset_label','RST',(x-1.8,y+2.0,-.025),.9,0,True)

scene=bpy.context.scene
scene['model']='ESP32-CAM with OV2640 photo reconstruction'
scene['canonical_axes']='mm contract: board centerXY0, PCBbottomZ0, lensX+11.67, front+Z; Blenderunitsmetres'
scene['model_limitations']='Nominal component heights and photo-based SMT layout; not vendor-certified or fit-verified'
scene['external_asset_license']='No explicit redistribution license found. External sourced meshes must not be publicly redistributed.'
scene['external_source_url']='https://www.protoflow.ai/library/parts/C277946/files/COMM-TH_16P-L40.0-W27.0-P2.54_ESP32-CAM.wrl'
scene['external_sha256']=hashlib.sha256(src.read_bytes()).hexdigest()
bpy.ops.wm.save_as_mainfile(filepath=str(out))
(out.parent/'model-provenance.json').write_text(json.dumps({'source_url':scene['external_source_url'],'source_sha256':scene['external_sha256'],'external_license':'Not found; do not publicly redistribute source or derived mesh asset','board_footprint_mm':[40,27],'datasheet_nominal_footprint_mm':[40.5,27],'pcb_thickness_nominal_mm':1.6,'source_connector_xy_scale':'unchanged at2.54mm perVRMLunit','source_z_remap':'PiecewiseZadaptation: sourceZ<=2.5 shifts−2.5mm; source2.5..3.5 scales1.6x into0..1.6mm; sourceZ>=3.5 shifts−1.9mm. Components crossingPCBslabareadapted, notrigidlytranslated. XYandheaderpitchunchanged.','canonical_lens_center_mm':[11.67,0],'housing_modified':False,'reconstructed_details':['Square camera package with low recessed circular lens','Orange bent flex','Flash LED','ESP32-CAM silkscreen','Visible SMT component groups and pads; approximate locations and package heights'],'not_vendor_certified':True,'records':records},indent=2))
print(json.dumps({'blend':str(out),'source_component_meshes':source_count,'object_count':len(collection.objects)}))
