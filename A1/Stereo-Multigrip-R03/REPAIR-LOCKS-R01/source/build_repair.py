"""Retrofit printed lock pins for Stereo-Multigrip R03.

Keeps the two already printed large parts unchanged. Builds three clearance
variants, original-profile retaining wedges and unsliced 3MF fit-test plates.
"""
from pathlib import Path
import json, sys, hashlib
import cadquery as cq

REPAIR=Path(__file__).resolve().parents[1]
ROOT=REPAIR.parent
sys.path.insert(0,str(ROOT/"source"))
from clean_stl import clean_stl
from make_print_plate import make
STL=REPAIR/"STL"; STEP=REPAIR/"STEP"; PLATES=REPAIR/"3MF"
for p in (STL,STEP,PLATES):p.mkdir(parents=True,exist_ok=True)
SLOT_W,SLOT_H=6.5,4.5
# Slots in the original two large parts are unchanged and have these bounds.
SIZES={"A_EASY":(6.00,4.30,1),"B_SNUG":(6.16,4.41,2),
       "C_FIRM":(6.28,4.47,3)}

def box(w,h,d,x=0,y=0,z=0,r=0):
 q=cq.Workplane("XY").box(w,h,d,centered=(True,True,False)).translate((x,y,z))
 if r:q=q.edges("|Z").fillet(min(r,w/2-.01,h/2-.01))
 return q.val()

def fuse(*parts):
 q=parts[0]
 for p in parts[1:]:q=q.fuse(p)
 return q.clean()

def make_pin(w,h,marks):
 z=6.25-h/2
 q=fuse(box(w,21.3,h,0,-2.35,z,.40),box(10,3,h,0,9.8,z,.7))
 q=q.cut(box(3.4,3.6,6,0,-9.8,3.25,.2))
 xs={1:[0],2:[-1.6,1.6],3:[-2.4,0,2.4]}[marks]
 for x in xs:q=q.cut(box(.8,.95,.65,x,10.0,z+h-.65,.12))
 return q.clean()

def make_wedge():
 taper=(cq.Workplane("XY").workplane(offset=-3.75).center(0,-9.8)
        .rect(3,2.4).workplane(offset=12.2).rect(3,3.6).loft(combine=True).val())
 q=fuse(taper,box(3,3.6,1.8,0,-9.8,8.45),
        box(3,7,2,0,-9.8,10.25,.6))
 return q.rotate((0,0,0),(0,1,0),90).clean()

def to_bed(q):
 b=q.BoundingBox()
 return q.translate((-(b.xmin+b.xmax)/2,-(b.ymin+b.ymax)/2,-b.zmin))

def export(name,q):
 assert q.isValid() and len(q.Solids())==1 and q.Volume()>0,name
 q=to_bed(q)
 stl=STL/(name+".stl")
 cq.exporters.export(q,str(stl),tolerance=.035,angularTolerance=.12)
 clean_stl(stl)
 cq.exporters.export(q,str(STEP/(name+".step")))
 return stl

paths={}
for name,(w,h,n) in SIZES.items():
 assert w<SLOT_W and h<SLOT_H
 paths[name]=export("R03_FRAME_PIN_"+name,make_pin(w,h,n))
paths["WEDGE"]=export("R03_CROSS_WEDGE_ORIGINAL",make_wedge())

make([paths[n] for n in ("A_EASY","B_SNUG","C_FIRM","WEDGE")],
 PLATES/"R03-00-FIT-TEST-TRY-FIRST.3mf","R03 physical lock fit - three head-marked variants")
for name in SIZES:
 make([paths[name]]*4+[paths["WEDGE"]]*4,
  PLATES/f"R03-01-FOUR-FRAME-LOCKS-{name}.3mf",
  f"R03 four FRAME locks - {name} (eight small parts)")
small=[ROOT/"STL"/("PRINT_"+n+".stl") for n in
 ("03_MB_keeper_left","04_MB_keeper_right",
  "05_sensor_yoke_left","06_sensor_yoke_right")]
assert all(p.is_file() for p in small),small
make(small+[paths["A_EASY"]]*8+[paths["WEDGE"]]*8,
 PLATES/"R03-02-REMAINING-SMALL-PARTS.3mf",
 "R03 four smaller keepers and yokes plus 8 pins and 8 wedges")
files=[]
for p in list(STL.glob("*.stl"))+list(STEP.glob("*.step"))+list(PLATES.glob("*")):
 if p.is_file():
  files.append({"path":str(p.relative_to(REPAIR)).replace("\\","/"),
                "bytes":p.stat().st_size,
                "sha256":hashlib.sha256(p.read_bytes()).hexdigest()})
report={"purpose":"Retrofit existing R03 cradle and multigrip carrier",
 "status":"Nominal CAD preflight only; physical fit not yet confirmed",
 "nominal_slot_mm":[SLOT_W,SLOT_H],
 "pin_sizes_mm":{n:{"width":w,"height":h,"identifying_notches":m,
   "slot_minus_width":round(SLOT_W-w,3),"slot_minus_height":round(SLOT_H-h,3)}
   for n,(w,h,m) in SIZES.items()},
 "retaining_wedge":"R03 original taper and exterior dimensions",
 "files":sorted(files,key=lambda x:x["path"])}
(REPAIR/"QA.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print("BUILT",len(files),"files",sum(v["bytes"] for v in files),"bytes")
print(json.dumps(report["pin_sizes_mm"],indent=2))
