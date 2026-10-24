import cadquery as cq, json, time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
ps={p.stem:cq.importers.importStep(str(p)).val() for p in sorted((R/'step').glob('*.step')) if not p.name.startswith('T')}
hw={
 'POWERBANK':cq.Workplane('XY').box(94,15,62).edges('|Y').fillet(5.3).translate((-17.95,14,0)).val(),
 'PCB_L':cq.Workplane('XY').box(27,1.6,40.5).translate((0,-8.2,-5.4)).val(),
 'PCB_R':cq.Workplane('XY').box(27,1.6,40.5).translate((43,-8.2,-5.4)).val(),
 'CAM_L':cq.Workplane('XY').box(9.2,5.3,9.2).translate((10,-19.6,7.2)).val(),
 'CAM_R':cq.Workplane('XY').box(9.2,5.3,9.2).translate((53,-19.6,7.2)).val(),
}

def collide(a,b):
 A,B=a.BoundingBox(),b.BoundingBox()
 if A.xmin>=B.xmax or B.xmin>=A.xmax or A.ymin>=B.ymax or B.ymin>=A.ymax or A.zmin>=B.zmax or B.zmin>=A.zmax:return 0
 return max((round(c.Volume(),3) for c in a.intersect(b).Solids()),default=0)

res=[]
for n,a in ps.items():
 for m,b in hw.items():
  v=collide(a,b)
  if v>0.02:res.append({'pair':[n,m],'intersection_mm3':v})
pr=list(ps.items())
for i,(n,a) in enumerate(pr):
 for m,b in pr[i+1:]:
  v=collide(a,b)
  if v>0.02:res.append({'pair':[n,m],'intersection_mm3':v})
print(json.dumps(res,indent=2))
with open(R/'verification'/'digital_collision_report.json','w') as f:json.dump({'unintended_intersections':res,'passed':not res,'scope':'nominal components and printed parts at their assembly coordinates; no physical fit verification'},f,indent=2)