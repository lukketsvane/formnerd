import json, sys, pathlib
import numpy as np, trimesh
from manifold3d import Manifold, Mesh, CrossSection, JoinType, FillRule
from scipy import ndimage
from skimage import measure

HER = pathlib.Path(__file__).resolve().parent
K = json.loads((HER / "delar_konfig.json").read_text())
S = K["skal"]
UT = (HER / K["ut_mappe"]).resolve()
for d in ("stl", "proxy"):
    (UT / d).mkdir(parents=True, exist_ok=True)
SEG = 96


def til_manifold(tm):
    return Manifold(Mesh(vert_properties=np.asarray(tm.vertices, np.float32), tri_verts=np.asarray(tm.faces, np.uint32)))


def til_trimesh(m):
    g = m.to_mesh()
    t = trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=True)
    t.merge_vertices()
    return t


def boks(x, y, z):
    return Manifold.cube([x[1] - x[0], y[1] - y[0], z[1] - z[0]]).translate([x[0], y[0], z[0]])


def vsyl(cx, cy, r, z0, z1, seg=SEG):
    return Manifold.cylinder(z1 - z0, r, r, seg).translate([cx, cy, z0])


def xskive(x, y, z, r, t=0.01):
    return Manifold.cylinder(t, r, r, SEG).rotate([0, 90, 0]).translate([x, y, z])


def rboks_x(x0, x1, yc, zc, by, hz, r):
    cs = CrossSection.square([by - 2 * r, hz - 2 * r]).offset(r, JoinType.Round, circular_segments=24)
    return cs.extrude(x1 - x0).rotate([90, 0, 90]).translate([x0, yc - by / 2 + r, zc - hz / 2 + r])


def rboks_y(y0, y1, xc, zc, bx, hz, r):
    return Manifold.batch_hull([Manifold.cylinder(y1 - y0, r, r, 32).rotate([-90, 0, 0]).translate([xc + sx * (bx / 2 - r), y0, zc + sz * (hz / 2 - r)])
                                for sx in (-1, 1) for sz in (-1, 1)])


def tak_boks(x, y, z):
    xm, w = (x[0] + x[1]) / 2, x[1] - x[0]
    return Manifold.batch_hull([boks(x, y, z), boks([xm - 0.05, xm + 0.05], y, [z[1] - 0.01, z[1] + w / 2])])


def rboks_y_tak(y0, y1, xc, zc, bx, hz, r):
    topp = zc + hz / 2 - r + (bx / 2 - r) + r * np.sqrt(2)
    return Manifold.batch_hull([rboks_y(y0, y1, xc, zc, bx, hz, r), Manifold.cylinder(y1 - y0, 0.2, 0.2, 12).rotate([-90, 0, 0]).translate([xc, y0, topp - 0.2])])


