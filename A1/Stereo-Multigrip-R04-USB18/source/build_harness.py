"""Stereo Multigrip R04 USB18. Nominal-fit editable CAD; all fasteners printed.
X horizontal, Y vertical, Z rear of bank towards lenses; millimetres.
Independent camera pods are rolled equally about the fixed optical axes.
"""
from pathlib import Path
import json, math
import cadquery as cq
from clean_stl import clean_stl
ROOT=Path(__file__).resolve().parents[1]
P=json.loads(Path(__file__).with_name('parameters.json').read_text())
for f in ['STEP','STL','checks','previews','fit_coupon']: (ROOT/f).mkdir(exist_ok=True)
def box(w,h,d,x=0,y=0,z=0,r=0):
 q=cq.Workplane('XY').box(w,h,d,centered=(True,True,False)).translate((x,y,z))
 if r:q=q.edges('|Z').fillet(min(r,w/2-.01,h/2-.01))
 return q.val()
def cyl(r,h,x=0,y=0,z=0):return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z))
def fuse(*parts):
 q=parts[0]
 for t in parts[1:]:q=q.fuse(t)
 return q.clean()
def rot(s,a=90):return s.rotate((0,0,0),(0,0,1),a)
W,H,D=[P[k] for k in ('bank_w','bank_h','bank_d')]
BASE=P['rear_lip']; BANKZ=BASE+.2; FRONT=BANKZ+D; SPLIT=FRONT+P['bank_front_gap'];FOOT=2.4;CAGEZ=SPLIT+FOOT
MBZ=P['mb_bottom_z'];MBT=P['mb_pcb_t'];PCBZ=MBZ+MBT+P['socket_height'];PCBT=P['camera_pcb_t'];PCBTOP=PCBZ+PCBT
SHOULDER=PCBTOP+P['sensor_shoulder_above_pcb'];YOKEZ=SHOULDER+P['sensor_pad_t']+P['sensor_free_gap']
LX=P['baseline']/2;CX=LX-P['lens_offset'];CW=P['camera_pcb_w'];CH=P['camera_pcb_h'];OUTW=W+10.6;OUTH=H+7.6
ROLL=P.get('module_roll_deg',12.0);CL=P['key_clearance'];KEYH=P.get('key_height',4.4);KEYZ=6.25-KEYH/2;KY=P['keeper_lock_y'];YY=P['yoke_lock_y'];KEEPZ=CAGEZ-2
assert P['mb_pcb_w']<=CW+.4 and P['mb_pcb_h']<=CH+.4,'Resize cage/keeper for larger MB.'
def pod(shape,side):return shape.rotate((side*LX,0,0),(side*LX,0,1),ROLL)
# Common non-threaded clevis: local pin axis Y; all units use same stout pin.
# Fork 10x16x10.25, male tongue8x6x8.0, pin6x4 cross-section.
def fork():
 q=box(10,16,10.25,z=0,r=.6)
 q=q.cut(box(8.6,6.6,9,x=0,z=2.0,r=.25))
 return q.cut(box(6+2*CL,22,4+2*CL,z=4.25-CL,r=.2)).clean()
def tongue():
 q=box(8,6,8,z=2.25,r=.4)
 return q.cut(box(6+2*CL,10,4+2*CL,z=4.25-CL,r=.2)).clean()
def key():
 q=fuse(box(6,21.3,KEYH,0,-2.35,KEYZ,.45),box(10,3,KEYH,0,9.8,KEYZ,.7))
 return q.cut(box(3.4,3.6,6,0,-9.8,3.25,.2)).clean()
def wedge():
 # Taper reaches full slotthickness at upperpinface; neck above it stays constant.
 q=cq.Workplane('XY').workplane(offset=-3.75).center(0,-9.8).rect(3,2.4).workplane(offset=12.2).rect(3,3.6).loft(combine=True).val()
 return fuse(q,box(3,3.6,1.8,0,-9.8,8.45),box(3,7,2,0,-9.8,10.25,.6))
