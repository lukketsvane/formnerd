import json, math
from pathlib import Path
import cadquery as cq

ROOT=Path(__file__).resolve().parents[1]
for folder in ['step','stl','review','verification','print','manual','reference']:(ROOT/folder).mkdir(parents=True,exist_ok=True)

P={
 'revision':'R08-MECH-01',
 'unit':'mm',
 'reference':'original_reference.jpg',
 'envelope_x_mm':[-68.0,68.0],
 'envelope_y_mm':[-23.0,25.0],
 'envelope_z_mm':[-39.0,39.0],
 'powerbank_size_xyz_mm':[94.0,15.0,62.0],
 'powerbank_center_xyz_mm':[-17.95,14.0,0],
 'powerbank_port_x_mm':-64.95,
 'usb_nominal_inside_side_wall_x_mm':-65.40,
 'usb_wall_clearance_nominal_mm':0.45,
 'battery_corner_radius_assumed_mm':5.3,
 'esp32_board_width_mm':27.0,
 'esp32_board_length_mm':40.5,
 'esp32_board_thickness_assumed_mm':1.6,
 'esp32_board_center_y_mm':-8.2,
 'esp32_board_center_z_mm':-5.4,
 'esp32_board_centers_x_mm':[0.0,43.0],
 'nominal_lens_offset_x_from_pcb_mm':10.0,
 'nominal_lens_offset_z_from_pcb_mm':12.6,
 'lens_centers_x_mm':[10.0,53.0],
 'lens_centers_z_mm':7.2,
 'flex_reach_verified':False,
 'esp32_cam_mb_in_final_camera':False,
 'usb_port_centers_z_assumed_mm':{'USB_C':11.5,'USB_A':-11.5},
 'snap_and_fasteners_fitted_physically':False,
 'production_outer_shell_available':False
}

def box(x,y,z,cx,cy,cz):return cq.Workplane('XY').box(x,y,z).translate((cx,cy,cz)).val()
def round_wire(xw,zh,r,cx,y,cz):
 a,b=xw/2,zh/2;r=min(r,a-0.001,b-0.001);t=math.sqrt(.5)
 return (cq.Workplane('XZ',origin=(cx,y,cz)).moveTo(-a+r,-b).lineTo(a-r,-b)
  .threePointArc((a-r+r*t,-b+r-r*t),(a,-b+r)).lineTo(a,b-r)
  .threePointArc((a-r+r*t,b-r+r*t),(a-r,b)).lineTo(-a+r,b)
  .threePointArc((-a+r-r*t,b-r+r*t),(-a,b-r)).lineTo(-a,-b+r)
  .threePointArc((-a+r-r*t,-b+r-r*t),(-a+r,-b)).close().val())
def prism(w,h,r,x,z,y0,y1):return cq.Solid.extrudeLinear(round_wire(w,h,r,x,y0,z),[],cq.Vector(0,y1-y0,0))
def cy(radius,x,z,y0,y1):return cq.Solid.makeCylinder(radius,y1-y0,cq.Vector(x,y0,z),cq.Vector(0,1,0))
def cx(radius,y,z,x0,x1):return cq.Solid.makeCylinder(radius,x1-x0,cq.Vector(x0,y,z),cq.Vector(1,0,0))
def cz(radius,x,y,z0,z1):return cq.Solid.makeCylinder(radius,z1-z0,cq.Vector(x,y,z0),cq.Vector(0,0,1))
def fuse(parts):
 result=parts[0]
 for part in parts[1:]:result=result.fuse(part)
 return result.clean()

printed={}; meta={}; refs={}; roles={}
def save(name,sh,role):
 sh=sh.clean()
 assert sh.isValid(),name+' invalid'
 assert len(sh.Solids())==1,(name,len(sh.Solids()))
 assert sh.Volume()>0,name+' volume'
 b=sh.BoundingBox()
 printed[name]=sh;roles[name]=role
 meta[name]={'volume_mm3':round(sh.Volume(),2),'bbox_mm':[round(b.xlen,2),round(b.ylen,2),round(b.zlen,2)],'valid':sh.isValid(),'role':role}
 print(name,round(sh.Volume(),1),'mm3',flush=True)

