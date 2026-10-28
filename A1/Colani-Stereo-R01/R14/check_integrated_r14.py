import bpy,bmesh,json,os
base=os.path.dirname(os.path.abspath(__file__))
model=os.path.join(base,"R14","Colani_R14_Integrated_Assembly.blend")
bpy.ops.wm.open_mainfile(filepath=model)
reference=bpy.data.objects["Tripo_organic_scaled_reference"]
shells=[bpy.data.objects["P01_front_Tripo_R12"],bpy.data.objects["P02_back_Tripo_R12"]]
def volume(o):
    bm=bmesh.new()
    bm.from_mesh(o.data)
    res=abs(bm.calc_volume(signed=True))
    bm.free()
    return res
def intersect_volume(obj,other,operation):
    cp=obj.copy()
    cp.data=obj.data.copy()
    bpy.context.collection.objects.link(cp)
    bpy.context.view_layer.objects.active=cp
    modifier=cp.modifiers.new("QA","BOOLEAN")
    modifier.operation=operation
    modifier.solver="EXACT"
    modifier.object=other
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    v=volume(cp)
    bpy.data.objects.remove(cp,do_unlink=True)
    return v
names=["REF_Linocell_5000mAh","REF_ESP32_CAM_L","REF_ESP32_CAM_R","P03_cradle_wall_-33.1","P03_cradle_wall_33.1","P04_vertical_0"]
ans={}
for name in names:
    obj=bpy.data.objects[name]
    v=volume(obj)
    outside=intersect_volume(obj,reference,"DIFFERENCE")
    shell_overlap=[intersect_volume(obj,sh,"INTERSECT") for sh in shells]
    ans[name]={"nominal_volume_mm3":round(v,1),"outside_envelope_mm3":round(outside,1),"intersection_with_shell_mm3":[round(x,1) for x in shell_overlap]}
report={"source":"Tripo R12 shell + nominal R13 reconstructed for R14 preview","valid_for":"static solid intersections only","tested":ans}
dest=os.path.join(base,"R14","mechanical_interferences.json")
open(dest,"w").write(json.dumps(report,indent=2))
print("INTERFERENCE_RESULTS",json.dumps(report))
