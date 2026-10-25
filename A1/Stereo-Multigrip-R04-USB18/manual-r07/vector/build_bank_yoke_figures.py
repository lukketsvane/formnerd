from pathlib import Path
import json,math,re,hashlib,sys
import numpy as np
import cadquery as cq
from OCP.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape
from OCP.HLRAlgo import HLRAlgo_Projector
from OCP.gp import gp_Ax2,gp_Pnt,gp_Dir
from OCP.BRepLib import BRepLib
from cadquery.occ_impl.exporters.svg import makeSVGedge

ROOT=Path(sys.argv[1])
OUT=Path(__file__).resolve().parent
P=json.loads((ROOT/'source/parameters.json').read_text())
manifest={'revision':'R04 USB18','source_commit':'88cc8f327fba72e6517ea30dcadc4e978419da37','geometry_modified':False,'figures':[]}

def source(name):
 return cq.importers.importStep(str(ROOT/'STEP'/f'{name}.step')).val()

def unit(v):
 v=np.array(v,dtype=float)
 return v/np.linalg.norm(v)

def render(name,shapes,camera,detail):
 f=unit(camera);right=unit(np.cross([0,0,1],f));up=unit(np.cross(f,right))
 alg=HLRBRep_Algo();alg.Add(cq.Compound.makeCompound(shapes).wrapped)
 alg.Projector(HLRAlgo_Projector(gp_Ax2(gp_Pnt(),gp_Dir(*f),gp_Dir(*right))));alg.Update();alg.Hide()
 h=HLRBRep_HLRToShape(alg)
 groups=[]
 for kind,ob in [('edge',h.VCompound()),('edge',h.Rg1LineVCompound()),('outline',h.OutLineVCompound())]:
  if ob.IsNull():continue
  BRepLib.BuildCurves3d_s(ob,1e-6)
  for e in cq.Shape.cast(ob).Edges():
   s=makeSVGedge(e)
   if s:
    a=np.array([float(v) for v in re.findall(r'[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?',s)]).reshape(-1,2)
    groups.append({'kind':kind,'xy':a.tolist()})
 pts=np.concatenate([np.array(g['xy']) for g in groups])
 x0,y0=pts.min(0);x1,y1=pts.max(0);pad=2
 paths=[]
 for g in groups:
  coords=g['xy'];d='M'+' L'.join(f'{x:.5f},{-y:.5f}' for x,y in coords)
  paths.append(f'<path d="{d}" stroke-width="{.20 if g["kind"]=="outline" else .12}"/>')
 svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0-pad} {-y1-pad} {x1-x0+2*pad} {y1-y0+2*pad}"><rect x="{x0-pad}" y="{-y1-pad}" width="{x1-x0+2*pad}" height="{y1-y0+2*pad}" fill="white"/><g fill="none" stroke="black" stroke-linejoin="round" stroke-linecap="round">'+''.join(paths)+'</g></svg>'
 (OUT/f'{name}.svg').write_text(svg)
 data={'groups':groups,'bbox':[x0,y0,x1,y1],'basis':[right.tolist(),up.tolist(),f.tolist()]}
 (OUT/f'{name}.json').write_text(json.dumps(data,separators=(',',':')))
 manifest['figures'].append({'name':name,'camera':camera,'line_count':len(groups),**detail})
 print(name,len(groups),flush=True)


def augment(name,meta):
 f=OUT/(name+'.json');d=json.loads(f.read_text());d.update(meta)
 anchors={}
 for n,a in meta.get('assembled_centers_local_mm',{}).items():
  b=meta.get('shown_centers_local_mm',{}).get(n,a)
  basis=np.array(d['basis'])
  anchors[n]={'assembled_center_mm':a,'shown_center_mm':b,'target_xy':(basis@np.array(a))[:2].tolist(),'shown_xy':(basis@np.array(b))[:2].tolist(),'move_mm':(np.array(b)-np.array(a)).tolist()}
 d['anchors']=anchors;f.write_text(json.dumps(d,separators=(',',':')))

