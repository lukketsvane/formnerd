import json
import math
from pathlib import Path
import cadquery as cq
from normalize_glb import normalize_glb
from shutter_details import refine_shutter, calibration_coupon
from optical_io_details import refine_interfaces
from service_cover import close_service
from form_refinements import refine_form

ROOT = Path(__file__).resolve().parents[1]
P = json.loads((ROOT / "cad/parameters.json").read_text())
PARTS = ROOT / "parts"
PARTS.mkdir(exist_ok=True)

def prism(x, z, y, depth, width, height, radius=0):
    plane = cq.Plane(origin=(x, y, z), xDir=(1, 0, 0), normal=(0, 1, 0))
    part = cq.Workplane(plane).rect(width, height).extrude(depth)
    return part.edges("|Y").fillet(radius) if radius else part

def cy(x, z, y, length, radius):
    return cq.Workplane(obj=cq.Solid.makeCylinder(radius, length, cq.Vector(x, y, z), cq.Vector(0, 1, 0)))

def cz(x, y, z, height, radius):
    return cq.Workplane("XY").workplane(offset=z).center(x, y).circle(radius).extrude(height)

def box(x, y, z, width, depth, height, radius=0):
    part = cq.Workplane("XY").box(width, depth, height).translate((x, y, z))
    return part.edges().fillet(radius) if radius else part

def rib(points, radius):
    edge = cq.Edge.makeSpline([cq.Vector(*point) for point in points])
    sections = []
    for index in range(15):
        t = index / 14
        point = edge.positionAt(t)
        tangent = edge.tangentAt(t)
        major = tangent.cross(cq.Vector(0, 1, 0)).normalized()
        plane = cq.Plane(origin=point, xDir=major, normal=tangent)
        taper = max(0.0, (t - 0.72) / 0.28) ** 2
        breadth = radius * (0.97 + 0.10 * math.sin(math.pi * t)) * (1 - 0.60 * taper)
        depth = min(4.5, radius * 0.72) * (0.95 + 0.05 * math.sin(math.pi * t)) * (1 - 0.45 * taper)
        sections.append(cq.Workplane(plane).ellipse(breadth, depth).val())
    return cq.Workplane(obj=cq.Solid.makeLoft(sections, ruled=False))

def log(message):
    print(message, flush=True)

width, height, wall = P["body_width"], P["body_height"], P["wall"]
front_y, rear_y = P["body_front_y"], P["body_rear_y"]
body_z = P["body_bottom_z"] + height / 2
outer = prism(0, body_z, front_y, rear_y-front_y, width, height, P["corner_radius"])
inner = prism(0, body_z, front_y+wall, rear_y-front_y+8, width-2*wall, height-2*wall, P["corner_radius"]-wall)
outer = outer.faces("<Y").edges().fillet(1.4)
body = outer.cut(inner)
body = body.cut(cy(31, 43, -20, 14, 23.8))
front_mounts = [(-56, 22), (-56, 66), (54, 21), (48, 71)]
rear_mounts = [(-59,16),(-59,72),(59,16),(59,72)]
for x, z in front_mounts:
    body = body.cut(cy(x, z, -18, 12, P["screw_clearance_diameter"]/2))
for x, z in rear_mounts:
    body = body.union(cy(x, z, 14, 11.5, 4.5))
    body = body.union(box(x + (5 if x>0 else -5),19.75,z,12,11.5,8).intersect(outer))
    body = body.cut(cy(x, z, 15.5, 11, P["pilot_diameter"]/2))
cassette_mounts = [(12, 15), (50, 15), (12, 71), (40, 71)]
for x, z in cassette_mounts:
    body = body.union(cy(x, z, -14, 13, 4.5))
    body = body.cut(cy(x, z, -10, 10, P["pilot_diameter"]/2))
body = body.cut(box(-64, 7, 37, 12, 14, 9))
body = body.cut(cz(47, 10, 77, 12, 3.3))
body = body.cut(box(-64,13,81,6,30,8))
for x in (16,46):
    body = body.cut(cz(x,-4,66.15,2.3,2.1))
