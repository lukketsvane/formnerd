"""Entropi-huset som B-rep-solidar (build123d/OCCT): holrom, opningar, deling og detaljar."""
import json, pathlib, sys, time, math
import numpy as np
from build123d import *
import cad_form as cf

HER = pathlib.Path(__file__).resolve().parent
K, F, S, D = cf.K, cf.F, cf.K["skal"], cf.K["detalj"]
UT = (HER / K["ut_mappe"]).resolve()
for d in ("stl", "step", "proxy"):
    (UT / d).mkdir(parents=True, exist_ok=True)
ay, az = K["akse"]["y"], K["akse"]["z"]
tid = cf.tid
MN = (Align.MIN, Align.MIN, Align.MIN)


def boks(x, y, z):
    return Pos(x[0], y[0], z[0]) * Box(x[1] - x[0], y[1] - y[0], z[1] - z[0], align=MN)


def vsyl(cx, cy, r, z0, z1):
    return cf.syl(cx, cy, r, z0, z1)


def xsyl(x0, x1, r, y=ay, z=az):
    return Pos(x0, y, z) * Rot(0, 90, 0) * Cylinder(r, x1 - x0, align=(Align.CENTER, Align.CENTER, Align.MIN))


def xkjegle(x0, x1, r0, r1, y=ay, z=az):
    return Pos(x0, y, z) * Rot(0, 90, 0) * Cone(r0, r1, x1 - x0, align=(Align.CENTER, Align.CENTER, Align.MIN))


def rboks_x(x0, x1, yc, zc, by, hz, r):
    return Pos(x0, yc, zc) * Rot(0, 90, 0) * extrude(RectangleRounded(hz, by, r), x1 - x0)


def rboks_y(y0, y1, xc, zc, bx, hz, r):
    return Pos(xc, y0, zc) * Rot(-90, 0, 0) * extrude(RectangleRounded(bx, hz, r), y1 - y0)


def tak_boks(x, y, z):
    xm, w = (x[0] + x[1]) / 2, x[1] - x[0]
    prof = Polygon((x[0], z[0]), (x[1], z[0]), (x[1], z[1]), (xm, z[1] + w / 2), (x[0], z[1]), align=None)
    return Pos(0, y[0], 0) * Rot(90, 0, 0) * extrude(prof, -(y[1] - y[0]))


def rboks_y_tak(y0, y1, xc, zc, bx, hz, r):
    topp = zc + hz / 2 - r + (bx / 2 - r) + r * math.sqrt(2)
    prof = Polygon((xc - bx / 2, zc - hz / 2 + r), (xc - bx / 2 + r, zc - hz / 2), (xc + bx / 2 - r, zc - hz / 2), (xc + bx / 2, zc - hz / 2 + r),
                   (xc + bx / 2, zc + hz / 2 - r), (xc, topp), (xc - bx / 2, zc + hz / 2 - r), align=None)
    prof = fillet([v for v in prof.vertices() if abs(v.Y - (zc - hz / 2 + r)) < 1e-6 or abs(v.Y - (zc - hz / 2)) < 1e-6], r * 0.45) if r > 0.6 else prof
    return Pos(0, y0, 0) * Rot(90, 0, 0) * extrude(prof, -(y1 - y0))


def sekskant(cx, cy, af, z0, z1):
    r = af / 2 / math.cos(math.radians(30))
    return Pos(cx, cy, z0) * Rot(0, 0, 30) * extrude(RegularPolygon(r, 6), z1 - z0)


def kjeglehol(cx, cy, r0, r1, z0, z1):
    return Pos(cx, cy, z0) * Cone(r0, r1, z1 - z0, align=(Align.CENTER, Align.CENTER, Align.MIN))


def union(delar):
    u = delar[0]
    for d in delar[1:]:
        u = u + d
    return u