FORK=fork();TONGUE=tongue();KEY=key();WEDGE=wedge()
WEDGE_SHORT=WEDGE.cut(box(30,40,P['camera_wedge_tip_relief'],z=-3.75)).clean()
def place(shape,x,y,z,angle=90):return rot(shape,angle).translate((x,y,z))
PRINTED={};LOCKS=[];JOINTS=[]
def lockpair(prefix,x,y,z,side=None,angle=90):
 JOINTS.append((prefix,x,y,z,side,angle))
 for tag,shape in [('pin',KEY),('wedge',WEDGE)]:
  if not prefix.startswith('10_frame_') and tag=='wedge':shape=WEDGE_SHORT
  q=place(shape,x,y,z,angle)
  if side:q=pod(q,side)
  PRINTED[f'{prefix}_{tag}']=q;LOCKS.append(f'{prefix}_{tag}')
# Rear bank cradle: same open-back capture, bank retained at its rim.
a=box(OUTW,OUTH,SPLIT,r=6.5)
a=a.cut(box(W+.6,H+.6,SPLIT+2,z=BASE,r=4.4)).cut(box(W-10,H-10,BASE+1,z=-.5,r=6))
for s in (-1,1):a=a.cut(box(18,45,SPLIT-BASE+1,s*OUTW/2,0,BASE+1,1))
a=a.cut(box(54,12,7,0,OUTH/2,7.5,2))
for sy in (-1,1):
 for x in (-28,0,28):a=a.cut(cyl(9.2,SPLIT+2,x,sy*(OUTH/2+8.25),-.5))
# Main keys run along X, positioned on long edges outside the bank/port envelope.
MAIN=[]
for sx in (-1,1):
 for sy in (-1,1):
  x=sx*P['main_lock_x'];y=sy*P['main_lock_y'];z=SPLIT-10.25
  a=a.fuse(place(FORK,x,y,z));MAIN.append((x,y,z))
# Carrier's global perimeter; camera pods connect through outward service lugs.
b=box(OUTW,OUTH,FOOT,z=SPLIT,r=6.5).cut(box(97,52,FOOT+2,z=SPLIT-1,r=5))
for i,(x,y,z) in enumerate(MAIN):
 b=b.fuse(place(TONGUE,x,y,z))
 # Tongue neck connects to the perimeter above the fork top.
 b=b.fuse(box(7,8,FOOT,x,y-math.copysign(3,y),SPLIT,.6))
 lockpair(f'10_frame_{i+1}',x,y,z)
