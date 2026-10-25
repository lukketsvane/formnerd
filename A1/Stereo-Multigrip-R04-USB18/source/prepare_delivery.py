from pathlib import Path
import json,math
import cadquery as cq
from clean_stl import clean_stl
from make_print_plate import make

ROOT=Path(__file__).resolve().parents[1]
P=json.loads((ROOT/'source/parameters.json').read_text())
OLD=ROOT.parent/'Stereo-Multigrip-R03'
for folder in ['3MF','previews/assets']:(ROOT/folder).mkdir(parents=True,exist_ok=True)
def box(w,h,d,x=0,y=0,z=0,r=0):
 q=cq.Workplane('XY').box(w,h,d,centered=(True,True,False)).translate((x,y,z))
 if r:q=q.edges('|Z').fillet(r)
 return q.val()
def read(name,root=ROOT):return cq.importers.importStep(str(root/'STEP'/f'{name}.step')).val()
def pod(shape,side):
 x=side*P['baseline']/2
 return shape.rotate((x,0,0),(x,0,1),P['module_roll_deg'])
carrier=read('02_multigrip_carrier')
split=P['rear_lip']+.2+P['bank_d']+P['bank_front_gap']
cagez=split+2.4
mbz=P['mb_bottom_z'];mbt=P['mb_pcb_t']
cx=P['baseline']/2-P['lens_offset'];cw=P['camera_pcb_w']
keepouts=cq.importers.importStep(str(ROOT/'STEP/USB-keepouts-reference.step')).val().Solids()
gauge=carrier.intersect(box(200,200,mbz+mbt+.2-split,z=split))
support=box(P['bank_w']+10.6,P['bank_h']+7.6,mbz-split,z=split,r=6.5).cut(box(97,52,mbz-split+2,z=split-1,r=5))
for side in [-1,1]:
 for sy in [-1,1]:
  xx=side*cx+side*(cw/2+1);yy=sy*17.5
  dx=xx-side*P['baseline']/2;angle=math.radians(P['module_roll_deg'])
  wx=side*P['baseline']/2+dx*math.cos(angle)-yy*math.sin(angle)
  wy=dx*math.sin(angle)+yy*math.cos(angle);end=side*50.2
  support=support.fuse(box(abs(end-wx)+5.5,5.5,mbz-split,(end+wx)/2,wy,split,r=.7))
for side in [-1,1]:support=support.cut(pod(box(cw+.6,P['camera_pcb_h']+.6,mbt+.3,side*cx,0,mbz-.15,r=1),side))
for shape in keepouts:support=support.cut(shape)
gauge=gauge.fuse(support)

for side in [-1,1]:
 for sx in [-1,1]:
  for sy in [-1,1]:
   foot=cq.Workplane('XY').box(2.2,3.8,mbz-cagez,centered=(True,True,False)).edges('|Z').fillet(.4).translate((side*cx+sx*(cw/2-.25),sy*7.5,cagez)).val()
   gauge=gauge.fuse(pod(foot,side))
