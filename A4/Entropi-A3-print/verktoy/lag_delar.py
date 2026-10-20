import json, sys, pathlib
import numpy as np, trimesh
from manifold3d import Manifold, Mesh, CrossSection, JoinType, FillRule

HER = pathlib.Path(__file__).resolve().parent
K = json.loads((HER / (sys.argv[1] if len(sys.argv) > 1 else "delar_konfig.json")).read_text())
UT = (HER / K["ut_mappe"]).resolve()
for d in ("stl", "proxy"):
    (UT / d).mkdir(parents=True, exist_ok=True)
SEG = 96


def til_manifold(tm):
    return Manifold(Mesh(vert_properties=np.asarray(tm.vertices, np.float32), tri_verts=np.asarray(tm.faces, np.uint32)))


def til_trimesh(m):
    g = m.to_mesh()
    return trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=False)


def boks(x, y, z):
    return Manifold.cube([x[1] - x[0], y[1] - y[0], z[1] - z[0]]).translate([x[0], y[0], z[0]])


def vsyl(cx, cy, r, z0, z1):
    return Manifold.cylinder(z1 - z0, r, r, SEG).translate([cx, cy, z0])


def xskive(x, y, z, r, t=0.01):
    return Manifold.cylinder(t, r, r, SEG).rotate([0, 90, 0]).translate([x, y, z])


def rboks_x(x0, x1, yc, zc, by, hz, r):
    cs = CrossSection.square([by - 2 * r, hz - 2 * r]).offset(r, JoinType.Round, circular_segments=24)
    return cs.extrude(x1 - x0).rotate([90, 0, 90]).translate([x0, yc - by / 2 + r, zc - hz / 2 + r])


def rboks_y(y0, y1, xc, zc, bx, hz, r):
    return Manifold.batch_hull([Manifold.cylinder(y1 - y0, r, r, 32).rotate([-90, 0, 0]).translate([xc + sx * (bx / 2 - r), y0, zc + sz * (hz / 2 - r)])
                                for sx in (-1, 1) for sz in (-1, 1)])


def rboks_y_tak(y0, y1, xc, zc, bx, hz, r):
    topp = zc + hz / 2 - r + (bx / 2 - r) + r * np.sqrt(2)
    return Manifold.batch_hull([rboks_y(y0, y1, xc, zc, bx, hz, r), Manifold.cylinder(y1 - y0, 0.2, 0.2, 12).rotate([-90, 0, 0]).translate([xc, y0, topp - 0.2])])


def draape(a, b, r):
    a, b = np.array(a, float), np.array(b, float)
    opp, tupp = np.array([0, 0, r * 0.6]), np.array([0, 0, r * 0.6 + r * np.sqrt(2) - 0.2])
    return Manifold.batch_hull([Manifold.sphere(r, 32).translate(p) for p in (a, b, a + opp, b + opp)] + [Manifold.sphere(0.2, 12).translate(p) for p in (a + tupp, b + tupp)])


def prisme(poly, z0, z1):
    return CrossSection([[tuple(p) for p in poly]], FillRule.Positive).extrude(z1 - z0).translate([0, 0, z0])


def tunnel(a, b, r):
    a, b = np.array(a, float), np.array(b, float)
    return Manifold.batch_hull([Manifold.sphere(r, 32).translate(a), Manifold.sphere(r, 32).translate(b)])


kjelde = trimesh.load(HER / K["kjelde_stl"])
ORIG = til_manifold(kjelde)
ay, az = K["akse"]["y"], K["akse"]["z"]
st, rom = K["stabel"], K["rom"]
golv = K["golv_z"]


def flate(o, d):
    loc, _, _ = kjelde.ray.intersects_location(np.array([o], float), np.array([d], float), multiple_hits=False)
    return loc[0] if len(loc) else None


def flate_y(x, z, fraa_minus):
    p = flate([x, -10.0 if fraa_minus else 130.0, z], [0, 1.0 if fraa_minus else -1.0, 0])
    return float(p[1])


