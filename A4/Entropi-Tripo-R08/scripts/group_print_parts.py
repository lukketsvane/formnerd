import bpy
import bmesh
import json
from pathlib import Path
from mathutils import Vector

root=Path(r"C:\Users\Iver\Documents\github\formnerd\A4\Entropi-Tripo-R08")
(root/"print_groups").mkdir(exist_ok=True)
(root/"render").mkdir(exist_ok=True)

def sel(o):
    bpy.ops.object.select_all(action="DESELECT")
    o.hide_set(False)
    o.select_set(True)
    bpy.context.view_layer.objects.active=o

def duplicate(name,source):
    s=bpy.data.objects[source]
    o=s.copy()
    o.data=s.data.copy()
    o.name=name
    bpy.context.scene.collection.objects.link(o)
    o.hide_render=False
    return o

def boolean(target,tool,operation):
    m=target.modifiers.new(operation,"BOOLEAN")
    m.operation=operation
    m.solver="EXACT"
    m.object=tool
    sel(target)
    bpy.ops.object.modifier_apply(modifier=m.name)

def connected(o):
    bm=bmesh.new()
    bm.from_mesh(o.data)
    bm.verts.ensure_lookup_table()
    pending=set(bm.verts)
    clusters=0
    while pending:
        seed=pending.pop()
        stack=[seed]
        clusters+=1
        while stack:
            v=stack.pop()
            for e in v.link_edges:
                other=e.other_vert(v)
                if other in pending:
                    pending.remove(other)
                    stack.append(other)
    result={"name":o.name,"faces":len(o.data.polygons),"vertices":len(o.data.vertices),"loose_shells":clusters,"nonmanifold_edges":sum(not e.is_manifold for e in bm.edges),"volume_mm3":round(abs(bm.calc_volume(signed=True)),1)}
    bm.free()
    return result

groups=[
    ("A_WHITE_TRIPO_RIB_SHELL",["A0_Tripo_quads_organic_front","tripo_part_3","tripo_part_4","tripo_part_6","tripo_part_8"],(.87,.88,.88,1)),
    ("B_BLACK_TRIPO_BACK",["tripo_part_1","tripo_part_2"],(.22,.23,.24,1)),
    ("C_TRIPO_OPTIC",["tripo_part_5","tripo_part_7"],(.3,.31,.32,1)),
    ("D_LEFT_TOP_BUTTON",["tripo_part_10"],(.12,.13,.14,1)),
    ("E_RIGHT_TOP_BUTTON",["tripo_part_9"],(.12,.13,.14,1)),
    ("F_BATTERY_HOLDER",["P1_BATTERY_RING"],(.34,.35,.36,1)),
    ("G_ESP32_LEFT_HOLDER",["P2_ESP32_BRACKET"],(.38,.39,.4,1)),
    ("H_ESP32_RIGHT_HOLDER",["P3_ESP32_BRACKET"],(.38,.39,.4,1)),
]
parts={}
before={}
for name,source_names,color in groups:
    part=duplicate(name,source_names[0])
    for s in source_names[1:]:
        addon=duplicate("_TEMP_"+s,s)
        boolean(part,addon,"UNION")
        bpy.data.objects.remove(addon,do_unlink=True)
    part.color=color
    parts[name]=part
    before[name]=connected(part)
    print("MERGED",name,json.dumps(before[name]))

for target_name in ["B_BLACK_TRIPO_BACK","C_TRIPO_OPTIC"]:
    target=parts[target_name]
    boolean(target,parts["A_WHITE_TRIPO_RIB_SHELL"],"DIFFERENCE")
boolean(parts["B_BLACK_TRIPO_BACK"],parts["C_TRIPO_OPTIC"],"DIFFERENCE")
boolean(parts["A_WHITE_TRIPO_RIB_SHELL"],parts["D_LEFT_TOP_BUTTON"],"DIFFERENCE")
boolean(parts["B_BLACK_TRIPO_BACK"],parts["E_RIGHT_TOP_BUTTON"],"DIFFERENCE")

for o in bpy.data.objects:
    if o.type=="MESH":
        o.hide_render=o.name not in parts

sc=bpy.context.scene
sc.display.shading.background_type="WORLD"
sc.world.color=(1,1,1)
sc.display.shading.color_type="OBJECT"
sc.display.shading.show_cavity=True
sc.display.shading.show_shadows=False
sc.render.resolution_x=1300
sc.render.resolution_y=1050
sc.render.image_settings.file_format="PNG"
cam=sc.camera
cam.data.ortho_scale=174
center=Vector((0,0,41))
p=center+Vector((1.3,-1.6,1)).normalized()*244
cam.location=p
cam.rotation_euler=(center-p).to_track_quat("-Z","Y").to_euler()
sc.render.filepath=str(root/"render"/"20_merged_parts_tripo.png")
bpy.ops.render.render(write_still=True)
for i,(name,_,_) in enumerate(groups):
    obj=parts[name]
    for p in parts.values():
        p.hide_render=(p!=obj)
    sc.render.filepath=str(root/"render"/("21_group_%02d_%s.png"%(i,name)))
    bpy.ops.render.render(write_still=True)
for p in parts.values():
    p.hide_render=False

final={}
for name,o in parts.items():
    final[name]=connected(o)
    sel(o)
    bpy.ops.wm.stl_export(filepath=str(root/"print_groups"/(name+".stl")),export_selected_objects=True,apply_modifiers=True)
print("GROUP_QA",json.dumps(final))
(root/"qa/grouped_print_parts.json").write_text(json.dumps({"before":before,"after":final},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(root/"ENTROPI_Tripo_GROUPED_R08.blend"))