bank=box(94,15,62,-17.95,14,0)
bank= cq.Workplane('XY').box(94,15,62).edges('|Y').fillet(5.3).translate((-17.95,14,0)).val()
refs['HW01_Linocell_5000mAh_BANK']=bank
for suffix,bx in zip(['L','R'],P['esp32_board_centers_x_mm']):
 pcb=box(27,1.6,40.5,bx,P['esp32_board_center_y_mm'],P['esp32_board_center_z_mm'])
 refs['HW02_'+suffix+'_ESP32CAM_PCB']=pcb
 camera=box(9.2,5.3,9.2,bx+10,-19.6,7.2)
 refs['HW03_'+suffix+'_OV2640_MODULE_ENVELOPE']=camera

refs['HW00_CONCEPT_ENVELOPE_REFERENCE_ONLY']=prism(136,78,12,0,0,-23,25)

rail0=box(123,2.3,4.1,1.3,-2.1,-31.1)
rail1=box(123,2.3,4.1,1.3,-2.1,20.4)
spine=box(3.6,2.3,59.1,61.1,-2.1,-5.4)
chassis=fuse([rail0,rail1,spine])
mount_coords=[]
for bx in P['esp32_board_centers_x_mm']:
 for xoff in [-18.2,18.2]:
  for z in [-31.1,20.4]:
   x=bx+xoff
   mount_coords.append([x,z])
   chassis=chassis.fuse(cy(3.45,x,z,-3.25,-0.95))
   chassis=chassis.cut(cy(1.55,x,z,-3.45,-.75))
chassis=chassis.clean()
save('P01_carrier_spine',chassis,'Mechanical base mounting two independent ESP32 trays')

low=box(93.0,2.4,2.0,-17.5,4.15,-32.9)
high=box(93.0,2.4,2.0,-17.5,4.15,32.9)
stop=box(2.4,2.4,67.8,30.2,4.15,0)
cradle=fuse([low,high,stop])
for z in [-33.15,33.15]:
 cradle=cradle.fuse(box(4.2,4.1,1.5,28.6,6.3,z))
cradle=cradle.clean()
save('P02_powerbank_open_U_cradle',cradle,'94x62x15 nominal powerbank cradle, open side toward USB wall')

for name,bx in [('L',0.0),('R',43.0)]:
 z=-5.4
 tray=prism(31.9,45.8,2.0,bx,z,-6.55,-4.7).cut(prism(28.2,42.5,.85,bx,z,-6.8,-4.4))
 for edge in [-15.1,15.1]:
  tray=tray.fuse(box(1.7,8.0,43.2,bx+edge,-10.5,z))
 for edge in [-18.2,18.2]:
  for mount_z in [-31.1,20.4]:
   tray=tray.fuse(box(4.8,2.3,7.2,bx+edge*.90,-5.2,18.1 if mount_z>0 else -29.0))
   tray=tray.fuse(cy(3.15,bx+edge,mount_z,-6.35,-3.28))
   tray=tray.cut(cy(2.05,bx+edge,mount_z,-6.5,-3.05))
 for edge in [-1,1]:
  x=bx+edge*18.2
  tray=tray.fuse(box(4.8,6.6,5.5,bx+edge*17.0,-11.2,z))
  tray=tray.fuse(cy(3.05,x,z,-14.5,-7.9))
  tray=tray.cut(cy(1.55,x,z,-14.8,-7.5))
 tray=tray.clean()
 save(f'P03_{name}_esp32_edge_sled',tray,'Slide-on cradle, ESP32-CAM only, MB excluded')
 keep=prism(34.35,45.0,2.5,bx,z,-16.15,-14.55).cut(prism(29.0,40.8,.8,bx,z,-16.3,-14.4))
 for dx in [-18.2,18.2]:
  keep=keep.fuse(cy(3.05,bx+dx,z,-16.15,-14.55))
  keep=keep.cut(cy(2.05,bx+dx,z,-16.3,-14.4))
 keep=keep.clean()
 save(f'P04_{name}_removable_PCB_retainer',keep,'Removable front retainer; screw fit assumed, no electronics contact checked physically')
 lx=bx+10
 turret=cy(8.65,lx,7.2,-29.7,-25.7).fuse(cy(6.5,lx,7.2,-25.7,-22.4))
 turret=turret.cut(cy(4.55,lx,7.2,-30,-22.0)).clean()
 save(f'P05_{name}_detachable_lens_turret',turret,'Open optical ring, 9.1 mm aperture, lens interface assumed')