# Local electronics pods: gaps at sockets remain open; all geometry rotates together.
LOCAL_KEEP={};LOCAL_YOKE={};PODS=[];KEEPOUTS={};PLUG_BODIES={};KEEPER_APPROACHES=[]
for side,label in [(-1,'L'),(1,'R')]:
 cx=side*CX;lx=side*LX
 c=box(CW+4,CH+6.2,PCBTOP+.2-CAGEZ,cx,0,CAGEZ,2)
 c=c.cut(box(CW+.6,CH+.6,PCBTOP+.2-CAGEZ+2,cx,0,CAGEZ-1,1))
 for sy in (-1,1):c=c.cut(box(29,10,5,cx,sy*16,CAGEZ+3,1.5))
 for sx in (-1,1):c=c.cut(box(8,21,9.2,cx+sx*(CW/2+1),0,CAGEZ+1.2,1.4))
 for sx in (-1,1):
  for sy in (-1,1):c=c.fuse(box(2.4,4.2,1.2,cx+sx*(CW/2-.4),sy*(CH/2+.1),PCBTOP+.2,.5))
 # Keeper locks are moved outside the sensor lock towers and cable paths.
 k=box(CW+3,36.8,2,cx,0,KEEPZ,2).cut(box(CW-3,28.6,4,cx,0,KEEPZ-1,1.4))
 for sx in (-1,1):
  for sy in (-1,1):
   k=k.fuse(box(2.2,3,MBZ-CAGEZ,cx+sx*(CW/2-.25),sy*7.5,CAGEZ,.4))
   c=c.cut(box(2.6,3.4,MBZ-CAGEZ+.25,cx+sx*(CW/2-.25),sy*7.5,CAGEZ-.01,.35))
 for sy in (-1,1):
  y=sy*KY;z=MBZ+P['keeper_lock_rise']
  c=c.fuse(box(9,18,3.4+P['keeper_lock_rise'],cx,sy*(KY-6.5),CAGEZ,.8))
  c=c.fuse(place(FORK,cx,y,z))
  k=k.fuse(box(6,17,2,cx,sy*(KY-6.5),KEEPZ,.6))
  k=k.fuse(box(6,8,5.55+P['keeper_lock_rise'],cx,y,KEEPZ,.5))
  k=k.fuse(place(TONGUE,cx,y,z))
  ox=cx+side*(CW/2+3.2);oy=sy*16.4;armz=z+2.4
  k=k.fuse(box(5.5,4,2,cx+side*(CW/2+2),oy,KEEPZ,.5))
  k=k.fuse(box(3.2,4,armz+2-KEEPZ,ox,oy,KEEPZ,.5))
  length=math.hypot(cx-ox,y-oy);angle=math.degrees(math.atan2(y-oy,cx-ox))
  arm=rot(box(length+4,4,2,z=armz,r=.5),angle).translate(((cx+ox)/2,(y+oy)/2,0))
  k=k.fuse(arm)
  approach=rot(box(length+4.4,4.4,armz+2.2-KEEPZ+.2,z=KEEPZ-.2,r=.5),angle).translate(((cx+ox)/2,(y+oy)/2,0))
  KEEPER_APPROACHES.append((label,pod(approach,side)))
  lockpair(f'20_keeper_{label}_{"up" if sy>0 else "down"}',cx,y,z,side)
 # Sensor yoke and paired fork towers: tongue enters from front, hard-stop on floor.
 yoke=box(13.8,14.6,2.2,lx,0,YOKEZ,2.2)
 yoke=yoke.cut(cyl(P['lens_clearance_d']/2,4,lx,0,YOKEZ-1))
 inward=-side;yoke=yoke.cut(box(12,P['flex_throat_w'],4,lx+inward*6,0,YOKEZ-1,.5))
 for sy in (-1,1):
  y=sy*YY;z=YOKEZ-2.0
  # Common clevis floor atYOKEZ-.25; yoke male tongue starts exactlyYOKEZ.
  c=c.fuse(box(16,10,z+2-CAGEZ,lx,y,CAGEZ,.7))
  c=c.fuse(place(FORK,lx,y,z))
  # Clear yoke arm under the fork while retaining two outer pillar walls.
  c=c.cut(box(6.6,12,2.3,lx,y,YOKEZ,.3))
  c=c.fuse(box(7,9,3.2,lx,sy*16,PCBTOP-1.3,.8))
  yoke=yoke.fuse(box(5.2,15.0,2.2,lx,sy*(YY/2+2),YOKEZ,1.2))
  yoke=yoke.fuse(place(TONGUE,lx,y,z))
  lockpair(f'30_yoke_{label}_{"up" if sy>0 else "down"}',lx,y,z,side)
 # Integral printed corner contacts retain the sensor without separate pad hardware.
 for sx in (-1,1):
  for sy in (-1,1):yoke=yoke.fuse(box(1,1,P['sensor_pad_t'],lx+sx*3.75,sy*3.75,YOKEZ-P['sensor_pad_t'],.12))
 LOCAL_KEEP[label]=pod(k.clean(),side);LOCAL_YOKE[label]=pod(yoke.clean(),side)
 inward=-side;face=cx+inward*(CW/2-1+2.75);usbz=MBZ+MBT+1.2
 clearance=P['usb_plug_clearance'];projection=P['usb_plug_projection'];bodyw=P['usb_plug_body_w'];bodyh=P['usb_plug_body_h']
 plug=box(projection,bodyw,bodyh,face+inward*projection/2,0,usbz-bodyh/2,.6)
 PLUG_BODIES[f'USB_{label}_plug_body']=pod(plug,side)
 service=box(projection+2*clearance,bodyw+2*clearance,bodyh+2*clearance,face+inward*projection/2,0,usbz-bodyh/2-clearance,.6)
 KEEPOUTS[f'USB_{label}_plug']=pod(service,side)
 travel=P['usb_insertion_travel']
 insertion=box(projection+travel+2*clearance,bodyw+2*clearance,bodyh+2*clearance,face+inward*(projection+travel)/2,0,usbz-bodyh/2-clearance,.6)
 KEEPOUTS[f'USB_{label}_insertion']=pod(insertion,side)
 radius=P['usb_cable_bend_radius'];away=-side
 p0=cq.Vector(face+inward*projection,0,usbz)
 p1=cq.Vector(face+inward*(projection+P['usb_cable_straight']),0,usbz)
 pm=cq.Vector(p1.x+inward*radius/math.sqrt(2),away*radius*(1-1/math.sqrt(2)),usbz)
 p2=cq.Vector(p1.x+inward*radius,away*radius,usbz)
 p3=cq.Vector(p2.x,away*(radius+P['usb_cable_exit']),usbz)
 wire=cq.Wire.assembleEdges([cq.Edge.makeLine(p0,p1),cq.Edge.makeThreePointArc(p1,pm,p2),cq.Edge.makeLine(p2,p3)])
 plane=cq.Plane(origin=p0,normal=(inward,0,0),xDir=(0,1,0))
 route=cq.Workplane(plane).circle(P['usb_cable_diameter']/2+clearance).sweep(wire).val()
 KEEPOUTS[f'USB_{label}_cable_route']=pod(route,side)
 PODS.append(pod(c.clean(),side))
