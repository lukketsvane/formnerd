import bpy
import bmesh
import json
from pathlib import Path
from mathutils import Vector

root=Path(r"C:\Users\Iver\Documents\github\formnerd\A4\Entropi-Tripo-R08")
names=["A0_Tripo_quads_organic_front"]+["tripo_part_"+str(i) for i in range(1,11)]
inserts=["P1_BATTERY_RING","P2_ESP32_BRACKET","P3_ESP32_BRACKET"]
refs=["REF_Linocell_94x62x15","REF_ESP32_CAM_1","REF_ESP32_CAM_2"]

def aabb(obj):
    pts=[obj.matrix_world@Vector(corner) for corner in obj.bound_box]
    return [(min(v[k] for v in pts),max(v[k] for v in pts)) for k in range(3)]

def near(a,b):
    return all(max(x[0],y[0]) < min(x[1],y[1])-0.0001 for x,y in zip(aabb(a),aabb(b)))

def select(o):
    bpy.ops.object.select_all(action="DESELECT")
    o.hide_set(False)
    o.select_set(True)
    bpy.context.view_layer.objects.active=o

def intersection(a,b):
    if not near(a,b):
        return 0.0,0
    o=a.copy()
    o.data=a.data.copy()
    o.name="_temp_intersection"
    bpy.context.scene.collection.objects.link(o)
    select(o)
    for prior in list(o.modifiers):
        bpy.ops.object.modifier_apply(modifier=prior.name)
    m=o.modifiers.new("_intersect","BOOLEAN")
    m.operation="INTERSECT"
    m.solver="EXACT"
    m.object=b
    bpy.ops.object.modifier_apply(modifier=m.name)
    bm=bmesh.new()
    bm.from_mesh(o.data)
    vol=abs(bm.calc_volume(signed=True)) if bm.faces else 0
    nm=sum(not e.is_manifold for e in bm.edges)
    bm.free()
    bpy.data.objects.remove(o,do_unlink=True)
    return round(vol,3),nm

pairs=[]
checked=0
for a in names+inserts:
    for b in inserts+refs:
        if a==b or (a in inserts and b in inserts and a>b):
            continue
        checked+=1
        v,n=intersection(bpy.data.objects[a],bpy.data.objects[b])
        if v>.01 or n>0:
            pairs.append({"first":a,"second":b,"volume_mm3":v,"nonmanifold_edges":n})
result={"checked_pairs":checked,"collision_count":len(pairs),"intersection_results":pairs,"threshold_mm3":.01}
(root/"qa/collisions.json").write_text(json.dumps(result,indent=2))
print("COLLISION_QA",json.dumps(result))