shutter=fuse([cz(6.1,-53,-7,34.5,37.4),cz(2.5,-53,-7,30.8,34.5),cz(3.7,-53,-7,30.2,30.9)])
save('P06_top_shutter_button',shutter,'Button only; user-visible cap and stem. Switch and spring interface pending')
washer=cz(3.85,-53,-7,31.0,32.35).cut(cz(2.8,-53,-7,30.9,32.5))
save('P07_shutter_retainer_washer',washer,'Mechanical button retainer, serviceable')

port_wall=box(2.6,22,45,-66.7,14,0)
port_wall=port_wall.cut(box(5.5,10.3,15.0,-66.7,14,-11.5))
port_wall=port_wall.cut(box(5.5,6.4,10.5,-66.7,14,11.5)).clean()
save('T01_USB_wall_fit_coupon',port_wall,'SACRIFICIAL COUPON ONLY: USB-A and USB-C nominal slots, locations assumed')

coupon=box(48,5.0,19,0,0,0)
for dx,rr in [(-17,1.65),(-7,2.1),(9,4.55),(22,5.1)]:coupon=coupon.cut(cy(rr,dx,0,-2.8,2.8))
coupon=coupon.clean()
save('T02_tolerance_fit_coupon',coupon,'Small geometry check before any major print')

asm=cq.Assembly(name='ENTROPI_STEREO_R08_INNER_ASSEMBLY')
colors={'P01':cq.Color(0.44,0.47,0.49),'P02':cq.Color(.55,.58,.59),'P03':cq.Color(.72,.74,.76),'P04':cq.Color(.67,.68,.69),'P05':cq.Color(.19,.20,.21),'P06':cq.Color(.14,.15,.16),'P07':cq.Color(.45,.47,.49),'T':cq.Color(.74,.76,.78)}
for name,obj in printed.items():
 if name.startswith('T'):continue
 asm.add(obj,name=name,color=colors[name[:3]])
asm.save(str(ROOT/'R08_inner_assembly.step'))
hw_asm=cq.Assembly(name='NOMINAL_HARDWARE_NONPRINT')
for name,obj in refs.items():
 if name.startswith('HW00_'):continue
 hw_asm.add(obj,name=name,color=cq.Color(.12,.32,.28) if 'PCB' in name else cq.Color(.4,.4,.42))
hw_asm.save(str(ROOT/'R08_nominal_hardware.step'))

for name,obj in printed.items():
 cq.exporters.export(obj,str(ROOT/'step'/f'{name}.step'))
 cq.exporters.export(obj,str(ROOT/'stl'/f'{name}.stl'),tolerance=.07,angularTolerance=.14)
for name,obj in refs.items():
 if name.startswith('HW00_'):continue
 cq.exporters.export(obj,str(ROOT/'review'/f'_ref_{name}.stl'),tolerance=.18,angularTolerance=.24)

with open(ROOT/'source'/'parameters.json','w') as f:json.dump(P,f,indent=2)
with open(ROOT/'source'/'parts_manifest.json','w') as f:json.dump(meta,f,indent=2)
with open(ROOT/'verification'/'native_solids.json','w') as f:json.dump({'parts':meta,'count':len(printed),'all_solid_valid':all(v['valid'] for v in meta.values())},f,indent=2)
print('COMPLETE',len(printed),'PRINT PARTS')