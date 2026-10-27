import argparse
import hashlib
import json
import math
import struct
from pathlib import Path
import cadquery as cq
import numpy as np
from OCP.BRepBndLib import BRepBndLib
from OCP.Bnd import Bnd_Box

p = argparse.ArgumentParser()
p.add_argument('--base', default=str(Path(__file__).with_name('01_bank_cradle_original.step')))
p.add_argument('--out', default=str(Path(__file__).resolve().parents[1] / 'cad'))
a = p.parse_args()
basepath = Path(a.base).resolve()
out = Path(a.out).resolve()
out.mkdir(parents=True, exist_ok=True)
base = cq.importers.importStep(str(basepath)).val()
D = 2.4

def xyz(p, z=0):
    return cq.Vector(-(p[0]-720)/10.2, (520-p[1])/10.08, z)

def loop(start, segments):
    edges = []
    current = start
    for segment in segments:
        if len(segment) == 2:
            edges.append(cq.Edge.makeLine(xyz(current), xyz(segment)))
            current = segment
        else:
            controls = [current] + [segment[i:i+2] for i in range(0, 6, 2)]
            edges.append(cq.Edge.makeBezier([xyz(v) for v in controls]))
            current = segment[-2:]
    if tuple(current) != tuple(start):
        edges.append(cq.Edge.makeLine(xyz(current), xyz(start)))
    wire = cq.Wire.assembleEdges(edges)
    face = cq.Face.makeFromWires(wire)
    assert face.isValid()
    return face

paths = [
    ('left_slender', (325, 258), [(378,258), (396,258,399,265,396,286), (363,542), (359,582,342,606,310,649), (296,669,291,669,291,645), (291,303), (291,275,303,258,325,258)]),
    ('upper_left', (485,258), [(546,258), (560,258,567,265,570,282), (585,386), (591,430,583,449,555,468), (464,523), (443,536,431,529,433,507), (453,283), (455,265,464,258,485,258)]),
    ('upper_middle', (650,258), [(737,258), (756,258,764,264,769,282), (789,365), (799,408,813,427,844,433), (910,445), (938,450,945,462,936,486), (929,508,918,529,899,528), (886,529,871,523,853,516), (677,447), (650,436,644,423,638,395), (626,286), (622,266,631,258,650,258)]),
    ('upper_right', (859,258), [(1095,258), (1133,258,1146,270,1146,301), (1145,397), (1145,415,1139,420,1122,418), (885,395), (860,393,851,382,846,361), (832,283), (829,263,836,258,859,258)]),
    ('lower_left', (329,782), [(440,782), (460,782,465,775,463,755), (454,648), (452,623,443,614,427,621), (413,626,403,637,391,651), (310,746), (295,766,301,782,329,782)]),
    ('lower_middle_left', (529,782), [(552,782), (567,782,572,775,579,756), (619,667), (627,648,642,641,663,636), (825,594), (848,588,851,577,831,568), (650,506), (631,499,617,496,599,505), (525,550), (507,560,501,576,505,603), (517,763), (518,777,521,782,529,782)]),
    ('lower_middle_right', (656,782), [(981,782), (1002,782,1008,774,996,754), (945,659), (933,638,923,629,905,632), (682,674), (661,678,651,689,645,709), (635,755), (630,775,635,782,656,782)]),
    ('lower_right', (1031,464), [(1124,480), (1141,484,1146,492,1146,511), (1146,720), (1146,749,1136,770,1117,779), (1103,785,1094,778,1084,761), (989,592), (976,568,973,552,980,525), (989,488), (994,468,1008,460,1031,464)])
]
faces = [(name, loop(start, segments)) for name,start,segments in paths]
panel = cq.Workplane('XY').box(87,55,D,centered=(True,True,False)).edges('|Z').fillet(7.5).val()
cutters = [cq.Solid.extrudeLinear(face.outerWire(),[],cq.Vector(0,0,D)) for _,face in faces]
web = panel.cut(*cutters).clean()
result = base.fuse(web).clean()
assert result.isValid() and len(result.Solids()) == 1
outer_edges = [edge for edge in result.Edges() if max(abs(edge.BoundingBox().zmin),abs(edge.BoundingBox().zmax))<.0001 and (abs(edge.Center().y)>33 or abs(edge.Center().x)>48)]
result = result.chamfer(.3,None,outer_edges).clean()
assert result.isValid() and len(result.Solids()) == 1
rear_treatment_removed=base.cut(result)
before_branding = result

def word(text, height, pitch, y):
    pieces=[]
    for i,ch in enumerate(text):
        part = cq.Workplane('XY').text(ch,height,.3,fontPath=str(Path(__file__).with_name('fonts')/'DejaVuSans-Bold.ttf'),kind='bold',halign='center',valign='center',combine=False).val()
        part = part.translate(((i-(len(text)-1)/2)*pitch,0,0))
        part = part.rotate((0,0,0),(0,1,0),180).translate((0,y,.3))
        pieces.extend(part.Solids())
    return cq.Compound.makeCompound(pieces)

letters = cq.Compound.makeCompound([word('finne',3.5,2.55,30.5),word('ENTROPI',2.7,2.55,-30.4)])
removed_branding = result.intersect(letters)
result = result.cut(letters).clean()
assert result.isValid() and len(result.Solids()) == 1