body = body.clean()
log("body complete")

paths = [
    ([(-69,-18,14),(-70,-20,49),(-66,-22,79),(-48,-25,99),(-15,-29,105),(22,-30,99),(49,-32,84),(57,-40,56.8)], 7.0),
    ([(-58,-21,15),(-58,-26,10),(-58,-29,16),(-58,-29,42),(-57,-30,66),(-47,-32,80),(-24,-34,87),(6,-35,87),(33,-36,80),(46.3,-40,68.2)], 5.8),
    ([(-45,-21,15),(-46,-28,9),(-47,-33,16),(-47,-34,40),(-45,-35,60),(-35,-36,73),(-14,-37,79),(10,-38,79),(31.9,-40,72.5)], 5.5),
    ([(-34,-21,17),(-35,-28,11),(-36,-34,18),(-36,-35,38),(-33,-36,54),(-22,-37,65),(-2,-38,72),(17,-39,73),(25.4,-40,71.95)], 5.1),
    ([(-23,-21,19),(-24,-28,14),(-25,-32,20),(-25,-34,35),(-21,-36,48),(-8,-38,59),(9,-39,66),(16.3,-40,68.55)], 4.8)
]
cage = cy(31,43,-45,10,P["front_ring_outer_diameter"]/2).cut(cy(31,43,-46,12,P["front_ring_clear_diameter"]/2))
cage = cage.edges().fillet(2.8)
cage = cage.union(cy(31, 43, -35.2, 4.2, 30).cut(cy(31, 43, -36, 6, P["rear_optical_clear_diameter"]/2)))
cage = cage.union(cy(31, 43, -32, 22, 23.5).cut(cy(31, 43, -33, 24, P["rear_optical_clear_diameter"]/2)))
for index, (points, radius) in enumerate(paths):
    cage = cage.union(rib(points, radius))
    log(f"rib {index + 1} complete")
cage = cage.union(box(-47,-20,14,54,7.5,7,3.2))
cage = cage.union(box(-68, -1, 47, 20, 47, 74, 8))
clearance_outer = prism(0,body_z,front_y-P["fit_clearance"],rear_y-front_y+2*P["fit_clearance"],width+2*P["fit_clearance"],height+2*P["fit_clearance"],P["corner_radius"]+P["fit_clearance"])
clearance_outer = clearance_outer.cut(cy(31,43,-50,90,23.8))
cage = cage.cut(clearance_outer)
for x, z in front_mounts:
    if x < 0:
        sections = []
        for py, radius in ((-30,2.1),(-24,4.6),(-16,4.6)):
            plane = cq.Plane(origin=(x,py,z),xDir=(1,0,0),normal=(0,1,0))
            sections.append(cq.Workplane(plane).circle(radius).val())
        cage = cage.union(cq.Workplane(obj=cq.Solid.makeLoft(sections,ruled=False)))
    else:
        radial = math.hypot(x-31,z-43)
        root_x = 31 + (x-31) * 29.2 / radial
        root_z = 43 + (z-43) * 29.2 / radial
        sections = []
        for px, pz, py, radius in ((root_x,root_z,-39,2.5),(x,z,-29,4.6),(x,z,-16,4.6)):
            plane = cq.Plane(origin=(px,py,pz),xDir=(1,0,0),normal=(0,1,0))
            sections.append(cq.Workplane(plane).circle(radius).val())
        cage = cage.union(cq.Workplane(obj=cq.Solid.makeLoft(sections,ruled=False)))
    cage = cage.cut(cy(x, z, -26, 10.1, P["pilot_diameter"]/2))
cage = cage.cut(cy(31,43,-51,16,P["front_ring_clear_diameter"]/2))
cage = cage.cut(cy(31, 43, -35.1, 26, P["rear_optical_clear_diameter"]/2))
for x in (14,48):
    cage = cage.union(cy(x,43,-11,2,4.5))
    cage = cage.cut(cy(x,43,-12,4,P["screw_clearance_diameter"]/2))
