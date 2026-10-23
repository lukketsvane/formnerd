import bpy,bmesh,os,glob,json
root=os.path.dirname(os.path.abspath(__file__))
p=glob.glob(os.path.join(root,"tripo","fbx","*.fbx"))[0]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=p)
report={"source":p,"parts":[]}
for o in bpy.context.scene.objects:
    if o.type!="MESH":continue
    b=bmesh.new();b.from_mesh(o.data)
    raw={"faces":len(b.faces),"verts":len(b.verts),"quads":sum(len(f.verts)==4 for f in b.faces),"tris":sum(len(f.verts)==3 for f in b.faces),"edges_open":sum(e.is_boundary for e in b.edges),"edges_nonmanifold":sum(not e.is_manifold for e in b.edges)}
    bmesh.ops.remove_doubles(b,verts=list(b.verts),dist=0.000001)
    report["parts"].append({"name":o.name, "raw":raw,"welded_verts":len(b.verts),"welded_boundary_edges":sum(e.is_boundary for e in b.edges),"welded_nonmanifold_edges":sum(not e.is_manifold for e in b.edges)})
    b.free()
out=os.path.join(root,"tripo","fbx","qa_fbx_quads.json")
with open(out,"w") as f:json.dump(report,f,indent=2)
print("FBX_QUAD_QA",json.dumps(report))
