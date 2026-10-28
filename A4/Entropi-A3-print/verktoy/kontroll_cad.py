"""Kontroll av dei ferdige delane mot proxyane, rekna berre frå STL-filene og delar_konfig.json: veggar, kollisjonar, sveip og klaring."""
import json, pathlib, time
import numpy as np, trimesh
from manifold3d import Manifold, Mesh, OpType

HER = pathlib.Path(__file__).resolve().parent
K = json.loads((HER / "delar_konfig.json").read_text())
F, S, D, st, ec = K["form"], K["skal"], K["detalj"], K["stabel"], K["skal"]["ec11"]
UT = (HER / K["ut_mappe"]).resolve()
ay, az = K["akse"]["y"], K["akse"]["z"]
SEG = 96
T0 = time.time()


def tid(namn):
    print(f"{time.time() - T0:6.1f} s  {namn}", flush=True)


def til_manifold(tm):
    return Manifold(Mesh(vert_properties=np.asarray(tm.vertices, np.float32), tri_verts=np.asarray(tm.faces, np.uint32)))


def les(sti):
    return til_manifold(trimesh.load(sti, force="mesh"))


def boks(x, y, z):
    return Manifold.cube([x[1] - x[0], y[1] - y[0], z[1] - z[0]]).translate([x[0], y[0], z[0]])


def vsyl(cx, cy, r, z0, z1):
    return Manifold.cylinder(z1 - z0, r, r, SEG).translate([cx, cy, z0])


def union(delar):
    return Manifold.batch_boolean(list(delar), OpType.Add)


def sveip(m, retning, lengd):
    return union([m.translate([c * d for c in retning]) for d in np.arange(0, lengd + 0.01, 0.5)])


def propp(omraade):
    return (SKAL ^ omraade).hull()


def ytre_luft(rom):
    skal = sorted(rom.decompose(), key=lambda c: c.volume(), reverse=True)
    holrom = [c for c in skal[1:] if c.volume() > 0.0]
    print(f"        lukka holrom: {len(holrom)}, {sum(c.volume() for c in holrom) / 1000:.1f} cm3", flush=True)
    return rom - union(holrom) if holrom else rom


def rund(v, n=3):
    return round(float(v), n) + 0.0


DELAR = {n: les(UT / "stl" / f"{n}.stl") for n in ("botn", "topp", "utloysar", "usb-lokk", "hjulaksel")}
PROXY_REKKJE = ("mb_kort", "mb_tappar", "usb_kontakt", "mb_knappar", "headerar", "pinnetappar", "esp32s", "cam_kort", "sd_kort", "sd_og_fpc", "kameramodul", "brytar6x6", "magnetar", "usb_plugg", "ec11")
P = {n: les(UT / "proxy" / f"{n}.stl") for n in PROXY_REKKJE}
P.update({p.stem: les(p) for p in sorted((UT / "proxy").glob("*.stl")) if p.stem not in P})
BOTN, TOPP = DELAR["botn"], DELAR["topp"]
BOTN_TOPP = BOTN + TOPP
SKAL = union([DELAR[n] for n in ("botn", "topp", "utloysar", "usb-lokk")])
STABEL = union([P[k] for k in ("mb_kort", "mb_tappar", "usb_kontakt", "mb_knappar", "headerar", "pinnetappar", "esp32s", "cam_kort", "sd_og_fpc", "sd_kort", "kameramodul")])
tid("lasta STL")

y_sd = ay - st["linse_fraa_sd"]
y_usb = y_sd + st["mb_innrykk_sd"] + st["mb_lengd"]
x_usb = st["cam_front_x"] - st["cam_pcb"] - st["header_gap"] + st["usb_akse_over_mb"]
hx, hy = F["hjulboss"]["senter"]
ux, uy = K["utloysar"]["senter"]
hb, kb, ut_t, ri = F["hjulboss"], F["knappboss"], K["usb_tunnel"], D["riller"]
x_front = SKAL.bounding_box()[3]
y_usb_munn = DELAR["usb-lokk"].bounding_box()[4]
tak_usb = az + ut_t["h_z"] / 2 - ut_t["r"] + (ut_t["b_x"] / 2 - ut_t["r"]) + ut_t["r"] * np.sqrt(2)
OPNINGAR = {
    "linse": propp(boks([x_front - 6.0, x_front + 1.0], [-50, 200], [-50, 200])),
    "utloysar": propp(vsyl(ux, uy, kb["r"] - 0.5, kb["z"][1] - 3.0, kb["z"][1] + 1.0)),
    "hjulaksel": propp(vsyl(hx, hy, hb["r"] - 0.5, hb["z"][1] - 3.0, hb["z"][1] + 1.0)),
    "usb-lokk": propp(boks([x_usb - ut_t["b_x"] / 2 - 1.5, x_usb + ut_t["b_x"] / 2 + 1.5], [y_usb_munn - 4.0, y_usb_munn + 1.0], [az - ut_t["h_z"] / 2 - 1.5, tak_usb + 1.0])),
}
zr = [ri["z"][0] - 1.0, ri["z"][1] + 1.0]
RILLEKANTAR = {
    "rillekant_x0": boks([ri["x"][0] - 0.1, ri["x"][0] + ri["djupn"] + 0.1], [-1.0, ri["y_maks"] + 0.1], zr),
    "rillekant_x1": boks([ri["x"][1] - ri["djupn"] - 0.1, ri["x"][1] + 0.1], [-1.0, ri["y_maks"] + 0.1], zr),
    "rillekant_y": boks([ri["x"][0] - 0.1, ri["x"][1] + 0.1], [ri["y_maks"] - ri["djupn"] - 0.1, ri["y_maks"] + 0.1], zr),
}
BOKS = boks([-20, 130], [-20, 140], [-20, 110])
ROM = BOKS - SKAL
UTE = ytre_luft(ROM - union(OPNINGAR.values()))
if (STABEL ^ UTE).volume() > 0.0:
    print("ÅTVARING: ytre luft når inn til stabelen gjennom skalet (sprekker langs rillekantane?); tettar rillekantane i tillegg til opningane", flush=True)
    UTE = ytre_luft(ROM - union([*OPNINGAR.values(), *RILLEKANTAR.values()]))
    if (STABEL ^ UTE).volume() > 0.0:
        print("ÅTVARING: skalet lek framleis; veggmåla under er klaring til holrommet, ikkje veggtjukn", flush=True)