cage = cage.cut(box(-74, 7, 37, 24, 10.2, 4.6, P["screw_clearance_diameter"]/2))
shutter_x, shutter_y = -68, 0
pod = cz(shutter_x, shutter_y, 72, 13, 8.3)
cage = cage.union(pod)
cage = cage.cut(cz(shutter_x, shutter_y, 71, 10, 6.4))
cage = cage.cut(cz(shutter_x, shutter_y, 80.9, 6, 4.2))
cage = cage.cut(box(shutter_x,shutter_y+20,77.5,11.2,40,7))
cage = cage.cut(outer.cut(cy(31,43,-50,90,23.8)))
cage = cage.clean()
if not cage.val().isValid():
    cage = cq.Workplane(obj=cage.val().fix())
log(f"cage complete: {len(cage.solids().vals())} solids")

clearance = P["fit_clearance"]
cover = prism(0,body_z,rear_y,2.4,width-2*clearance,height-2*clearance,P["corner_radius"]-clearance)
lip = prism(0,body_z,rear_y-2.3,2.4,width-2*wall-2*clearance,height-2*wall-2*clearance,P["corner_radius"]-wall-clearance).cut(prism(0,body_z,rear_y-2.5,3,width-2*wall-2*clearance-3,height-2*wall-2*clearance-3,P["corner_radius"]-wall-clearance-1.5))
for x,z in rear_mounts:
    lip = lip.cut(cy(x,z,rear_y-2.6,2.7,4.8))
    lip = lip.cut(box(x+(5 if x>0 else -5),rear_y-1.1,z,12.6,2.8,8.6))
cover = cover.union(lip)
for x, z in rear_mounts:
    cover = cover.cut(cy(x, z, 22, 8, P["screw_clearance_diameter"]/2))
    cover = cover.cut(cy(x, z, 26.9, 2, 2.5))
cover = cover.faces(">Y").edges().fillet(0.35)
cover = cover.clean()

frame = prism(31, 43, -1, 3, 46, 64, 3).cut(prism(31,43,-2,5,33.2,51.2,1.6))
for x, z in cassette_mounts:
    frame = frame.cut(cy(x, z, -2, 6, P["screw_clearance_diameter"]/2))
board_w = P["esp32_board_width_nominal"]
board_h = P["esp32_board_length_nominal"]
board_y = P["board_plane_y"]
for side in (-1, 1):
    x = 31 + side * (board_w / 2 + 1.5)
    rail = box(x, -4, 43, 5.2, 10, board_h + 1.2)
    slot = box(31, board_y, 44, board_w + 2*P["board_edge_clearance"], P["esp32_pcb_thickness_assumed"] + 0.6, board_h + 7)
    rail = rail.cut(slot)
    frame = frame.union(rail)
frame = frame.union(box(31,-4,43-board_h/2-1.6,34.4,10,3.0))
frame = frame.cut(box(31,board_y,43,board_w+0.6,2.2,board_h+2*P["board_edge_clearance"]))
for x in (16,46):
    frame = frame.cut(cz(x,-4,59,10,P["pilot_diameter"]/2))
for x in (14,48):
    frame = frame.cut(cy(x,43,-9.1,2.4,2.1))
frame = frame.clean()

clamp = box(31,-5,43+(board_h+1.2)/2+1.2,36,8,2.4,0.5)
for x in (16,46):
    clamp = clamp.cut(cz(x,-4,63,6,P["screw_clearance_diameter"]/2))

baffle = cy(31,43,-32,2.4,20.2).cut(cy(31,43,-33,5,7.5))
for angle in (0,180):
    x = 31 + (17 if angle == 0 else -17)
    baffle = baffle.union(cy(x,43,-30,19,2.2))
    baffle = baffle.cut(cy(x,43,-20,10,P["pilot_diameter"]/2))
    body = body.cut(cy(x,43,-17,8,P["screw_clearance_diameter"]/2))
