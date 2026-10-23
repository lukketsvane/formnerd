import bpy,os,math
from mathutils import Vector
root=os.path.dirname(os.path.abspath(__file__))
source=os.path.join(root,"tripo","Colani_Lady_Quad_Cage_Edit.blend")
bpy.ops.wm.open_mainfile(filepath=source)
obj=next(o for o in bpy.context.scene.objects if o.type=="MESH")
mod=obj.modifiers.new(name="SUBD_REFERENCE_NOT_NURBS",type="SUBSURF")
mod.subdivision_type="CATMULL_CLARK"
mod.levels=2
mod.render_levels=2
obj.name="TRIPO_QUAD_CAGE_WITH_NONDESTRUCTIVE_SUBD__NOT_MECHANICAL_CAD"
output=os.path.join(root,"tripo","Colani_Lady_Quad_SubD_Reference.blend")
scene=bpy.context.scene
bbox=[obj.matrix_world @ Vector(v) for v in obj.bound_box]
a=Vector([min(v[i] for v in bbox) for i in range(3)])
z=Vector([max(v[i] for v in bbox) for i in range(3)])
center=(z+a)*0.5
scale=(z-a).length
cam=scene.camera
for name,direction in [("06_Tripo_SubD_3quarter",(1,-1,0.40)),("07_Tripo_SubD_front",(0,-1,0.12))]:
    cam.location=center+Vector(direction).normalized()*(scale*2.4)
    cam.rotation_euler=(center-cam.location).to_track_quat("-Z","Y").to_euler()
    scene.render.filepath=os.path.join(root,"preview",name+".png")
    bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=output)
print("SUBD_SOURCE_SAVED",output)
