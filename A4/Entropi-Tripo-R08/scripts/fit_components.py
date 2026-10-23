import bpy
import bmesh
import json
import math
from mathutils import Matrix, Vector
from pathlib import Path

root=Path(r"C:\Users\Iver\Documents\github\formnerd\A4\Entropi-Tripo-R08")
(root/"print_candidates").mkdir(exist_ok=True)
(root/"qa").mkdir(exist_ok=True)
(root/"render").mkdir(exist_ok=True)
S=118.0
Z0=0.3716315031051636
source=[o for o in bpy.data.objects if o.type=="MESH"]
for o in source:
    mat=o.matrix_world.copy()
    for v in o.data.vertices:
        p=mat@v.co
        v.co=(p.y*S,-p.x*S,(p.z+Z0)*S)
    o.matrix_world=Matrix.Identity(4)
    o.name="SOURCE_"+o.name if o.name=="tripo_part_0" else o.name
    o.color=(0.74,0.74,0.74,1)
src0=bpy.data.objects["SOURCE_tripo_part_0"]
src0.hide_render=True
src0.hide_set(True)
q=bpy.data.objects["Tripo_Part0_Quad_SubD"]
q.name="A0_Tripo_quads_organic_front"
q.color=(0.83,0.83,0.83,1)
for n in ("tripo_part_1","tripo_part_2"):
    bpy.data.objects[n].color=(0.24,0.24,0.24,1)
for n in ("tripo_part_5","tripo_part_7","tripo_part_9","tripo_part_10"):
    bpy.data.objects[n].color=(0.14,0.14,0.14,1)

def selected(o):
    bpy.ops.object.select_all(action="DESELECT")
    o.hide_set(False)
    o.select_set(True)
    bpy.context.view_layer.objects.active=o

def apply(o,m):
    selected(o)
    bpy.ops.object.modifier_apply(modifier=m.name)

def cube(name,center,dims,bevel=0,color=(.44,.46,.49,1)):
    bpy.ops.mesh.primitive_cube_add(size=1,location=center)
    o=bpy.context.object
    o.name=name
    o.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel>0:
        m=o.modifiers.new("Rounded corners","BEVEL")
        m.width=bevel
        m.segments=4
        apply(o,m)
        m=o.modifiers.new("Weighted normals","WEIGHTED_NORMAL")
        apply(o,m)
    o.color=color
    return o

def boolean(target,cutter,op="DIFFERENCE"):
    m=target.modifiers.new("Precision "+op,"BOOLEAN")
    m.operation=op
    m.solver="EXACT"
    m.object=cutter
    apply(target,m)

def remove(o):
    bpy.data.objects.remove(o,do_unlink=True)

def mesh_stats(o):
    bm=bmesh.new()
    bm.from_mesh(o.data)
    bm.normal_update()
    n=sum(not e.is_manifold for e in bm.edges)
    v=abs(bm.calc_volume(signed=True))
    bm.free()
    return {"name":o.name,"verts":len(o.data.vertices),"faces":len(o.data.polygons),"nonmanifold_edges":n,"volume_mm3":round(v,1)}

battery=cube("REF_Linocell_94x62x15",(0,15.5,37.7),(94,15,62),2.2,(.65,.65,.65,1))
battery.hide_render=False
pcb=[]
for i,x in enumerate((-29.0,29.0)):
    o=cube("REF_ESP32_CAM_"+str(i+1),(x,-3.0,29.0),(27,10.4,40.5),0,(.30,.34,.38,1))
    pcb.append(o)
    cam=cube("REF_LENS_"+str(i+1),(x,-9.4,37.1),(8.0,2.5,8.0),1.0,(.09,.09,.09,1))

tray=cube("P1_BATTERY_RING",(0,14.7,37.7),(99.2,21.5,67.8),2.8,(.27,.28,.29,1))
inside=cube("_battery_hollow",(0,14.7,37.7),(95.0,30.0,63.2),2.4)
boolean(tray,inside)
remove(inside)
for ix in (-1,1):
    for iz in (-1,1):
        stop=cube("_stop",(ix*43.5,24.4,37.7+iz*27.5),(7.5,2.1,7.5),0.7)
        boolean(tray,stop,"UNION")
        remove(stop)

cradles=[]
for i,x in enumerate((-29.0,29.0)):
    base=cube("P%d_ESP32_BRACKET"%(i+2),(x,5.4,29.0),(30.2,2.4,44.0),1.4,(.35,.36,.38,1))
    for z in (7.5,50.5):
        rail=cube("_endstop",(x,2.9,z),(25.8,6.5,1.8),.45)
        boolean(base,rail,"UNION")
        remove(rail)
    cradles.append(base)

