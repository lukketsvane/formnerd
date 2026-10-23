import bpy, bmesh, json, zipfile
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring
from mathutils import Vector

root=Path(r"C:\Users\Iver\Documents\github\formnerd\A4\Entropi-Tripo-R08")
out=root/"print_tests"
out.mkdir(parents=True,exist_ok=True)
parts=[
  ("01_battery_corner", "P1_BATTERY_RING", (45.5,14.5,65.2),(21,25,21)),
  ("02_esp32_retention", "P2_ESP32_BRACKET",(-29.0,3.3,49.0),(31,13,13)),
]
bpy.ops.object.select_all(action="DESELECT")
for o in bpy.data.objects:
  if o.type=="MESH":o.hide_render=True

objout=[]
records=[]
for n,(name,source,ctr,dims) in enumerate(parts):
    original=bpy.data.objects[source]
    sample=original.copy()
    sample.data=original.data.copy()
    sample.name=name
    bpy.context.scene.collection.objects.link(sample)
    sample.hide_render=False
    bpy.ops.mesh.primitive_cube_add(size=1,location=ctr)
    tool=bpy.context.object
    tool.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    tool.name="_coupon_tool"
    bpy.ops.object.select_all(action="DESELECT")
    sample.select_set(True)
    bpy.context.view_layer.objects.active=sample
    m=sample.modifiers.new("Cut small passform section","BOOLEAN")
    m.operation="INTERSECT"
    m.solver="EXACT"
    m.object=tool
    bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.data.objects.remove(tool,do_unlink=True)
    bm=bmesh.new()
    bm.from_mesh(sample.data)
    bmesh.ops.triangulate(bm,faces=list(bm.faces))
    bm.to_mesh(sample.data)
    bm.free()
    pts=[sample.matrix_world@v.co for v in sample.data.vertices]
    mins=[min(v[i] for v in pts) for i in range(3)]
    maxs=[max(v[i] for v in pts) for i in range(3)]
    offset=Vector(((-30 if n==0 else 30)-(mins[0]+maxs[0])/2, -(mins[1]+maxs[1])/2, -mins[2]))
    for v in sample.data.vertices: v.co+=offset
    objout.append(sample)
    bm=bmesh.new()
    bm.from_mesh(sample.data)
    rec={"name":name,"vertices":len(sample.data.vertices),"triangles":len(sample.data.polygons),"nonmanifold_edges":sum(not e.is_manifold for e in bm.edges),"dimensions_mm":[round(maxs[i]-mins[i],2) for i in range(3)]}
    bm.free()
    records.append(rec)
    bpy.ops.object.select_all(action="DESELECT")
    sample.select_set(True)
    bpy.context.view_layer.objects.active=sample
    bpy.ops.wm.stl_export(filepath=str(out/(name+".stl")),export_selected_objects=True,apply_modifiers=True)

ns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
model=Element("{%s}model"%ns,{"unit":"millimeter","xml:lang":"en-US"})
resources=SubElement(model,"{%s}resources"%ns)
build=SubElement(model,"{%s}build"%ns)
for i,o in enumerate(objout):
    obj=SubElement(resources,"{%s}object"%ns,{"id":str(i+1),"name":o.name,"type":"model"})
    mesh=SubElement(obj,"{%s}mesh"%ns)
    vs=SubElement(mesh,"{%s}vertices"%ns)
    for v in o.data.vertices:
        p=o.matrix_world@v.co
        SubElement(vs,"{%s}vertex"%ns,{"x":str(round(p.x,5)),"y":str(round(p.y,5)),"z":str(round(p.z,5))})
    ts=SubElement(mesh,"{%s}triangles"%ns)
    for poly in o.data.polygons:
        ids=list(poly.vertices)
        SubElement(ts,"{%s}triangle"%ns,{"v1":str(ids[0]),"v2":str(ids[1]),"v3":str(ids[2])})
    SubElement(build,"{%s}item"%ns,{"objectid":str(i+1)})
target=out/"00_FIT_COUPONS_P1S_GEOMETRY_ONLY.3mf"
with zipfile.ZipFile(target,"w",zipfile.ZIP_DEFLATED) as z:
    z.writestr("[Content_Types].xml",'<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    z.writestr("_rels/.rels",'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    z.writestr("3D/3dmodel.model",'<?xml version="1.0" encoding="UTF-8"?>'+tostring(model,encoding="unicode"))
sc=bpy.context.scene
for o in bpy.data.objects:
    if o.type=="MESH":o.hide_render=o not in objout
sc.render.filepath=str(root/"render"/"40_print_fit_coupons.png")
sc.camera.data.ortho_scale=100
sc.camera.location=(90,-100,90)
sc.camera.rotation_euler=(Vector((0,0,5))-sc.camera.location).to_track_quat("-Z","Y").to_euler()
bpy.ops.render.render(write_still=True)
print("COUPON_REPORT",json.dumps(records))
(root/"qa/fit_coupon_qa.json").write_text(json.dumps(records,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(out/"FIT_COUPONS_R08.blend"))