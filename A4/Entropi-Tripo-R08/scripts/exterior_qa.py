import bpy, json, runpy
from pathlib import Path
root=Path(r"C:\Users\Iver\Documents\github\formnerd\A4\Entropi-Tripo-R08")
ns=runpy.run_path(str(root/"scripts/collision_qa.py"))
inter=ns["intersection"]
names=ns["names"]
result=[]
for i,a in enumerate(names):
 for b in names[i+1:]:
  v,n=inter(bpy.data.objects[a],bpy.data.objects[b])
  if v>.01 or n:
   result.append({"first":a,"second":b,"volume_mm3":v,"nonmanifold":n})
print("EXTERIOR_PAIRS",json.dumps(result))
(root/"qa/exterior_intersections.json").write_text(json.dumps(result,indent=2))