for c in PODS:b=b.fuse(c)
# Broad outboard webs establish material continuity to the perimeter.
for side in (-1,1):
 for sy in (-1,1):
  xx=side*CX+side*(CW/2+1); yy=sy*17.5
  dx=xx-side*LX; rr=math.radians(ROLL)
  wx=side*LX+dx*math.cos(rr)-yy*math.sin(rr)
  wy=dx*math.sin(rr)+yy*math.cos(rr)
  end=side*50.2
  web=box(abs(end-wx)+5.5,5.5,FOOT+5.0,(end+wx)/2,wy,SPLIT,.7)
  b=b.fuse(web)
# Clear all keeper backs, including rotated ears, through the global ring.
for k in LOCAL_KEEP.values():b=b.cut(k)
for label,q in KEEPER_APPROACHES:b=b.cut(q)
# Bank plugs remain accessible; add dedicated slots for removable cord ties.
for sx in (-1,1):
 for sy in (-1,1):b=b.cut(box(2.4,8,FOOT+1,sx*44,sy*29,SPLIT-.5,.7))
for name,q in KEEPOUTS.items():
 b=b.cut(q)
 for label in LOCAL_KEEP:LOCAL_KEEP[label]=LOCAL_KEEP[label].cut(q)
 for label in LOCAL_YOKE:LOCAL_YOKE[label]=LOCAL_YOKE[label].cut(q)
