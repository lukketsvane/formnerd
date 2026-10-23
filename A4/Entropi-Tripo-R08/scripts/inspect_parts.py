import bpy
import json
import bmesh
from pathlib import Path
from mathutils import Vector

repo = Path(r"C:\Users\Iver\Documents\github\formnerd")
out = repo / "A4/Entropi-Tripo-R08"
stats = []
for o in sorted([o for o in bpy.data.objects if o.type == "MESH"],key=lambda v:v.name):
    w = [o.matrix_world @ v.co for v in o.data.vertices]
    a = [round(min(v[i] for v in w),4) for i in range(3)]
    b = [round(max(v[i] for v in w),4) for i in range(3)]
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.normal_update()
    bad = sum(not e.is_manifold for e in bm.edges)
    volume = bm.calc_volume(signed=True)
    bm.free()
    stats.append({"part":o.name,"size":len(o.data.polygons),"min":a,"max":b,"center":[round((a[i]+b[i])/2,4) for i in range(3)],"nonmanifold_edges":bad,"signed_volume":round(volume,6)})
(out/"qa/part_diagnostics.json").write_text(json.dumps(stats,indent=2))
print("PART_DIAGNOSTICS",json.dumps(stats))
scene=bpy.context.scene
scene.display.shading.color_type="MATERIAL"
palette=[(0.83,0.83,0.83,1),(0.24,0.24,0.24,1),(0.72,0.72,0.72,1),(0.43,0.43,0.43,1),(0.9,0.9,0.9,1),(0.58,0.58,0.58,1)]
for i,o in enumerate(sorted([o for o in bpy.data.objects if o.type=="MESH"],key=lambda v:v.name)):
    mat=bpy.data.materials.new("Tripo Segment %s"%o.name)
    mat.diffuse_color=palette[i%len(palette)]
    o.data.materials.clear()
    o.data.materials.append(mat)
scene.render.filepath=str(out/"render/04_Tripo_segmented.png")
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out/"Tripo_segmented_master.blend"))