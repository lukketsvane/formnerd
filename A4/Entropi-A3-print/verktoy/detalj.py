import numpy as np
from PIL import Image, ImageDraw, ImageFont
from skimage import measure
from manifold3d import Manifold, CrossSection, JoinType, FillRule

FONT = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"


def boks(x, y, z):
    return Manifold.cube([x[1] - x[0], y[1] - y[0], z[1] - z[0]]).translate([x[0], y[0], z[0]])


def band_z(m, z0, tjukn, breidd, region=None):
    """Spor som følgjer ytterflata til m ved høgda z0: breidd i z, tjukn inn i flata."""
    cs = m.slice(z0)
    b = cs - cs.offset(-tjukn, JoinType.Miter)
    if region is not None:
        b = b ^ region
    return b.extrude(breidd).translate([0, 0, z0 - breidd / 2])


def band_x(m, x0, tjukn, breidd, region=None):
    """Same som band_z, men rundt x-aksen (linseaksen)."""
    r = m.rotate([0, -90, 0])  # x -> z
    cs = r.slice(x0)
    b = cs - cs.offset(-tjukn, JoinType.Round)
    if region is not None:
        b = b ^ region.rotate(90)
    return b.extrude(breidd).translate([0, 0, x0 - breidd / 2]).rotate([0, 90, 0])


def radialslabar(n, tjukn, lengd, akse_pos, akse="x", x_spenn=None, vinkel0=0.0):
    """n tynne plater gjennom aksen, til knurling."""
    ay, az = akse_pos
    ut = []
    for i in range(n):
        v = vinkel0 + 360.0 * i / n
        p = boks([x_spenn[0], x_spenn[1]], [-tjukn / 2, tjukn / 2], [0, lengd]).rotate([v, 0, 0]).translate([0, ay, az])
        ut.append(p)
    return Manifold.batch_boolean(ut, 1) if hasattr(Manifold, "batch_boolean") else sum(ut, Manifold())


def radialslabar_z(n, tjukn, r0, r1, senter, z_spenn, vinkel0=0.0):
    cx, cy = senter
    ut = []
    for i in range(n):
        v = vinkel0 + 360.0 * i / n
        p = boks([r0, r1], [-tjukn / 2, tjukn / 2], z_spenn).rotate([0, 0, v]).translate([cx, cy, 0])
        ut.append(p)
    return sum(ut, Manifold())


def tekst_polygonar(tekst, hogd_mm, px_per_mm=24):
    font = ImageFont.truetype(FONT, int(hogd_mm * px_per_mm * 1.36))
    l, t, r, b = font.getbbox(tekst)
    pad = 8
    im = Image.new("L", (r - l + 2 * pad, b - t + 2 * pad), 0)
    ImageDraw.Draw(im).text((pad - l, pad - t), tekst, font=font, fill=255)
    a = np.asarray(im) > 127
    H = a.shape[0]
    polys = []
    for c in measure.find_contours(a.astype(float), 0.5):
        pts = [((p[1] - pad) / px_per_mm, (H - pad - p[0]) / px_per_mm) for p in c[::2]]
        if len(pts) >= 3:
            polys.append(pts)
    cs = CrossSection(polys, FillRule.EvenOdd)
    bb = cs.bounds()
    return cs.translate([-(bb[0] + bb[2]) / 2, -(bb[1] + bb[3]) / 2]), (bb[2] - bb[0], bb[3] - bb[1])


def gravert_tekst(tekst, hogd_mm, djupn, senter, plan_z, retning_deg=0.0):
    """Tekst skore ned i eit flatt tak ved z = plan_z (senter = (x, y))."""
    cs, _ = tekst_polygonar(tekst, hogd_mm)
    return cs.rotate(retning_deg).extrude(djupn + 1.0).translate([senter[0], senter[1], plan_z - djupn])


def dovetail_skinne(x0, x1, y0, y1, z_botn, hogd_dovetail, z_topp):
    """Arca-Swiss-liknande skinne: 45° svalehale, breidd x1-x0 i botnen."""
    xm = (x0 + x1) / 2
    hb = (x1 - x0) / 2
    ht = hb - hogd_dovetail
    prof = CrossSection([[(xm - hb, z_botn), (xm + hb, z_botn), (xm + ht, z_botn + hogd_dovetail), (xm + ht, z_topp), (xm - ht, z_topp), (xm - ht, z_botn + hogd_dovetail)]], FillRule.Positive)
    return prof.extrude(y1 - y0).rotate([90, 0, 0]).translate([0, y1, 0])


def sekskant(cx, cy, af, z0, z1):
    r = af / 2 / np.cos(np.radians(30))
    return Manifold.cylinder(z1 - z0, r, r, 6).rotate([0, 0, 30]).translate([cx, cy, z0])