def voksel(m, h, pad=3, off=0.0137):
    lo = m.bounds[0] - pad * h + off
    n = np.ceil((m.bounds[1] + pad * h - lo) / h).astype(int)
    V = m.vertices[m.faces]
    tmin, tmax = V[:, :, :2].min(1), V[:, :, :2].max(1)
    i0 = np.ceil((tmin[:, 0] - lo[0]) / h - 0.5).astype(int); i1 = np.floor((tmax[:, 0] - lo[0]) / h - 0.5).astype(int)
    j0 = np.ceil((tmin[:, 1] - lo[1]) / h - 0.5).astype(int); j1 = np.floor((tmax[:, 1] - lo[1]) / h - 0.5).astype(int)
    ni, nj = np.maximum(i1 - i0 + 1, 0), np.maximum(j1 - j0 + 1, 0)
    cnt = ni * nj; keep = cnt > 0
    tid = np.repeat(np.nonzero(keep)[0], cnt[keep])
    start = np.cumsum(cnt[keep]) - cnt[keep]
    local = np.arange(tid.size) - np.repeat(start, cnt[keep])
    ii = i0[tid] + local // nj[tid]; jj = j0[tid] + local % nj[tid]
    px, py = lo[0] + (ii + 0.5) * h, lo[1] + (jj + 0.5) * h
    a, b, c = V[tid, 0], V[tid, 1], V[tid, 2]
    v0x, v0y, v1x, v1y = b[:, 0] - a[:, 0], b[:, 1] - a[:, 1], c[:, 0] - a[:, 0], c[:, 1] - a[:, 1]
    v2x, v2y = px - a[:, 0], py - a[:, 1]
    den = v0x * v1y - v1x * v0y
    ok = np.abs(den) > 1e-14
    u = (v2x * v1y - v1x * v2y) / np.where(ok, den, 1); v = (v0x * v2y - v2x * v0y) / np.where(ok, den, 1)
    ins = ok & (u >= 0) & (v >= 0) & (u + v <= 1)
    z = (a[:, 2] + u * (b[:, 2] - a[:, 2]) + v * (c[:, 2] - a[:, 2]))[ins]
    k = np.clip(np.floor((z - lo[2]) / h - 0.5).astype(int) + 1, 0, n[2])
    acc = np.zeros((n[0], n[1], n[2] + 1), np.uint8)
    np.add.at(acc, (ii[ins], jj[ins], k), 1)
    return (np.cumsum(acc, axis=2, dtype=np.uint16) % 2).astype(bool)[:, :, :n[2]], lo


kjelde = trimesh.load(HER / K["kjelde_stl"])
ORIG = til_manifold(kjelde)
ay, az = K["akse"]["y"], K["akse"]["z"]
st = K["stabel"]


def flate(o, d):
    loc, _, _ = kjelde.ray.intersects_location(np.array([o], float), np.array([d], float), multiple_hits=False)
    return loc[0] if len(loc) else None


def flate_y(x, z, fraa_minus):
    return float(flate([x, -10.0 if fraa_minus else 130.0, z], [0, 1.0 if fraa_minus else -1.0, 0])[1])


# --- formrettingar (som i lag_delar.py) ------------------------------------
yv = max(flate_y(9, 67.5, True), flate_y(9, 81.5, True)) + 0.05
yh = min(flate_y(9, 67.5, False), flate_y(9, 81.5, False)) - 0.05
hf = K["usbc_hjul_fyll"]
y_panel = float(np.median([flate_y(x, z, False) for x, z in [(24.0, 27.0), (30.6, 27.0), (27.2, 21.5), (27.2, 32.5)]]))
KROPP0 = ORIG + boks([2.0, 16.5], [yv, yh], [69.5, 80.5]) + boks(hf["x"], [y_panel - 3.0, y_panel], hf["z"])


def xsyl(x0, x1, r):
    return Manifold.cylinder(x1 - x0, r, r, SEG).rotate([0, 90, 0]).translate([x0, ay, az])


lt = S["linsetrakt"]
KROPP0 += (ORIG ^ xsyl(lt["fyll_x"][0], lt["fyll_x"][1], lt["slab_r"])).hull() ^ xsyl(lt["fyll_x"][0], lt["fyll_x"][1], lt["fyll_r"])