# --- ytre form ---------------------------------------------------------------
FORM, KOMP = cf.bygg_form()
KROPP0 = FORM
hx, hy = F["hjulboss"]["senter"]
hr = F["hjulboss"]["r"]
st, ec = K["stabel"], S["ec11"]
def flate_y(x, z, fraa_minus):
    sek = section(KOMP["kropp"], Plane.XY.offset(z))
    pts = [p for f in sek.faces() for e in f.outer_wire().edges() for p in [e.position_at(t) for t in np.linspace(0, 1, 900)] if abs(p.X - x) < 0.6]
    ys = [p.Y for p in pts]
    return min(ys) if fraa_minus else max(ys)


y_hjul_usb = flate_y(st["cam_front_x"] - st["cam_pcb"] - st["header_gap"] + st["usb_akse_over_mb"], az, False)
y_grep = flate_y(K["usbc_grep"]["x"], K["usbc_grep"]["z"], True)
print("y_hjul_usb", round(y_hjul_usb, 2), "y_grep", round(y_grep, 2))

ok_r = D["okularring"]
oc = ok_r["senter"]
okring = Pos(ok_r["x"][0], oc[0], oc[1]) * Rot(0, 90, 0) * Cone(ok_r["r_front"], ok_r["r_ytre"], ok_r["x"][1] - ok_r["x"][0], align=(Align.CENTER, Align.CENTER, Align.MIN))
okring -= xsyl(ok_r["x"][0] - 1, ok_r["x"][1] + 1, ok_r["r_indre"], oc[0], oc[1])
KROPP0 += okring
kp = D["knapp"]
for x, y in D["knappar"]:
    KROPP0 += vsyl(x, y, kp["r"], kp["z"] - 0.5, kp["z"] + kp["hogd"])
sk_ = D["skinne"]
xm_, hb = (sk_["x"][0] + sk_["x"][1]) / 2, (sk_["x"][1] - sk_["x"][0]) / 2
ht = hb - sk_["dovetail"]
prof = Polygon((xm_ - hb, sk_["z_botn"]), (xm_ + hb, sk_["z_botn"]), (xm_ + ht, sk_["z_botn"] + sk_["dovetail"]), (xm_ + ht, sk_["z_topp"]), (xm_ - ht, sk_["z_topp"]), (xm_ - ht, sk_["z_botn"] + sk_["dovetail"]), align=None)
KROPP0 += Pos(0, sk_["y"][0], 0) * Rot(90, 0, 0) * extrude(prof, -(sk_["y"][1] - sk_["y"][0]))
lr = D["linsering"]
L = F["linse"]
EF = F["ef"]


def vinkel_pos(rr, grader):
    return ay + rr * math.cos(math.radians(grader)), az + rr * math.sin(math.radians(grader))


def bogesegment(r0, r1, senter_grader, spenn_grader, x0, x1):
    a = senter_grader + 90.0
    pts = [(0.0, 0.0)] + [(60 * math.cos(math.radians(a - spenn_grader / 2 + spenn_grader * i / 8)), 60 * math.sin(math.radians(a - spenn_grader / 2 + spenn_grader * i / 8))) for i in range(9)]
    kile = Polygon(*pts, align=None)
    ring = (Circle(r1) - Circle(r0)) & kile
    return Pos(x0, ay, az) * Rot(0, 90, 0) * extrude(ring, x1 - x0)


ef_pin_y, ef_pin_z = vinkel_pos(EF["pinne"]["rr"], EF["pinne"]["vinkel"])
KROPP0 += xsyl(EF["flens_x"][1] - 0.5, EF["flens_x"][1] + EF["pinne"]["hogd"], EF["pinne"]["r"], ef_pin_y, ef_pin_z)
eu = EF["utloysar"]
EF_KNAPP = Pos(eu["x"][0], eu["senter"][0], eu["senter"][1]) * Rot(0, 90, 0) * fillet(Cylinder(eu["r"], eu["x"][1] - eu["x"][0], align=(Align.CENTER, Align.CENTER, Align.MIN)).edges().group_by(Axis.Z)[-1], 1.0)
KROPP0_CACHE = cf.HER.parent / "print" / "cad" / "kropp0.brep"
KROPP0_LASTA = Solid(import_brep(KROPP0_CACHE).solids()[0].wrapped) if "--kropp0" in sys.argv and KROPP0_CACHE.exists() else None
tid("kropp0")

