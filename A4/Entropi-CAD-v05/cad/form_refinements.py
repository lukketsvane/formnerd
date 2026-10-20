import json
import math
import shutil
from pathlib import Path
import tempfile

import cadquery as cq
from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet
from OCP.TColgp import TColgp_Array1OfPnt2d
from OCP.gp import gp_Pnt2d


def _box(x, y, z, width, depth, height):
    return cq.Workplane('XY').box(width, depth, height).translate((x, y, z))


def _rail(P):
    points = [(-70,-21,13),(-61,-27,10.5),(-49,-32,10),(-37,-34,11),(-24,-33,14.5)]
    curve = cq.Edge.makeSpline([cq.Vector(*p) for p in points])
    wires = []
    for i in range(12):
        t = i / 11
        tangent = curve.tangentAt(t)
        major = tangent.cross(cq.Vector(0,1,0)).normalized()
        plane = cq.Plane(origin=curve.positionAt(t),xDir=major,normal=tangent)
        taper = max(0,(t-.8)/.2)
        wires.append(cq.Workplane(plane).ellipse(P['base_rail_height']/2*(1-.35*taper),P['base_rail_depth']/2*(1-.35*taper)).val())
    return cq.Workplane(obj=cq.Solid.makeLoft(wires,ruled=False))


def refine_base(cage, P):
    rail = _rail(P)
    rail = rail.union(cq.Workplane('XY').sphere(P['base_start_cap_radius']).translate((-70,-21,13)))
    rail = rail.union(cq.Workplane('XY').sphere(P['base_end_cap_radius']).translate((-24,-33,14.5)))
    initial_volume = cage.val().Volume()
    cage = cage.union(rail,tol=.001)
    if cage.val().Volume() < initial_volume - .01:
        raise RuntimeError('Base rail union lost original cage material')
    return cage.cut(_box(-33,-10,8,36,30,40)).clean()


def refine_port(cage, P):
    width=P['port_well_width']
    height=P['port_well_height']
    cutter=_box(-74,7,37,26,width,height).edges('|X').fillet(P['port_well_corner_radius'])
    cage=cage.cut(cutter)
    edges=[]
    for edge in cage.val().Edges():
        b=edge.BoundingBox()
        if abs(b.xmin+78)<.001 and abs(b.xmax+78)<.001 and b.ymin>7-width/2-.1 and b.ymax<7+width/2+.1 and b.zmin>37-height/2-.1 and b.zmax<37+height/2+.1:
            edges.append(edge)
    if len(edges)!=8:
        raise RuntimeError(f'Expected eight port lip edges, found {len(edges)}')
    return cage.newObject(edges).fillet(P['port_lip_radius'])


def refine_shutter_root(cage, P):
    faces=cage.val().Faces()
    edges=[]
    for edge in cage.val().Edges():
        b=edge.BoundingBox()
        if b.xmax < -65.4 and 80.8<=b.zmin and b.zmax<84.01:
            points=[edge.positionAt(t) for t in (0,.25,.5,.75,1)]
            if all(abs(math.hypot(p.x+68,p.y)-8.3)<.01 for p in points):
                adjacent=[f for f in faces if any(e.isSame(edge) for e in f.Edges())]
                normals=[f.normalAt(edge.positionAt(.5)) for f in adjacent]
                if len(normals)==2 and normals[0].dot(normals[1])<.99:
                    edges.append(edge)
    if len(edges)!=5:
        raise RuntimeError(f'Expected five exterior shutter root edges, found {len(edges)}')
    return cage.newObject(edges).fillet(P['shutter_root_fillet_radius'])


def _near_edge(shape, center):
    target=cq.Vector(*center)
    candidates=[e for e in shape.Edges() if e.geomType()=='BSPLINE']
    edge=min(candidates,key=lambda e:(e.Center()-target).Length)
    if (edge.Center()-target).Length>1:
        raise RuntimeError(f'Junction edge was not found near {center}')
    return edge


def _constant_fillet(cage, center, radius, allow_fix=False):
    edge=_near_edge(cage.val(),center)
    shape=cage.newObject([edge]).fillet(radius).val()
    if allow_fix and not shape.isValid():
        shape=shape.fix()
    return cq.Workplane(obj=shape)


