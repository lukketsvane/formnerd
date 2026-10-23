import bpy, os, sys, json
from mathutils import Vector
base=os.path.dirname(os.path.abspath(__file__))
source=sys.argv[sys.argv.index("--")+1] if "--" in sys.argv else os.path.join(base,"tripo","Colani_Lady_Tripo_H31_Master.glb")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=source)
objs=[o for o in bpy.context.scene.objects if o.type=="MESH"]
minimum=[float("inf")]*3
maximum=[float("-inf")]*3
parts=[]
for o in objs:
    mesh=o.data
    verts=[o.matrix_world @ Vector(corner) for corner in o.bound_box]
    for v in verts:
        for i in range(3):
            minimum[i]=min(minimum[i],v[i])
            maximum[i]=max(maximum[i],v[i])
    parts.append({"name":o.name,"vertices":len(mesh.vertices),"triangles":sum(len(p.vertices)-2 for p in mesh.polygons),"materials":[m.name for m in mesh.materials]})
data={"source":os.path.basename(source),"source_file_bytes":os.path.getsize(source),"objects":parts,"bbox_units":[round(v,5) for v in [maximum[i]-minimum[i] for i in range(3)]],"bbox_minimum":minimum,"bbox_maximum":maximum,"coordinate_units_unverified":True}
out=os.path.join(base,"tripo","blender_inspection_"+os.path.splitext(os.path.basename(source))[0]+".json")
with open(out,"w",encoding="utf-8") as f:json.dump(data,f,indent=2)
print("TRIPO_INSPECT",json.dumps({"meshes":len(objs),"triangles":sum(x["triangles"] for x in parts),"bbox":data["bbox_units"],"output":out}))
