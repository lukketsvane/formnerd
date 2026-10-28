import bpy,bmesh,math,os,json
from mathutils import Vector
root=os.path.dirname(os.path.abspath(__file__))
dest=os.path.join(root,"R12")
os.makedirs(dest,exist_ok=True)
source=os.path.join(root,"tripo","Colani_Lady_repaired_unscaled.stl")
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.wm.stl_import(filepath=source)
master=next(o for o in bpy.context.scene.objects if o.type=="MESH")
master.name="Tripo_organic_scaled_reference"
W,H,D=96.0,145.0,46.0
verts=master.data.vertices
lo=[min(v.co[i] for v in verts) for i in range(3)]
hi=[max(v.co[i] for v in verts) for i in range(3)]
scale=[W/(hi[0]-lo[0]),D/(hi[1]-lo[1]),H/(hi[2]-lo[2])]
for v in verts:
    for i in range(3):v.co[i]=(v.co[i]-(lo[i]+hi[i])/2)*scale[i]
master.data.update()
bpy.context.view_layer.objects.active=master
bpy.ops.object.select_all(action="DESELECT")
master.select_set(True)
master.data.remesh_voxel_size=0.65
bpy.ops.object.voxel_remesh()
def bbox(obj):
    p=[v.co for v in obj.data.vertices]
    return [round(max(v[i] for v in p)-min(v[i] for v in p),2) for i in range(3)]
def qa(obj):
    bm=bmesh.new();bm.from_mesh(obj.data)
    result={"faces":len(bm.faces),"verts":len(bm.verts),"boundary_edges":sum(e.is_boundary for e in bm.edges),"irregular_edges":sum(not e.is_manifold for e in bm.edges),"volume_mm3":round(abs(bm.calc_volume(signed=True)),1),"bbox_mm":bbox(obj)}
    bm.free();return result
masterqa=qa(master)
def cut_half(front):
    obj=master.copy();obj.data=master.data.copy()
    bpy.context.collection.objects.link(obj)
    obj.name="P01_front_Tripo_R12" if front else "P02_back_Tripo_R12"
    bm=bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.bisect_plane(
        bm,
        geom=list(bm.verts)+list(bm.edges)+list(bm.faces),
        plane_co=(0,0,0),
        plane_no=(0,1,0),
        dist=0.0001,
        clear_outer=front,
        clear_inner=not front
    )
    removed=sum(e.is_boundary for e in bm.edges)
    print("BISECT_QA",obj.name,len(bm.faces),removed)
    if not bm.faces or not removed:
        raise RuntimeError("Bisect did not open shell")
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    print("SPLIT_BEFORE_SOLIDIFY",obj.name,qa(obj))
    bpy.context.view_layer.objects.active=obj
    bpy.ops.object.select_all(action="DESELECT");obj.select_set(True)
    solid=obj.modifiers.new("ShellWall","SOLIDIFY")
    solid.thickness=2.4;solid.offset=-1.0;solid.use_even_offset=False
    bpy.ops.object.modifier_apply(modifier=solid.name)
    print("SPLIT_AFTER_SOLIDIFY",obj.name,qa(obj))
    obj.data.remesh_voxel_size=0.5
    bpy.ops.object.voxel_remesh()
    print("SPLIT_AFTER_VOXEL",obj.name,qa(obj))
    return obj,removed
front,nf=cut_half(True)
back,nb=cut_half(False)
master.hide_render=True
master.hide_set(True)
for xc in (-14.75,14.75):
    bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=4.3,depth=90,location=(xc,-35,-24),rotation=(math.pi/2,0,0))
    cutter=bpy.context.object
    bpy.context.view_layer.objects.active=front
    mod=front.modifiers.new("OpticalPort","BOOLEAN")
    mod.operation="DIFFERENCE";mod.solver="EXACT";mod.object=cutter
    bpy.ops.object.modifier_apply(modifier=mod.name)
    print("AFTER_LENS_PORT",xc,qa(front))
    bpy.data.objects.remove(cutter,do_unlink=True)
result={"source":source,"scaled_outer_mm":[W,H,D],"wall_nominal_mm":2.4,"stereo_holes_mm":[[-14.75,-24,8.6],[14.75,-24,8.6]],"seam_faces_removed":{"front":nf,"back":nb},"master":masterqa,"parts":{}}
for obj in [front,back]:
    bpy.ops.object.select_all(action="DESELECT");obj.hide_set(False);obj.select_set(True)
    bpy.context.view_layer.objects.active=obj
    f=os.path.join(dest,obj.name+".stl")
    bpy.ops.wm.stl_export(filepath=f,export_selected_objects=True,ascii_format=False)
    result["parts"][obj.name]={"path":f,**qa(obj)}
blend=os.path.join(dest,"Colani_R12_Tripo_geometry.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend)
with open(os.path.join(dest,"R12_geometry_qa.json"),"w") as f:json.dump(result,f,indent=2)
print("R12_GEOMETRY_QA",json.dumps(result))