# --- formrettingar -------------------------------------------------------
yv = max(flate_y(9, 67.5, True), flate_y(9, 81.5, True)) + 0.05
yh = min(flate_y(9, 67.5, False), flate_y(9, 81.5, False)) - 0.05
sokar_fyll = boks([2.0, 16.5], [yv, yh], [69.5, 80.5])
hf = K["usbc_hjul_fyll"]
y_panel = float(np.median([flate_y(x, z, False) for x, z in [(24.0, 27.0), (30.6, 27.0), (27.2, 21.5), (27.2, 32.5)]]))
hjul_fyll = boks(hf["x"], [y_panel - 3.0, y_panel], hf["z"])
KROPP0 = ORIG + sokar_fyll + hjul_fyll

ug = K["usbc_grep"]
y_grep = float(np.median([flate_y(x, z, True) for x, z in [(24.0, 27.0), (30.6, 27.0), (27.2, 21.0), (27.2, 33.0)]]))
r_s = ug["breidd_x"] / 2
usbc = Manifold.batch_hull([Manifold.cylinder(ug["djupn"] + 3, r_s, r_s, 48).rotate([-90, 0, 0]).translate([ug["x"], y_grep - 3, ug["z"] + s * (ug["lengd_z"] / 2 - r_s)]) for s in (-1, 1)])
ok = K["sokar"]["okular"]
okular = sum((rboks_x(-1, d, ok["y"], ok["z"], b, h, 1.5) for b, h, d in (ok["ytre"], ok["indre"])), Manifold())

# --- stabelen (ESP32-CAM på MB), liggjande med linsa i +x ---------------
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
z_lag, z_hog = rom["golv_front_z"] + 0.2, rom["golv_front_z"] + 0.2 + st["cam_breidd"]
x_usb = x_mb_topp + st["usb_akse_over_mb"]

# --- holrom --------------------------------------------------------------
sm = rom["smal"]
romA = boks([rom["bak_x"], rom["deling_x"]], rom["y"], [rom["golv_front_z"] - 0.01, rom["tak_z"]])
romA += boks([rom["bak_x"], rom["deling_x"]], [rom["y"][0], sm["y_fraa"]], [golv - 0.01, rom["golv_front_z"]])
romA += boks([rom["bak_x"], sm["x_maks"]], [sm["y_fraa"] - 0.01, rom["y"][1]], [golv - 0.01, rom["golv_front_z"]])
romA += boks([rom["bak_x"], rom["deling_x"]], [sm["y_fraa"] - 0.01, rom["y"][1]], [sm["z_under"], rom["golv_front_z"]])
ksp_ = rom["knappespor"]
romA += boks([rom["bak_x"], rom["deling_x"]], ksp_["y"], [rom["tak_z"] - 0.01, ksp_["z_topp"]])
romB = boks([rom["deling_x"] - 0.01, rom["front_x"]], rom["y"], [rom["golv_front_z"], rom["tak_z"]])
kg, fs = rom["kabelgap"], rom["frontstopp"]
kabelgap = boks(kg["x"], [kg["y_fraa"], rom["y"][0] + 0.01], [kg["z_fraa"], rom["tak_z"]])
sk = K["sd_kort"]
x_kort = x_cam_front + 0.6
sd_spor = boks([x_kort - (x_tappar - rom["bak_x"] - 0.1) - sk["klaring"], rom["deling_x"] + 0.01], [sk["spor_y_fraa"], rom["y"][0] + 0.01], [golv - 0.01, az + 5.5 + sk["klaring"]])
sd_spor += boks([rom["deling_x"], x_kort + 0.8 + sk["klaring"]], [sk["spor_y_fraa"], rom["y"][0] + 0.01], [az - 5.5 - sk["klaring"], az + 5.5 + sk["klaring"]])
frontstopp = sum((boks([x_cam_front + fs["klaring"], rom["front_x"] + 0.01], fs["y"], z) for z in fs["z"]), Manifold())
ks, lk = K["kamerasete"], K["linsekonus"]
sete = boks([rom["front_x"] - 0.1, x_konus + 0.8], [ay - ks["side"] / 2, ay + ks["side"] / 2], [az - ks["side"] / 2, az + ks["side"] / 2])
konus = Manifold.batch_hull([xskive(x_konus, ay, az, lk["bak_r"]), xskive(lk["front_x"], ay, az, lk["front_r"])])
konus += Manifold.cylinder(lk["fram_til_x"] - lk["front_x"], lk["front_r"], lk["front_r"], SEG).rotate([0, 90, 0]).translate([lk["front_x"], ay, az])