# Recut all locking paths after structural unions, which otherwise refill holes.
for prefix,x,y,z,side,angle in JOINTS:
 channel=place(box(6+2*CL,36,4.5,z=4.0,r=.2),x,y,z,angle)
 headpath=place(box(10.4,5,4.8,0,10.5,3.85,.4),x,y,z,angle)
 # Wedge insertion paths clear adjacent structure; the fork exit remains a bearing face.
 wedgepath=place(fuse(box(3.4,3.8,14.25,0,-9.8,-4,.2),box(3.4,7.4,5,0,-9.8,10.25,.4)),x,y,z,angle)
 if side:
  channel=pod(channel,side);wedgepath=pod(wedgepath,side);headpath=pod(headpath,side)
 b=b.cut(channel).cut(wedgepath).cut(headpath)
 if prefix.startswith('10_'):
  pocket=place(box(8.6,6.6,9,z=2.0,r=.25),x,y,z,angle)
  a=a.cut(pocket).cut(channel).cut(wedgepath).cut(headpath)
  for label in LOCAL_KEEP:LOCAL_KEEP[label]=LOCAL_KEEP[label].cut(wedgepath)
 else:
  a=a.cut(wedgepath)
  if prefix.startswith('20_keeper_'):
   label='L' if '_L_' in prefix else 'R'
   LOCAL_KEEP[label]=LOCAL_KEEP[label].cut(channel).cut(headpath)
# Board margin relief: structural bridges never overlap bare PCB envelopes.
for side in (-1,1):
 for zz,th in [(MBZ,MBT),(PCBZ,PCBT)]:
  void=pod(box(CW+.6,CH+.6,th+.3,side*CX,0,zz-.15,1),side)
  b=b.cut(void)
# Yoke plate unions can cover their tongue bores. Clear the complete path again.
for label,side in [('L',-1),('R',1)]:
 q=LOCAL_YOKE[label]
 for sy in (-1,1):
  channel=pod(place(box(6+2*CL,36,4.5,z=4.0,r=.2),side*LX,sy*YY,YOKEZ-2.0),side)
  q=q.cut(channel)
 LOCAL_YOKE[label]=q.clean()
KEEPER_SWEEPS={}
for label,k in LOCAL_KEEP.items():
 sweep=k
 for face in k.Faces():
  if face.normalAt().z<-.999999:
   distance=SPLIT-20-face.Center().z
   if distance<0:
    sweep=sweep.fuse(cq.Solid.extrudeLinear(face.outerWire(),face.innerWires(),cq.Vector(0,0,distance)))
 KEEPER_SWEEPS[label]=sweep.clean()
 b=b.cut(sweep)
a=a.clean();b=b.clean()
# Keep the single material solid and heal Boolean remnants before export.
if not b.isValid():
 solid=b.Solids()[0].fix()
 if solid.isValid():b=solid
 else:
  transfer=ROOT/'checks'/'carrier-transfer.step'
  tmp=cq.Assembly(name='Carrier_transfer');tmp.add(b,name='carrier');tmp.save(str(transfer))
  b=cq.importers.importStep(str(transfer)).val().Solids()[0].fix()
  transfer.unlink()
detached=[]
if len(b.Solids())>1:
 solids=sorted(b.Solids(),key=lambda shape:shape.Volume(),reverse=True)
 for fragment in solids[1:]:
  bb=fragment.BoundingBox()
  usb_strip=fragment.Volume()<12 and bb.zmax<=MBZ+.01 and bb.zmin>=CAGEZ-.01
  web_tip=fragment.Volume()<22 and bb.zmin>=SPLIT-.01 and bb.zmax<=SPLIT+FOOT+5+.01 and (bb.xmin>OUTW/2 or bb.xmax<-OUTW/2)
  assert usb_strip or web_tip,'Unexpected disconnected carrier material'
  detached.append({'purpose':'USB-side orphan wall relief' if usb_strip else 'non-bearing exterior web tip removed for rear keeper access','volume_mm3':round(fragment.Volume(),6),'bbox':[round(v,6) for v in (bb.xmin,bb.ymin,bb.zmin,bb.xmax,bb.ymax,bb.zmax)]})
 b=solids[0].clean()
assert b.isValid() and len(b.Solids())==1,'Carrier must export as one valid solid.'


