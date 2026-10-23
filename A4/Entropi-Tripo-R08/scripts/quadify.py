import bpy
import bmesh
import json
import math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

repo=Path(r"C:\Users\Iver\Documents\github\formnerd")
root=repo/"A4/Entropi-Tripo-R08"
src=bpy.data.objects["tripo_part_0"]
new=src.copy()
new.data=src.data.copy()
new.name="Tripo_Part0_Quad_SubD"
bpy.context.scene.collection.objects.link(new)
for o in bpy.context.selected_objects:o.select_set(False)
new.select_set(True)
bpy.context.view_layer.objects.active=new
bm=bmesh.new()
bm.from_mesh(new.data)
edges=[e for e in bm.edges if e.is_boundary]
if edges:
    bmesh.ops.holes_fill(bm,edges=edges)
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
bm.to_mesh(new.data)
bm.free()
try:
    status=bpy.ops.object.quadriflow_remesh(mode="FACES",target_faces=4000,use_preserve_boundary=False,use_preserve_sharp=False)
    print("QUADRIFLOW_STATUS",str(status))
except Exception as e:
    print("QUADRIFLOW_ERROR",str(e))
quads=sum(len(p.vertices)==4 for p in new.data.polygons)
triangles=sum(len(p.vertices)==3 for p in new.data.polygons)
stats={"new_faces":len(new.data.polygons),"new_quads":quads,"new_triangles":triangles}
bvh=BVHTree.FromObject(new,bpy.context.evaluated_depsgraph_get())
errors=[]
for i,v in enumerate(src.data.vertices):
    if i%5:continue
    pt=src.matrix_world@v.co
    hit=bvh.find_nearest(pt)
    if hit and hit[3] is not None:errors.append(float(hit[3])*112)
errors.sort()
stats.update({"mean_abs_deviation_mm":sum(errors)/len(errors) if errors else None,"p95_deviation_mm":errors[int(.95*(len(errors)-1))] if errors else None,"max_deviation_mm":errors[-1] if errors else None})
m=new.modifiers.new("Preview smooth surface","SUBSURF")
m.subdivision_type="CATMULL_CLARK"
m.levels=1
m.render_levels=1
(root/"qa/quad_retopy.json").write_text(json.dumps(stats,indent=2))
print("QUAD_REPORT",json.dumps(stats))
for o in bpy.data.objects:
    if o.type=="MESH":o.hide_render=o!=new
sc=bpy.context.scene
cam=sc.camera
a=Vector((-0.26,-0.50,-0.37));b=Vector((0.26,0.50,0.37));cent=(a+b)/2
pos=cent+Vector((1.3,-1.7,0.9)).normalized()*2.7
cam.location=pos
cam.rotation_euler=(cent-pos).to_track_quat("-Z","Y").to_euler()
sc.render.filepath=str(root/"render/09_Tripo_Quad_SubD.png")
bpy.ops.render.render(write_still=True)
for o in bpy.data.objects:
    if o.type=="MESH":o.hide_render=False
bpy.ops.wm.save_as_mainfile(filepath=str(root/"Tripo_Quad_SubD.blend"))