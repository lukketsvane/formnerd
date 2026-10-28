import bpy, math, os, json
from mathutils import Vector
base=os.path.dirname(os.path.abspath(__file__))
source=os.path.join(base,"R12","Colani_R12_Tripo_geometry.blend")
out=os.path.join(base,"R14")
imgs=os.path.join(out,"renders")
os.makedirs(imgs,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=source)
scene=bpy.context.scene
shellF=bpy.data.objects["P01_front_Tripo_R12"]
shellB=bpy.data.objects["P02_back_Tripo_R12"]
original=bpy.data.objects.get("Tripo_organic_scaled_reference")
if original:
    original.hide_render=True
    original.hide_set(True)
def material(name,rgb,rough=0.5,metal=0.0):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color=(*rgb,1)
    m.use_nodes=True
    bs=m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value=(*rgb,1)
    bs.inputs["Roughness"].default_value=rough
    bs.inputs["Metallic"].default_value=metal
    return m
cream=material("01 Warm porcelain-grey",(0.61,0.62,0.60),0.4)
silver=material("02 Silver composite",(0.46,0.48,0.48),0.4)
graphite=material("03 Graphite rubber",(0.13,0.14,0.15),0.64)
batteryMat=material("04 Battery matte charcoal",(0.24,0.25,0.26),0.5)
pcbMat=material("05 ESP32 board",(0.13,0.24,0.27),0.5)
lensMat=material("06 Lens glass",(0.015,0.021,0.028),0.11,0.3)
refMat=material("07 Reference blue",(0.17,0.32,0.34),0.5)
for obj,mat in [(shellF,cream),(shellB,cream)]:
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    obj.color=mat.diffuse_color
def box(name,sz,loc,mat,rootname=None):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=bpy.context.object
    o.name=name
    o.dimensions=sz
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(mat)
    o.color=mat.diffuse_color
    o["part_id"]=rootname or name.split("_")[0]
    return o
def cylinder(name,radius,length,loc,mat,rot=0,n=64):
    bpy.ops.mesh.primitive_cylinder_add(vertices=n,radius=radius,depth=length,location=loc,rotation=(rot,0,0))
    o=bpy.context.object
    o.name=name
    o.data.materials.append(mat)
    o.color=mat.diffuse_color
    return o
def tube(name,ro,ri,length,loc,mat,rot=0):
    o=cylinder(name,ro,length,loc,mat,rot)
    c=cylinder(name+"_CUTTER",ri,length+2,loc,mat,rot)
    bpy.context.view_layer.objects.active=o
    m=o.modifiers.new("InnerBore","BOOLEAN")
    m.operation="DIFFERENCE"
    m.solver="EXACT"
    m.object=c
    bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.data.objects.remove(c,do_unlink=True)
    return o
partsets={}
def assign(part,objects):
    partsets[part]=objects
    for o in objects:
        o["part_id"]=part
        o["component_type"]="physical_print_part"
    return objects
c=[]
for x in (-33.1,33.1):
    c.append(box("P03_cradle_wall_"+str(x),(2.8,17.6,99.2),(x-9,10,-5),silver,"P03"))
c.append(box("P03_lower_bridge",(69,17.6,3),(-9,10,-54.1),silver,"P03"))
for i,z in enumerate((-39.5,-6,28)):
    c.append(box("P03_back_rib_"+str(i),(69,2,4),(-9,19,z),silver,"P03"))
for x in (-33.1,33.1):
    c.append(box("P03_top_detent_"+str(x),(2.8,4,5.5),(x-9,3.9,43),silver,"P03"))
assign("P03_batterivogge",c)
carrier=[]
for i,x in enumerate((-29.7,0,29.7)):
    carrier.append(box("P04_vertical_"+str(i),(2 if i!=1 else 1.4,9,45),(x,-13,-25),silver,"P04"))
carrier.append(box("P04_bottom",(61.4,9,2.35),(0,-13,-47.1),silver,"P04"))
for i,z in enumerate((-16.5,15)):
    carrier.append(box("P04_stereo_rib_"+str(i),(61.4,1.9,3),(0,-7.8,-25+z),silver,"P04"))
for i,x in enumerate((-29.7,0,29.7)):
    for z in (-10,11):
        carrier.append(box("P04_lock_"+str(i)+"_"+str(z),(2,1.1,4.2),(x,-17.75,-25+z),silver,"P04"))
assign("P04_ESP32_felleshaldar",carrier)
lb=box("REF_Linocell_5000mAh",(62,15,94),(-9,10,-5),batteryMat)
lb["component_type"]="reference_not_print"
boards=[]
for i,x in enumerate((-14.75,14.75)):
    board=box("REF_ESP32_CAM_"+("L" if i==0 else "R"),(27,4.2,40.5),(x,-13,-25),pcbMat)
    board["component_type"]="reference_not_print"
    boards.append(board)
bridge=[box("P10_bridge",(51.5,3,4.5),(0,-16,-24),silver)]
for x in (-14.75,14.75):
    bridge.append(tube("P10_mount_"+str(x),7.0,4.55,5.5,(x,-17.5,-24),silver,math.pi/2))