baffle = baffle.clean()
lens_blank = cy(31,43,-33.5,1.5,19.6).union(cy(31,43,-32,3,7.3)).cut(cy(31,43,-31.8,3,0.9))
lens_blank_retainer = cy(31,43,-29,1.2,8.5).cut(cy(31,43,-30,4,1.2))

shutter = cz(shutter_x,shutter_y,85+P["shutter_travel"],3,6.0).edges(">Z").fillet(0.8)
shutter = shutter.union(cz(shutter_x,shutter_y,78,8.2,3.9))
shutter = shutter.cut(cq.Workplane(obj=cq.Solid.makeCylinder(1.0,14,cq.Vector(shutter_x-7,shutter_y,80.0),cq.Vector(1,0,0))))
pin = cq.Workplane(obj=cq.Solid.makeCylinder(0.98,10,cq.Vector(shutter_x-5,shutter_y,80.0),cq.Vector(1,0,0)))
dial = cz(47,10,83.0,4,10).edges(">Z").fillet(1.0)
dial = dial.union(cz(47,10,80.2,3.2,3.0)).cut(cz(47,10,79,7.8,P["pilot_diameter"]/2))
for index in range(32):
    angle = 2 * math.pi * index / 32
    dial = dial.cut(cz(47 + 10.1 * math.cos(angle), 10 + 10.1 * math.sin(angle), 83.6, 2.4, 0.45))
dial_retainer = cz(47,10,79.0,1.2,4.5).cut(cz(47,10,78,4,P["screw_clearance_diameter"]/2))

io = box(-60.2,7,37,2.0,P["io_plate_width"],14.4,0.8)
io = io.cut(box(-60.2,7,37,5,9.4,3.8,1.0))
body = body.cut(box(-63.4,7,37,4.2,20,15))
for y in (P["usb_axis_y"]-P["io_mount_pitch"]/2,P["usb_axis_y"]+P["io_mount_pitch"]/2):
    io = io.cut(cq.Workplane(obj=cq.Solid.makeCylinder(P["screw_clearance_diameter"]/2,10,cq.Vector(-66,y,37),cq.Vector(1,0,0))))
    boss = cq.Workplane(obj=cq.Solid.makeCylinder(3.6,3.6,cq.Vector(-64.8,y,37),cq.Vector(1,0,0)))
    body = body.union(boss)
    body = body.cut(cq.Workplane(obj=cq.Solid.makeCylinder(P["pilot_diameter"]/2,6,cq.Vector(-65,y,37),cq.Vector(1,0,0))))
body = body.clean()

coupon = box(0,0,1.6,62,24,3.2,0.8)
for index, diameter in enumerate((1.6,1.7,1.8,2.1,2.2,2.4)):
    coupon = coupon.cut(cz(-25+index*10,-6,-1,6,diameter/2))
for index, clearance in enumerate((0.2,0.3,0.4)):
    coupon = coupon.cut(box(-20+index*20,5,2,14,1.6+clearance,6))

cage, shutter, pin, shutter_extras = refine_shutter(cage, shutter, pin, P)
baffle, io, interface_extras = refine_interfaces(baffle, io, P)
cage, service_extras = close_service(cage, P)
cage = refine_form(cage,P,ROOT/"cad/form_refinement_report.json")

