from pathlib import Path
import argparse,hashlib,json,math,re
import numpy as np
import cadquery as cq
from OCP.HLRBRep import HLRBRep_Algo,HLRBRep_HLRToShape
from OCP.HLRAlgo import HLRAlgo_Projector
from OCP.gp import gp_Ax2,gp_Pnt,gp_Dir
from OCP.BRepLib import BRepLib
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from cadquery.occ_impl.exporters.svg import makeSVGedge
from PIL import Image,ImageDraw

ap=argparse.ArgumentParser()
ap.add_argument('--step',type=Path,default=Path('formnerd/A1/Stereo-Multigrip-R04-USB18/STEP/02_multigrip_carrier.step'))
ap.add_argument('--out',type=Path,default=Path(__file__).resolve().parent)
ap.add_argument('--qa',action='store_true')
a=ap.parse_args();a.out.mkdir(exist_ok=True,parents=True)
s=cq.importers.importStep(str(a.step)).val();source_hash=hashlib.sha256(a.step.read_bytes()).hexdigest()
angle=math.radians(18);rot=np.array([[math.cos(angle),-math.sin(angle),0],[math.sin(angle),math.cos(angle),0],[0,0,1]])
pivot=np.array([-38.163,0,0])
pod=lambda v:pivot+rot@(np.array(v)-pivot)
raw={'guide_stop':pod([-6.643,13.6,35.1]),'pin_aperture':pod([-18.493,28,37.5])}
points={};distances={}
for n,p in raw.items():
 d=BRepExtrema_DistShapeShape(s.wrapped,cq.Vertex.makeVertex(*p).wrapped);d.Perform();q=d.PointOnShape1(1)
 points[n]=np.array([q.X(),q.Y(),q.Z()]);distances[n]=d.Value()

def project(cam):
 f=np.array(cam,dtype=float);f/=np.linalg.norm(f);r=np.cross([0,1,0],f);r/=np.linalg.norm(r);u=np.cross(f,r)
 alg=HLRBRep_Algo();alg.Add(s.wrapped);alg.Projector(HLRAlgo_Projector(gp_Ax2(gp_Pnt(),gp_Dir(*f),gp_Dir(*r))));alg.Update();alg.Hide();h=HLRBRep_HLRToShape(alg)
 groups=[]
 for typ,sh in [('edge',h.VCompound()),('edge',h.Rg1LineVCompound()),('outline',h.OutLineVCompound())]:
  if sh.IsNull():continue
  BRepLib.BuildCurves3d_s(sh,1e-6)
  for e in cq.Shape.cast(sh).Edges():
   path=makeSVGedge(e)
   if path:
    xy=np.array([float(x) for x in re.findall(r'[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?',path)]).reshape(-1,2)
    if len(xy)>1:groups.append({'kind':typ,'xy':xy.tolist()})
 return groups,np.array([r,u,f])

def clip_segment(p,q,box):
 x0,y0,x1,y1=box;delta=q-p;t0,t1=0.,1.
 for den,num in [(-delta[0],p[0]-x0),(delta[0],x1-p[0]),(-delta[1],p[1]-y0),(delta[1],y1-p[1])]:
  if abs(den)<1e-12:
   if num<0:return None
  else:
   t=num/den
   if den<0:t0=max(t0,t)
   else:t1=min(t1,t)
   if t0>t1:return None
 return [list(p+t0*delta),list(p+t1*delta)]

def clipped(groups,box):
 result=[]
 for g in groups:
  xy=np.array(g['xy'])
  for p,q in zip(xy[:-1],xy[1:]):
   z=clip_segment(p,q,box)
   if z and np.linalg.norm(np.array(z[1])-z[0])>1e-8:result.append({'kind':g['kind'],'xy':z})
 return result