# --- stabelen ----------------------------------------------------------------
x_cam_front = st["cam_front_x"]
x_tupp = x_cam_front + st["linse_over_cam"]
x_konus = x_cam_front + st["linse_over_cam_min"]
x_cam_bak = x_cam_front - st["cam_pcb"]
x_mb_topp = x_cam_bak - st["header_gap"]
x_mb_botn = x_mb_topp - st["mb_pcb"]
x_tappar = x_mb_botn - st["mb_tappar"]
y_sd = ay - st["linse_fraa_sd"]
y_ant = y_sd + st["cam_lengd"]
y_usb = y_sd + st["mb_innrykk_sd"] + st["mb_lengd"]
z_lag = K["rom"]["golv_front_z"] + 0.2
z_hog = z_lag + st["cam_breidd"]
x_usb = x_mb_topp + st["usb_akse_over_mb"]
sk = K["sd_kort"]
x_kort = x_cam_front + 0.6

# --- opningar ----------------------------------------------------------------
ks, lk, lt = K["kamerasete"], K["linsekonus"], S["linsetrakt"]
sete = boks([S["front_x"] - 1.0, x_konus + 0.8], [ay - ks["side"] / 2, ay + ks["side"] / 2], [az - ks["side"] / 2, az + ks["side"] / 2])
konus = xkjegle(x_konus, lk["front_x"], lk["bak_r"], lk["front_r"]) + xsyl(lk["front_x"], lk["fram_til_x"], lk["front_r"])
ef_hals = xsyl(EF["hals_x"][0], EF["hals_x"][1], EF["hals_r"])
ek = EF["kammer"]
ef_kammer = boks(ek["x"], [ay - ek["y_halv"], ay + ek["y_halv"]], [az - ek["z_halv"], az + ek["z_halv"]])
es = EF["sensor"]
ef_sensor = boks(es["x"], [ay - es["b"] / 2, ay + es["b"] / 2], [az - es["h"] / 2, az + es["h"] / 2])
kl_ = EF["klor"]
EF_KLOR = union([bogesegment(kl_["r_indre"], EF["hals_r"] + 0.3, kl_["start"] + 360.0 * i / kl_["n"], kl_["spenn"], kl_["x"][0], kl_["x"][1]) for i in range(kl_["n"])])
ko_ = EF["kontaktar"]
EF_KONTAKT = bogesegment(ko_["r_indre"], EF["hals_r"] + 0.3, ko_["senter"], ko_["spenn"], ko_["x"][0], ko_["x"][1])
EF_KONTAKTHOL = union([xsyl(ko_["x"][1] - ko_["djupn"], ko_["x"][1] + 1.0, ko_["hol_r"], *vinkel_pos(ko_["r"], ko_["senter"] - ko_["spenn"] / 2 + 4 + (ko_["spenn"] - 8) * i / (ko_["n"] - 1))) for i in range(ko_["n"])])
sk_ef = EF["skruar"]
EF_SKRUAR = union([Pos(EF["flens_x"][1] - sk_ef["djupn"], *vinkel_pos(sk_ef["r"], sk_ef["start"] + 360.0 * i / sk_ef["n"])) * Rot(0, 90, 0) * Cone(sk_ef["r_hovud"] / 2, sk_ef["r_hovud"], sk_ef["djupn"], align=(Align.CENTER, Align.CENTER, Align.MIN)) for i in range(sk_ef["n"])] + [xsyl(EF["flens_x"][1] - 0.01, EF["flens_x"][1] + 1.0, sk_ef["r_hovud"], *vinkel_pos(sk_ef["r"], sk_ef["start"] + 360.0 * i / sk_ef["n"])) for i in range(sk_ef["n"])])
pr_ = EF["prikk"]
EF_PRIKK = xsyl(EF["flens_x"][1] - pr_["djupn"], EF["flens_x"][1] + 1.0, pr_["r"], *vinkel_pos(pr_["rr"], pr_["vinkel"]))
ut_ = K["utloysar"]
ux, uy = ut_["senter"]
brunn_golv = ut_["kapp_z"] - ut_["vandring"]
brunn = vsyl(ux, uy, ut_["brunn_r"], brunn_golv, 90)
br = K["brytar"]
lomme_botn = ut_["kapp_z"] - br["hogd_med_bein"]
bx, by = br["senter"]
brytarlomme = boks([bx - br["side_x"] / 2, bx + br["side_x"] / 2], [by - br["side_y"] / 2, by + br["side_y"] / 2], [lomme_botn, brunn_golv + 0.1])
bt = S["brytartrakt"]
brytarhol = vsyl(bx, by, bt["leidning_r"], 20.0, lomme_botn + 0.5)
ut_t = K["usb_tunnel"]
usb_tunnel = rboks_y_tak(y_usb - 1.0, y_hjul_usb + 5, x_usb, az, ut_t["b_x"], ut_t["h_z"], ut_t["r"])
ug = K["usbc_grep"]
r_s = ug["breidd_x"] / 2
usbc = Pos(ug["x"], y_grep - 3, ug["z"]) * Rot(-90, 0, 0) * extrude(SlotOverall(ug["lengd_z"], 2 * r_s, rotation=90), ug["djupn"] + 3)
ok_ = K["sokar"]["okular"]
okular = union([rboks_x(-2, d, ok_["y"], ok_["z"], b, h, 1.5) for b, h, d in (ok_["ytre"], ok_["indre"])])
ec_hol = vsyl(hx, hy, ec["hol_d"] / 2, ec["hol_botn_z"] - 0.01, ec["kapp_z"] + 5) + vsyl(hx, hy, ec["mutter_d"] / 2, ec["mutter_botn_z"], ec["kapp_z"] + 5)
pw, pd = ec["pipe"]
ec_pipe = boks([hx - pw / 2, hx + pw / 2], [hy - pd / 2, hy + pd / 2], [S["tak_z"] - 10.0, ec["tak_botn_z"]])
ec_pipe += Pos(hx, hy, ec["tak_botn_z"] - 0.01) * loft([Rectangle(pw, pd), Pos(0, 0, ec["hol_botn_z"] - ec["tak_botn_z"] + 0.01) * Circle(ec["hol_d"] / 2)])
EC11 = ec_hol + ec_pipe
stv = D["stativ"]
z_mutter = sk_["z_botn"] + stv["mutter_djupn"]
stativ_hol = sekskant(stv["senter"][0], stv["senter"][1], stv["mutter_af"], sk_["z_botn"] - 1, z_mutter)
stativ_hol += Pos(stv["senter"][0], stv["senter"][1], z_mutter - 0.01) * loft([Rot(0, 0, 30) * RegularPolygon(stv["mutter_af"] / 2 / math.cos(math.radians(30)), 6), Pos(0, 0, stv["tak_z"] - z_mutter + 0.01) * Circle(stv["hol_d"] / 2)])
tid("opningar")