# --- hjulet: skoren av, EC11 under A17-knappen ------------------------------
ec = S["ec11"]
gx, gy = np.meshgrid(np.arange(15, 48, 0.5), np.arange(90, 122, 0.5))
O = np.c_[gx.ravel(), gy.ravel(), np.full(gx.size, 120.0)]
loc, ir, _ = kjelde.ray.intersects_location(O, np.tile([0, 0, -1.0], (len(O), 1)), multiple_hits=False)
hjul = loc[loc[:, 2] > ec["kapp_z"] + 1.0]
hx, hy = hjul[:, 0].mean(), hjul[:, 1].mean()
hr = float(np.hypot(hjul[:, 0] - hx, hjul[:, 1] - hy).max())
KROPP0 -= vsyl(hx, hy, hr + ec["lomme_r_ekstra"], ec["kapp_z"], 120)
pw, pd = ec["pipe"]
ec_hol = vsyl(hx, hy, ec["hol_d"] / 2, ec["hol_botn_z"] - 0.01, ec["kapp_z"] + 5) + vsyl(hx, hy, ec["mutter_d"] / 2, ec["mutter_botn_z"], ec["kapp_z"] + 5)
ec_pipe = boks([hx - pw / 2, hx + pw / 2], [hy - pd / 2, hy + pd / 2], [S["tak_z"] - 10.0, ec["tak_botn_z"]])
ec_pipe += Manifold.batch_hull([boks([hx - pw / 2, hx + pw / 2], [hy - pd / 2, hy + pd / 2], [ec["tak_botn_z"] - 0.01, ec["tak_botn_z"]]),
                                vsyl(hx, hy, ec["hol_d"] / 2, ec["hol_botn_z"] - 0.01, ec["hol_botn_z"])])
EC11 = ec_hol + ec_pipe

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

# --- opningar gjennom skalet -------------------------------------------------
ks, lk = K["kamerasete"], K["linsekonus"]
sete = boks([S["front_x"] - 1.0, x_konus + 0.8], [ay - ks["side"] / 2, ay + ks["side"] / 2], [az - ks["side"] / 2, az + ks["side"] / 2])
konus = Manifold.batch_hull([xskive(x_konus, ay, az, lk["bak_r"]), xskive(lk["front_x"], ay, az, lk["front_r"])])
konus += Manifold.cylinder(lk["fram_til_x"] - lk["front_x"], lk["front_r"], lk["front_r"], SEG).rotate([0, 90, 0]).translate([lk["front_x"], ay, az])
trakt = sum((Manifold.batch_hull([xskive(x1, ay, az, r1), xskive(x2, ay, az, r2)]) for (r1, x1), (r2, x2) in zip(lt["profil"][:-1], lt["profil"][1:])), Manifold())
ut_ = K["utloysar"]
ux, uy = ut_["senter"]
brunn_golv = ut_["kapp_z"] - ut_["vandring"]
brunn = vsyl(ux, uy, ut_["brunn_r"], brunn_golv, 90)
br = K["brytar"]
lomme_botn = ut_["kapp_z"] - br["hogd_med_bein"]
bx, by = br["senter"]
brytarlomme = boks([bx - br["side_x"] / 2, bx + br["side_x"] / 2], [by - br["side_y"] / 2, by + br["side_y"] / 2], [lomme_botn, brunn_golv + 0.1])
bt = S["brytartrakt"]
brytarhol = vsyl(bx, by, bt["leidning_r"], 20.0, lomme_botn + 0.5, 32)
ut_t = K["usb_tunnel"]
y_hjul_usb = flate_y(x_usb, az, False)
usb_tunnel = rboks_y_tak(y_usb - 1.0, y_hjul_usb + 5, x_usb, az, ut_t["b_x"], ut_t["h_z"], ut_t["r"])
ug = K["usbc_grep"]
y_grep = float(np.median([flate_y(x, z, True) for x, z in [(24.0, 27.0), (30.6, 27.0), (27.2, 21.0), (27.2, 33.0)]]))
r_s = ug["breidd_x"] / 2
usbc = Manifold.batch_hull([Manifold.cylinder(ug["djupn"] + 3, r_s, r_s, 48).rotate([-90, 0, 0]).translate([ug["x"], y_grep - 3, ug["z"] + s * (ug["lengd_z"] / 2 - r_s)]) for s in (-1, 1)])
ok_ = K["sokar"]["okular"]
okular = sum((rboks_x(-1, d, ok_["y"], ok_["z"], b, h, 1.5) for b, h, d in (ok_["ytre"], ok_["indre"])), Manifold())

