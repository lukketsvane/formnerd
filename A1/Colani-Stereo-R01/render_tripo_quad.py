import bpy,math,os,glob
from mathutils import Vector
root=os.path.dirname(os.path.abspath(__file__))
src=glob.glob(os.path.join(root,"tripo","fbx","*.fbx"))[0]
out=os.path.join(root,"preview")
os.makedirs(out,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=src)
obj=next(o for o in bpy.context.scene.objects if o.type=="MESH")
for o in list(bpy.context.scene.objects):
    if o!=obj:bpy.data.objects.remove(o,do_unlink=True)
obj.name="TRIPO_SMART_MESH_QUAD_9750_REFERENCE_NOT_SOLID"
scene=bpy.context.scene
bb=[obj.matrix_world@Vector(p) for p in obj.bound_box]
lo=Vector(tuple(min(p[i] for p in bb) for i in range(3)))
hi=Vector(tuple(max(p[i] for p in bb) for i in range(3)))
center=(hi+lo)/2
world_size=hi-lo
scene.render.engine="BLENDER_WORKBENCH"
scene.display.shading.light="STUDIO"
scene.display.shading.color_type="SINGLE"
scene.display.shading.single_color=(0.76,0.76,0.77)
scene.display.shading.show_shadows=False
scene.display.shading.show_cavity=True
scene.display.shading.cavity_type="BOTH"
scene.display.shading.curvature_ridge_factor=1.1
scene.display.shading.curvature_valley_factor=0.85
scene.display.shading.background_type="VIEWPORT"
scene.display.shading.background_color=(1,1,1)
scene.world=bpy.data.worlds.new("White_Background")
scene.world.color=(1,1,1)
scene.render.resolution_x=1350
scene.render.resolution_y=1500
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.film_transparent=False
scene.camera=None
camera_data=bpy.data.cameras.new("Orthographic_Camera")
camera=bpy.data.objects.new("Orthographic_Camera",camera_data)
scene.collection.objects.link(camera)
camera_data.type="ORTHO"
camera_data.ortho_scale=max(world_size.z*1.30,world_size.x*1.95)
scene.camera=camera
scale=max(world_size)
views=[("01_Tripo_3quarter_frontA",(1,-1,0.40)),("02_Tripo_3quarter_frontB",(1,1,0.40)),("03_Tripo_frontA",(0,-1,0.12)),("04_Tripo_frontB",(0,1,0.12)),("05_Tripo_side",(1,0,0.12))]
for name,direction in views:
    p=Vector(direction).normalized()
    camera.location=center+p*(2.8*scale)
    q=(center-camera.location).to_track_quat("-Z","Y")
    camera.rotation_euler=q.to_euler()
    scene.render.filepath=os.path.join(out,name+".png")
    bpy.ops.render.render(write_still=True)
    print("RENDER_SAVED",scene.render.filepath)
scene.unit_settings.system="METRIC"
scene.unit_settings.scale_length=1.0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(root,"tripo","Colani_Lady_Quad_Cage_Edit.blend"))
print("EDITABLE_BLENDER_SAVED")
