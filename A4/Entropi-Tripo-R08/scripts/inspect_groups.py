import bpy
from pathlib import Path
from mathutils import Vector

repo=Path(r"C:\Users\Iver\Documents\github\formnerd")
out=repo/"A4/Entropi-Tripo-R08/render"
objs={o.name:o for o in bpy.data.objects if o.type=="MESH"}
a=Vector((-0.2585,-0.4994,-0.372));b=Vector((0.26,0.5,0.373))
center=(a+b)/2
cam=bpy.context.scene.camera
pos=center+Vector((1.3,-1.7,0.9)).normalized()*2.7
cam.location=pos
cam.rotation_euler=(center-pos).to_track_quat("-Z","Y").to_euler()
sc=bpy.context.scene
sc.display.shading.color_type="OBJECT"
sc.display.shading.background_type="WORLD"
sc.world.color=(1,1,1)
for i,o in enumerate(objs.values()):
    o.color=((0.2+0.07*i)%1,(0.2+0.085*i)%1,(0.2+0.1*i)%1,1)
for label,chosen in [
    ("05_Tripo_part0",["tripo_part_0"]),
    ("06_Tripo_rear_housing",["tripo_part_1","tripo_part_2"]),
    ("07_Tripo_ribs",["tripo_part_0","tripo_part_3","tripo_part_4","tripo_part_6","tripo_part_8"]),
    ("08_Tripo_optics",["tripo_part_5","tripo_part_7"]),
]:
    for n,o in objs.items():
        o.hide_render=n not in chosen
    sc.render.filepath=str(out/(label+".png"))
    bpy.ops.render.render(write_still=True)
    print("SAVED",label)
for o in objs.values():o.hide_render=False