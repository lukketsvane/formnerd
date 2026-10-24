import bpy,math,os,json
from mathutils import Vector
root=os.path.dirname(os.path.abspath(__file__))
build=os.path.join(root,"R12")
out=os.path.join(build,"process")
os.makedirs(out,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(build,"Colani_R12_Tripo_geometry.blend"))
scene=bpy.context.scene
front=bpy.data.objects["P01_front_Tripo_R12"]
back=bpy.data.objects["P02_back_Tripo_R12"]
original=bpy.data.objects.get("Tripo_organic_scaled_reference")
if original:original.hide_render=True
scene.render.engine="BLENDER_WORKBENCH"
scene.display.shading.light="STUDIO"
scene.display.shading.studio_light="paint.sl"
scene.display.shading.color_type="OBJECT"
scene.display.shading.background_type="VIEWPORT"
scene.display.shading.background_color=(1,1,1)
scene.display.shading.show_shadows=True
scene.display.shading.show_cavity=True
scene.display.shading.cavity_type="BOTH"
scene.display.shading.curvature_ridge_factor=1.2
scene.display.shading.curvature_valley_factor=0.8
scene.render.resolution_x=1000
scene.render.resolution_y=1200
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.film_transparent=False
scene.camera=None
bpy.ops.object.camera_add()
cam=bpy.context.object
cam.name="R12_OrthographicCamera"
cam.data.type="ORTHO"
cam.data.ortho_scale=178
scene.camera=cam
def pose(camera_position,focus=(0,0,0),scale=178):
    cam.location=camera_position
    aim=Vector(focus)-cam.location
    cam.rotation_euler=aim.to_track_quat("-Z","Y").to_euler()
    cam.data.ortho_scale=scale
def snap(filename,camera_position,focus=(0,0,0),scale=178):
    pose(camera_position,focus,scale)
    scene.render.filepath=os.path.join(out,filename)
    bpy.ops.render.render(write_still=True)
    print("RENDER_DONE",scene.render.filepath,os.path.getsize(scene.render.filepath))
front.color=(0.86,0.83,0.78,1)
back.color=(0.64,0.65,0.63,1)
front.hide_render=False
back.hide_render=False
snap("01_tripo_r12_assembled.png",(108,-155,77),(0,0,0),185)
snap("02_tripo_r12_front.png",(0,-230,26),(0,0,0),170)
front.location.y=-22
back.location.y=22
snap("03_tripo_r12_exploded.png",(145,-190,100),(0,0,0),192)
front.location.y=0
back.location.y=0
front.hide_render=True
snap("04_tripo_r12_back_open.png",(115,175,75),(0,0,0),180)
back.hide_render=True
def cube(name,dimensions,location,color):
    bpy.ops.mesh.primitive_cube_add(size=1,location=location)
    ob=bpy.context.object
    ob.name=name
    ob.dimensions=dimensions
    ob.color=(*color,1.0)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    be=ob.modifiers.new("Small_corner_radii","BEVEL")
    be.width=1.0
    be.segments=3
    no=ob.modifiers.new("WeightedNormals","WEIGHTED_NORMAL")
    return ob
cube("Powerbank_envelope_94x62x15",(62,15,94),(-9,0,-5),(0.25,0.31,0.34))
cube("ESP32_CAM_L_27x40p5",(27,5.5,40.5),(-20.75,-14.5,-25),(0.20,0.46,0.57))
cube("ESP32_CAM_R_27x40p5",(27,5.5,40.5),(8.75,-14.5,-25),(0.20,0.46,0.57))
for x in (-14.75,14.75):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=4,depth=5,location=(x,-19,-24),rotation=(math.pi/2,0,0))
    bpy.context.object.color=(0.05,0.07,0.09,1)
snap("05_battery_two_esp32.png",(128,-185,80),(0,0,0),195)
print("DONE")