# --- holkjerne: jamn vegg innanfor overflata ---------------------------------
h = S["voksel"]
fast, lo = voksel(til_trimesh(KROPP0), h)
avst = ndimage.distance_transform_edt(fast).astype(np.float32) * h
vf, fl, _, _ = measure.marching_cubes(np.pad(avst, 1), level=S["vegg"], spacing=(h, h, h))
kjerne_tm = trimesh.Trimesh(vf + lo - h, fl[:, ::-1], process=True)
if kjerne_tm.volume < 0:
    kjerne_tm.invert()
KJERNE = til_manifold(kjerne_tm) ^ boks([-50, S["front_x"]], [-50, 200], [-50, S["tak_z"]])
v = S["vegg"]
vern = Manifold.batch_hull([boks([bx - br["side_x"] / 2 - v, bx + br["side_x"] / 2 + v], [by - br["side_y"] / 2 - v, by + br["side_y"] / 2 + v], [lomme_botn - v, 90]),
                            boks([bx - bt["leidning_r"] - 1.2, bx + bt["leidning_r"] + 1.2], [by - bt["leidning_r"] - 1.2, by + bt["leidning_r"] + 1.2], [lomme_botn - v - (br["side_y"] / 2 + v - bt["leidning_r"] - 1.2), lomme_botn - v])])
vern += vsyl(ux, uy, ut_["brunn_r"] + v, brunn_golv - v, 90)
uh = S["usb_hylse"]
vern += rboks_y(y_hjul_usb - uh["djupn"], y_hjul_usb + 5, x_usb, az + 2.0, ut_t["b_x"] + 2 * uh["vegg"], ut_t["h_z"] + 4 + 2 * uh["vegg"], ut_t["r"] + uh["vegg"])
vern += Manifold.batch_hull([usbc.translate([0, -1.0, 0]), usbc.translate([0, v + 1.0, 0])]).translate([0, 0, 0]) + boks([ug["x"] - r_s - v, ug["x"] + r_s + v], [y_grep - 3, y_grep + ug["djupn"] + v], [ug["z"] - ug["lengd_z"] / 2 - v, ug["z"] + ug["lengd_z"] / 2 + v])
vern += boks([hx - pw / 2 - v, hx + pw / 2 + v], [hy - pd / 2 - v, hy + pd / 2 + v], [S["tak_z"] - 6, 90])

# --- søyler for magnetar og pinnar -------------------------------------------
dz = S["deling_z"]
SOYLER = sum((vsyl(x, y, S["soyle_r_magnet"], -10, S["tak_z"] + 1, 48) for x, y in S["magnetar"]), Manifold())
SOYLER += sum((vsyl(x, y, S["soyle_r_pinne"], -10, S["tak_z"] + 1, 48) for x, y in S["pinnar"]), Manifold())

# --- kortstolpar: stabelen fell rett ned i spor ------------------------------
sp = S["stolpe"]
kl = sp["klaring"]
x0, x1 = x_tappar - sp["bak"], x_cam_front + sp["fram"]


def stolpe(y0, y1):
    return boks([x0, x1], [y0, y1], [-10, S["tak_z"] + 1])


STOLPAR = stolpe(y_sd - kl - sp["ende"], y_sd + sp["inn"]) + stolpe(y_ant - sp["inn"], y_ant + kl + sp["ende"])
spor = tak_boks([x_cam_bak - kl, x_cam_front + kl], [y_sd - kl, y_ant + kl], [z_lag - kl, z_hog + kl])
spor += tak_boks([x_mb_botn - kl, x_mb_topp + kl], [y_usb - st["mb_lengd"] - kl, y_usb + kl], [z_lag - kl, z_hog + kl])
spor += tak_boks([x_cam_front - 0.01, x1 + 1.0], [y_sd - 10, y_sd + 16], [az - 7.5 - kl, z_hog + kl])
spor += tak_boks([x_kort - 0.4, x_kort + 1.2], [y_sd - 10, y_sd + 13], [az - 5.5 - 0.4, z_hog + kl])
spor += boks([x_cam_front - 0.01, x1 + 1], [y_sd - 10, y_sd + 13], [-10, sp["leidning_z"]])
spor += tak_boks([x_cam_bak - 3.2 - kl, x_cam_bak + 0.01], [y_sd + 14.5 - kl, y_ant + kl], [az - 9.0 - kl, z_hog + kl])
spor += tak_boks([x_mb_topp - 0.01, x_mb_topp + 3.0 + kl], [y_usb - 6.5, y_usb + 1.0], [az - 4.0 - kl, z_hog + kl])
spor += rboks_y_tak(y_usb - 1.0, y_usb + 30, x_usb, az, 9.4, 11.6, 1.8)
STOLPAR -= spor

