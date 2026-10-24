import os,sys,struct,zipfile,xml.etree.ElementTree as ET,json
from pathlib import Path
root=Path(__file__).resolve().parent
out=root/"print"
NS="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
ET.register_namespace("",NS)
def convert(stl,filename):
    with open(stl,"rb") as f:data=f.read()
    faces,=struct.unpack_from("<I",data,80)
    assert 84+faces*50==len(data)
    verts={}
    triangles=[]
    for face in range(faces):
        offset=84+face*50
        tri=[]
        for n in range(3):
            key=data[offset+12+n*12:offset+24+n*12]
            idx=verts.get(key)
            if idx is None:
                idx=len(verts)
                verts[key]=idx
            tri.append(idx)
        triangles.append(tri)
    model=ET.Element("{%s}model"%NS,{"unit":"millimeter","xml:lang":"en-US"})
    res=ET.SubElement(model,"{%s}resources"%NS)
    obj=ET.SubElement(res,"{%s}object"%NS,{"id":"1","type":"model","name":stl.stem})
    mesh=ET.SubElement(obj,"{%s}mesh"%NS)
    vv=ET.SubElement(mesh,"{%s}vertices"%NS)
    for key in verts:
        x,y,z=struct.unpack("<fff",key)
        ET.SubElement(vv,"{%s}vertex"%NS,{"x":format(x,'.7g'),"y":format(y,'.7g'),"z":format(z,'.7g')})
    tt=ET.SubElement(mesh,"{%s}triangles"%NS)
    for a,b,c in triangles:
        ET.SubElement(tt,"{%s}triangle"%NS,{"v1":str(a),"v2":str(b),"v3":str(c)})
    build=ET.SubElement(model,"{%s}build"%NS)
    ET.SubElement(build,"{%s}item"%NS,{"objectid":"1","transform":"1 0 0 0 1 0 0 0 1 128 128 0"})
    xml=ET.tostring(model,encoding="utf-8",xml_declaration=True)
    cont=b'<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>'
    rels=b'<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>'
    with zipfile.ZipFile(filename,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.writestr("[Content_Types].xml",cont)
        z.writestr("_rels/.rels",rels)
        z.writestr("3D/3dmodel.model",xml)
    with zipfile.ZipFile(filename) as z:
        data=z.read("3D/3dmodel.model")
        rootxml=ET.fromstring(data)
        assert len(rootxml.findall(".//{%s}triangle"%NS))==faces
    print(json.dumps({"file":str(filename),"faces":faces,"vertices":len(verts),"bytes":filename.stat().st_size}))
for a in ["P01_front_Tripo_R12_P1S","P02_back_Tripo_R12_P1S"]:
    convert(out/(a+".stl"),out/(a+".3mf"))
