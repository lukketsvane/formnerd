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
P=json.loads((SOURCE/'source/parameters.json').read_text());pivot=np.array([-P['main_lock_x'],P['main_lock_y'],P['rear_lip']+.2+P['bank_d']+P['bank_front_gap']-10.25]);angle=-90
ids=['01_bank_cradle','02_multigrip_carrier','10_frame_2_pin','10_frame_2_wedge'];hashes={};original={}
for n in ids:
 p=SOURCE/'STEP'/(n+'.step');hashes[n]=hashlib.sha256(p.read_bytes()).hexdigest();original[n]=cq.importers.importStep(str(p)).val().translate(tuple(-pivot)).rotate((0,0,0),(0,0,1),angle)
manifest={'geometry_modified':False,'joint':'10_frame_2','source_STEP_sha256':hashes,'figures':[]}
for name,reference,selected,moves in [('frame2_pin_stage','frame_pin_stage',ids[:3],{ids[2]:[0,24,0]}),('frame2_wedge_stage','lock_frame_wedge_stage',ids,{ids[3]:[0,0,22]}),('frame2_lock_seated','frame_lock_seated',ids,{})]:
 ref=json.loads((OUT/(reference+'.json')).read_text());basis=np.array(ref['basis']);alternate=len(sys.argv)>2 and sys.argv[2]=='--alternate'
 if alternate:
  name+='_clear';f=np.array([1.5,1.0,1.1] if name.startswith('frame2_pin') else [3.0,-.6,1.4]);f=f/np.linalg.norm(f);right=np.cross([0,0,1],f);right/=np.linalg.norm(right);up=np.cross(f,right);basis=np.array([right,up,f])
 roi=ref['crop']['local_box_mm'];lo=np.array(roi[:3]);hi=np.array(roi[3:]);size=hi-lo;crop=cq.Workplane('XY').box(*size,centered=(False,False,False)).translate(tuple(lo)).val();local={n:(original[n].intersect(crop) if n in ids[:2] else original[n]) for n in selected}
 section_override={}
 if alternate:
  carrier_roi=[-11,-7,-6,11,7,16];clo=np.array(carrier_roi[:3]);chi=np.array(carrier_roi[3:]);carrier_crop=cq.Workplane('XY').box(*(chi-clo),centered=(False,False,False)).translate(tuple(clo)).val();local['02_multigrip_carrier']=original['02_multigrip_carrier'].intersect(carrier_crop);section_override={'02_multigrip_carrier':{'local_box_mm':carrier_roi,'purpose':'Display section removes only surrounding carrier perimeter outside Y±7mm; actual tongue engagement region remains fully present. Original STEP is unchanged.'}}
 assembled={n:list(local[n].Center().toTuple()) for n in selected if n.endswith(('_pin','_wedge'))};shown={n:(np.array(q)+np.array(moves.get(n,[0,0,0]))).tolist() for n,q in assembled.items()}
 center_error=max(float(np.linalg.norm(np.array(q)-ref['assembled_centers_local_mm'][n.replace('frame_2','frame_1')])) for n,q in assembled.items());assert center_error<1e-7
 alg=HLRBRep_Algo();alg.Add(cq.Compound.makeCompound([local[n].translate(tuple(moves.get(n,[0,0,0]))) for n in selected]).wrapped);alg.Projector(HLRAlgo_Projector(gp_Ax2(gp_Pnt(),gp_Dir(*basis[2]),gp_Dir(*basis[0]))));alg.Update();alg.Hide();hidden=HLRBRep_HLRToShape(alg);groups=[]
 for kind,shape in [('edge',hidden.VCompound()),('edge',hidden.Rg1LineVCompound()),('outline',hidden.OutLineVCompound())]:
  if shape.IsNull():continue
  BRepLib.BuildCurves3d_s(shape,1e-6)
  for edge in cq.Shape.cast(shape).Edges():
   data=makeSVGedge(edge)
   if data:
    xy=np.array([float(v) for v in re.findall(r'[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?',data)]).reshape(-1,2);groups.append({'kind':kind,'xy':xy.tolist()})
 points=np.concatenate([np.array(g['xy']) for g in groups]);p0=points.min(0);p1=points.max(0);x0,y0=p0;x1,y1=p1;pad=2
 anchors={n:{'assembled_center_mm':q,'shown_center_mm':shown[n],'target_xy':(basis@np.array(q))[:2].tolist(),'shown_xy':(basis@np.array(shown[n]))[:2].tolist(),'move_mm':moves.get(n,[0,0,0])} for n,q in assembled.items()}
 meta={'groups':groups,'bbox':[x0,y0,x1,y1],'basis':basis.tolist(),'parts':selected,'local_transform':{'world_pivot_mm':pivot.tolist(),'rotate_z_deg':angle},'crop':ref['crop'],'pin_insertion_local':[0,-1,0],'wedge_insertion_local':[0,0,-1],'translations_mm':moves,'assembled_centers_local_mm':assembled,'shown_centers_local_mm':shown,'anchors':anchors,'source_stage':reference,'source_stage_sha256':hashlib.sha256((OUT/(reference+'.json')).read_bytes()).hexdigest(),'source_STEP_sha256':{n:hashes[n] for n in selected},'basis_matches_reference_exactly':not alternate,'max_fastener_center_error_vs_frame1_local_coordinates_mm':center_error,'display_section_overrides':section_override,'arrow_guides_local':{'pin':{'start':[0,22,6.25],'end':[0,8,6.25]},'wedge':{'start':[0,-9.8,17],'end':[0,-9.8,8.45]}},'source_geometry_note':'Actual frame2 surrounding cradle/carrier geometry read from original assembly-position STEP, moved only to local display coordinates. Section crop applies only to surrounding cradle/carrier.'}
 (OUT/(name+'.json')).write_text(json.dumps(meta,separators=(',',':')))
 paths=[]
 for g in groups:
  coords='M'+' L'.join(f'{x:.5f},{-y:.5f}' for x,y in g['xy']);paths.append(f'<path d="{coords}" stroke-width="{.20 if g["kind"]=="outline" else .12}"/>')
 svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0-pad} {-y1-pad} {x1-x0+2*pad} {y1-y0+2*pad}"><rect x="{x0-pad}" y="{-y1-pad}" width="{x1-x0+2*pad}" height="{y1-y0+2*pad}" fill="white"/><g fill="none" stroke="black" stroke-linejoin="round" stroke-linecap="round">'+''.join(paths)+'</g></svg>'
 (OUT/(name+'.svg')).write_text(svg)
 im=Image.new('RGB',(1200,1000),'white');draw=ImageDraw.Draw(im);sc=min(1080/(x1-x0),880/(y1-y0));ox=600-(x0+x1)/2*sc;oy=500+(y0+y1)/2*sc
 for g in groups:draw.line([(ox+x*sc,oy-y*sc) for x,y in g['xy']],fill='black',width=3 if g['kind']=='outline' else 2)
 im.save(OUT/(name+'.png'))
 manifest['figures'].append({k:meta[k] for k in ['parts','basis','local_transform','crop','translations_mm','basis_matches_reference_exactly','max_fastener_center_error_vs_frame1_local_coordinates_mm','source_geometry_note','display_section_overrides','arrow_guides_local']}|{'name':name,'line_groups':len(groups)})
 print(name,len(groups),center_error,flush=True)
for n,h in hashes.items():assert hashlib.sha256((SOURCE/'STEP'/(n+'.step')).read_bytes()).hexdigest()==h
(OUT/('frame2-joint-clear-manifest.json' if len(sys.argv)>2 else 'frame2-joint-manifest.json')).write_text(json.dumps(manifest,indent=2))