# --- samanstilling ----------------------------------------------------------
HOLROM = (KJERNE - vern - SOYLER - STOLPAR) + sete + konus + trakt + brunn + brytarlomme + brytarhol + usb_tunnel + usbc + okular + EC11
KROPP = KROPP0 - HOLROM
KNAPP = KROPP0 ^ vsyl(ux, uy, ut_["kapp_r"], ut_["kapp_z"], 90)
lokk_ytre = rboks_y_tak(y_hjul_usb - ut_t["lokk_lengd"], y_hjul_usb + 6, x_usb, az, ut_t["b_x"] - 2 * ut_t["lokk_klaring"], ut_t["h_z"] - 2 * ut_t["lokk_klaring"], max(ut_t["r"] - ut_t["lokk_klaring"], 0.5))
USBLOKK = KROPP0 ^ lokk_ytre

mg_d, mg_h = K["magnetar"]["d"] + K["magnetar"]["klaring_d"], K["magnetar"]["h"] + K["magnetar"]["klaring_h"]
pn = S["pinne"]
mag_lommer = sum((vsyl(x, y, mg_d / 2, dz - mg_h, dz + mg_h, 48) + Manifold.cylinder(mg_d / 2 - 0.3, mg_d / 2, 0.3, 48).translate([x, y, dz + mg_h - 0.01]) for x, y in S["magnetar"]), Manifold())
pinnar = sum((vsyl(x, y, pn["d"] / 2, dz - 0.5, dz + pn["h"] - pn["fas"], 48) + Manifold.cylinder(pn["fas"], pn["d"] / 2, pn["d"] / 2 - pn["fas"], 48).translate([x, y, dz + pn["h"] - pn["fas"]]) for x, y in S["pinnar"]), Manifold())
pinnehol = sum((vsyl(x, y, pn["d"] / 2 + pn["klaring"], dz - 1, dz + pn["h"] + 0.5, 48) + Manifold.cylinder(pn["fas"], pn["d"] / 2 + pn["klaring"] + pn["fas"], pn["d"] / 2 + pn["klaring"], 48).translate([x, y, dz - 0.01]) for x, y in S["pinnar"]), Manifold())
OPP, NED = boks([-50, 200], [-50, 200], [dz, 200]), boks([-50, 200], [-50, 200], [-50, dz])
BOTN = ((KROPP ^ NED) - mag_lommer) + pinnar
TOPP = (KROPP ^ OPP) - mag_lommer - pinnehol
AKSEL = vsyl(hx, hy, ec["hol_d"] / 2 - 0.15, ec["hol_botn_z"], ec["mutter_botn_z"] + 0.01) + vsyl(hx, hy, ec["mutter_d"] / 2 - 0.15, ec["mutter_botn_z"], ec["kapp_z"]) + (vsyl(hx, hy, 3.0, ec["kapp_z"], ec["kapp_z"] + 5.5, 48) - boks([hx - 5, hx + 5], [hy + 1.5, hy + 5], [ec["kapp_z"] + 0.5, ec["kapp_z"] + 6]))