ut_ = K["utloysar"]
ux, uy = ut_["senter"]
brunn_golv = ut_["kapp_z"] - ut_["vandring"]
brunn = vsyl(ux, uy, ut_["brunn_r"], brunn_golv, 80)
br = K["brytar"]
lomme_botn = ut_["kapp_z"] - br["hogd_med_bein"]
bx, by = br["senter"]
brytarlomme = boks([bx - br["side_x"] / 2, bx + br["side_x"] / 2], [by - br["side_y"] / 2, by + br["side_y"] / 2], [lomme_botn, brunn_golv + 0.1])
kt = K["kabeltunnel"]
kabeltunnel = draape([bx, by, lomme_botn + kt["r"] * 0.5], kt["slutt"], kt["r"])

ut_t = K["usb_tunnel"]
y_hjul_usb = flate_y(x_usb, az, False)
usb_tunnel = rboks_y_tak(rom["y"][1] - 0.5, y_hjul_usb + 5, x_usb, az, ut_t["b_x"], ut_t["h_z"], ut_t["r"])

lu, mg = K["luke"], K["magnetar"]
luke_prisme = prisme(lu["polygon"], -5, golv)
mag_d, mag_h = mg["d"] + mg["klaring_d"], mg["h"] + mg["klaring_h"]
mag_kropp = sum((vsyl(x, y, mag_d / 2, golv - 0.01, golv + mag_h) + Manifold.cylinder(mag_d / 2 - 0.3, mag_d / 2, 0.3, SEG).translate([x, y, golv + mag_h - 0.01]) for x, y in mg["pos"]), Manifold())
mag_luke = sum((vsyl(x, y, mag_d / 2, golv - mag_h, golv + 0.01) for x, y in mg["pos"]), Manifold())

HOLROM = romA + romB + sete + konus + brunn + brytarlomme + kabeltunnel + usb_tunnel + usbc + okular + kabelgap + sd_spor - frontstopp
KROPP = KROPP0 - luke_prisme - HOLROM - mag_kropp
luke_inn = CrossSection([[tuple(p) for p in lu["polygon"]]], FillRule.Positive).offset(-lu["klaring"], JoinType.Miter).extrude(golv + 5).translate([0, 0, -5])
LUKE = (KROPP0 ^ luke_inn) - mag_luke
nh = lu["negl_hakk"]
negl_hakk = boks(nh["x"], nh["y"], nh["z"])
KROPP -= negl_hakk
KNAPP = KROPP0 ^ vsyl(ux, uy, ut_["kapp_r"], ut_["kapp_z"], 80)

hd = K["haldar"]
c = hd["klaring"]
x_stopp = x_cam_front + rom["frontstopp"]["klaring"]
ksp = hd["kabelspor"]