assign("P10_stereobase",bridge)
lenses=[]
for i,x in enumerate((-14.75,14.75)):
    parts=[
        tube("P0"+str(6+i)+"_lens_shaft",4.05,3.25,6,(x,-19,-24),graphite,math.pi/2),
        tube("P0"+str(6+i)+"_lens_flange",6.25,3.25,1.2,(x,-22.4,-24),silver,math.pi/2)
    ]
    assign("P0"+str(6+i)+"_lens_sleeve",parts)
    lenses+=parts
    lens=cylinder("REF_optical_unit_"+str(i),3.05,0.8,(x,-23.0,-24),lensMat,math.pi/2)
    lens["component_type"]="reference_not_print"
assign("P08_utloysarknapp",[
    cylinder("P08_button_face",4.4,1.6,(16,-23.3,20),silver,math.pi/2),
    cylinder("P08_button_post",2.45,5.5,(16,-19.8,20),silver,math.pi/2)
])
def look(o,target):
    o.rotation_euler=(Vector(target)-o.location).to_track_quat("-Z","Y").to_euler()
scene.render.engine="BLENDER_WORKBENCH"
scene.display.shading.light="STUDIO"
scene.display.shading.studio_light="paint.sl"
scene.display.shading.color_type="MATERIAL"
scene.display.shading.show_cavity=True
scene.display.shading.cavity_type="BOTH"
scene.display.shading.curvature_ridge_factor=1.5
scene.display.shading.curvature_valley_factor=1.3
scene.display.shading.background_type="VIEWPORT"
scene.display.shading.background_color=(1,1,1)
scene.display.shading.show_shadows=True
scene.view_settings.view_transform="Standard"
scene.render.resolution_x=1060
scene.render.resolution_y=1280
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
bpy.ops.object.camera_add()
cam=bpy.context.object
cam.name="R14_StudioCamera"
cam.data.type="ORTHO"
cam.data.ortho_scale=184
scene.camera=cam
def hide(objs,value):
    for o in objs:o.hide_render=value
physical=[o for objects in partsets.values() for o in objects]
nominal=[lb,*boards,*[bpy.data.objects["REF_optical_unit_"+str(i)] for i in range(2)]]
def capture(filename,eye,target=(0,0,0),scale=184):
    cam.location=eye
    look(cam,target)
    cam.data.ortho_scale=scale
    scene.render.filepath=os.path.join(imgs,filename)
    bpy.ops.render.render(write_still=True)
    print("CAPTURED",filename,os.path.getsize(scene.render.filepath))
hide([*physical,*nominal],True)
shellF.hide_render=False
shellB.hide_render=False
capture("01_finished_hero_actual_CAD.png",(117,-205,78))
capture("02_finished_front_actual_CAD.png",(0,-250,13),scale=172)
capture("03_finished_right_actual_CAD.png",(240,80,66))
capture("04_finished_rear_actual_CAD.png",(60,240,85))
hide(physical,False)
hide(nominal,False)
shellF.hide_render=True
shellB.hide_render=False
capture("05_open_back_with_electronics.png",(122,-185,82),scale=182)
shellF.hide_render=False
shellF.location.y=-42
shellB.location.y=33
hide(physical,False)
hide(nominal,True)
capture("06_exploded_outer_inner.png",(145,-185,98),scale=232)
shellF.location.y=0
shellB.location.y=0
shellF.hide_render=True
shellB.hide_render=True
hide(nominal,False)
capture("07_internal_assembled.png",(105,-185,76),scale=170)
hide(nominal,True)
capture("08_mechanical_parts_only.png",(105,-185,76),scale=170)
hide(nominal,False)
shellB.hide_render=False
capture("09_rear_section_side.png",(240,5,55),scale=175)
shellF.hide_render=False
for o in bpy.context.scene.objects:
    if o.type=="MESH":o.hide_render=False
if original:original.hide_render=True
bpy.ops.object.select_all(action="DESELECT")
bpy.context.view_layer.objects.active=shellF
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out,"Colani_R14_Integrated_Assembly.blend"))
bpy.ops.export_scene.gltf(filepath=os.path.join(out,"Colani_R14_Integrated_Assembly.glb"),export_format="GLB",export_cameras=False,export_lights=False,export_materials="EXPORT")
bpy.ops.export_scene.gltf(filepath=os.path.join(out,"Colani_R14_Integrated_Assembly_NoRefs.glb"),export_format="GLB",export_cameras=False,export_lights=False,export_materials="EXPORT")
manifest={"revision":"R14","outer_source":source,"actual_outer_geometry":"R12 Tripo-derived shell","internals":"R13 CAD primitive geometry reconstructed with verified nominal dimensions and R14 shift of powerbank into rear half","envelope_mm":[96,145,46],"powerbank_center_mm":[-9,10,-5],"pcb_centers_mm":[[-14.75,-13,-25],[14.75,-13,-25]],"lens_baseline_mm":29.5,"pictures":sorted(os.listdir(imgs)),"status":"digital assembly visualization, not production fit certified"}
open(os.path.join(out,"assembly_manifest.json"),"w",encoding="utf8").write(json.dumps(manifest,indent=2))
print("FINISHED_ASSEMBLY",json.dumps(manifest))