# --- proxyar ---------------------------------------------------------------
zb = [z_lag, z_hog]
P = {
    "mb_kort": boks([x_mb_botn, x_mb_topp], [y_usb - st["mb_lengd"], y_usb], zb),
    "mb_tappar": boks([x_tappar, x_mb_botn], [y_usb - st["mb_lengd"] + 2, y_usb - 4], [zb[0] + 1, zb[1] - 1]),
    "usb_kontakt": boks([x_mb_topp, x_mb_topp + 3.0], [y_usb - 6.0, y_usb + 0.4], [az - 4.0, az + 4.0]),
    "mb_knappar": boks([x_mb_topp, x_mb_topp + 3.0], [y_usb - st["knapp_fraa_usb"][1], y_usb - st["knapp_fraa_usb"][0]], [zb[0] - st["knapp_utstikk"], zb[1] + st["knapp_utstikk"]]),
    "headerar": boks([x_mb_topp, x_cam_bak], [y_sd + 3.3, y_sd + 23.6], [zb[0] + 0.8, zb[0] + 3.3]) + boks([x_mb_topp, x_cam_bak], [y_sd + 3.3, y_sd + 23.6], [zb[1] - 3.3, zb[1] - 0.8]),
    "pinnetappar": boks([x_cam_front, x_cam_front + 1.6], [y_sd + 3.3, y_sd + 23.6], [zb[0] + 1.3, zb[0] + 2.8]) + boks([x_cam_front, x_cam_front + 1.6], [y_sd + 3.3, y_sd + 23.6], [zb[1] - 2.8, zb[1] - 1.3]),
    "esp32s": boks([x_cam_bak - 3.2, x_cam_bak], [y_sd + 14.5, y_ant], [az - 9.0, az + 9.0]),
    "cam_kort": boks([x_cam_bak, x_cam_front], [y_sd, y_ant], zb),
    "sd_kort": boks([x_kort, x_kort + 0.8], [y_sd - sk["utstikk"], y_sd + 12.0], [az - 5.5, az + 5.5]),
    "sd_og_fpc": boks([x_cam_front, x_cam_front + 2.0], [y_sd + 0.3, y_sd + 15.3], [az - 7.5, az + 7.5]) + boks([x_cam_front, x_cam_front + 2.7], [y_sd + 23.0, y_sd + 28.0], [az - 8.5, az + 8.5]),
    "kameramodul": boks([x_cam_front + 2.5, x_tupp - 1.9], [ay - 4.06, ay + 4.06], [az - 4.06, az + 4.06]) + Manifold.cylinder(1.9, 3.96, 3.96, 48).rotate([0, 90, 0]).translate([x_tupp - 1.9, ay, az]),
    "brytar6x6": boks([bx - 3, bx + 3], [by - 3, by + 3], [lomme_botn + 3.5, lomme_botn + 7.0]) + vsyl(bx, by, 1.75, lomme_botn + 7.0, ut_["kapp_z"] - 0.02)
                 + sum((boks([bx + sx * 3.25 - 0.35, bx + sx * 3.25 + 0.35], [by + sy * 2.25 - 0.4, by + sy * 2.25 + 0.4], [lomme_botn, lomme_botn + 3.6]) for sx in (-1, 1) for sy in (-1, 1)), Manifold()),
    "magnetar": sum((vsyl(x, y, K["magnetar"]["d"] / 2, dz - K["magnetar"]["h"], dz + K["magnetar"]["h"], 48) for x, y in S["magnetar"]), Manifold()),
    "usb_plugg": rboks_y(y_usb + 0.3, y_usb + 26, x_usb, az, 8.5, 10.8, 1.5),
    "ec11": boks([hx - 6.2, hx + 6.2], [hy - 6.6, hy + 6.6], [ec["tak_botn_z"] - 7.0, ec["tak_botn_z"] - 0.5]) + vsyl(hx, hy, 3.5, ec["tak_botn_z"] - 0.5, ec["hol_botn_z"] + 4) + vsyl(hx, hy, 3.0, ec["hol_botn_z"] + 4, ec["kapp_z"] + 5.5),
}
STABEL = sum((P[k] for k in ("mb_kort", "mb_tappar", "usb_kontakt", "mb_knappar", "headerar", "pinnetappar", "esp32s", "cam_kort", "sd_og_fpc", "sd_kort", "kameramodul")), Manifold())
DELAR = {"botn": BOTN, "topp": TOPP, "utloysar": KNAPP, "usb-lokk": USBLOKK, "hjulaksel": AKSEL}