def save(name,cam,feature=None,half=None):
 groups,basis=project(cam);allxy=np.array([p for g in groups for p in g['xy']]);lo=allxy.min(0);hi=allxy.max(0)
 if feature:
  xy=(basis@points[feature])[:2];lo=xy-np.array(half);hi=xy+np.array(half);groups=clipped(groups,[*lo,*hi])
 anchors={n:{'point_mm':p.tolist(),'center_mm':p.tolist(),'shown_xy':(basis@p)[:2].tolist(),'surface_distance_mm':s.distance(cq.Vertex.makeVertex(*p))} for n,p in points.items()}
 data={'name':name,'parts':['02_multigrip_carrier'],'camera':cam,'basis':basis.tolist(),'bbox':[*lo.tolist(),*hi.tolist()],'translations_mm':{},'anchors':anchors,'groups':groups,'source_step':a.step.name,'source_sha256':source_hash,'geometry_changes':'none; original solid projected with visible-line HLR only','crop_feature':feature,'crop_note':'Projection crop only; no section cuts or invented support material.' if feature else None,'permanent_features':{'guide_stop':'Permanent camera corner stop and adjoining thin guide rim. Preserve.','pin_aperture':'Permanent printed lock housing, including the through aperture. Preserve.'}}
 (a.out/(name+'.json')).write_text(json.dumps(data,separators=(',',':')))
 pad=1.2 if feature else 2.;w,h=hi-lo+2*pad
 paths=['<path d="M'+' L'.join(f'{x:.6f},{-y:.6f}' for x,y in g['xy'])+'" stroke-width="'+('0.25' if g['kind']=='outline' else '0.16')+'"/>' for g in groups]
 svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{lo[0]-pad} {-hi[1]-pad} {w} {h}"><rect x="{lo[0]-pad}" y="{-hi[1]-pad}" width="{w}" height="{h}" fill="white"/><g fill="none" stroke="black" stroke-linecap="round" stroke-linejoin="round">'+''.join(paths)+'</g></svg>'
 (a.out/(name+'.svg')).write_text(svg)
 scale=min(1600/w,1200/h);iw,ih=round(w*scale),round(h*scale);im=Image.new('RGB',(iw,ih),'white');draw=ImageDraw.Draw(im)
 toxy=lambda xy:((xy[0]-lo[0]+pad)*scale,(hi[1]+pad-xy[1])*scale)
 for g in groups:draw.line([toxy(p) for p in g['xy']],fill='black',width=max(1,round((.12 if g['kind']=='outline' else .09)*scale)))
 im.save(a.out/(name+'.png'))
 qa=im.copy();d=ImageDraw.Draw(qa)
 for n,v in anchors.items():
  xy=v['shown_xy']
  if lo[0]<=xy[0]<=hi[0] and lo[1]<=xy[1]<=hi[1]:
   x,y=toxy(xy);d.ellipse((x-8,y-8,x+8,y+8),outline='red',width=2);d.text((x+10,y+3),n,fill='red')
 if a.qa:qa.save(a.out/(name+'-qa.png'))
 return {'name':name,'group_count':len(groups),'source_sha256':source_hash,'anchors':anchors,'bbox':data['bbox'],'camera':cam,'feature':feature}

results=[save('carrier_preserve_front',[1,.65,2.5]),save('carrier_preserve_rear',[-1,-.65,-2.5]),save('carrier_preserve_guide',[1,.65,2.5],'guide_stop',[9,8]),save('carrier_preserve_fork',[2,.7,1.3],'pin_aperture',[9,9])]
assert all(x['group_count']>10 for x in results)
assert all(v['surface_distance_mm']<1e-6 for x in results for v in x['anchors'].values())
(a.out/'carrier-preservation-manifest.json').write_text(json.dumps({'source_sha256':source_hash,'source_volume_mm3':s.Volume(),'source_solid_count':len(s.Solids()),'source_bounds_mm':[getattr(s.BoundingBox(),k) for k in ['xmin','ymin','zmin','xmax','ymax','zmax']],'raw_anchor_adjustment_mm':distances,'figures':results,'geometry_unchanged':True},indent=2))
print(json.dumps({'figures':len(results),'out':str(a.out),'source_sha256':source_hash}))
