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

side=-1
lx=side*P['baseline']/2;cx=side*(P['baseline']/2-P['lens_offset']);y=P['keeper_lock_y'];z=P['mb_bottom_z']+P['keeper_lock_rise'];r=math.radians(P['module_roll_deg'])
pivot=(lx+(cx-lx)*math.cos(r)-y*math.sin(r),(cx-lx)*math.sin(r)+y*math.cos(r),z)
angle=90+P['module_roll_deg']

def local(shape):
 return shape.translate(tuple(-v for v in pivot)).rotate((0,0,0),(0,0,1),-angle)

ids=['02_multigrip_carrier','03_MB_keeper_left','20_keeper_L_up_pin','20_keeper_L_up_wedge']
shapes={n:local(source(n)) for n in ids}
crop=cq.Workplane('XY').box(22,26,22,centered=(True,True,False)).translate((0,0,-6)).val()
for n in ids[:2]:shapes[n]=shapes[n].intersect(crop)
common={'parts':ids,'local_transform':{'world_pivot_mm':pivot,'rotate_z_deg':-angle},'crop':{'scope':'carrier and keeper only; surrounding material sectioned for close-up','local_box_mm':[-11,-13,-6,11,13,16]},'pin_insertion_local':[0,-1,0],'wedge_insertion_local':[0,0,-1],'keeper_insertion_local':[0,0,1]}
render('lock_keeper_seated',[shapes[n] for n in ids],[1.5,1.0,1.4],{**common,'translations_mm':{}})
moves={ids[0]:(0,0,0),ids[1]:(0,0,-16),ids[2]:(0,24,0),ids[3]:(0,0,22)}
render('lock_keeper_exploded',[shapes[n].translate(moves[n]) for n in ids],[1.5,1.0,1.4],{**common,'translations_mm':moves,'note':'All translations describe individual part interfaces; not a board insertion path.'})
render('lock_keeper_pin_stage',[shapes[n].translate((0,24,0) if n.endswith('_pin') else (0,0,0)) for n in ids[:3]],[1.5,1.0,1.4],{**common,'parts':ids[:3],'translations_mm':{ids[2]:[0,24,0]}})
render('lock_keeper_wedge_stage',[shapes[n].translate((0,0,22) if n.endswith('_wedge') else (0,0,0)) for n in ids],[1.5,1.0,1.4],{**common,'translations_mm':{ids[3]:[0,0,22]}})
short=shapes[ids[3]].translate((0,9.8,-2.75))
long=source('10_frame_1_wedge').translate((P['main_lock_x'],P['main_lock_y'],-(18.4-10.25))).rotate((0,0,0),(0,0,1),-90)
long=long.translate((0,9.8,3.75))
render('wedge_short_profile',[short],[1,0,0],{'parts':[ids[3]],'nominal_length_mm':9.5,'view':'orthographic profile','note':'Pure rigid transform of actual short wedge STEP.'})
render('wedge_long_profile',[long],[1,0,0],{'parts':['10_frame_1_wedge'],'nominal_length_mm':16.0,'view':'orthographic profile','note':'Pure rigid transform of actual long wedge STEP.'})
render('wedge_short_iso',[short],[1.2,.8,.9],{'parts':[ids[3]],'nominal_length_mm':9.5})
render('wedge_long_iso',[long],[1.2,.8,.9],{'parts':['10_frame_1_wedge'],'nominal_length_mm':16.0})
(OUT/'lock-detail-manifest.json').write_text(json.dumps(manifest,indent=2))