# --- detaljar skorne i overflata ---------------------------------------------
YTRE_BLOKK = KOMP["kropp"]
KROPP = KROPP0_LASTA if KROPP0_LASTA is not None else KROPP0
dz = S["deling_z"]


def band_z(flate, z0, tjukn, breidd, region=None):
    ytre = region if region is not None else offset(flate, 1.0)
    b = ytre - offset(flate, -tjukn)
    return extrude(b, breidd).moved(Pos(0, 0, z0 - breidd / 2))


def kropp_snitt(z):
    sek = section(KOMP["kropp"], Plane.XY.offset(z))
    return Sketch() + [Pos(0, 0, -z) * make_face(f.outer_wire()) for f in sek.faces()]


def polar_z(n, r0, r1, tjukn, senter, z, vinkel0=0.0):
    sk = Sketch() + [Rot(0, 0, vinkel0 + 360.0 * i / n) * Pos((r0 + r1) / 2, 0) * Rectangle(r1 - r0, tjukn) for i in range(n)]
    return Pos(senter[0], senter[1], z[0]) * extrude(sk, z[1] - z[0])


def polar_x(n, r0, r1, tjukn, x, vinkel0=0.0, y=ay, z=az):
    return Pos(x[0], y, z) * Rot(0, 90, 0) * extrude(Sketch() + [Rot(0, 0, vinkel0 + 360.0 * i / n) * Pos((r0 + r1) / 2, 0) * Rectangle(r1 - r0, tjukn) for i in range(n)], x[1] - x[0])


