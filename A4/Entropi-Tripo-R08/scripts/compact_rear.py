import bpy
import bmesh
import json
from pathlib import Path
from mathutils import Vector

root=Path(r"C:\Users\Iver\Documents\github\formnerd\A4\Entropi-Tripo-R08")
sc=bpy.context.scene
for n in ("tripo_part_1","tripo_part_2","P1_BATTERY_RING"):
    o=bpy.data.objects[n]
    o.hide_render=True
    o.hide_set(True)

def select(o):
    bpy.ops.object.select_all(action="DESELECT")
    o.hide_set(False)
    o.select_set(True)
    bpy.context.view_layer.objects.active=o

def box(name,at,size,r=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=at)
    o=bpy.context.object
    o.name=name
    o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if r:
        mod=o.modifiers.new("Rounded corners","BEVEL")
        mod.width=r
        mod.segments=6
        select(o)
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return o

rear=box("B1_POWERBANK_FITTED_ROUNDED_CUBE",(0,5.2,37.7),(101.4,46.5,70.8),6)
rear.color=(.22,.22,.22,1)
void=box("_electronics_inside_cut",(0,-4.1,37.7),(96.4,61.0,65.8),2.5)
cut=rear.modifiers.new("Front access cavity","BOOLEAN")
cut.operation="DIFFERENCE"
cut.solver="EXACT"
cut.object=void
select(rear)
bpy.ops.object.modifier_apply(modifier=cut.name)
bpy.data.objects.remove(void,do_unlink=True)
front=box("B2_OPTICAL_INSERT_STATION",(0,-16.5,37.7),(92,2.4,57.0),2)
front.color=(.36,.36,.36,1)
mounts=(bpy.data.objects["P2_ESP32_BRACKET"],bpy.data.objects["P3_ESP32_BRACKET"])
for m in mounts:m.hide_render=False

cam=sc.camera
center=Vector((0,0,42))
at=center+Vector((1.2,-1.6,.95)).normalized()*245
cam.location=at
cam.rotation_euler=(center-at).to_track_quat("-Z","Y").to_euler()
sc.display.shading.color_type="OBJECT"
def shot(filename,names):
    for o in bpy.data.objects:
        if o.type=="MESH":
            o.hide_render=o.name not in names
    sc.render.filepath=str(root/"render"/filename)
    bpy.ops.render.render(write_still=True)
tripo=["A0_Tripo_quads_organic_front"]+["tripo_part_"+str(i) for i in range(3,11)]
shot("14_R08_Tripo_actual_with_close_cube.png",tripo+[rear.name])
shot("15_R08_close_fitted_electronics.png",[rear.name,front.name]+[m.name for m in mounts]+["REF_Linocell_94x62x15","REF_ESP32_CAM_1","REF_ESP32_CAM_2"])
shot("16_R08_tubes_and_cube_separated.png",tripo[:]+[rear.name])
for o in bpy.data.objects:
    if o.type=="MESH":
        o.hide_render=o.name.startswith(("SOURCE_","REF_UNCUT_","REF_")) or o.name in ("tripo_part_1","tripo_part_2","P1_BATTERY_RING")
bm=bmesh.new()
bm.from_mesh(rear.data)
report={"rear_case_dimensions_mm":[101.4,46.5,70.8],"powerbank_dimensions_mm":[94,15,62],"minimum_nominal_sidewall_mm":2.5,"case_nonmanifold_edges":sum(not e.is_manifold for e in bm.edges),"case_volume_mm3":round(abs(bm.calc_volume(signed=True)),2),"status":"WIP CAD; fit and external intersections require check"}
bm.free()
(root/"qa/rear_closefit.json").write_text(json.dumps(report,indent=2))
print("REAR_CLOSE_FIT",json.dumps(report))
select(rear)
bpy.ops.wm.stl_export(filepath=str(root/"print_candidates/B1_POWERBANK_FITTED_ROUNDED_CUBE.stl"),export_selected_objects=True)
bpy.ops.wm.save_as_mainfile(filepath=str(root/"ENTROPI_Tripo_hybrid_R08_CLOSEFIT.blend"))