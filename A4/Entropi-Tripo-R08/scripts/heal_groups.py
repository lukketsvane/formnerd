import bpy
import bmesh
import json
from pathlib import Path
root=Path(r"C:\Users\Iver\Documents\github\formnerd\A4\Entropi-Tripo-R08")
names={"A_WHITE_TRIPO_RIB_SHELL":.38,"B_BLACK_TRIPO_BACK":.42,"C_TRIPO_OPTIC":.35}
for name,voxel in names.items():
    o=bpy.data.objects[name]
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active=o
    o.data.remesh_voxel_size=voxel
    bpy.ops.object.voxel_remesh()
    bm=bmesh.new()
    bm.from_mesh(o.data)
    bad=sum(not e.is_manifold for e in bm.edges)
    seen=set()
    count=0
    for start in bm.verts:
        if start in seen:continue
        count+=1
        stack=[start]
        seen.add(start)
        while stack:
            for e in stack.pop().link_edges:
                v=e.other_vert(start) if False else None
                for v in e.verts:
                    if v not in seen:
                        seen.add(v)
                        stack.append(v)
    bm.free()
    print("VOXEL",json.dumps({"name":name,"voxel_mm":voxel,"faces":len(o.data.polygons),"nonmanifold_edges":bad,"shells":count}))
for o in bpy.data.objects:
    if o.type=="MESH":o.hide_render=o.name not in list(names)+["D_LEFT_TOP_BUTTON","E_RIGHT_TOP_BUTTON"]
sc=bpy.context.scene
sc.render.filepath=str(root/"render/30_healed_Tripo_parts.png")
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(root/"ENTROPI_Tripo_HEALED_R08.blend"))