gauge=gauge.clean()
assert gauge.isValid() and len(gauge.Solids())==1
cq.exporters.export(gauge,str(ROOT/'fit_coupon/TEST_USB_clearance_18deg.step'))
bb=gauge.BoundingBox();flat=gauge.translate((-(bb.xmin+bb.xmax)/2,-(bb.ymin+bb.ymax)/2,-bb.zmin))
cq.exporters.export(flat,str(ROOT/'fit_coupon/TEST_USB_clearance_18deg.stl'),tolerance=.04,angularTolerance=.12)
clean_stl(ROOT/'fit_coupon/TEST_USB_clearance_18deg.stl')
make([ROOT/'fit_coupon/TEST_USB_clearance_18deg.stl'],ROOT/'3MF/00_USB_CLEARANCE_TEST_FIRST.3mf','R04 18 degree USB clearance gauge - unsliced')
names=['02_multigrip_carrier','03_MB_keeper_left','04_MB_keeper_right','20_keeper_L_up_wedge','20_keeper_L_down_wedge','20_keeper_R_up_wedge','20_keeper_R_down_wedge','30_yoke_L_up_wedge','30_yoke_L_down_wedge','30_yoke_R_up_wedge','30_yoke_R_down_wedge']
make([ROOT/'STL'/f'PRINT_{name}.stl' for name in names],ROOT/'3MF/01_R04_REPLACEMENT_PARTS.3mf','R04 18 degree carrier, raised keepers and eight short camera wedges - unsliced')
scene=json.loads((ROOT/'scene_assembled.json').read_text())
scene['items']=[item for item in scene['items'] if item['name'] not in ['01_bank_cradle','REF_power_bank','REF_bank_indicator','REF_LED_9','REF_LED_16'] and not item['name'].startswith('10_frame_')]
for item in scene['items']:item['stl']='../'+item['stl']
for side,label in [(-1,'L'),(1,'R')]:
 inward=-side;face=side*cx+inward*(cw/2-1+2.75);depth=P['usb_plug_projection'];usbz=mbz+mbt+1.2
 plug=pod(box(depth,P['usb_plug_body_w'],P['usb_plug_body_h'],face+inward*depth/2,0,usbz-P['usb_plug_body_h']/2),side)
 name=f'USB_{label}_nominal_body';cq.exporters.export(plug,str(ROOT/'previews/assets'/f'{name}.stl'))
 scene['items'].append({'name':name,'stl':f'assets/{name}.stl','color':[.12,.13,.14],'category':'assumed_plug'})
routes=[shape for shape in keepouts if shape.Volume()<3000]
assert len(routes)==2
gauge_service=[round(gauge.intersect(shape).Volume(),7) for shape in keepouts]
assert all(volume<1e-4 for volume in gauge_service),gauge_service
(ROOT/'checks/gauge-checks.json').write_text(json.dumps({'valid':gauge.isValid(),'solids':len(gauge.Solids()),'height_mm':round(bb.zlen,3),'service_intersection_volumes_mm3':gauge_service,'support_foot_y_mm':3.8,'status':'nominal fit test; physical fitting not verified'},indent=2))
for index,shape in enumerate(routes):
 name=f'cable_clearance_{index}';cq.exporters.export(shape,str(ROOT/'previews/assets'/f'{name}.stl'))
 scene['items'].append({'name':name,'stl':f'assets/{name}.stl','color':[.22,.23,.24],'category':'assumed_cable_clearance'})
(ROOT/'previews/scene_cable_clearance.json').write_text(json.dumps(scene,indent=2))
reuse={'source':'Stereo-Multigrip-R03','target':'Stereo-Multigrip-R04-USB18','new_prints':names,'reused_parts':{},'status':'not checked'}
if OLD.exists():
 for name in ['01_bank_cradle','05_sensor_yoke_left','06_sensor_yoke_right']+[p.stem for p in (OLD/'STEP').glob('10_frame_*.step')]+[p.stem for p in (OLD/'STEP').glob('20_keeper_*_pin.step')]+[p.stem for p in (OLD/'STEP').glob('30_yoke_*_pin.step')]:
  old=read(name,OLD);new=read(name)
  if name.startswith(('05_','06_','20_','30_')):
   side=-1 if ('left' in name or '_L_' in name) else 1
   axis=side*P['baseline']/2
   old=old.rotate((axis,0,0),(axis,0,1),P['module_roll_deg']-12)
   if name.startswith('20_'):old=old.translate((0,0,P['keeper_lock_rise']))
  outside=max(0,old.cut(new).Volume());missing=max(0,new.cut(old).Volume())
  assert outside<1e-4,(name,outside)
  if name!='01_bank_cradle':assert missing<1e-4,(name,missing)
  reuse['reused_parts'][name]={'material_outside_new_mm3':round(outside,7),'new_material_not_in_old_mm3':round(missing,7)}
 reuse['status']='passed'
(ROOT/'checks/reuse-checks.json').write_text(json.dumps(reuse,indent=2))
print(json.dumps({'gauge_valid':gauge.isValid(),'gauge_solids':len(gauge.Solids()),'gauge_height_mm':round(bb.zlen,3),'reuse':reuse['status'],'new_prints':len(names)}))