assert all(q.isValid() and len(q.Solids())==1 for q in LOCAL_KEEP.values()),[(label,q.isValid(),len(q.Solids())) for label,q in LOCAL_KEEP.items()]
PRINTED={'01_bank_cradle':a,'02_multigrip_carrier':b,'03_MB_keeper_left':LOCAL_KEEP['L'],'04_MB_keeper_right':LOCAL_KEEP['R'],'05_sensor_yoke_left':LOCAL_YOKE['L'],'06_sensor_yoke_right':LOCAL_YOKE['R'],**PRINTED}
assert all(q.isValid() and len(q.Solids())==1 and q.Volume()>0 for q in PRINTED.values()),[(name,q.isValid(),len(q.Solids())) for name,q in PRINTED.items()]
# Export actual solids and scene. LockSTLs are rotated so pin-axis lies in printbed.
scene=[];REF={};assembly=cq.Assembly(name='Stereo_Multigrip_R04_USB18_nominal_fit')
def add(name,shape,color,category='hardware',printable=False):
 assembly.add(shape,name=name,color=cq.Color(*color));path=ROOT/'STL'/f'{name}.stl';cq.exporters.export(shape,str(path),tolerance=.06,angularTolerance=.15)
 scene.append({'name':name,'stl':str(path.relative_to(ROOT)),'color':list(color),'category':category})
 if printable:
  cq.exporters.export(shape,str(ROOT/'STEP'/f'{name}.step'))
  flat=shape
  # Wedges are flat on broad face, keeping the taper in the XY printplane.
  if name.endswith('_wedge'):flat=(WEDGE_SHORT if not name.startswith('10_frame_') else WEDGE).rotate((0,0,0),(0,1,0),90)
  bb=flat.BoundingBox();flat=flat.translate((-(bb.xmin+bb.xmax)/2,-(bb.ymin+bb.ymax)/2,-bb.zmin))
  cq.exporters.export(flat,str(ROOT/'STL'/f'PRINT_{name}.stl'),tolerance=.04,angularTolerance=.12)
for name,q in PRINTED.items():add(name,q,(.69,.71,.72) if not name.endswith(('_pin','_wedge')) else(.26,.29,.31),'printed',True)
def ref(name,shape,color,category='hardware',side=None):
 if side:shape=pod(shape,side)
 REF[name]=shape;add(name,shape,color,category)
bank=box(W,H,D,z=BANKZ,r=4.1);ref('REF_power_bank',bank,(.055,.065,.073))
ref('REF_bank_indicator',box(6,24,.25,-29,4,FRONT,.9),(.018,.025,.03))
for yy in(9,16):ref(f'REF_LED_{yy}',cyl(.75,.3,-29,yy,FRONT+.25),(.15,.65,.72))
for side,label in[(-1,'L'),(1,'R')]:
 cx=side*CX;lx=side*LX
 ref(f'REF_{label}_MB',box(P['mb_pcb_w'],P['mb_pcb_h'],MBT,cx,0,MBZ,1),(.045,.075,.065),side=side)
 ref(f'REF_{label}_CAM',box(CW,CH,PCBT,cx,0,PCBZ,1),(.035,.065,.06),side=side)
 for sy in(-1,1):
  ref(f'REF_{label}_socket_{sy}',box(20.4,2.5,P['socket_height'],cx+side*3,sy*10.9,MBZ+MBT,.4),(.055,.06,.065),side=side)
  for i in range(8):
   px=cx+side*3+(i-3.5)*2.54
   ref(f'REF_{label}_pin_{sy}_{i}',box(.6,.6,P['pin_projection'],px,sy*10.9,MBZ-P['pin_projection']),(.62,.65,.66),side=side)
 ref(f'REF_{label}_SD_cage',box(13,14,2.45,lx,0,PCBTOP,.6),(.59,.62,.64),side=side)
 ref(f'REF_{label}_sensor_carrier',box(P['sensor_carrier_w'],P['sensor_carrier_h'],1.25,lx,0,SHOULDER-1.25,.3),(.09,.095,.10),side=side)
 ref(f'REF_{label}_lens_barrel',cyl(P['lens_barrel_d']/2,P['lens_projection'],lx,0,SHOULDER),(.06,.065,.073),side=side)
 ref(f'REF_{label}_lens_glass',cyl(1.7,.15,lx,0,SHOULDER+P['lens_projection']),(.05,.23,.24),side=side)
 inward=-side
 ref(f'REF_{label}_flex',box(9,5,.2,lx+inward*8.6,0,PCBTOP+2.5),(.75,.31,.055),side=side)
 ref(f'REF_{label}_flex_socket',box(2.4,17,1.8,cx+inward*5,0,PCBTOP,.3),(.82,.82,.74),side=side)
 ref(f'REF_{label}_USB_socket',box(5.5,7.5,2.4,cx+inward*(CW/2-1),0,MBZ+MBT,.4),(.57,.60,.62),side=side)