def linse_r(x):
    pr = np.asarray(L["profil"])
    return float(np.interp(x, pr[:, 0], pr[:, 1]))


ri = D["riller"]
tid("riller")
over_golv = boks([-50, 200], [-50, 200], [D["knurl_z_min"], 200])
KNURL = Part()
for kn, v0 in ((D["knurl_linse2"], 3.0),):
    rm = linse_r((kn["x"][0] + kn["x"][1]) / 2)
    KNURL += polar_x(kn["n"], rm - kn["djupn"], rm + 1.5, kn["tjukn"], kn["x"], v0) & over_golv
pl = D["panel_linje"]
rp = linse_r(pl["x"])
PANEL = (xsyl(pl["x"] - pl["breidd"] / 2, pl["x"] + pl["breidd"] / 2, rp + 1.5) - xsyl(pl["x"] - 1, pl["x"] + 1, rp - pl["djupn"])) & over_golv
KNURL = (KNURL + PANEL) - YTRE_BLOKK
hs = D["hjulskala"]
HJULSKALA = polar_z(hs["n"], hs["r"][0], hs["r"][1], hs["tjukn"], (hx, hy), hs["z"]) + polar_z(hs["n"] // hs["lang_kvar"], hs["r"][0], hs["r_lang"], hs["tjukn"] + 0.2, (hx, hy), hs["z"])
nm = D["namn"]
tekst = Text(nm["tekst"], nm["hogd"] * 1.36, font_path=str(pathlib.Path("/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf")), rotation=nm["retning"])
NAMN = Pos(nm["senter"][0], nm["senter"][1], nm["z"] - nm["djupn"]) * extrude(tekst, nm["djupn"] + 1.0)
OKULARKNURL = polar_x(ok_r["n"], ok_r["r_indre"] + 0.8, ok_r["r_ytre"] + 1.0, ok_r["tjukn"], [ok_r["x"][0] - 0.5, ok_r["x"][0] + ok_r["djupn"]], 0.0, oc[0], oc[1])
tid("detaljar")

# --- saumar: spor der dei to gråtonane møtest --------------------------------
sa = F["saum"]
sb = F["sokar"]
sokar_flate = Pos((sb["x"][0] + sb["x"][1]) / 2, (sb["y"][0] + sb["y"][1]) / 2) * RectangleRounded(sb["x"][1] - sb["x"][0], sb["y"][1] - sb["y"][0], sb["fillet"])
saum_sokar = band_z(sokar_flate, sa["z"], sa["djupn"], sa["breidd"]) & boks([-10, sb["x"][1] - 0.5], [-10, 200], [-10, 200])
saum_hjul = band_z(Pos(hx, hy) * Circle(hr), sa["z"], sa["djupn"], sa["breidd"])
saum_knapp = band_z(Pos(ux, uy) * Circle(F["knappboss"]["r"]), sa["z"], sa["djupn"], sa["breidd"])
andre = union([KOMP[n] for n in KOMP if n not in ("kropp", "sokar", "hjulboss", "knappboss", "linse")])
SAUM = (saum_sokar + saum_hjul + saum_knapp) - andre
tid("saumar")

kutt_ = [("knurl", KNURL), ("ef_skruar", EF_SKRUAR), ("ef_prikk", EF_PRIKK), ("hjulskala", HJULSKALA), ("namn", NAMN), ("okularknurl", OKULARKNURL), ("saum", SAUM)]
for namn_, op_ in ([] if KROPP0_LASTA is not None else kutt_):
    try:
        ny_ = KROPP - op_
    except Exception as e_:
        print("   feil i kutt", namn_, e_)
        ny_ = None
    ok_ = ny_ is not None and ny_.is_valid and len(ny_.solids()) == 1
    if not ok_ and ny_ is not None:
        try:
            ny_ = ny_.fix()
            ok_ = ny_.is_valid and len(ny_.solids()) == 1
        except Exception as e_:
            ok_ = False
        print("   fix etter", namn_, "gyldig", ok_)
    if ok_:
        KROPP = Solid(ny_.solids()[0].wrapped)
    else:
        print("   HOPPA OVER", namn_, "(ugyldig resultat)")
    tid("  - " + namn_)
print("KROPP0 med detaljar gyldig", KROPP.is_valid, "solidar", len(KROPP.solids()))
KROPP0 = KROPP
if KROPP0_LASTA is None:
    KROPP0 = Solid((KROPP0 + EF_KNAPP).solids()[0].wrapped)
    print("utløysarknapp for objektivet lagd til: gyldig", KROPP0.is_valid, "skal", len(KROPP0.shells()))
    export_brep(KROPP0, KROPP0_CACHE)

# --- holkjerne ---------------------------------------------------------------
v = S["vegg"]
KJERNE = cf.holrom_loft() & boks([-50, S["front_x"]], [-50, 200], [-50, 200])
vern = vsyl(bx, by, 8.8, lomme_botn - v, 90.0)
vern += vsyl(ux, uy, ut_["brunn_r"] + v, brunn_golv - v, 90)
uh = S["usb_hylse"]
vern += rboks_y(y_hjul_usb - uh["djupn"], y_hjul_usb + 5, x_usb, az + 2.0, ut_t["b_x"] + 2 * uh["vegg"], ut_t["h_z"] + 4 + 2 * uh["vegg"], ut_t["r"] + uh["vegg"])
kjol_b = ut_t["b_x"] + 2 * uh["vegg"]
kjol_zu = az + 2.0 - (ut_t["h_z"] + 4 + 2 * uh["vegg"]) / 2
kjol_prof = Polygon((x_usb - kjol_b / 2, kjol_zu + 0.5), (x_usb, kjol_zu + 0.5 - kjol_b / 2), (x_usb + kjol_b / 2, kjol_zu + 0.5), align=None)
vern += Pos(0, y_hjul_usb - uh["djupn"], 0) * Rot(90, 0, 0) * extrude(kjol_prof, -(5 + uh["djupn"]))
vern += boks([ug["x"] - r_s - v, ug["x"] + r_s + v], [y_grep - 3, y_grep + ug["djupn"] + v], [ug["z"] - ug["lengd_z"] / 2 - v, ug["z"] + ug["lengd_z"] / 2 + v])
vern += boks([hx - pw / 2 - v, hx + pw / 2 + v], [hy - pd / 2 - v, hy + pd / 2 + v], [S["tak_z"] - 6, 90])
vern += vsyl(stv["senter"][0], stv["senter"][1], stv["boss_r"], sk_["z_botn"] - 1, stv["boss_z_topp"])
dz = S["deling_z"]
SOYLER = union([vsyl(x, y, S["soyle_r_magnet"], -10, S["tak_z"] + 1) for x, y in S["magnetar"]] + [vsyl(x, y, S["soyle_r_pinne"], -10, S["tak_z"] + 1) for x, y in S["pinnar"]])
sp = S["stolpe"]
kl = sp["klaring"]
x0, x1 = x_tappar - sp["bak"], x_cam_front + sp["fram"]
STOLPAR = boks([x0, x1], [y_sd - kl - sp["ende"], y_sd + sp["inn"]], [-10, S["tak_z"] + 1]) + boks([x0, x1], [y_ant - sp["inn"], y_ant + kl + sp["ende"]], [-10, S["tak_z"] + 1])
spor = tak_boks([x_cam_bak - kl, x_cam_front + kl], [y_sd - kl, y_ant + kl], [z_lag - kl, z_hog + kl])
spor += tak_boks([x_mb_botn - kl, x_mb_topp + kl], [y_usb - st["mb_lengd"] - kl, y_usb + kl], [z_lag - kl, z_hog + kl])
spor += tak_boks([x_cam_front - 0.01, x1 + 1.0], [y_sd - 10, y_sd + 16], [az - 7.5 - kl, z_hog + kl])
spor += tak_boks([x_kort - 0.4, x_kort + 1.2], [y_sd - 10, y_sd + 13], [az - 5.5 - 0.4, z_hog + kl])
spor += boks([x_cam_front - 0.01, x1 + 1], [y_sd - 10, y_sd + 13], [-10, sp["leidning_z"]])
spor += tak_boks([x_cam_bak - 3.2 - kl, x_cam_bak + 0.01], [y_sd + 14.5 - kl, y_ant + kl], [az - 9.0 - kl, z_hog + kl])
spor += tak_boks([x_mb_topp - 0.01, x_mb_topp + 3.0 + kl], [y_usb - 6.5, y_usb + 1.0], [az - 4.0 - kl, z_hog + kl])
spor += rboks_y_tak(y_usb - 1.0, y_usb + 30, x_usb, az, 9.4, 11.6, 1.8)
STOLPAR -= spor
tid("kjerne+stolpar")
KJ = KJERNE - vern - SOYLER - STOLPAR
tid("kjerne - soyler")


def hol_solid(ytre, indre):
    """Solid med holrom: ytre skal + dei indre skala snudde, utan boolsk operasjon."""
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeSolid
    from OCP.BRepLib import BRepLib
    from OCP.TopoDS import TopoDS
    skal = getattr(TopoDS, "Shell_s", None) or TopoDS.Shell
    orient = getattr(BRepLib, "OrientClosedSolid_s", None) or BRepLib.OrientClosedSolid
    ys = sorted(ytre.solids()[0].shells(), key=lambda sh: -sh.bounding_box().diagonal)
    behald = []
    for sh in ys[1:]:
        bb = sh.bounding_box()
        tynn = min(bb.size.X, bb.size.Y, bb.size.Z) < 0.5
        print("   indre skal i ytre kropp:", [round(v, 1) for v in (bb.min.X, bb.min.Y, bb.min.Z, bb.max.X, bb.max.Y, bb.max.Z)], "(fjerna, tynnare enn 0,5 mm)" if tynn else "(behalden)")
        if not tynn:
            behald.append(sh)
    ms = BRepBuilderAPI_MakeSolid(skal(ys[0].wrapped))
    for sh in behald:
        ms.Add(skal(sh.wrapped))
    for sol in indre.solids():
        for sh in sol.shells():
            ms.Add(skal(sh.wrapped.Reversed()))
    s = ms.Solid()
    orient(s)
    return Solid(s)


KROPP = hol_solid(KROPP0, KJ)
print("hol kropp gyldig", KROPP.is_valid, "solidar", len(KROPP.solids()), "skal", len(KROPP.solids()[0].shells()))
tid("kropp med holrom")
for namn_, op_ in (("sete", sete), ("konus", konus), ("ef_hals", ef_hals), ("ef_kammer", ef_kammer), ("ef_sensor", ef_sensor), ("brunn", brunn), ("brytarlomme", brytarlomme), ("brytarhol", brytarhol), ("usb_tunnel", usb_tunnel),
                   ("usbc", usbc), ("okular", okular), ("EC11", EC11), ("stativ_hol", stativ_hol)):
    KROPP = KROPP - op_
    tid("  - " + namn_)
KROPP = KROPP + EF_KLOR + EF_KONTAKT
KROPP = KROPP - EF_KONTAKTHOL
print("EF-klør og kontaktar lagde til: gyldig", KROPP.is_valid, "solidar", len(KROPP.solids()))
tid("ef-klør")
print("KROPP gyldig", KROPP.is_valid, "solidar", len(KROPP.solids()))

if "--form" in sys.argv:
    export_stl(KROPP, UT / "stl" / "kropp.stl", tolerance=0.02, angular_tolerance=0.15)
    tid("stl kropp")
    sys.exit()

# --- lause delar ---------------------------------------------------------------
KNAPP = KROPP0 & vsyl(ux, uy, ut_["kapp_r"], ut_["kapp_z"], 90)
lokk_ytre = rboks_y_tak(y_hjul_usb - ut_t["lokk_lengd"], y_hjul_usb + 6, x_usb, az, ut_t["b_x"] - 2 * ut_t["lokk_klaring"], ut_t["h_z"] - 2 * ut_t["lokk_klaring"], max(ut_t["r"] - ut_t["lokk_klaring"], 0.5))
USBLOKK = KROPP0 & lokk_ytre
AKSEL = vsyl(hx, hy, ec["hol_d"] / 2 - 0.15, ec["hol_botn_z"], ec["mutter_botn_z"] + 0.01) + vsyl(hx, hy, ec["mutter_d"] / 2 - 0.15, ec["mutter_botn_z"], ec["kapp_z"])
AKSEL += vsyl(hx, hy, 3.0, ec["kapp_z"], ec["kapp_z"] + 5.5) - boks([hx - 5, hx + 5], [hy + 1.5, hy + 5], [ec["kapp_z"] + 0.5, ec["kapp_z"] + 6])

# --- deling, magnetar og pinnar -----------------------------------------------
mg_d, mg_h = K["magnetar"]["d"] + K["magnetar"]["klaring_d"], K["magnetar"]["h"] + K["magnetar"]["klaring_h"]
pn = S["pinne"]
mag_lommer = union([vsyl(x, y, mg_d / 2, dz - mg_h, dz + mg_h) + kjeglehol(x, y, mg_d / 2, 0.3, dz + mg_h - 0.01, dz + mg_h - 0.01 + mg_d / 2 - 0.3) for x, y in S["magnetar"]])
pinnar = union([vsyl(x, y, pn["d"] / 2, dz - 0.5, dz + pn["h"] - pn["fas"]) + kjeglehol(x, y, pn["d"] / 2, pn["d"] / 2 - pn["fas"], dz + pn["h"] - pn["fas"], dz + pn["h"]) for x, y in S["pinnar"]])
pinnehol = union([vsyl(x, y, pn["d"] / 2 + pn["klaring"], dz - 1, dz + pn["h"] + 0.5) + kjeglehol(x, y, pn["d"] / 2 + pn["klaring"] + pn["fas"], pn["d"] / 2 + pn["klaring"], dz - 0.01, dz + pn["fas"] - 0.01) for x, y in S["pinnar"]])
NED = boks([-50, 200], [-50, 200], [-50, dz])
OPP = boks([-50, 200], [-50, 200], [dz, 200])
df_ = D["delingsfas"]
snitt = section(FORM, Plane.XY.offset(dz))
fas_flate = Sketch() + [Pos(0, 0, -dz) * make_face(f.outer_wire()) for f in snitt.faces()]
fas = band_z(fas_flate, dz, df_["djupn"], 2 * df_["breidd"] + 0.2, Pos(-20, -20) * Rectangle(150, 160, align=(Align.MIN, Align.MIN)))
BOTN = ((KROPP & NED) - mag_lommer) + pinnar - (fas & boks([-50, 200], [-50, 200], [-50, dz + 0.1]))
TOPP = (KROPP & OPP) - mag_lommer - pinnehol - (fas & boks([-50, 200], [-50, 200], [dz - 0.1, 200]))
tid("deling")


def rydd(m):
    return union([s for s in m.solids() if s.volume > 0.05])


DELAR = {"botn": rydd(BOTN), "topp": rydd(TOPP), "utloysar": KNAPP, "usb-lokk": USBLOKK, "hjulaksel": AKSEL}


def skriv_stl(m, fil):
    import trimesh
    export_stl(m, fil, tolerance=0.01, angular_tolerance=0.08)
    t = trimesh.load(fil, process=True)
    t.update_faces(t.nondegenerate_faces())
    t.merge_vertices()
    if not t.is_watertight:
        trimesh.repair.fill_holes(t)
    t.export(fil)
    return t.is_watertight, round(t.volume / 1000, 2)


for n, m in DELAR.items():
    vasstett, vol = skriv_stl(m, UT / "stl" / f"{n}.stl")
    print(f"{n:<10} gyldig {m.is_valid!s:<5} solidar {len(m.solids())}  stl vasstett {vasstett!s:<5} volum {vol:6.2f} cm3")
    export_step(m, UT / "step" / f"{n}.step")
tid("eksport")
