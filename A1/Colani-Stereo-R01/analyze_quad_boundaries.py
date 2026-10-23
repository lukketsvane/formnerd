import bpy,bmesh,os,glob,json
from collections import defaultdict,deque
from mathutils import Vector
base=os.path.dirname(os.path.abspath(__file__))
p=glob.glob(os.path.join(base,"tripo","fbx","*.fbx"))[0]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=p)
o=next(ob for ob in bpy.context.scene.objects if ob.type=="MESH")
mesh=o.data
b=bmesh.new();b.from_mesh(mesh);b.verts.ensure_lookup_table()
bound=[e for e in b.edges if e.is_boundary]
nonman=[e for e in b.edges if (not e.is_manifold and not e.is_boundary)]
adj=defaultdict(list)
for e in bound:
    for v in e.verts: adj[v.index].append(e)
remaining=set(id(e) for e in bound)
edge_by_id={id(e):e for e in bound}
groups=[]
while remaining:
    one=edge_by_id[next(iter(remaining))]
    stack=[one]
    visited_e=set()
    pts=[]
    while stack:
        e=stack.pop()
        if id(e) in visited_e: continue
        visited_e.add(id(e));remaining.discard(id(e))
        for v in e.verts:
            pts.append(o.matrix_world@v.co)
            for ee in adj[v.index]:
                if id(ee) not in visited_e:stack.append(ee)
    mins=[min(pt[i] for pt in pts) for i in range(3)]
    maxs=[max(pt[i] for pt in pts) for i in range(3)]
    groups.append({"edge_count":len(visited_e),"bbox_min":mins,"bbox_max":maxs})
r={"boundary_groups":sorted(groups,key=lambda a:-a["edge_count"]),"edges_nonmanifold_interior":len(nonman),"interior_nonmanifold_edges":[[[float((o.matrix_world@v.co)[i]) for i in range(3)] for v in e.verts] for e in nonman[:8]]}
path=os.path.join(base,"tripo","fbx","boundary_regions.json")
with open(path,"w") as f:json.dump(r,f,indent=2)
print("BOUNDARY_REGIONS",json.dumps(r)[:5000])
b.free()