assembly.save(str(ROOT/'STEP'/'Stereo-Multigrip-R04-USB18-assembly.step'))
pa=cq.Assembly(name='Printed_parts_only')
for n,s in PRINTED.items():pa.add(s,name=n,color=cq.Color(.7,.72,.73))
pa.save(str(ROOT/'STEP'/'Stereo-Multigrip-R04-USB18-harness-only.step'))
(ROOT/'scene_assembled.json').write_text(json.dumps({'items':scene},indent=2))
(ROOT/'scene_harness.json').write_text(json.dumps({'items':[i for i in scene if i['category']=='printed']},indent=2))
exploded=[]
for i in scene:
 q=dict(i);n=q['name'];q['translation']=[0,0,-18 if n=='01_bank_cradle' else 35 if'yoke'in n else -6 if'keeper'in n else 18 if n=='02_multigrip_carrier' else 5];exploded.append(q)
(ROOT/'scene_exploded.json').write_text(json.dumps({'items':exploded},indent=2))
ko=cq.Assembly(name='USB_reference_keepouts')
for n,s in KEEPOUTS.items():ko.add(s,name=n,color=cq.Color(1,.4,.1,.35))
ko.save(str(ROOT/'STEP'/'USB-keepouts-reference.step'))
# A separate compact fit-test: same clevis, tongue and pin, plus slotclearance options.
for n,s in [('TEST_fork',FORK),('TEST_tongue',TONGUE),('TEST_pin',KEY),('TEST_wedge',WEDGE)]:
 flat=s
 if n.endswith('wedge'):flat=WEDGE.rotate((0,0,0),(0,1,0),90)
 bb=flat.BoundingBox();flat=flat.translate((-(bb.xmin+bb.xmax)/2,-(bb.ymin+bb.ymax)/2,-bb.zmin))
 cq.exporters.export(flat,str(ROOT/'fit_coupon'/f'{n}.stl'));cq.exporters.export(s,str(ROOT/'fit_coupon'/f'{n}.step'))
for mesh_path in list((ROOT/'STL').glob('*.stl'))+list((ROOT/'fit_coupon').glob('*.stl')):clean_stl(mesh_path)
checks={'status':'NOMINAL FIT PROTOTYPE; physical/cable fitting not verified','parts':{},'printed_pair_intersections':[],'hardware_intersections':[],'plug_material_intersections':[],'service_hardware_intersections':[],'keeper_insertion_hardware_intersections':[],'assumptions':P['_assumptions'],'removed_disconnected_service_cut_fragments':detached}
for n,s in PRINTED.items():
 bb=s.BoundingBox();checks['parts'][n]={'valid':s.isValid(),'solids':len(s.Solids()),'volume_mm3':round(s.Volume(),2),'bbox_mm':[round(v,3)for v in(bb.xlen,bb.ylen,bb.zlen)]}
 print(n,checks['parts'][n],flush=True)
