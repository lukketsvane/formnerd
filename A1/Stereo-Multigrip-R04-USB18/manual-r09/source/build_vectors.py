from pathlib import Path
import sys,json,re,math,hashlib
import numpy as np
import cadquery as cq
from OCP.HLRBRep import HLRBRep_Algo,HLRBRep_HLRToShape
from OCP.HLRAlgo import HLRAlgo_Projector
from OCP.gp import gp_Ax2,gp_Pnt,gp_Dir
from OCP.BRepLib import BRepLib
from cadquery.occ_impl.exporters.svg import makeSVGedge
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(sys.argv[1])
OUT=ROOT/'vectors'
OUT.mkdir(exist_ok=True)
P={p.stem:cq.importers.importStep(str(p)).val() for p in SOURCE.glob('*.step') if re.match(r'^\d\d_',p.name)}
vec=np.array([math.cos(math.radians(18)),math.sin(math.radians(18)),0.])
C=['02_multigrip_carrier'];K=['03_MB_keeper_left','04_MB_keeper_right'];Y=['05_sensor_yoke_left','06_sensor_yoke_right'];F=['01_bank_cradle']
KP=sorted(n for n in P if n.startswith('20_') and n.endswith('_pin'));KW=[n.replace('_pin','_wedge') for n in KP]
YP=sorted(n for n in P if n.startswith('30_') and n.endswith('_pin'));YW=[n.replace('_pin','_wedge') for n in YP]
FP=sorted(n for n in P if n.startswith('10_') and n.endswith('_pin'));FW=[n.replace('_pin','_wedge') for n in FP]
def draw(name,names,moves=None,cam=(1.0,.65,2.5)):
 moves=moves or {};f=np.array(cam);f=f/np.linalg.norm(f);r=np.cross([0,1,0],f);r/=np.linalg.norm(r);u=np.cross(f,r)
 compound=cq.Compound.makeCompound([P[n].translate(tuple(moves.get(n,[0,0,0]))) for n in names])
 alg=HLRBRep_Algo();alg.Add(compound.wrapped);alg.Projector(HLRAlgo_Projector(gp_Ax2(gp_Pnt(),gp_Dir(*f),gp_Dir(*r))));alg.Update();alg.Hide();h=HLRBRep_HLRToShape(alg)
 paths=[];points=[];groups=[]
 for typ,sh in [('edge',h.VCompound()),('edge',h.Rg1LineVCompound()),('outline',h.OutLineVCompound())]:
  if sh.IsNull():continue
  BRepLib.BuildCurves3d_s(sh,1e-6)
  for e in cq.Shape.cast(sh).Edges():
   s=makeSVGedge(e)
   if not s:continue
   a=np.array([float(x) for x in re.findall(r'[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?',s)]).reshape(-1,2)
   points.extend(a.tolist());groups.append({'kind':typ,'xy':a.tolist()})
 points=np.array(points);lo=points.min(0);hi=points.max(0)
 pad=3.;w,hv=hi-lo+2*pad
 for g in groups:
  paths.append('<path d="M'+' L'.join(f'{x:.5f},{-y:.5f}' for x,y in g['xy'])+'" stroke-width="'+('0.25' if g['kind']=='outline' else '0.16')+'"/>')
 svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{lo[0]-pad} {-hi[1]-pad} {w} {hv}"><rect x="{lo[0]-pad}" y="{-hi[1]-pad}" width="{w}" height="{hv}" fill="white"/><g fill="none" stroke="#111" stroke-linecap="round" stroke-linejoin="round">'+''.join(paths)+'</g></svg>'
 (OUT/(name+'.svg')).write_text(svg)
 anchors={}
 for n in names:
  q=np.array(P[n].Center().toTuple());off=np.array(moves.get(n,[0,0,0]));anchors[n]={'center_mm':q.tolist(),'move_mm':off.tolist(),'shown_xy':[(q+off)@r,(q+off)@u],'target_xy':[q@r,q@u]}
 data={'name':name,'parts':names,'camera':cam,'basis':[r.tolist(),u.tolist(),f.tolist()],'bbox':[*lo,*hi],'translations_mm':moves,'anchors':anchors,'groups':groups}
 (OUT/(name+'.json')).write_text(json.dumps(data,separators=(',',':')))
 print(name,len(groups),flush=True)
for n in ['01_bank_cradle','02_multigrip_carrier','03_MB_keeper_left','04_MB_keeper_right','05_sensor_yoke_left','06_sensor_yoke_right',KP[0],KW[0],FW[0]]:draw('part_'+n,[n])
draw('keeper_pins',C+K+KP,{n:(-vec*20).tolist() for n in KP},(.5,.7,2.5))
draw('keeper_wedges',C+K+KP+KW,{n:[0,0,24] for n in KW},(.6,.7,2.5))
draw('yoke_pins',C+K+KP+KW+Y+YP,{n:(-vec*20).tolist() for n in YP},(.5,.7,2.5))
draw('yoke_wedges',C+K+KP+KW+Y+YP+YW,{n:[0,0,24] for n in YW},(.6,.7,2.5))
A=C+K+KP+KW+Y+YP+YW
draw('bank_placement',A+F,{'01_bank_cradle':[0,0,-42]},(1.2,.7,1.8))
draw('frame_pins',A+F+FP,{n:[-23,0,0] for n in FP},(1.0,.6,-2.5))
draw('frame_wedges',A+F+FP+FW,{n:[0,0,24] for n in FW},(1.0,.6,-2.5))
draw('assembled_printed',A+F+FP+FW)
(OUT/'geometry-hashes.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in SOURCE.glob('*.step') if re.match(r'^\d\d_',p.name)},indent=2))