for mod in list(q.modifiers):
    apply(q, mod)
keepouts=[]
for src in [battery]+pcb+[tray]+cradles:
    coords=[src.matrix_world @ Vector(v) for v in src.bound_box]
    low=[min(v[k] for v in coords) for k in range(3)]
    high=[max(v[k] for v in coords) for k in range(3)]
    clearance=.55 if src.name.startswith("REF_") else .40
    cutter=cube("_KEEP_"+src.name, tuple((low[k]+high[k])/2 for k in range(3)), tuple(high[k]-low[k]+2*clearance for k in range(3)), 0)
    keepouts.append(cutter)
pocket_results=[]
for n in ["A0_Tripo_quads_organic_front"]+["tripo_part_"+str(i) for i in range(1,11)]:
    obj=bpy.data.objects[n]
    before=mesh_stats(obj)
    for cutter in keepouts:
        boolean(obj,cutter)
    after=mesh_stats(obj)
    pocket_results.append({"part":n,"before":before,"after":after,"retained_fraction":round(after["volume_mm3"]/max(before["volume_mm3"],.001),4)})
for cutter in keepouts:
    remove(cutter)
sc=bpy.context.scene
sc.unit_settings.system="METRIC"
sc.unit_settings.scale_length=.001
sc.unit_settings.length_unit="MILLIMETERS"
sc.display.shading.background_type="WORLD"
sc.world.color=(1,1,1)
sc.display.shading.color_type="OBJECT"
sc.display.shading.show_cavity=True
sc.display.shading.show_shadows=False
sc.render.resolution_x=1400
sc.render.resolution_y=1060
sc.render.image_settings.file_format="PNG"
cam=sc.camera
cam.data.ortho_scale=170
center=Vector((0,0,41))
p=center+Vector((1.2,-1.6,.95)).normalized()*245
cam.location=p
cam.rotation_euler=(center-p).to_track_quat("-Z","Y").to_euler()

groups={"source":["A0_Tripo_quads_organic_front"]+["tripo_part_"+str(i) for i in range(1,11)],
        "mechanics":["P1_BATTERY_RING","P2_ESP32_BRACKET","P3_ESP32_BRACKET"],
        "hardware":["REF_Linocell_94x62x15","REF_ESP32_CAM_1","REF_ESP32_CAM_2","REF_LENS_1","REF_LENS_2"]}
def view(name,visible):
    for o in bpy.data.objects:
        if o.type=="MESH":
            o.hide_render=(o.name not in visible)
    sc.render.filepath=str(root/"render"/name)
    bpy.ops.render.render(write_still=True)
view("10_Tripo_sculpture_packaged.png",groups["source"]+groups["mechanics"])
view("11_powerbank_exact_envelope.png",["tripo_part_1","tripo_part_2"]+groups["mechanics"]+["REF_Linocell_94x62x15"])
view("12_two_esp32_exact_envelopes.png",groups["mechanics"]+groups["hardware"])
view("13_separate_tripo_and_electronics.png",groups["source"]+groups["hardware"])
for o in bpy.data.objects:
    if o.type=="MESH":
        o.hide_render=o.name.startswith(("SOURCE_","REF_UNCUT_","REF_"))

targets=[q]+[bpy.data.objects["tripo_part_"+str(i)] for i in range(1,11)]+[tray]+cradles
issues=[]
for o in targets:
    s=mesh_stats(o)
    issues.append(s)
    selected(o)
    p=root/"print_candidates"/(o.name+".stl")
    bpy.ops.wm.stl_export(filepath=str(p),export_selected_objects=True,apply_modifiers=True)
result={"input":"actual Tripo v3 retopology, saved mesh, 11 parts",
        "source_mm_scale":S,
        "expected_outer_envelope_mm":[round(.998505*S,1),round(.74394*S,1),round(.51846*S,1)],
        "powerbank_mm":[94,62,15],
        "battery_clearance_side_mm":.5,
        "module_nominal_mm":[27,40.5,10.4],
        "camera_axis_centers_mm":[[-29.0,37.1],[29.0,37.1]],
        "lens_center_distance_mm":58.0,
        "pocket_results":pocket_results,
        "meshes":issues,
        "print_status":"UNVERIFIED CANDIDATES, NOT SLICED, PHYSICAL HARDWARE NOT TESTED"}
(root/"qa/engineering_r08.json").write_text(json.dumps(result,indent=2))
print("FIT_R08",json.dumps(result))
bpy.ops.wm.save_as_mainfile(filepath=str(root/"ENTROPI_Tripo_hybrid_R08.blend"))