keys=list(PRINTED)
for i,n in enumerate(keys):
 for m in keys[i+1:]:
  s,t=PRINTED[n],PRINTED[m];bb,bt=s.BoundingBox(),t.BoundingBox()
  if bb.xmax<bt.xmin or bt.xmax<bb.xmin or bb.ymax<bt.ymin or bt.ymax<bb.ymin or bb.zmax<bt.zmin or bt.zmax<bb.zmin:continue
  v=s.intersect(t).Volume()
  if v>1e-4:checks['printed_pair_intersections'].append([n,m,round(v,6)])
for n,s in PRINTED.items():
 for m,t in REF.items():
  if m.startswith('PAD'):continue
  bb,bt=s.BoundingBox(),t.BoundingBox()
  if bb.xmax<bt.xmin or bt.xmax<bb.xmin or bb.ymax<bt.ymin or bt.ymax<bb.ymin or bb.zmax<bt.zmin or bt.zmax<bb.zmin:continue
  v=s.intersect(t).Volume()
  if v>1e-4:checks['hardware_intersections'].append([n,m,round(v,6)])
 for m,t in KEEPOUTS.items():
  v=s.intersect(t).Volume()
  if v>1e-4:checks['plug_material_intersections'].append([n,m,round(v,6)])
for label,q in KEEPER_SWEEPS.items():
 for name,hardware in REF.items():
  if not name.startswith(('REF_L_','REF_R_')):continue
  volume=q.intersect(hardware).Volume()
  if volume>1e-4:checks['keeper_insertion_hardware_intersections'].append([label,name,round(volume,6)])
checks['keeper_insertion']={'method':'continuous negative-Z sweep of all downward planar faces plus the final prismatic keeper; bank, yokes, pins and cables are fitted afterwards','rear_limit_z_mm':SPLIT-20}
checks['plug_pair_overlap_mm3']=round(PLUG_BODIES['USB_L_plug_body'].intersect(PLUG_BODIES['USB_R_plug_body']).Volume(),6)
checks['plug_pair_clearance_mm']=round(PLUG_BODIES['USB_L_plug_body'].distance(PLUG_BODIES['USB_R_plug_body']),6)
checks['insertion_pair_clearance_mm']=round(KEEPOUTS['USB_L_insertion'].distance(KEEPOUTS['USB_R_insertion']),6)
for label,other in [('L','R'),('R','L')]:
 for name,q in {**KEEPOUTS,**PLUG_BODIES}.items():
  if not name.startswith('USB_'+label+'_'):continue
  for refname,hardware in REF.items():
   if not refname.startswith('REF_'+other+'_'):continue
   volume=q.intersect(hardware).Volume()
   if volume>1e-4:checks['service_hardware_intersections'].append([name,refname,round(volume,6)])
checks['plug_to_opposite_MB_clearance_mm']={label:round(PLUG_BODIES['USB_'+label+'_plug_body'].distance(REF['REF_'+other+'_MB']),6) for label,other in [('L','R'),('R','L')]}

bb=cq.Compound.makeCompound(list(PRINTED.values())+[bank]).BoundingBox()
checks['dimensions_mm']={'harness_bbox':[round(v,3)for v in(bb.xlen,bb.ylen,bb.zlen)],'baseline':2*LX,'module_roll_deg':ROLL,'bank':[W,H,D],'sensor_gap':P['sensor_free_gap']}
(ROOT/'checks'/'geometry-checks.json').write_text(json.dumps(checks,indent=2));print(json.dumps({k:v for k,v in checks.items()if k!='parts'},indent=2),flush=True)

assert not checks['printed_pair_intersections'],checks['printed_pair_intersections']
assert not checks['hardware_intersections'],checks['hardware_intersections']
assert not checks['plug_material_intersections'],checks['plug_material_intersections']
assert not checks['service_hardware_intersections'],checks['service_hardware_intersections']
assert checks['plug_pair_overlap_mm3']==0
assert not checks['keeper_insertion_hardware_intersections'],checks['keeper_insertion_hardware_intersections']
