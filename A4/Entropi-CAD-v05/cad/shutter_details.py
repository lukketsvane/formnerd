import cadquery as cq


def _defaults(P):
    values = {
        "shutter_pin_diameter": 1.8,
        "shutter_pin_diametral_clearance": 0.3,
        "shutter_flexure_thickness": 0.8,
        "shutter_flexure_width": 4.8,
        "shutter_flexure_length": 14.8,
        "shutter_flexure_seat_clearance": 0.3,
        "shutter_shoulder_fillet": 1.6,
        "shutter_switch_seat_enabled": True,
        "shutter_switch_width_assumed": 6.0,
        "shutter_switch_length_assumed": 6.0,
        "shutter_switch_body_height_assumed": 3.6,
        "shutter_switch_plunger_height_assumed": 1.0,
        "shutter_switch_pretravel_gap_assumed": 0.7,
        "shutter_switch_body_clearance": 0.4,
    }
    for name, value in values.items():
        P.setdefault(name, value)
    return P


def _box(x, y, z, width, depth, height):
    return cq.Workplane("XY").box(width, depth, height).translate((x, y, z))


def _cz(x, y, z, height, radius):
    return cq.Workplane("XY").workplane(offset=z).center(x, y).circle(radius).extrude(height)


def _cy(x, z, y, length, radius):
    return cq.Workplane(obj=cq.Solid.makeCylinder(radius, length, cq.Vector(x, y, z), cq.Vector(0, 1, 0)))


def shutter_motion(P, displacement=0):
    _defaults(P)
    x, y = -68.0, 0.0
    travel = P["shutter_travel"]
    pin_radius = P["shutter_pin_diameter"] / 2
    pin_z = 81.0 - pin_radius - displacement
    shutter = _cz(x, y, 85 + travel - displacement, 3, 6).edges(">Z").fillet(0.8)
    shutter = shutter.union(_cz(x, y, 78 - displacement, 8.2 + travel - 1, 3.9))
    shutter = shutter.cut(_cy(x, pin_z, -10, 20, (P["shutter_pin_diameter"] + P["shutter_pin_diametral_clearance"]) / 2))
    pin = _cy(x, pin_z, -6.2, 11.6, pin_radius)
    plane = cq.Plane(origin=(x, -5.8, pin_z), xDir=(1, 0, 0), normal=(0, 1, 0))
    lead = cq.Workplane(plane).ellipse(pin_radius, pin_radius * 0.82).workplane(offset=0.8).ellipse(pin_radius + 0.3, pin_radius * 0.88).loft()
    flange = cq.Workplane(cq.Plane(origin=(x, -5, pin_z), xDir=(1, 0, 0), normal=(0, 1, 0))).ellipse(pin_radius + 0.3, pin_radius * 0.88).extrude(0.5)
    pin = pin.union(lead).union(flange)
    pin = pin.union(_box(x, 6.6, pin_z, 4, 3.2, 1.5).edges("|Z").fillet(0.3))
    pin = pin.cut(_box(x, -3.7, pin_z, 0.5, 5.6, 3))
    return shutter.clean(), pin.clean(), return_flexure(P, displacement)


def return_flexure(P, displacement=0):
    _defaults(P)
    width = P["shutter_flexure_width"]
    datum_x = -65.4
    x = datum_x - width / 2
    thickness = P["shutter_flexure_thickness"]
    length = P["shutter_flexure_length"]
    positions = [-1.2, 0, 1.2] + [1.2 + (length - 1.2) * i / 12 for i in range(1, 13)] + [length + 0.4]
    top = []
    for y in positions:
        f = min(1, max(0, (y - 1.2) / (length - 1.2)))
        u = 1 - f
        z = 78 - 2.7 * f - displacement * u * u * (3 - u) / 2
        top.append((y, z))
    profile = top + [(y, z - thickness) for y, z in reversed(top)]
    plane = cq.Plane(origin=(x - width / 2, 0, 0), xDir=(0, 1, 0), normal=(1, 0, 0))
    leaf = cq.Workplane(plane).polyline(profile).close().extrude(width)
    base_start = length + 0.2
    base_end = length + 5.2
    foot = _box(datum_x - 3.2, (base_start + base_end) / 2, 73.25, 6.4, 5, 0.9)
    neck = _box(x, (base_start + base_end) / 2, 74.5, width, 5, 1.6)
    latch = _box(datum_x - 6.65 / 2, length + 4.2, 73.25, 6.65, 0.8, 0.9)
    tab = _box(datum_x - 1.5, length + 5.5, 74.75, 3.0, 1.4, 1.1)
    result = leaf.union(foot).union(neck).union(latch).union(tab)
    result = result.cut(_box(datum_x - 5.25, length + 3.2, 74, 0.7, 4.6, 4.0))
    return result.clean()


