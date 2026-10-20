import cadquery as cq


def box(x, y, z, width, depth, height):
    return cq.Workplane('XY').box(width, depth, height).translate((x, y, z))


def cy(x, z, y, length, radius):
    return cq.Workplane(obj=cq.Solid.makeCylinder(radius, length, cq.Vector(x, y, z), cq.Vector(0, 1, 0)))


def cz(x, y, z, height, radius):
    return cq.Workplane('XY').workplane(offset=z).center(x, y).circle(radius).extrude(height)


def slot_z(x, y, z, height, diameter, length):
    return cq.Workplane('XY').workplane(offset=z).center(x, y).slot2D(length, diameter, angle=90).extrude(height)


def refine_interfaces(baffle, io, P):
    lens_x = P.get('optical_axis_x', 31.0)
    lens_z = P.get('optical_axis_z', 43.0)
    barrel_diameter = P.get('camera_barrel_diameter_assumed', 8.0)
    barrel_clearance = P.get('camera_barrel_diametral_clearance', 0.3)
    collar_y = P.get('camera_collar_y', -26.0)
    collar_depth = P.get('camera_collar_depth', 6.2)
    collar_split = P.get('camera_collar_split_gap', 0.6)
    collar_radius = max(7.5, barrel_diameter / 2 + 3.0)
    screw_clearance = P.get('screw_clearance_diameter', 2.4)
    pilot = P.get('pilot_diameter', 1.8)
    collar_mid_y = collar_y + collar_depth / 2
    base_top = lens_z - collar_radius + 0.5
    base_bottom = base_top - 2.2
    rail_top = base_bottom - 0.3
    mount_x = 10.0
    mount_y = collar_y + collar_depth + 3.1
    base_front = collar_y - 0.4
    base_back = collar_y + collar_depth + 6.2
    rail_front = -29.8
    rail_back = mount_y + 2.3
    for side in (-1, 1):
        x = lens_x + side * mount_x
        rail = box(x, (rail_front + rail_back) / 2, rail_top - 2.25, 5.2, rail_back - rail_front, 4.5)
        rail = rail.cut(cz(x, mount_y, rail_top - 4.6, 5.0, pilot / 2))
        baffle = baffle.union(rail)
    ring = cy(lens_x, lens_z, collar_y, collar_depth, collar_radius)
    ring = ring.cut(cy(lens_x, lens_z, collar_y - 1, collar_depth + 2, (barrel_diameter + barrel_clearance) / 2))
    lower = ring.intersect(box(lens_x, collar_mid_y, lens_z - 10 - collar_split / 2, 40, 30, 20))
    lower = lower.union(box(lens_x, (base_front + base_back) / 2, (base_top + base_bottom) / 2, 25, base_back - base_front, base_top - base_bottom))
    upper = ring.intersect(box(lens_x, collar_mid_y, lens_z + 10 + collar_split / 2, 40, 30, 20))
    for side in (-1, 1):
        x = lens_x + side * 9.5
        lower = lower.union(box(x, collar_mid_y, lens_z - collar_split / 2 - 1.4, 4.4, collar_depth, 2.8))
        lower = lower.cut(cz(x, collar_mid_y, lens_z - 7.0, 8.0, pilot / 2))
        upper = upper.union(box(x, collar_mid_y, lens_z + collar_split / 2 + 2.5, 4.4, collar_depth, 5.0))
        upper = upper.cut(cz(x, collar_mid_y, lens_z, 9.0, screw_clearance / 2))
    for side in (-1, 1):
        x = lens_x + side * mount_x
        lower = lower.cut(slot_z(x, mount_y, base_bottom - 1, 4.2, screw_clearance, 5.2))
    seat_z = P.get('usb_pcb_seat_z_assumed', 33.4)
    pcb_thickness = P.get('usb_pcb_thickness_assumed', 1.6)
    pcb_width = P.get('usb_pcb_width_assumed', 14.0)
    pcb_length = P.get('usb_pcb_length_assumed', 16.0)
    usb_y = P.get('usb_axis_y', 7.0)
    tray_front = -59.4
    tray_back = tray_front + pcb_length + 1.8
    tray_length = tray_back - tray_front
    tray_width = max(24.4, pcb_width + 10.4)
    tray = box((tray_front + tray_back) / 2, usb_y, seat_z - 1.2, tray_length, tray_width, 2.4)
    for side in (-1, 1):
        guide_y = usb_y + side * (pcb_width / 2 + 0.8)
        tray = tray.union(box((tray_front + tray_back) / 2 + 1.0, guide_y, seat_z + 0.75, tray_length - 2.0, 1.0, 1.5))
    clamp_x = tray_back - 3.8
    screw_y = pcb_width / 2 + 2.8
    boss_top = seat_z + pcb_thickness + 0.4
    for side in (-1, 1):
        y = usb_y + side * screw_y
        tray = tray.union(cz(clamp_x, y, seat_z - 0.2, boss_top - seat_z + 0.2, 2.3))
        tray = tray.cut(cz(clamp_x, y, seat_z - 2.2, 5.0, pilot / 2))
    anchor_front = tray_back - 0.4
    anchor_back = tray_back + 7.2
    anchor = box((anchor_front + anchor_back) / 2, usb_y, seat_z - 1.2, anchor_back - anchor_front, 16, 2.4)
    for side in (-1, 1):
        anchor = anchor.cut(box(tray_back + 3.7, usb_y + side * 4.0, seat_z - 1.2, 2.0, 3.2, 4.0))
    io = io.union(tray).union(anchor)
    clamp_bottom = boss_top + 0.3
    usb_clamp = box(clamp_x, usb_y, clamp_bottom + 1.2, 4.0, 2 * screw_y + 5.0, 2.4)
    press_bottom = seat_z + pcb_thickness + 0.2
    usb_clamp = usb_clamp.union(box(clamp_x, usb_y, (clamp_bottom + press_bottom) / 2, 4.0, max(6.0, pcb_width - 4.0), clamp_bottom - press_bottom + 0.2))
    for side in (-1, 1):
        usb_clamp = usb_clamp.cut(cz(clamp_x, usb_y + side * screw_y, press_bottom - 1, 6, screw_clearance / 2))
    extras = [
        ('17_camera_saddle', lower.clean(), [0.35, 0.38, 0.39], [0, -20, -14]),
        ('18_camera_clamp', upper.clean(), [0.35, 0.38, 0.39], [0, -20, 15]),
        ('19_usb_retainer', usb_clamp.clean(), [0.35, 0.38, 0.39], [-20, 0, 15]),
    ]
    return baffle.clean(), io.clean(), extras