tid("ytre luft")

rap = {"hjul": {"senter": [rund(hx, 2), rund(hy, 2)], "r_skore": rund(hb["r"], 2)}, "delar": {}, "veggar_mm": {}, "kollisjonar_mm3": {}, "sveip_mm3": {}}
for n, m in DELAR.items():
    bb = m.bounding_box()
    kv = sorted((c.volume() for c in m.decompose()), reverse=True)
    rap["delar"][n] = {"status": str(m.status()), "volum_cm3": rund(m.volume() / 1000), "komponentar": len(kv), "smaa_komponentar_mm3": [rund(v) for v in kv[1:6]],
                       "bbox": [[rund(q, 2) for q in bb[:3]], [rund(q, 2) for q in bb[3:]]]}
tid("delar")
VEGG = {"stabel": union([P["cam_kort"], P["mb_kort"], P["esp32s"]]), "brytarlomme": P["brytar6x6"], "ec11_pipe": P["ec11"] ^ boks([-50, 200], [-50, 200], [-50, ec["hol_botn_z"]]),
        "magnetlommer": P["magnetar"], "usb_tunnel": P["usb_plugg"] ^ boks([-50, 200], [y_usb, y_usb + 10.0], [-50, 200])}
for n, q in VEGG.items():
    rap["veggar_mm"][n] = rund(q.min_gap(UTE, 15.0), 2)
tid("veggar")
for n, p in P.items():
    if n != "magnetar":
        rap["kollisjonar_mm3"][n] = {k: rund((p ^ DELAR[k]).volume()) for k in ("botn", "topp")}
rap["kollisjonar_mm3"]["magnetar_i_lommene"] = rund((P["magnetar"] ^ BOTN_TOPP).volume())
rap["kollisjonar_mm3"]["botn_mot_topp"] = rund((BOTN ^ TOPP).volume())
tid("kollisjonar")
rap["sveip_mm3"]["stabel_ned_i_botn"] = rund((sveip(STABEL, [0, 0, 1], 40) ^ BOTN).volume())
rap["sveip_mm3"]["topp_ned_paa_stabelen"] = rund((sveip(STABEL, [0, 0, -1], 40) ^ TOPP).volume())
rap["sveip_mm3"]["usb_plugg_inn"] = rund((sveip(P["usb_plugg"], [0, 1, 0], 30) ^ BOTN_TOPP).volume())
rap["sveip_mm3"]["ec11_opp_gjennom_pipa"] = rund((sveip(P["ec11"], [0, 0, -1], 25) ^ TOPP).volume())
rap["sveip_mm3"]["brytar_ned_i_lomma"] = rund((sveip(P["brytar6x6"], [0, 0, 1], 30) ^ TOPP).volume())
tid("sveip")
rap["klaring_stabel_mm"] = {k: rund(STABEL.min_gap(DELAR[k], 3.0), 2) for k in ("botn", "topp")}
rap["ytre_volum_cm3"] = rund((BOKS.volume() - UTE.volume()) / 1000, 1)
tid("klaring")

br_, ut__ = K["brytar"], K["utloysar"]
lb_ = ut__["kapp_z"] - br_["hogd_med_bein"]
bx_, by_ = br_["senter"]
tm_topp = trimesh.load(UT / "stl" / "topp.stl", force="mesh")
golv = []
for dx_ in (2.5, -2.5):
    loc_ = tm_topp.ray.intersects_location(np.array([[bx_ + dx_, by_, lb_ + 0.3]]), np.array([[0.0, 0.0, -1.0]]))[0]
    zs_ = sorted(np.atleast_2d(loc_)[:, 2], reverse=True) if len(loc_) else []
    golv.append(rund(zs_[0] - zs_[1], 2) if len(zs_) >= 2 else 0.0)
rap["brytargolv_mm"] = min(golv)
tid("brytargolv")

(UT / "kontroll.json").write_text(json.dumps(rap, indent=2, ensure_ascii=False))
print(json.dumps(rap, indent=1, ensure_ascii=False))