def haldar(D):
    xf = x_stopp - D
    h = boks([rom["bak_x"] + c, xf - c], [rom["y"][0] + c, rom["y"][1] - c], [golv, rom["tak_z"] - 2.0])
    h += boks([xf - c - 0.01, rom["deling_x"] - c], [hd["vogge_y"][0], sm["y_fraa"] - c], [golv, z_lag - c])
    h += boks([xf - c - 0.01, sm["x_maks"] - c], [sm["y_fraa"] - 0.01, hd["vogge_y"][1]], [golv, z_lag - c])
    h += boks([xf - c - 0.01, x_mb_topp - 0.3], [rom["y"][0] + c, y_usb - st["mb_lengd"] - c], [golv, 34.0])
    h += boks([xf - c - 0.01, x_mb_topp - 0.3], [y_usb - st["mb_lengd"] - 0.6, hd["vogge_y"][0] + 0.1], [golv, z_lag - c])
    h += boks([xf - c - 0.01, x_mb_topp - 0.3], [y_usb + c, rom["y"][1] - c], [z_lag + 0.5, rom["tak_z"] - 2.0])
    h -= rboks_y(y_usb - 3.5, rom["y"][1] + 5, x_usb, az, ut_t["b_x"], ut_t["h_z"], ut_t["r"])
    h -= boks(ksp["x"], [ksp["y"][0] - 1, ksp["y"][1]], [golv - 1, rom["tak_z"]])
    return h


D_NOM = round(x_stopp - x_tappar, 2)
HALDAR = haldar(D_NOM)
HALDAR_VAR = {D: haldar(D) for D in hd["d_variantar"]}

lokk_ytre = rboks_y_tak(y_hjul_usb - ut_t["lokk_lengd"], y_hjul_usb + 6, x_usb, az, ut_t["b_x"] - 2 * ut_t["lokk_klaring"], ut_t["h_z"] - 2 * ut_t["lokk_klaring"], max(ut_t["r"] - ut_t["lokk_klaring"], 0.5))
USBLOKK = KROPP0 ^ lokk_ytre

# --- komponent-proxyar ----------------------------------------------------
yb = [y_sd, y_ant]
zb = [z_lag, z_hog]
P = {
    "mb_kort": boks([x_mb_botn, x_mb_topp], [y_usb - st["mb_lengd"], y_usb], zb),
    "mb_tappar": boks([x_tappar, x_mb_botn], [y_usb - st["mb_lengd"] + 2, y_usb - 4], [zb[0] + 1, zb[1] - 1]),
    "usb_kontakt": boks([x_mb_topp, x_mb_topp + 3.0], [y_usb - 6.0, y_usb + 0.4], [az - 4.0, az + 4.0]),
    "mb_knappar": boks([x_mb_topp, x_mb_topp + 3.0], [y_usb - st["knapp_fraa_usb"][1], y_usb - st["knapp_fraa_usb"][0]], [zb[0] - st["knapp_utstikk"], zb[1] + st["knapp_utstikk"]]),
    "headerar": boks([x_mb_topp, x_cam_bak], [y_sd + 3.3, y_sd + 23.6], [zb[0] + 0.8, zb[0] + 3.3]) + boks([x_mb_topp, x_cam_bak], [y_sd + 3.3, y_sd + 23.6], [zb[1] - 3.3, zb[1] - 0.8]),
    "esp32s": boks([x_cam_bak - 3.2, x_cam_bak], [y_sd + 14.5, y_ant], [az - 9.0, az + 9.0]),
    "cam_kort": boks([x_cam_bak, x_cam_front], yb, zb),
    "sd_kort": boks([x_kort, x_kort + 0.8], [y_sd - sk["utstikk"], y_sd + 12.0], [az - 5.5, az + 5.5]),
    "sd_og_fpc": boks([x_cam_front, x_cam_front + 2.0], [y_sd + 0.3, y_sd + 15.3], [az - 7.5, az + 7.5]) + boks([x_cam_front, x_cam_front + 2.7], [y_sd + 23.0, y_sd + 28.0], [az - 8.5, az + 8.5]),
    "kameramodul": boks([x_cam_front + 2.5, x_tupp - 1.9], [ay - 4.06, ay + 4.06], [az - 4.06, az + 4.06]) + Manifold.cylinder(1.9, 3.96, 3.96, 48).rotate([0, 90, 0]).translate([x_tupp - 1.9, ay, az]),
    "brytar6x6": boks([bx - 3, bx + 3], [by - 3, by + 3], [lomme_botn + 3.5, lomme_botn + 7.0]) + vsyl(bx, by, 1.75, lomme_botn + 7.0, ut_["kapp_z"] - 0.02)
                 + sum((boks([bx + sx * 3.25 - 0.35, bx + sx * 3.25 + 0.35], [by + sy * 2.25 - 0.4, by + sy * 2.25 + 0.4], [lomme_botn, lomme_botn + 3.6]) for sx in (-1, 1) for sy in (-1, 1)), Manifold()),
    "magnetar": sum((vsyl(x, y, mg["d"] / 2, golv, golv + mg["h"]) + vsyl(x, y, mg["d"] / 2, golv - mg["h"], golv) for x, y in mg["pos"]), Manifold()),
    "usb_plugg": rboks_y(y_usb + 0.3, y_usb + 26, x_usb, az, 8.5, 10.8, 1.5),
}

