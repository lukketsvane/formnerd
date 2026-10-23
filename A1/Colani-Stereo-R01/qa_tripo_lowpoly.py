import bpy, bmesh, json, os, math
from mathutils import Vector
base=os.path.dirname(os.path.abspath(__file__))
src=os.path.join(base,"tripo","Colani_Lady_Tripo_SmartMesh_10k_Quad.glb")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
objs=[o for o in bpy.context.scene.objects if o.type=="MESH"]
report={"input_file":os.path.basename(src),"meshes":len(objs),"parts":[]}
for o in objs:
    mesh=o.data
    b=bmesh.new()
    b.from_mesh(mesh)
    boundary=sum(1 for e in b.edges if e.is_boundary)
    non_manifold=sum(1 for e in b.edges if not e.is_manifold)
    loose=sum(1 for e in b.edges if e.is_wire)
    faces=len(b.faces)
    triangle_faces=sum(1 for f in b.faces if len(f.verts)==3)
    quad_faces=sum(1 for f in b.faces if len(f.verts)==4)
    bmesh.ops.remove_doubles(b,verts=list(b.verts),dist=0.000001)
    after_boundary=sum(1 for e in b.edges if e.is_boundary)
    after_nonmanifold=sum(1 for e in b.edges if not e.is_manifold)
    report["parts"].append({"mesh":o.name,"verts":len(b.verts),"faces":faces,"triangles":triangle_faces,"quads":quad_faces,"boundary_edges_raw":boundary,"non_manifold_edges_raw":non_manifold,"boundary_edges_welded":after_boundary,"non_manifold_edges_welded":after_nonmanifold,"loose_edges":loose,"watertight_after_weld":after_nonmanifold==0})
    b.free()
out=os.path.join(base,"tripo","lowpoly_mesh_qa.json")
with open(out,"w",encoding="utf-8") as f:json.dump(report,f,indent=2)
print("LOWPOLY_QA",json.dumps(report))
