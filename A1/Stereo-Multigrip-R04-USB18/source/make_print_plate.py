"""Pack binary STL parts into a standards-based, unsliced 3MF build layout.

This intentionally contains no guessed filament, nozzle, heater or machine
commands. Import into Bambu Studio, choose the actual printer/material, slice.
"""
from pathlib import Path
import argparse, struct, json, zipfile, math
import xml.etree.ElementTree as ET
from xml.parsers import expat

NS='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
REL='http://schemas.openxmlformats.org/package/2006/relationships'
CT='http://schemas.openxmlformats.org/package/2006/content-types'
ET.register_namespace('',NS)

def read_stl(p):
    b=p.read_bytes();n=struct.unpack_from('<I',b,80)[0]
    assert len(b)==84+50*n, f'Not binary STL: {p}'
    verts=[];tris=[];lookup={}
    for i in range(n):
        a=struct.unpack_from('<12fH',b,84+50*i)
        ids=[]
        for k in (3,6,9):
            key=tuple(round(x,6) for x in a[k:k+3])
            if key not in lookup:lookup[key]=len(verts);verts.append(key)
            ids.append(lookup[key])
        tris.append(tuple(ids))
    mins=[min(v[i] for v in verts) for i in range(3)]
    maxs=[max(v[i] for v in verts) for i in range(3)]
    verts=[(x,y,max(0,z-mins[2])) for x,y,z in verts]
    vol=sum(sum(verts[a][i]*(verts[b][(i+1)%3]*verts[c][(i+2)%3]-verts[b][(i+2)%3]*verts[c][(i+1)%3]) for i in range(3)) for a,b,c in tris)/6
    assert vol>0,(p,'negative or empty mesh')
    return {'name':p.stem,'path':str(p),'vertices':verts,'triangles':tris,'mins':mins,'maxs':maxs,'size':[maxs[i]-mins[i] for i in range(3)],'volume':vol}

def make(parts,out,title,bed=256,margin=16,gap=8):
    items=sorted([read_stl(p) for p in parts],key=lambda i:(-i['size'][1],-i['size'][0]))
    x=y=margin;row=0;bounds=[]
    for item in items:
        w,h,d=item['size']
        if x+w>bed-margin:x=margin;y+=row+gap;row=0
        assert y+h<=bed-margin,(item['name'],'does not fit plate')
        item['translation']=[x-item['mins'][0],y-item['mins'][1],0]
        bounds.append([x,y,x+w,y+h]);x+=w+gap;row=max(row,h)
    # Every model stays away from bed edges and neighbours at bounding-box level.
    for i,a in enumerate(bounds):
        for b in bounds[i+1:]:assert a[2]<=b[0] or b[2]<=a[0] or a[3]<=b[1] or b[3]<=a[1]
    model=ET.Element(f'{{{NS}}}model',{'unit':'millimeter','{http://www.w3.org/XML/1998/namespace}lang':'en-US'})
    for name,value in [('Title',title),('Application','CadQuery solid export / 3MF Core layout'),('Description','UNSLICED fit-test layout. No machine commands or filament temperatures. Verify supports, current nozzle, filament and bed in Bambu Studio before printing.')]:
        ET.SubElement(model,f'{{{NS}}}metadata',{'name':name}).text=value
    resources=ET.SubElement(model,f'{{{NS}}}resources')
    build=ET.SubElement(model,f'{{{NS}}}build')
    for id,item in enumerate(items,1):
        obj=ET.SubElement(resources,f'{{{NS}}}object',{'id':str(id),'type':'model','name':item['name']})
        mesh=ET.SubElement(obj,f'{{{NS}}}mesh');vs=ET.SubElement(mesh,f'{{{NS}}}vertices');ts=ET.SubElement(mesh,f'{{{NS}}}triangles')
        for v in item['vertices']:ET.SubElement(vs,f'{{{NS}}}vertex',{k:f'{n:.6f}' for k,n in zip('xyz',v)})
        for t in item['triangles']:ET.SubElement(ts,f'{{{NS}}}triangle',{k:str(n) for k,n in zip(('v1','v2','v3'),t)})
        tx,ty,tz=item['translation']
        ET.SubElement(build,f'{{{NS}}}item',{'objectid':str(id),'transform':f'1 0 0 0 1 0 0 0 1 {tx:.6f} {ty:.6f} {tz:.6f}'})
    content=ET.Element(f'{{{CT}}}Types')
    ET.SubElement(content,f'{{{CT}}}Default',{'Extension':'rels','ContentType':'application/vnd.openxmlformats-package.relationships+xml'})
    ET.SubElement(content,f'{{{CT}}}Default',{'Extension':'model','ContentType':'application/vnd.ms-package.3dmanufacturing-3dmodel+xml'})
    rels=ET.Element(f'{{{REL}}}Relationships')
    ET.SubElement(rels,f'{{{REL}}}Relationship',{'Target':'/3D/3dmodel.model','Id':'rel0','Type':'http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel'})
    out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,tree,namespace in [('[Content_Types].xml',content,CT),('_rels/.rels',rels,REL),('3D/3dmodel.model',model,NS)]:
            ET.register_namespace('',namespace)
            z.writestr(name,ET.tostring(tree,encoding='utf-8',xml_declaration=True))
    with zipfile.ZipFile(out) as z:
        assert z.testzip() is None
        for name in z.namelist():ET.fromstring(z.read(name))
        for name,root_tag,child_tag in [('[Content_Types].xml','Types','Default'),('_rels/.rels','Relationships','Relationship'),('3D/3dmodel.model','model','object')]:
            tags=[];parser=expat.ParserCreate()
            parser.StartElementHandler=lambda tag,attrs:tags.append(tag)
            parser.Parse(z.read(name),True)
            assert tags[0]==root_tag and child_tag in tags,(name,'prefixed or missing package elements')
    report={'file':str(out),'type':'unsliced 3MF Core build layout','bed_mm':[bed,bed],'margin_mm':margin,'gap_mm':gap,'parts':[{'name':i['name'],'size_mm':i['size'],'translation_mm':i['translation'],'triangles':len(i['triangles'])} for i in items]}
    out.with_suffix('.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({'file':str(out),'objects':len(items),'checks':'ZIP/XML, positive mesh volume, part separation and bed containment passed'}))
    return items

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--output',required=True);a.add_argument('--title',default='Stereo Multigrip print layout');a.add_argument('parts',nargs='+');p=a.parse_args()
    make([Path(x) for x in p.parts],Path(p.output),p.title)