printed={f.stem:source(f.stem) for f in (ROOT/'STEP').glob('*.step') if re.match(r'^\d\d_',f.name)}
names=[n for n in printed if n=='02_multigrip_carrier' or n.startswith(('03_','04_','05_','06_','20_','30_'))]+['01_bank_cradle']
shapes={n:printed[n] for n in names}
bank=cq.Workplane('XY').box(P['bank_w'],P['bank_h'],P['bank_d'],centered=(True,True,False)).edges('|Z').fillet(4.1).translate((0,0,P['rear_lip']+.2)).val()
shapes['REF_power_bank']=bank;names.append('REF_power_bank')
moves={'01_bank_cradle':[0,0,-42],'REF_power_bank':[0,0,-42]}
assembled={n:list(shapes[n].Center().toTuple()) for n in moves}
shown={n:(np.array(assembled[n])+np.array(moves[n])).tolist() for n in moves}
meta={'parts':names,'translations_mm':moves,'bank':'Nominal source envelope94x62x15mm, lowerZ2.8, vertical corner fillet4.1; no modeled ports. Not a measurement of user hardware.','bank_nominal_mm':[94,62,15],'bank_bottom_z_mm':2.8,'assembled_centers_local_mm':assembled,'shown_centers_local_mm':shown,'motion':'Cradle and bank separated42mm toward rear; nominal illustrative placement, no verified bank motion sweep.'}
render('bank_placement_with_bank',[shapes[n].translate(tuple(moves.get(n,[0,0,0]))) for n in names],[1.35,.75,1.6],meta)
augment('bank_placement_with_bank',meta)

side=-1;lx=side*P['baseline']/2;y=P['yoke_lock_y'];z=P['mb_bottom_z']+P['mb_pcb_t']+P['socket_height']+P['camera_pcb_t']+P['sensor_shoulder_above_pcb']+P['sensor_pad_t']-2
r=math.radians(P['module_roll_deg']);pivot=(lx-y*math.sin(r),y*math.cos(r),z);angle=90+P['module_roll_deg']
ids=['02_multigrip_carrier','05_sensor_yoke_left','30_yoke_L_up_pin','30_yoke_L_up_wedge']
local={n:printed[n].translate(tuple(-v for v in pivot)).rotate((0,0,0),(0,0,1),-angle) for n in ids}
crop=cq.Workplane('XY').box(22,26,22,centered=(True,True,False)).translate((0,0,-6)).val()
for n in ids[:2]:local[n]=local[n].intersect(crop)
common={'parts':ids,'local_transform':{'world_pivot_mm':pivot,'rotate_z_deg':-angle},'crop':{'scope':'carrier and yoke only; surrounding material sectioned for joint detail','local_box_mm':[-11,-13,-6,11,13,16]},'pin_insertion_local':[0,-1,0],'wedge_insertion_local':[0,0,-1],'slot_upper_center_local_mm':[0,-9.8,8.45]}
for name,selected,moves in [('yoke_pin_stage',ids[:3],{ids[2]:[0,24,0]}),('yoke_wedge_stage',ids,{ids[3]:[0,0,22]}),('yoke_lock_seated',ids,{})]:
 assembled={n:list(local[n].Center().toTuple()) for n in selected if n.endswith(('_pin','_wedge'))}
 shown={n:(np.array(a)+np.array(moves.get(n,[0,0,0]))).tolist() for n,a in assembled.items()}
 meta={**common,'parts':selected,'translations_mm':moves,'assembled_centers_local_mm':assembled,'shown_centers_local_mm':shown}
 render(name,[local[n].translate(tuple(moves.get(n,[0,0,0]))) for n in selected],[-1.5,1.0,1.8] if name=='yoke_pin_stage' else [-1.5,-1.0,1.8],meta)
 augment(name,meta)
(OUT/'additional-figure-manifest.json').write_text(json.dumps(manifest,indent=2))
