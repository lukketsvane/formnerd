import bpy
import bmesh
import json
from pathlib import Path

root=Path(r"C:\Users\Iver\Documents\github\formnerd\A4\Entropi-Tripo-R08")
outer=["A0_Tripo_quads_organic_front"]+["tripo_part_"+str(i) for i in (3,4,5,6,7,8)]
def select(o):
    bpy.ops.object.select_all(action="DESELECT")
    o.hide_set(False)
    o.select_set(True)
    bpy.context.view_layer.objects.active=o
def stats(o):
    bm=bmesh.new()
    bm.from_mesh(o.data)
    bad=sum(not e.is_manifold for e in bm.edges)
    volume=abs(bm.calc_volume(signed=True)) if bm.faces else 0
    bm.free()
    return {"faces":len(o.data.polygons),"edges_nonmanifold":bad,"volume_mm3":round(volume,2)}
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,5.2,37.7))
core=bpy.context.object
core.name="_black_body_keepout"
core.dimensions=(102.2,47.3,71.6)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
bevel=core.modifiers.new("Rounded black body keepout","BEVEL")
bevel.width=6.1
bevel.segments=6
select(core)
bpy.ops.object.modifier_apply(modifier=bevel.name)
results=[]
for n in outer:
    o=bpy.data.objects[n]
    for sub in list(o.modifiers):
        select(o)
        bpy.ops.object.modifier_apply(modifier=sub.name)
    before=stats(o)
    cut=o.modifiers.new("Tripo cosmetic inner clearance","BOOLEAN")
    cut.operation="DIFFERENCE"
    cut.solver="EXACT"
    cut.object=core
    select(o)
    bpy.ops.object.modifier_apply(modifier=cut.name)
    after=stats(o)
    results.append({"part":n,"before":before,"after":after,"retained_fraction":round(after["volume_mm3"]/max(1,before["volume_mm3"]),4)})
    select(o)
    bpy.ops.wm.stl_export(filepath=str(root/"print_candidates"/(o.name+"_cleared.stl")),export_selected_objects=True)
bpy.data.objects.remove(core,do_unlink=True)
sc=bpy.context.scene
for o in bpy.data.objects:
    if o.type=="MESH":
        o.hide_render=o.name.startswith(("SOURCE_","REF_UNCUT_","REF_")) or o.name in ("tripo_part_1","tripo_part_2","P1_BATTERY_RING")
sc.render.filepath=str(root/"render/20_Tripo_form_carved_only_internally.png")
bpy.ops.render.render(write_still=True)
(root/"qa/trimmed_shroud.json").write_text(json.dumps(results,indent=2))
print("TRIPO_SHROUD_CLEARANCE",json.dumps(results))
bpy.ops.wm.save_as_mainfile(filepath=str(root/"ENTROPI_Tripo_hybrid_R08_CLEARED.blend"))