# --- kontroll --------------------------------------------------------------
UTE = boks([-20, 130], [-20, 140], [-20, 110]) - KROPP0
rap = {"hjul": {"senter": [round(hx, 2), round(hy, 2)], "r_skore": round(hr + ec["lomme_r_ekstra"], 2)}, "delar": {}, "veggar_mm": {}, "kollisjonar_mm3": {}, "sveip_mm3": {}}
for n, m in DELAR.items():
    bb = m.bounding_box()
    rap["delar"][n] = {"status": str(m.status()), "volum_cm3": round(m.volume() / 1000, 3), "komponentar": len(m.decompose()), "bbox": [[round(q, 2) for q in bb[:3]], [round(q, 2) for q in bb[3:]]]}
for n, q in {"kjerne": KJERNE - vern - SOYLER - STOLPAR, "brytarlomme": brytarlomme, "brunn": brunn ^ boks([-50, 200], [-50, 200], [-50, ut_["kapp_z"] - 0.5]),
             "ec11_pipe": ec_pipe, "magnetlommer": mag_lommer, "pinnehol": pinnehol,
             "usb_tunnel": usb_tunnel ^ boks([-50, 200], [y_usb, y_hjul_usb - 4.0], [-50, 200])}.items():
    rap["veggar_mm"][n] = round(q.min_gap(UTE, 15.0), 2)
for n, p in P.items():
    if n in ("magnetar",):
        continue
    rap["kollisjonar_mm3"][n] = {k: round((p ^ DELAR[k]).volume(), 3) for k in ("botn", "topp")}
rap["kollisjonar_mm3"]["magnetar_i_lommene"] = round((P["magnetar"] ^ (BOTN + TOPP)).volume(), 3)
rap["kollisjonar_mm3"]["botn_mot_topp"] = round((BOTN ^ TOPP).volume(), 3)
rap["sveip_mm3"]["stabel_ned_i_botn"] = round((sum((STABEL.translate([0, 0, d]) for d in np.arange(0, 40.01, 0.5)), Manifold()) ^ BOTN).volume(), 3)
rap["sveip_mm3"]["topp_ned_paa_stabelen"] = round((sum((STABEL.translate([0, 0, -d]) for d in np.arange(0, 40.01, 0.5)), Manifold()) ^ TOPP).volume(), 3)
rap["sveip_mm3"]["usb_plugg_inn"] = round((sum((P["usb_plugg"].translate([0, d, 0]) for d in np.arange(0, 30.01, 0.5)), Manifold()) ^ (BOTN + TOPP)).volume(), 3)
rap["sveip_mm3"]["ec11_opp_gjennom_pipa"] = round((sum((P["ec11"].translate([0, 0, -d]) for d in np.arange(0, 25.01, 0.5)), Manifold()) ^ TOPP).volume(), 3)
rap["sveip_mm3"]["brytar_ned_i_lomma"] = round((sum((P["brytar6x6"].translate([0, 0, d]) for d in np.arange(0, 30.01, 0.5)), Manifold()) ^ TOPP).volume(), 3)
rap["klaring_stabel_mm"] = {k: round(STABEL.min_gap(DELAR[k], 3.0), 2) for k in ("botn", "topp")}
rap["innvendig_volum_cm3"] = round((KROPP0.volume() - KROPP.volume()) / 1000, 1)

for n, m in DELAR.items():
    til_trimesh(m).export(UT / "stl" / f"{n}.stl")
for n, m in P.items():
    til_trimesh(m).export(UT / "proxy" / f"{n}.stl")
(UT / "kontroll.json").write_text(json.dumps(rap, indent=2, ensure_ascii=False))
print(json.dumps(rap, indent=1, ensure_ascii=False))
