import json
from pathlib import Path
import struct
import cadquery as cq
import numpy as np

ROOT=Path(__file__).resolve().parents[1]


def topology(points, triangles):
    points,inverse=np.unique(points,axis=0,return_inverse=True)
    triangles=inverse[triangles]
    edges=np.concatenate((triangles[:,[0,1]],triangles[:,[1,2]],triangles[:,[2,0]]))
    _,counts=np.unique(np.sort(edges,axis=1),axis=0,return_counts=True)
    bad=int(np.count_nonzero(counts!=2))
    return {'vertices':len(points),'triangles':len(triangles),'boundary_or_nonmanifold_edges':bad,'closed':bad==0}


def main():
    data=(ROOT/'Entropi-assembly-v05.glb').read_bytes()
    length=struct.unpack_from('<I',data,12)[0]
    doc=json.loads(data[20:20+length])
    binary=data[28+length:]
    types={5121:np.dtype('u1'),5123:np.dtype('<u2'),5125:np.dtype('<u4'),5126:np.dtype('<f4')}
    widths={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}
    def accessor(index):
        a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
        dtype=types[a['componentType']];width=widths[a['type']]
        offset=v.get('byteOffset',0)+a.get('byteOffset',0)
        stride=v.get('byteStride',width*dtype.itemsize)
        return np.ndarray((a['count'],width),dtype=dtype,buffer=binary,offset=offset,strides=(stride,dtype.itemsize)).copy()
    transforms={}
    def visit(index,parent):
        node=doc['nodes'][index]
        if 'matrix' in node:
            local=np.array(node['matrix']).reshape((4,4),order='F')
        else:
            x,y,z,w=node.get('rotation',[0,0,0,1])
            rotation=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
            local=np.eye(4)
            local[:3,:3]=rotation@np.diag(node.get('scale',[1,1,1]))
            local[:3,3]=node.get('translation',[0,0,0])
        world=parent@local
        transforms[index]=world
        for child in node.get('children',[]):
            visit(child,world)
    for scene in doc['scenes']:
        for index in scene['nodes']:
            visit(index,np.eye(4))
    mesh_nodes=[(i,n) for i,n in enumerate(doc['nodes']) if 'mesh' in n]
    rows=[];all_points=[]
    for node_index,node in mesh_nodes:
        points=[];triangles=[];offset=0
        for primitive in doc['meshes'][node['mesh']]['primitives']:
            p=accessor(primitive['attributes']['POSITION'])
            t=accessor(primitive['indices']).astype(np.int64).reshape(-1,3)+offset
            points.append(p);triangles.append(t);offset+=len(p)
        p=np.concatenate(points);t=np.concatenate(triangles)
        homogeneous=np.column_stack((p,np.ones(len(p))))
        all_points.append((homogeneous@transforms[node_index].T)[:,:3])
        rows.append({'name':node['name'],**topology(p,t)})
    roots=[doc['nodes'][index] for scene in doc['scenes'] for index in scene['nodes']]
    scales=[root.get('scale') for root in roots]
    metallic=[m.get('pbrMetallicRoughness',{}).get('metallicFactor',1) for m in doc['materials']]
    step=cq.importers.importStep(str(ROOT/'Entropi-assembly-v05.step')).val();b=step.BoundingBox()
    native_size=[b.xlen,b.ylen,b.zlen]
    vertices=np.concatenate(all_points)
    mesh_size=(vertices.max(0)-vertices.min(0)).astype(float).tolist()
    passed=len(mesh_nodes)==18 and all(row['closed'] for row in rows) and all(scale==[.001,.001,.001] for scale in scales) and all(value==0 for value in metallic) and step.isValid() and len(step.Solids())==18 and np.allclose(np.array(native_size)[[0,2,1]]*.001,mesh_size,atol=.0001)
    report={'assembly_step_valid':step.isValid(),'assembly_step_solids':len(step.Solids()),'native_size_mm':native_size,'glb_world_size_m':mesh_size,'glb_meshes':rows,'glb_root_scale':scales,'glb_root_rotation':[r.get('rotation') for r in roots],'all_materials_nonmetallic':all(value==0 for value in metallic),'export_pass':bool(passed)}
    (ROOT/'cad/export_verification.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report),flush=True)
    if not passed:
        raise SystemExit(1)


if __name__=='__main__':
    main()