DELAR = {"kropp": KROPP, "luke": LUKE, "utloysar": KNAPP, "stabelhaldar": HALDAR, "usb-lokk": USBLOKK}

# --- kontroll -------------------------------------------------------------
STOR = boks([-20, 120], [-20, 140], [-20, 110])
UTE = STOR - KROPP0
rap = {"stabel_x": {"tappar": x_tappar, "mb_botn": x_mb_botn, "mb_topp": x_mb_topp, "cam_bak": x_cam_bak, "cam_front": x_cam_front, "linse_tupp": x_tupp},
       "stabel_y": {"sd_ende": y_sd, "antenne_ende": y_ant, "usb_munn": y_usb}, "stabel_z": [z_lag, z_hog], "usb_akse_x": x_usb,
       "usb_tunnel_ut_y": y_hjul_usb, "brytarlomme_botn_z": lomme_botn, "y_grep_flate": y_grep, "y_hjul_panel": y_panel,
       "delar": {}, "veggar_mm": {}, "kollisjonar_mm3": {}}
for n, m in DELAR.items():
    bb = m.bounding_box()
    rap["delar"][n] = {"status": str(m.status()), "volum_cm3": round(m.volume() / 1000, 3), "genus": m.genus(), "komponentar": len(m.decompose()),
                       "bbox": [[round(v, 2) for v in bb[:3]], [round(v, 2) for v in bb[3:]]]}
for n, h in {"rom_A": romA - luke_prisme, "rom_B": romB, "brytarlomme": brytarlomme, "kabeltunnel": kabeltunnel, "magnetlommer": mag_kropp, "kabelgap": kabelgap, "sd_spor": sd_spor,
             "usb_tunnel_sidevegg": usb_tunnel ^ boks([-50, 200], [rom["y"][1], min(flate_y(x_usb + sx * ut_t["b_x"] / 2, az + sz * ut_t["h_z"] / 2, False) for sx in (-1, 1) for sz in (-1, 1)) - 2.5], [-50, 200])}.items():
    rap["veggar_mm"][n] = round(h.min_gap(UTE, 15.0), 2)
rap["veggar_mm"]["usbc_mot_holrom"] = round(usbc.min_gap(romA + romB + brytarlomme + kabeltunnel, 30.0), 2)
rap["veggar_mm"]["okular_mot_holrom"] = round(okular.min_gap(romA + romB + kabeltunnel, 30.0), 2)
for n, p in P.items():
    rap["kollisjonar_mm3"][n] = {k: round((p ^ m).volume(), 3) for k, m in (("kropp", KROPP), ("luke", LUKE), ("haldar", HALDAR))}
for a, b in (("utloysar", "kropp"), ("stabelhaldar", "kropp"), ("luke", "kropp"), ("usb-lokk", "kropp"), ("stabelhaldar", "luke")):
    rap["kollisjonar_mm3"][f"{a}_mot_{b}"] = round((DELAR[a] ^ DELAR[b]).volume(), 3)
