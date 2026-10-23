import bpy
import bmesh
import json
from mathutils import Vector
from pathlib import Path

root=Path(r"C:\Users\Iver\Documents\github\formnerd\A4\Entropi-Tripo-R08")
sc=bpy.context.scene
cam=sc.camera
sc.display.shading.color_type="OBJECT"
sc.display.shading.background_type="WORLD"
sc.world.color=(1,1,1)
sc.display.shading.show_shadows=False
sc.display.shading.show_cavity=True
sc.render.resolution_x=1300
sc.render.resolution_y=1000
def orient(distance=245,orthoscale=160):
    c=Vector((0,0,40))
    v=c+Vector((1.0,-1.7,.8)).normalized()*distance
    cam.location=v
    cam.rotation_euler=(c-v).to_track_quat("-Z","Y").to_euler()
    cam.data.ortho_scale=orthoscale
def view(name,visible):
    for o in bpy.data.objects:
        if o.type=="MESH":
            o.hide_render=o.name not in visible
    sc.render.filepath=str(root/"render"/name)
    bpy.ops.render.render(write_still=True)
outer=["A0_Tripo_quads_organic_front"]+["tripo_part_"+str(i) for i in range(3,11)]
hardware=["REF_Linocell_94x62x15","REF_ESP32_CAM_1","REF_ESP32_CAM_2","REF_LENS_1","REF_LENS_2"]
mechanical=["B1_POWERBANK_FITTED_ROUNDED_CUBE","B2_OPTICAL_INSERT_STATION","P2_ESP32_BRACKET","P3_ESP32_BRACKET"]
orient()
view("17_battery_two_esp32_visible.png",hardware+["P2_ESP32_BRACKET","P3_ESP32_BRACKET"])
view("18_separate_white_tripo_and_black_case.png",outer+["B1_POWERBANK_FITTED_ROUNDED_CUBE"])
saved={o.name:o.location.copy() for o in bpy.data.objects if o.type=="MESH"}
for n in outer:bpy.data.objects[n].location.y-=68
bpy.data.objects["B1_POWERBANK_FITTED_ROUNDED_CUBE"].location.y+=85
orient(340,270)
view("19_exploded_tripo_compact_assembly.png",outer+hardware+mechanical)
for n,pos in saved.items():
    bpy.data.objects[n].location=pos
def volume_intersection(a,b):
    me=bpy.data.meshes.new_from_object(a.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    tmp=bpy.data.objects.new("_check",me)
    sc.collection.objects.link(tmp)
    tmp.matrix_world=a.matrix_world.copy()
    m=tmp.modifiers.new("Intersection","BOOLEAN")
    m.operation="INTERSECT"
    m.solver="EXACT"
    m.object=b
    bpy.ops.object.select_all(action="DESELECT")
    tmp.select_set(True)
    bpy.context.view_layer.objects.active=tmp
    bpy.ops.object.modifier_apply(modifier=m.name)
    bm=bmesh.new()
    bm.from_mesh(tmp.data)
    v=abs(bm.calc_volume(signed=True)) if bm.faces else 0
    bm.free()
    bpy.data.objects.remove(tmp,do_unlink=True)
    return round(v,2)
rear=bpy.data.objects["B1_POWERBANK_FITTED_ROUNDED_CUBE"]
report={"rear_case_vs_battery_and_boards_mm3":{n:volume_intersection(rear,bpy.data.objects[n]) for n in hardware[:3]+mechanical[2:]},"rear_case_vs_tripo_sculpture_mm3":{n:volume_intersection(rear,bpy.data.objects[n]) for n in outer}}
(root/"qa/closefit_collision.json").write_text(json.dumps(report,indent=2))
print("CLOSEFIT_INTERSECTION_QA",json.dumps(report))