def bounds(q):
    b=Bnd_Box()
    BRepBndLib.AddOptimal_s(q.wrapped,b,False,False)
    return list(b.Get())

def mesh_check(path):
    data=path.read_bytes();count=struct.unpack_from('<I',data,80)[0]
    dtype=np.dtype([('normal','<f4',3),('vertices','<f4',(3,3)),('attr','<u2')])
    vertices=np.frombuffer(data,dtype=dtype,offset=84,count=count)['vertices'].astype(float)
    unique,indices=np.unique(vertices.reshape(-1,3),axis=0,return_inverse=True)
    faces=indices.reshape(-1,3)
    edges=np.sort(np.vstack([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1)
    _,counts=np.unique(edges,axis=0,return_counts=True)
    degenerates=int(np.sum(np.linalg.norm(np.cross(vertices[:,1]-vertices[:,0],vertices[:,2]-vertices[:,0]),axis=1)<1e-8))
    bad=int(np.sum(counts!=2))
    volume=float(np.sum(np.einsum('ij,ij->i',vertices[:,0],np.cross(vertices[:,1],vertices[:,2])))/6)
    assert bad==0 and degenerates==0 and volume>0
    return {'triangles':count,'nonmanifold_or_boundary_edges':bad,'degenerate_triangles':degenerates,'signed_volume_mm3':volume,'mesh_bounds_mm':vertices.reshape(-1,3).min(0).tolist()+vertices.reshape(-1,3).max(0).tolist()}

step=out/'01_backcase.step';stl=out/'01_backcase.stl'
cq.exporters.export(result,str(step))
roundtrip = cq.importers.importStep(str(step)).val()
assert roundtrip.isValid() and len(roundtrip.Solids())==1
assert abs(roundtrip.Volume()-result.Volume())<.001
cq.exporters.export(result,str(stl),tolerance=.018,angularTolerance=.07)
mesh=mesh_check(stl)
source_removed = base.cut(result)
functional_zone=cq.Workplane('XY').box(200,200,100,centered=(True,True,False)).translate((0,0,.301)).val()
functional_removed=source_removed.intersect(functional_zone).Volume()
rear_unintended_removed = source_removed.cut(letters).cut(rear_treatment_removed).Volume()
assert functional_removed<1e-6 and rear_unintended_removed<1e-6
distances=[]
for i,(name,face) in enumerate(faces):
    for name2,face2 in faces[i+1:]:
        distances.append({'between':[name,name2],'distance_mm':face.distance(face2)})
minimum=min(distances,key=lambda item:item['distance_mm'])
assert minimum['distance_mm']>3.6
bank=cq.Workplane('XY').box(94,62,15,centered=(True,True,False)).edges('|Z').fillet(4.1).translate((0,0,2.8)).val()
added=result.cut(base)
bank_collision=result.intersect(bank).Volume()
assert bank_collision<1e-6
assert abs(bounds(added)[5]-D)<.001
report={'version':'selected_asymmetric_backcase','reference_image':'signal-2026-10-27-224818.jpeg','source_step_sha256':hashlib.sha256(basepath.read_bytes()).hexdigest(),'units':'mm','solid_count':len(result.Solids()),'solid_valid':result.isValid(),'volume_mm3':result.Volume(),'bounds_mm':bounds(result),'original_volume_mm3':base.Volume(),'added_volume_mm3':added.Volume(),'original_geometry_removed_mm3':source_removed.Volume(),'removed_material_purpose':'Rear exposed perimeter and opening-edge chamfers plus recessed branding, all within Z0..0.3 mm','unintended_original_geometry_removed_mm3':rear_unintended_removed,'functional_geometry_removed_above_z_0_301_mm3':functional_removed,'rear_web_thickness_mm':D,'cutout_count':len(faces),'hole_construction':'Closed cubic Bezier analytic CAD wires traced from selected reference; mm scale retains original cradle interfaces','rear_edge_chamfer_mm':.3,'minimum_web_width_between_cutouts':minimum,'minimum_web_at_rear_chamfer_mm':minimum['distance_mm']-.6,'cutout_pair_clearances':distances,'original_window_mm':[84,52,6],'brand_engrave_depth_mm':.3,'brand_text':['finne','ENTROPI'],'bank_envelope_mm':[94,62,15],'bank_start_z_mm':2.8,'bank_collision_mm3':bank_collision,'added_web_to_bank_clearance_mm':added.distance(bank),'bank_to_original_rear_lip_clearance_mm':.2,'hardware_dimensions':'Nominal existing design values, not newly measured','print_orientation':{'description':'Rear face on bed, cavity/forks up, identical to assembly coordinates','transform_4x4':[[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]],'file':'01_backcase.stl'},'mesh_check':mesh,'step_sha256':hashlib.sha256(step.read_bytes()).hexdigest(),'stl_sha256':hashlib.sha256(stl.read_bytes()).hexdigest(),'physical_fit_verified':False,'slicer_verified':False,'status':'CAD and mesh digitally validated; slicing and physical first-article fit remain separate gates'}
(out.parent/'reports'/'backcase-geometry.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