items = [
    ("01_rib_cage",cage,[0.68,0.70,0.70],[0,-65,0]),
    ("02_chassis",body,[0.24,0.27,0.28],[0,0,0]),
    ("03_rear_cover",cover,[0.24,0.27,0.28],[0,70,0]),
    ("04_esp32_carrier",frame,[0.48,0.51,0.52],[0,35,0]),
    ("05_board_clamp",clamp,[0.48,0.51,0.52],[0,35,25]),
    ("06_optical_baffle",baffle,[0.20,0.23,0.24],[0,-30,0]),
    ("07_shutter",shutter,[0.22,0.25,0.26],[0,-65,18]),
    ("08_shutter_pin",pin,[0.22,0.25,0.26],[-15,-65,18]),
    ("09_rear_dial",dial,[0.22,0.25,0.26],[0,0,25]),
    ("10_io_plate",io,[0.22,0.25,0.26],[-25,0,0]),
    ("12_lens_blank",lens_blank,[0.14,0.17,0.18],[0,-45,0]),
    ("13_lens_blank_retainer",lens_blank_retainer,[0.22,0.25,0.26],[0,-25,0]),
    ("14_dial_retainer",dial_retainer,[0.22,0.25,0.26],[0,0,10])
]
items.extend(shutter_extras + interface_extras + service_extras)
explosion = json.loads((ROOT/"cad/explode_positions.json").read_text())
items = [(name,part,color,explosion.get(name,offset)) for name,part,color,offset in items]
assembly = cq.Assembly(name="Entropi_CAD_v05")
manifest = []
checks = []
reference_dir = ROOT/"reference_hardware"
reference_dir.mkdir(exist_ok=True)
cq.exporters.export(box(31,board_y,43,board_w,P["esp32_pcb_thickness_assumed"],board_h),str(reference_dir/"esp32_pcb_nominal.step"))
cq.exporters.export(box(31,13,43,P["mb_keepout_width_assumed"],P["mb_keepout_depth_assumed"],P["mb_keepout_height_assumed"]),str(reference_dir/"esp32_cam_mb_keepout_ASSUMED.step"))
for name, part, color, explode in items:
    shape = part.val()
    solid_count = len(part.solids().vals())
    valid = shape.isValid()
    bb = shape.BoundingBox()
    row = {"name":name,"valid":valid,"solids":solid_count,"volume_mm3":shape.Volume(),"size_mm":[bb.xlen,bb.ylen,bb.zlen],"fits_p1s_bbox":max(bb.xlen,bb.ylen,bb.zlen)<250}
    checks.append(row)
    log(row)
    if not valid or solid_count != 1 or shape.Volume() <= 0:
        raise RuntimeError(f"Invalid printable part: {name}")
    temporary_step=PARTS/f"{name}.write.step"
    cq.exporters.export(part,str(temporary_step))
    remeshed = cq.importers.importStep(str(temporary_step))
    if not remeshed.val().isValid() or len(remeshed.solids().vals())!=1:
        raise RuntimeError(f"Invalid exported STEP: {name}")
    temporary_step.replace(PARTS/f"{name}.step")
    temporary_stl=PARTS/f"{name}.write.stl"
    remeshed.val().exportStl(str(temporary_stl),tolerance=0.06,angularTolerance=0.08,relative=False,parallel=False)
    temporary_stl.replace(PARTS/f"{name}.stl")
    assembly.add(remeshed,name=name,color=cq.Color(*color))
    manifest.append({"name":name,"file":f"parts/{name}.stl","color":color,"explode":explode})
cq.exporters.export(coupon,str(PARTS/"11_fit_coupon.step"))
cq.exporters.export(coupon,str(PARTS/"11_fit_coupon.stl"),tolerance=0.04,angularTolerance=0.12)
shutter_coupon = calibration_coupon(P)
cq.exporters.export(shutter_coupon,str(PARTS/"16_shutter_calibration.step"))
shutter_coupon.val().exportStl(str(PARTS/"16_shutter_calibration.stl"),tolerance=0.04,angularTolerance=0.08,relative=False,parallel=False)
assembly.save(str(ROOT/"Entropi-assembly-v05.step"))
assembly.save(str(ROOT/"Entropi-assembly-v05.glb"))
normalize_glb(ROOT/"Entropi-assembly-v05.glb")
(ROOT/"cad/assembly_manifest.json").write_text(json.dumps(manifest,indent=2))
(ROOT/"cad/geometry_checks.json").write_text(json.dumps(checks,indent=2))
log("exports complete")