def calibration_coupon(P):
    _defaults(P)
    coupon = _box(-22.5, 0, 1.2, 25, 25, 2.4)
    pin_d = P["shutter_pin_diameter"]
    pin_hole = pin_d + P["shutter_pin_diametral_clearance"]
    for x, diameter in zip((-30, -22, -14), (pin_hole - 0.1, pin_hole, pin_hole + 0.1)):
        coupon = coupon.cut(_cz(x, -7, -1, 5, diameter / 2))
    for x, diameter in zip((-30, -22, -14), (pin_d - 0.1, pin_d, pin_d + 0.1)):
        coupon = coupon.union(_cz(x, 6, 2.4, 6, diameter / 2))
    length = P["shutter_flexure_length"]
    thickness = P["shutter_flexure_thickness"]
    width = P["shutter_flexure_width"]
    root_x = -10.0
    end_x = root_x + length
    coupon = coupon.union(_box(root_x - 1.5, 0, width / 2, 3, 4, width))
    coupon = coupon.union(_box(root_x + length / 2, 0, width / 2, length + 0.2, thickness, width))
    coupon = coupon.union(_box((root_x + end_x + 2) / 2, 4, width / 2, length + 2, 2, width))
    coupon = coupon.union(_box(end_x + 1, (thickness / 2 + 1 + 5) / 2, width / 2, 2, 5 - thickness / 2 - 1, width))
    return coupon.clean()


def refine_shutter(cage, shutter, pin, P):
    _defaults(P)
    x, y = -68.0, 0.0
    edges = [edge for edge in cage.val().Edges() if abs(edge.Center().z - 85) < 0.02 and abs(edge.Center().x - x) < 0.1 and abs(edge.Center().y - y) < 0.1 and edge.Length() > 40]
    if edges:
        cage = cage.newObject(edges).fillet(P["shutter_shoulder_fillet"])
    spring_x = -69.0
    datum_x = -65.4
    leaf_x = datum_x - P["shutter_flexure_width"] / 2
    length = P["shutter_flexure_length"]
    clearance = P["shutter_flexure_seat_clearance"]
    groove_front = length - 0.1
    groove_rear = length + 10
    groove_depth = groove_rear - groove_front
    groove_y = (groove_front + groove_rear) / 2
    cage = cage.cut(_box(datum_x - 3.2, groove_y, 73.25, 6.4 + clearance, groove_depth, 0.9 + clearance))
    cage = cage.cut(_box(leaf_x, groove_y, 74.1, P["shutter_flexure_width"] + clearance, groove_depth, 1.2))
    cage = cage.cut(_box(datum_x - 6.65 / 2, length + 4.2, 73.25, 6.65 + clearance, 1.4, 0.9 + clearance))
    if P["shutter_switch_seat_enabled"]:
        switch_w = P["shutter_switch_width_assumed"]
        switch_l = P["shutter_switch_length_assumed"]
        switch_h = P["shutter_switch_body_height_assumed"] + P["shutter_switch_plunger_height_assumed"]
        switch_clearance = P["shutter_switch_body_clearance"]
        seat_z = 78 - P["shutter_flexure_thickness"] - P["shutter_switch_pretravel_gap_assumed"] - switch_h
        outer_w = switch_w + switch_clearance + 0.8
        outer_l = switch_l + switch_clearance + 0.8
        if spring_x + outer_w / 2 >= -65.05 or seat_z < 71.3:
            raise ValueError("Switch seat exceeds the concealed guide envelope")
        seat = _box(spring_x, 0, seat_z - 0.6, outer_w, outer_l, 1.2)
        walls = _box(spring_x, 0, seat_z + 1.5, outer_w, outer_l, 3.0)
        walls = walls.cut(_box(spring_x, 0.6, seat_z + 1.5, switch_w + switch_clearance, outer_l + 1.2, 3.2))
        cage = cage.union(seat).union(walls)
    shutter, pin, spring = shutter_motion(P)
    cage = cage.clean()
    return cage, shutter, pin, [("15_shutter_return_flexure", spring, [0.38, 0.41, 0.42], [0, 25, 0])]