def _variable_fillet(cage, center, radius):
    edge=_near_edge(cage.val(),center)
    values=TColgp_Array1OfPnt2d(1,5)
    for i,(t,r) in enumerate(((0,.015),(.2,radius),(.5,radius),(.8,radius),(1,.015)),1):
        values.SetValue(i,gp_Pnt2d(t,r))
    maker=BRepFilletAPI_MakeFillet(cage.val().wrapped)
    maker.Add(values,edge.wrapped)
    maker.Build()
    if not maker.IsDone():
        raise RuntimeError(f'Variable fillet failed near {center}')
    return cq.Workplane(obj=cq.Shape.cast(maker.Shape()))


def terminal_faces(shape):
    result=[]
    for face in shape.Faces():
        c=face.Center()
        if face.geomType()=='PLANE' and -51<c.x<-15 and -25.1<c.y<-15 and 0<c.z<28 and face.normalAt().z>.7:
            result.append({'center_mm':list(c.toTuple()),'area_mm2':face.Area()})
    return result


def refine_form(cage, P, report_path=None, checkpoint_directory=None):
    initial_volume=cage.val().Volume()
    stages=[]
    before=terminal_faces(cage.val())
    if report_path is not None:
        Path(report_path).write_text(json.dumps({'native_feature_pass':False,'status':'building','features':[]}))
    if checkpoint_directory is not None:
        Path(checkpoint_directory).mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='entropi-form-') as directory:
        def checkpoint(part,name):
            shape=part.val()
            if not shape.isValid() or len(shape.Solids())!=1 or shape.Volume()<initial_volume*.95:
                raise RuntimeError(f'Invalid form feature: {name}')
            path=Path(directory)/f'{name}.step'
            cq.exporters.export(part,str(path))
            fresh=cq.importers.importStep(str(path))
            s=fresh.val()
            if not s.isValid() or len(s.Solids())!=1 or s.Volume()<initial_volume*.95 or s.BoundingBox().ymax<22:
                raise RuntimeError(f'Invalid STEP readback: {name}')
            stages.append({'feature':name,'native_valid':True,'step_readback_valid':True,'solids':1,'volume_mm3':s.Volume()})
            if checkpoint_directory is not None:
                shutil.copyfile(path,Path(checkpoint_directory)/path.name)
            if report_path is not None:
                Path(report_path).write_text(json.dumps({'native_feature_pass':False,'status':'building','features':stages},indent=2))
            print(json.dumps(stages[-1]),flush=True)
            return fresh
        cage=checkpoint(refine_base(cage,P),'continuous_base')
        cage=checkpoint(refine_shutter_root(cage,P),'shutter_root')
        cage=checkpoint(_variable_fillet(cage,(-58.59,-31.51,13.98),P['base_main_blend_radius']),'base_blend_1')
        cage=checkpoint(_variable_fillet(cage,(-38.06,-36.08,15.71),P['base_main_blend_radius']),'base_blend_3')
        cage=checkpoint(_constant_fillet(cage,(-47.61,-35.32,14.24),P['base_narrow_blend_radius']),'base_blend_2')
        cage=checkpoint(_constant_fillet(cage,(-26.68,-34.32,17.22),P['base_end_blend_radius']),'base_blend_4')
        cage=checkpoint(_constant_fillet(cage,(4.784,-41.145,64.255),P['front_fan_blend_radius']),'front_fan_lower')
        cage=checkpoint(_constant_fillet(cage,(38.392,-39.402,75.894),P['front_fan_blend_radius']),'front_fan_upper')
        cage=checkpoint(_constant_fillet(cage,(57.143,-39.013,64.511),P['front_crown_blend_radius']),'front_crown')
        cage=checkpoint(_constant_fillet(cage,(15.583,-41.473,73.227),P['front_middle_blend_radius'],allow_fix=True),'front_fan_middle')
        cage=checkpoint(refine_port(cage,P),'usb_access_well')
    after=terminal_faces(cage.val())
    if after:
        raise RuntimeError('Upward terminal faces remain behind the base ribs')
    report={'units':'mm','features':stages,'upward_terminal_faces_before':before,'upward_terminal_faces_after':after,'native_feature_pass':True,'physical_fit_tested':False}
    if report_path is not None:
        Path(report_path).write_text(json.dumps(report,indent=2))
    return cage
