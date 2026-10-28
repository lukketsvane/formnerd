import bpy, math, os
from mathutils import Vector
base=os.path.dirname(os.path.abspath(__file__))
out=os.path.join(base,"R14","renders")
os.makedirs(out,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(base,"R14","Colani_R14_Integrated_Assembly.blend"))
sc=bpy.context.scene
sc.render.engine="CYCLES"
sc.cycles.samples=20
sc.cycles.use_denoising=True
sc.render.resolution_x=840
sc.render.resolution_y=940
sc.render.resolution_percentage=100
sc.render.image_settings.file_format="PNG"
sc.view_settings.view_transform="Standard"
sc.view_settings.look="Medium High Contrast"
sc.view_settings.exposure=0
sc.view_settings.gamma=1
world=sc.world or bpy.data.worlds.new("StudioWorld")
sc.world=world
world.use_nodes=True
nodes=world.node_tree.nodes
nodes.clear()
outW=nodes.new("ShaderNodeOutputWorld")
mix=nodes.new("ShaderNodeMixShader")
lightp=nodes.new("ShaderNodeLightPath")
bg=nodes.new("ShaderNodeBackground")
bg.inputs["Color"].default_value=(1,1,1,1)
bg.inputs["Strength"].default_value=0.12
white=nodes.new("ShaderNodeBackground")
white.inputs["Color"].default_value=(1,1,1,1)
white.inputs["Strength"].default_value=1.0
lnk=world.node_tree.links
lnk.new(lightp.outputs["Is Camera Ray"],mix.inputs[0])
lnk.new(bg.outputs["Background"],mix.inputs[1])
lnk.new(white.outputs["Background"],mix.inputs[2])
lnk.new(mix.outputs[0],outW.inputs["Surface"])
cam=sc.camera
if not cam:
    bpy.ops.object.camera_add()
    cam=bpy.context.object
    sc.camera=cam
cam.data.type="ORTHO"
def look(obj,at):
    obj.rotation_euler=(Vector(at)-obj.location).to_track_quat("-Z","Y").to_euler()
for o in list(bpy.data.objects):
    if o.type=="LIGHT":bpy.data.objects.remove(o,do_unlink=True)
def area(name,loc,power,size,color=(1,1,1)):
    bpy.ops.object.light_add(type="AREA",location=loc)
    ob=bpy.context.object
    ob.name=name
    ob.data.energy=power
    ob.data.color=color
    ob.data.shape="DISK"
    ob.data.size=size
    look(ob,(0,0,0))
area("01 Key Softbox",(-90,-125,150),310000,170)
area("02 Fill Softbox",(125,-75,80),105000,200)
area("03 Rim Softbox",(30,100,110),170000,140)
def material(name,rgb,rough=0.5,metal=0.0):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes=True
    m.diffuse_color=(*rgb,1)
    node=m.node_tree.nodes.get("Principled BSDF")
    node.inputs["Base Color"].default_value=(*rgb,1)
    node.inputs["Roughness"].default_value=rough
    node.inputs["Metallic"].default_value=metal
    return m
m_shell=material("R14 Finish | warm grey composite",(0.68,0.67,0.65),0.5)
m_metal=material("R14 Finish | cast alloy",(0.42,0.44,0.46),0.43,0.22)
m_dark=material("R14 Finish | black rubber",(0.10,0.11,0.12),0.54)
m_battery=material("R14 Hardware | bank",(0.22,0.23,0.24),0.64)
m_pcb=material("R14 Hardware | PCB",(0.08,0.25,0.28),0.5)
m_glass=material("R14 Optic | gloss black",(0.008,0.010,0.015),0.12,0.22)
shellF=bpy.data.objects["P01_front_Tripo_R12"]
shellB=bpy.data.objects["P02_back_Tripo_R12"]
for shell in (shellF,shellB):
    shell.data.materials.clear()
    shell.data.materials.append(m_shell)
    for poly in shell.data.polygons:poly.use_smooth=True
    sm=shell.modifiers.new("VISUAL_ONLY_geometry_smoothing","SMOOTH")
    sm.factor=1.2
    sm.iterations=5
for ob in bpy.data.objects:
    if ob.type!="MESH" or ob in (shellF,shellB):continue
    if ob.name.startswith("P03") or ob.name.startswith("P04") or ob.name.startswith("P10"):target=m_metal
    elif ob.name.startswith("P06") or ob.name.startswith("P07"):target=m_metal
    elif ob.name.startswith("P08"):target=m_metal
    elif ob.name.startswith("REF_Linocell"):target=m_battery
    elif ob.name.startswith("REF_ESP32"):target=m_pcb
    elif ob.name.startswith("REF_optical"):target=m_glass
    else:target=m_dark
    ob.data.materials.clear()
    ob.data.materials.append(target)
original=bpy.data.objects.get("Tripo_organic_scaled_reference")
if original:original.hide_render=True
physical=[o for o in bpy.data.objects if o.type=="MESH" and (o.name.startswith("P03") or o.name.startswith("P04") or o.name.startswith("P10"))]
optics=[o for o in bpy.data.objects if o.type=="MESH" and (o.name.startswith("P06") or o.name.startswith("P07") or o.name.startswith("REF_optical"))]
button=[o for o in bpy.data.objects if o.type=="MESH" and o.name.startswith("P08")]
electronics=[o for o in bpy.data.objects if o.type=="MESH" and (o.name.startswith("REF_Linocell") or o.name.startswith("REF_ESP32"))]
def visible(objects,state):
    for o in objects:o.hide_render=not state
def render(filename,eye,scale=181,focus=(0,0,0)):
    cam.location=eye
    look(cam,focus)
    cam.data.ortho_scale=scale
    sc.render.filepath=os.path.join(out,filename)
    bpy.ops.render.render(write_still=True)
    print("RENDER",filename,os.path.getsize(sc.render.filepath))
visible(physical,False)
visible(electronics,False)
visible(optics,True)
visible(button,True)
shellF.hide_render=False
shellB.hide_render=False
render("20_R14_hero_iso_white.png",(112,-175,80),188)
render("21_R14_front_white.png",(0,-195,10),171)
render("22_R14_side_white.png",(190,0,72),176)
render("23_R14_back_white.png",(35,195,65),181)
shellF.hide_render=True
shellB.hide_render=False
visible(electronics,True)
visible(physical,True)
render("24_R14_open_shell_white.png",(105,-165,79),188)
shellF.hide_render=False
shellF.location.y=-45
shellB.location.y=27
visible(electronics,True)
visible(physical,True)
render("25_R14_exploded_white.png",(150,-182,95),221)
shellF.location.y=0
shellB.location.y=0
shellF.hide_render=True
shellB.hide_render=True
render("26_R14_electronics_white.png",(103,-172,75),165)
print("PRODUCT_RENDERS_COMPLETE")
