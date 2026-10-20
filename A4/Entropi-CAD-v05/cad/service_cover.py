import cadquery as cq


def _box(x, y, z, width, depth, height, radius=0):
    shape = cq.Workplane("XY").box(width, depth, height).translate((x, y, z))
    return shape.edges().fillet(radius) if radius else shape


def _cy(x, z, y, length, radius):
    return cq.Workplane(obj=cq.Solid.makeCylinder(radius, length, cq.Vector(x, y, z), cq.Vector(0, 1, 0)))


def _patch(width, height, radius):
    plane = cq.Plane(origin=(-69.9, 10, 77.5), xDir=(1, 0, 0), normal=(0, 1, 0))
    return cq.Workplane(plane).rect(width, height).extrude(25).edges("|Y").fillet(radius)


def close_service(cage, P):
    P.setdefault("shutter_service_cover_thickness", 1.2)
    P.setdefault("shutter_service_cover_edge_clearance", 0.15)
    thickness = P["shutter_service_cover_thickness"]
    clearance = P["shutter_service_cover_edge_clearance"]
    envelope = _box(-68, -1, 47, 20, 47, 74, 8)
    skin = envelope.cut(envelope.translate((0, -thickness, 0)))
    cover = skin.intersect(_patch(9.0, 8.8, 0.8))
    x, z, bearing_y = -70.5, 78.0, 20.3
    bearing = _cy(x, z, bearing_y, 1.4, 2.2)
    cover = cover.union(bearing)
    pocket_skin = envelope.cut(envelope.translate((0, -thickness - clearance, 0)))
    cage = cage.cut(pocket_skin.intersect(_patch(9.0 + 2 * clearance, 8.8 + 2 * clearance, 0.8 + clearance)))
    cage = cage.cut(_cy(x, z, bearing_y, 8, 2.2 + clearance))
    boss = _cy(x, z, 15, bearing_y - 15, 2.1)
    boss = boss.union(_box(-73.2, 17.65, z, 6.4, 5.3, 3.6)).intersect(envelope)
    boss = boss.cut(_cy(x, z, 15.2, 6, P["pilot_diameter"] / 2))
    cage = cage.union(boss)
    cover = cover.cut(_cy(x, z, 16, 12, P["screw_clearance_diameter"] / 2))
    cover = cover.cut(_cy(x, z, 21.4, 5, 2.1))
    cage = cage.cut(cover).clean()
    cover = cover.clean()
    return cage, [("20_shutter_service_cover", cover, [0.68, 0.70, 0.70], [0, 40, 0])]
