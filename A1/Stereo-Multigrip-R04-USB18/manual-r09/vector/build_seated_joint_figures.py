from pathlib import Path
import sys,json,re,hashlib
import numpy as np
import cadquery as cq
from OCP.HLRBRep import HLRBRep_Algo,HLRBRep_HLRToShape
from OCP.HLRAlgo import HLRAlgo_Projector
from OCP.gp import gp_Ax2,gp_Pnt,gp_Dir
from OCP.BRepLib import BRepLib
from cadquery.occ_impl.exporters.svg import makeSVGedge
from PIL import Image,ImageDraw
SOURCE=Path(sys.argv[1]).resolve();OUT=Path(__file__).resolve().parent
manifest={'geometry_modified':False,'figures':[]}
for name,stage in [('yoke_lock_seated','yoke_wedge_stage'),('frame_lock_seated','lock_frame_wedge_stage')]:
 ref=json.loads((OUT/(stage+'.json')).read_text());basis=np.array(ref['basis']);ids=ref['parts'];pivot=np.array(ref['local_transform']['world_pivot_mm']);angle=ref['local_transform']['rotate_z_deg'];roi=ref['crop']['local_box_mm'];lo=np.array(roi[:3]);hi=np.array(roi[3:]);size=hi-lo
 crop=cq.Workplane('XY').box(*size,centered=(False,False,False)).translate(tuple(lo)).val()
 shapes={};hashes={}
 for i,n in enumerate(ids):
  p=SOURCE/'STEP'/(n+'.step');hashes[n]=hashlib.sha256(p.read_bytes()).hexdigest();shape=cq.importers.importStep(str(p)).val().translate(tuple(-pivot)).rotate((0,0,0),(0,0,1),angle)
  shapes[n]=shape.intersect(crop) if i<2 else shape
 centers={n:list(shapes[n].Center().toTuple()) for n in ids[2:]}
 max_center_error=max(float(np.linalg.norm(np.array(a)-ref['assembled_centers_local_mm'][n])) for n,a in centers.items());assert max_center_error<1e-7
 alg=HLRBRep_Algo();alg.Add(cq.Compound.makeCompound(list(shapes.values())).wrapped);alg.Projector(HLRAlgo_Projector(gp_Ax2(gp_Pnt(),gp_Dir(*basis[2]),gp_Dir(*basis[0]))));alg.Update();alg.Hide();hidden=HLRBRep_HLRToShape(alg);groups=[]
 for kind,shape in [('edge',hidden.VCompound()),('edge',hidden.Rg1LineVCompound()),('outline',hidden.OutLineVCompound())]:
  if shape.IsNull():continue
  BRepLib.BuildCurves3d_s(shape,1e-6)
  for edge in cq.Shape.cast(shape).Edges():
   data=makeSVGedge(edge)
   if data:
    xy=np.array([float(v) for v in re.findall(r'[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?',data)]).reshape(-1,2);groups.append({'kind':kind,'xy':xy.tolist()})
 points=np.concatenate([np.array(g['xy']) for g in groups]);p0=points.min(0);p1=points.max(0);x0,y0=p0;x1,y1=p1;pad=2
 anchors={n:{'assembled_center_mm':q,'shown_center_mm':q,'target_xy':(basis@np.array(q))[:2].tolist(),'shown_xy':(basis@np.array(q))[:2].tolist(),'move_mm':[0,0,0]} for n,q in centers.items()}
 meta={'groups':groups,'bbox':[x0,y0,x1,y1],'basis':basis.tolist(),'parts':ids,'local_transform':ref['local_transform'],'crop':ref['crop'],'pin_insertion_local':ref['pin_insertion_local'],'wedge_insertion_local':ref['wedge_insertion_local'],'translations_mm':{},'assembled_centers_local_mm':centers,'shown_centers_local_mm':centers,'anchors':anchors,'state':'Original source assembly pose: pin and wedge both seated, no illustration translation.','source_stage':stage,'source_stage_sha256':hashlib.sha256((OUT/(stage+'.json')).read_bytes()).hexdigest(),'source_STEP_sha256':hashes,'basis_matches_source_stage_exactly':True,'max_fastener_center_error_vs_source_stage_mm':max_center_error}
 (OUT/(name+'.json')).write_text(json.dumps(meta,separators=(',',':')))
 paths=[]
 for g in groups:
  coords='M'+' L'.join(f'{x:.5f},{-y:.5f}' for x,y in g['xy']);paths.append(f'<path d="{coords}" stroke-width="{.20 if g["kind"]=="outline" else .12}"/>')
 svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0-pad} {-y1-pad} {x1-x0+2*pad} {y1-y0+2*pad}"><rect x="{x0-pad}" y="{-y1-pad}" width="{x1-x0+2*pad}" height="{y1-y0+2*pad}" fill="white"/><g fill="none" stroke="black" stroke-linejoin="round" stroke-linecap="round">'+''.join(paths)+'</g></svg>'
 (OUT/(name+'.svg')).write_text(svg)
 im=Image.new('RGB',(1200,1000),'white');draw=ImageDraw.Draw(im);sc=min(1080/(x1-x0),880/(y1-y0));ox=600-(x0+x1)/2*sc;oy=500+(y0+y1)/2*sc
 for g in groups:draw.line([(ox+x*sc,oy-y*sc) for x,y in g['xy']],fill='black',width=3 if g['kind']=='outline' else 2)
 im.save(OUT/(name+'.png'))
 for n,h in hashes.items():assert hashlib.sha256((SOURCE/'STEP'/(n+'.step')).read_bytes()).hexdigest()==h
 manifest['figures'].append({'name':name,'source_stage':stage,'basis_matches_source_stage_exactly':True,'max_fastener_center_error_mm':max_center_error,'line_groups':len(groups),'source_STEP_sha256':hashes,'local_transform':ref['local_transform'],'crop':ref['crop'],'basis':basis.tolist(),'translations_mm':{}})
 print(name,len(groups),max_center_error,flush=True)
(OUT/'seated-joint-manifest.json').write_text(json.dumps(manifest,indent=2))
