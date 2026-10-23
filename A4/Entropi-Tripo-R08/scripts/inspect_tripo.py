import bpy
import json
from pathlib import Path
from mathutils import Vector

repo = Path(r"C:\Users\Iver\Documents\github\formnerd")
src = repo / "A4/arkiv/tripo-a1/mesh/04-smart-retopology-preview.glb"
out = repo / "A4/Entropi-Tripo-R08"
(out / "render").mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(src))
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
verts = [o.matrix_world @ v.co for o in meshes for v in o.data.vertices]
mins = [min(v[i] for v in verts) for i in range(3)]
maxs = [max(v[i] for v in verts) for i in range(3)]
center = Vector([(mins[i] + maxs[i]) / 2 for i in range(3)])
spans = [maxs[i]-mins[i] for i in range(3)]
major = max(spans)
stats = {"source": str(src.relative_to(repo)).replace("\\","/"),"bounds_min":mins,"bounds_max":maxs,"dimensions":spans,"objects":[{"name":o.name,"verts":len(o.data.vertices),"faces":len(o.data.polygons),"triangles":sum(len(p.vertices)-2 for p in o.data.polygons)} for o in meshes]}
(out / "qa").mkdir(exist_ok=True)
(out / "qa/mesh_input.json").write_text(json.dumps(stats, indent=2))
print("TRIPO_MESH_STATS", json.dumps(stats))
for o in list(bpy.data.objects):
    if o.type in ("CAMERA", "LIGHT"):
        bpy.data.objects.remove(o, do_unlink=True)
scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "SINGLE"
scene.display.shading.single_color = (0.71,0.72,0.74)
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = "BOTH"
scene.display.shading.curvature_ridge_factor = 1.25
scene.display.shading.curvature_valley_factor = 0.8
scene.display.shading.background_type = "WORLD"
scene.world = bpy.data.worlds.new("White")
scene.world.color = (1,1,1)
scene.render.resolution_x = 1200
scene.render.resolution_y = 930
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camdata = bpy.data.cameras.new("Orthographic inspection")
cam = bpy.data.objects.new("Inspection Camera",camdata)
scene.collection.objects.link(cam)
scene.camera = cam
camdata.type = "ORTHO"
camdata.ortho_scale = major * 1.52
for name, dr in [("01_three_quarter",(1.3,-1.7,0.9)),("02_opposite",(-1.4,1.7,0.9)),("03_elevation",(0,-2,0.15))]:
    pos = Vector(dr).normalized()*major*2.8+center
    cam.location = pos
    cam.rotation_euler = (center - pos).to_track_quat("-Z","Y").to_euler()
    scene.render.filepath = str(out/"render"/(name+".png"))
    bpy.ops.render.render(write_still=True)
    print("SAVED",scene.render.filepath)
bpy.ops.wm.save_as_mainfile(filepath=str(out/"Tripo_20k_master.blend"))