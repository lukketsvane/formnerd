import json
import hashlib
from pathlib import Path
import numpy as np
import trimesh
import cadquery as cq

HERE=Path(__file__).resolve().parent
R09=HERE.parent
P=HERE/"print"
P.mkdir(exist_ok=True)
report={"revision":"R10","printer":"Bambu Lab P1S","plate_mm":[256,256],"source":"Tripo-derived geometry and analytic CadQuery parts","plates":[]}

def place(scene, occupied, label, filepath, cx, cy, rotate=None):
    m=trimesh.load(filepath,force="mesh")
    if not m.is_watertight or m.volume<=0:
        raise RuntimeError(label+" open or no solid")
    if rotate is not None:
        m.apply_transform(trimesh.transformations.rotation_matrix(np.deg2rad(rotate[0]),rotate[1]))
    center=m.bounds.mean(axis=0)
    m.apply_translation([cx-center[0],cy-center[1],-m.bounds[0,2]])
    lo,hi=m.bounds
    if lo[0]<3 or lo[1]<3 or hi[0]>253 or hi[1]>253:
        raise RuntimeError(label+" outside P1S bed: "+str(m.bounds))
    for prev,p,q in occupied:
        if min(hi[0],q[0])>max(lo[0],p[0])+0.4 and min(hi[1],q[1])>max(lo[1],p[1])+0.4:
            raise RuntimeError(label+" overlaps "+prev)
    occupied.append((label,lo,hi))
    m.visual.face_colors=[127,128,130,255]
    scene.add_geometry(m,geom_name=label,node_name=label)
    return {"id":label,"file":str(Path(filepath).relative_to(HERE)) if HERE in Path(filepath).parents else str(filepath),"bounds_mm":np.round(m.bounds,2).tolist(),"watertight":True,"volume_mm3":round(m.volume,2)}

def make_plate(name,placements):
    scene=trimesh.Scene()
    occupied=[]
    items=[place(scene,occupied,*args) for args in placements]
    out=P/(name+".3mf")
    scene.export(out)
    reread=trimesh.load(out,force="scene")
    if len(reread.geometry)!=len(items):
        raise RuntimeError(name+" 3mf object count mismatch")
    plate={"file":out.name,"format":"3mf geometry only, NOT gcode","number_of_objects":len(items),"objects":items,"sha256":hashlib.sha256(out.read_bytes()).hexdigest(),"bytes":out.stat().st_size}
    report["plates"].append(plate)
    print("PLATE",name,len(items),out.stat().st_size,flush=True)

src=HERE/"parts"
r09=R09/"harness"/"stl"
make_plate("01_R10_Tripo_shells_P1S",[
    ("P01_R10_Tripo_front",src/"P01_R10_Tripo_front_shell_SMOOTH_CLEAR.stl",67,128,(180,(1,0,0))),
    ("P02_R10_Tripo_rear",src/"P02_R10_Tripo_rear_shell_SMOOTH_CLEAR.stl",188,128,None),
])
make_plate("02_R10_mechanics_P1S",[
    ("H11_R09_dual_MB_harness",r09/"H11_dual_ESP32CAM_MB_harness.stl",63,186,None),
    ("H12_R10_centered_battery_cage",src/"H12_R10_centered_Linocell_U_cage.stl",185,186,None),
    ("P03_L_lens_bezel",src/"P03_R10_lens_bezel_L.stl",28,61,None),
    ("P03_R_lens_bezel",src/"P03_R10_lens_bezel_R.stl",52,61,None),
    ("P04_trigger",src/"P04_R10_trigger_cap.stl",77,61,(90,(1,0,0))),
    ("P05_front_spacer_1",src/"P05F1_M3_front_spacer.stl",103,51,None),
    ("P05_front_spacer_2",src/"P05F2_M3_front_spacer.stl",125,51,None),
    ("P05_front_spacer_3",src/"P05F3_M3_front_spacer.stl",147,51,None),
    ("P05_front_spacer_4",src/"P05F4_M3_front_spacer.stl",169,51,None),
    ("P05_rear_spacer_1",src/"P05R1_M3_rear_spacer.stl",103,82,None),
    ("P05_rear_spacer_2",src/"P05R2_M3_rear_spacer.stl",125,82,None),
    ("P05_rear_spacer_3",src/"P05R3_M3_rear_spacer.stl",147,82,None),
    ("P05_rear_spacer_4",src/"P05R4_M3_rear_spacer.stl",169,82,None),
])
make_plate("00_R10_fit_tests_P1S",[
    ("T11_ESP32_MB_fit",r09/"T11_MB_edge_fit_coupon.stl",57,105,None),
    ("T12_Linocell_corner_fit",r09/"T12_Linocell_corner_fit_coupon.stl",126,105,None),
    ("T13_USB_wall_test",src/"T13_USB_wall_coupon.stl",198,105,(90,(0,1,0)))
])

scene=trimesh.Scene()
objects=[
 ("front_shell",src/"P01_R10_Tripo_front_shell_SMOOTH_CLEAR.stl"),
 ("rear_shell",src/"P02_R10_Tripo_rear_shell_SMOOTH_CLEAR.stl"),
 ("camera_carrier",r09/"H11_dual_ESP32CAM_MB_harness.stl"),
 ("battery_cradle",src/"H12_R10_centered_Linocell_U_cage.stl"),
 ("battery_nominal",r09/"HW01_Linocell_5000mAh.stl"),
 ("camera_L_nominal",r09/"HW02_L_ESP32CAM_MB_stack.stl"),
 ("camera_R_nominal",r09/"HW02_R_ESP32CAM_MB_stack.stl"),
 ("lens_L",src/"P03_R10_lens_bezel_L.stl"),
 ("lens_R",src/"P03_R10_lens_bezel_R.stl"),
 ("trigger",src/"P04_R10_trigger_cap.stl")
]
for name,p in objects:
    m=trimesh.load(p,force="mesh")
    if name=="battery_nominal":
        m.apply_translation([-20.5,0,0])
    scene.add_geometry(m,geom_name=name,node_name=name)
full=HERE/"R10_hybrid_assembly.glb"
scene.export(full)
if len(trimesh.load(full,force="scene").geometry)!=len(objects):
    raise RuntimeError("GLB component count mismatch")
analytic=cq.Assembly(name="ENTROPI_R10_ANALYTIC_INSERTS")
for name,p in objects[2:4]+objects[7:]:
    st=p.with_suffix(".step")
    if not st.exists():
        if name=="camera_carrier":
            st=R09/"harness"/"step"/"H11_dual_ESP32CAM_MB_harness.step"
        else:
            raise RuntimeError("No STEP for "+name)
    analytic.add(cq.importers.importStep(str(st)).val(),name=name)
for i in range(1,5):
    for prefix in ("P05F","P05R"):
        p=src/(prefix+str(i)+"_M3_"+("front" if prefix=="P05F" else "rear")+"_spacer.step")
        analytic.add(cq.importers.importStep(str(p)).val(),name=p.stem)
analytic.save(str(HERE/"R10_analytic_inserts.step"))
report["assembly"]={"hybrid_mesh_glb":full.name,"analytic_step":"R10_analytic_inserts.step","mesh_shell_is_nurbs":False,"nominal_hardware":"in GLB only"}
(HERE/"qa"/"print_plates.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
print("ASSEMBLY_READY",full.stat().st_size,(HERE/"R10_analytic_inserts.step").stat().st_size,flush=True)