stabel = sum((P[k] for k in ("mb_kort", "mb_tappar", "usb_kontakt", "mb_knappar", "headerar", "esp32s", "cam_kort", "sd_og_fpc", "sd_kort", "kameramodul")), Manifold())
rap["stabel_klaring_mm"] = {"kropp": round(stabel.min_gap(KROPP, 5.0), 2), "haldar": round(stabel.min_gap(HALDAR, 5.0), 2)}
skyv = x_tappar - rom["bak_x"] - 0.1
sveip_lyft = sum((stabel.translate([-skyv, 0, -dz]) for dz in np.arange(0, 45.01, 1.0)), Manifold())
sveip_skyv = sum((stabel.translate([-dx, 0, 0]) for dx in np.arange(0, skyv + 0.01, 0.5)), Manifold())
sveip_haldar = sum((HALDAR.translate([0, 0, -dz]) for dz in np.arange(0, 45.01, 1.0)), Manifold())
rap["monteringsveg_kollisjon_mm3"] = {"stabel_lyft_opp_gjennom_luka": round((sveip_lyft ^ KROPP).volume(), 3),
                                      "stabel_skyv_fram_til_linsa": round((sveip_skyv ^ KROPP).volume(), 3),
                                      "haldar_lyft_opp_bak_stabelen": round((sveip_haldar ^ (KROPP + stabel)).volume(), 3)}
rap["stabel_innsetjing"] = {"skyv_fram_mm": round(x_tappar - rom["bak_x"], 2),
                            "stabel_inn_i_romA_ved_innsetjing": bool(((stabel.translate([-(x_tappar - rom["bak_x"] - 0.1), 0, 0])) - romA).volume() < 1e-3)}

poly = np.array(lu["polygon"])
gx, gy = np.meshgrid(np.arange(poly[:, 0].min(), poly[:, 0].max(), 0.5), np.arange(poly[:, 1].min(), poly[:, 1].max(), 0.5))
pts = np.c_[gx.ravel(), gy.ravel()]
inne = np.zeros(len(pts), bool)
for (x1, y1), (x2, y2) in zip(poly, np.roll(poly, -1, 0)):
    inne ^= ((y1 > pts[:, 1]) != (y2 > pts[:, 1])) & (pts[:, 0] < (x2 - x1) * (pts[:, 1] - y1) / (y2 - y1 + 1e-12) + x1)
pts = pts[inne]
loc, idx, _ = kjelde.ray.intersects_location(np.c_[pts, np.full(len(pts), -10.0)], np.tile([0, 0, 1.0], (len(pts), 1)), multiple_hits=False)
tj = golv - loc[:, 2]
rap["luke_tjukn_mm"] = {"min": round(float(tj.min()), 2), "p5": round(float(np.percentile(tj, 5)), 2), "min_ved": [round(float(v), 1) for v in pts[idx[np.argmin(tj)]]]}

for n, m in DELAR.items():
    til_trimesh(m).export(UT / "stl" / f"{n}.stl")
(UT / "stl" / "haldar-variantar").mkdir(exist_ok=True)
for D, m in HALDAR_VAR.items():
    til_trimesh(m).export(UT / "stl" / "haldar-variantar" / f"stabelhaldar-D{D:.1f}.stl")
rap["stabel_d_nominell"] = D_NOM
rap["haldar_variantar"] = {f"D{D:.1f}": {"front_x": round(x_stopp - D - c, 2), "kollisjon_mot_kropp_mm3": round((m ^ KROPP).volume(), 3),
                                         "klaring_til_stabel_mm": round(max(0.0, (x_tappar) - (x_stopp - D - c)), 2)} for D, m in HALDAR_VAR.items()}
for n, m in P.items():
    til_trimesh(m).export(UT / "proxy" / f"{n}.stl")
(UT / "kontroll.json").write_text(json.dumps(rap, indent=2, ensure_ascii=False))
print(json.dumps(rap, indent=1, ensure_ascii=False))
