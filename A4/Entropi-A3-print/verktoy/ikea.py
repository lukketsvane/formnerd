import json, subprocess, pathlib, shutil
import numpy as np, trimesh
from PIL import Image, ImageDraw, ImageFont

HER = pathlib.Path(__file__).resolve().parent
A3 = HER.parent
P = A3 / "print"
UT = A3 / "montering"
TMP = UT / "_render"
TMP.mkdir(parents=True, exist_ok=True)
K = json.loads((HER / "delar_konfig.json").read_text())
R = json.loads((P / "kontroll.json").read_text())
FB = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"
W, H = 1754, 1240
ay, az = K["akse"]["y"], K["akse"]["z"]
golv = K["golv_z"]
sx, sy = R["stabel_x"], R["stabel_y"]
skyv = R["stabel_innsetjing"]["skyv_fram_mm"] - 0.1
ux, uy = K["utloysar"]["senter"]
bx, by = K["brytar"]["senter"]
kapp_z = K["utloysar"]["kapp_z"]


def f(name, size):
    return ImageFont.truetype(FB if name == "b" else FR, size)


# --- ekstra illustrasjonsgeometri ----------------------------------------
def rør(punkt, r=0.55):
    deler = []
    for a, b in zip(punkt[:-1], punkt[1:]):
        if np.linalg.norm(np.subtract(b, a)) > 1e-6:
            deler.append(trimesh.creation.cylinder(r, segment=[a, b], sections=12))
    deler += [trimesh.creation.icosphere(1, r) .apply_translation(p) for p in punkt]
    return trimesh.util.concatenate(deler)


def lagre(m, namn):
    p = TMP / f"{namn}.stl"
    m.export(p)
    return str(p)


z_pin = R["stabel_z"][0] + 2.07
x_pin = sx["cam_front"] + 1.0
kt_slutt = K["kabeltunnel"]["slutt"]
lomme_botn = R["brytarlomme_botn_z"]


def leidning(y_pin, dx, topp=66.0):
    return [[x_pin, y_pin, z_pin], [62.6, y_pin, z_pin - 0.6], [62.6, 54.2, z_pin - 0.4], [52.0, 54.2, 22.0], [49.5 + dx, 54.2, 36.0],
            [kt_slutt[0] + dx, kt_slutt[1], kt_slutt[2]], [bx + dx, by, lomme_botn + 1.5], [bx + dx, by, topp]]


GND_Y, IO13_Y = sy["sd_ende"] + 7.12, sy["sd_ende"] + 12.20
UTE = (-skyv, 0.0, -42.0)


def leidning_ute(y_pin, dx, topp=70.0):
    p = [x_pin + UTE[0], y_pin, z_pin + UTE[2]]
    return [p, [p[0] + 1.2, y_pin, p[2] - 0.6], [p[0] + 1.2, 54.2, p[2] - 0.4], [46.5 + dx, 54.2, -4], [46.5 + dx, 54.2, 35], [46 + dx, 53.6, 40],
            [kt_slutt[0] + dx, kt_slutt[1], kt_slutt[2]], [bx + dx, by, lomme_botn + 1.5], [bx + dx, by, topp]]
LEID = lagre(trimesh.util.concatenate([rør(leidning(GND_Y, -0.8)), rør(leidning(IO13_Y, 0.8))]), "leidning")
LEID_UTE = lagre(trimesh.util.concatenate([rør(leidning_ute(GND_Y, -0.8)), rør(leidning_ute(IO13_Y, 0.8))]), "leidning_ute")
LEID_UTE_B = lagre(trimesh.util.concatenate([rør(leidning_ute(GND_Y, -0.8, lomme_botn + 2)), rør(leidning_ute(IO13_Y, 0.8, lomme_botn + 2))]), "leidning_ute_b")
LEID_KORT = lagre(trimesh.util.concatenate([rør([[x_pin, y, z_pin], [x_pin + 6, y, z_pin - 2], [x_pin + 14, y - 6, z_pin - 6]]) for y in (GND_Y, IO13_Y)]), "leidning_kort")
LEID_BRYTAR = lagre(trimesh.util.concatenate([rør([[bx + d * 3.25, by + d * 2.25, lomme_botn + 18.3], [bx + d * 4.5, by + d * 2.25, lomme_botn + 15], [bx + d * 1.5, by + d, kapp_z + 2], [bx + d, by, lomme_botn]]) for d in (-1, 1)]), "leidning_brytar")

mag = []
for i, (x, y) in enumerate(K["magnetar"]["pos"]):
    mag.append(lagre(trimesh.creation.cylinder(3.0, 3.0, sections=40).apply_translation([x, y, golv + 1.5]), f"magnet{i}"))
KABEL = lagre(rør([[R["usb_akse_x"], sy["usb_munn"] + 26, az], [R["usb_akse_x"], sy["usb_munn"] + 60, az], [R["usb_akse_x"], sy["usb_munn"] + 75, az + 10]], r=1.8), "usb_kabel")
BORD = lagre(trimesh.creation.box(extents=[256, 256, 0.6]).apply_translation([128, 128, -0.3]), "bord")

PX = {n: str(P / "proxy" / f"{n}.stl") for n in ["mb_kort", "mb_tappar", "usb_kontakt", "mb_knappar", "headerar", "esp32s", "cam_kort", "sd_og_fpc", "kameramodul", "brytar6x6", "usb_plugg", "sd_kort"]}
DEL = {n: str(P / "stl" / f"{n}.stl") for n in ["kropp", "luke", "utloysar", "stabelhaldar", "usb-lokk"]}
CAM = ["cam_kort", "esp32s", "sd_og_fpc", "kameramodul"]
MB = ["mb_kort", "mb_tappar", "usb_kontakt", "mb_knappar", "headerar"]
GRAA = 0xD9D9D9


def o(stl, **kw):
    d = {"stl": stl, "style": "ikea"}
    d.update(kw)
    return d


def stabel(pos=(0, 0, 0), farge=0xFFFFFF, med_leidning=False):
    ob = [o(PX[n], pos=list(pos), color=farge, crease=30, outline=0.25) for n in CAM + ["sd_kort"] + MB]
    if med_leidning:
        ob.append(o(LEID, pos=list(pos), color=0x222222, outline=0.15))
    return ob


# --- render ---------------------------------------------------------------
TELJAR = [0]


def render(objekt, dir, up=(0, 0, 1), span=70, target=None, anchors=(), size=(1500, 980)):
    TELJAR[0] += 1
    out = TMP / f"r{TELJAR[0]:03d}.png"
    spec = {"size": list(size), "dir": list(dir), "up": list(up), "span": span, "out": str(out), "outline": 0.4, "objects": objekt, "anchors": [list(a) for a in anchors]}
    if target is not None:
        spec["target"] = list(target)
    sp = TMP / f"r{TELJAR[0]:03d}.json"
    sp.write_text(json.dumps(spec))
    subprocess.run(["node", str(HER / "scene.mjs"), str(sp)], check=True, capture_output=True, timeout=900)
    img = Image.open(out).convert("RGB")
    ank = json.loads(out.with_suffix(".anchors.json").read_text()) if anchors else []
    return img, ank


def beskjer(img, marg=12):
    a = np.asarray(img.convert("L")) < 250
    ys, xs = np.nonzero(a)
    if len(xs) == 0:
        return img
    return img.crop((max(xs.min() - marg, 0), max(ys.min() - marg, 0), min(xs.max() + marg, img.width), min(ys.max() + marg, img.height)))


# --- teikning ---------------------------------------------------------------
def pil(d, a, b, w=13, hovud=42, farge=(0, 0, 0)):
    a, b = np.array(a, float), np.array(b, float)
    v = b - a
    L = np.linalg.norm(v)
    if L < 1:
        return
    u = v / L
    n = np.array([-u[1], u[0]])
    spiss = b
    base = b - u * hovud
    tri = [tuple(spiss), tuple(base + n * hovud * 0.55), tuple(base - n * hovud * 0.55)]
    for (lw, c) in ((w + 10, (255, 255, 255)), (w, farge)):
        d.line([tuple(a), tuple(base + u * 2)], fill=c, width=lw)
    d.polygon([tuple(spiss + u * 6), tuple(base + n * (hovud * 0.55 + 6) - u * 4), tuple(base - n * (hovud * 0.55 + 6) - u * 4)], fill=(255, 255, 255))
    d.polygon(tri, fill=farge)


def boge_pil(d, c, r, a0, a1, w=12):
    t = np.radians(np.linspace(a0, a1, 40))
    pts = [(c[0] + r * np.cos(x), c[1] + r * np.sin(x)) for x in t]
    d.line(pts[:-3], fill=(0, 0, 0), width=w, joint="curve")
    pil(d, pts[-6], pts[-1], w=w, hovud=34)


def stegnummer(d, n):
    d.text((60, 30), str(n), font=f("b", 130), fill=(0, 0, 0))


def tekst(d, xy, t, s=34, b=False, anker="la", strek=0):
    d.text(xy, t, font=f("b" if b else "r", s), fill=(0, 0, 0), anchor=anker, stroke_width=strek, stroke_fill="white")


def ikon_lim(d, x, y, s=1.0):
    d.rounded_rectangle([x, y + 30 * s, x + 46 * s, y + 120 * s], 10 * s, outline=(0, 0, 0), width=5, fill=(255, 255, 255))
    d.polygon([(x + 10 * s, y + 30 * s), (x + 36 * s, y + 30 * s), (x + 23 * s, y)], outline=(0, 0, 0), fill=(255, 255, 255), width=5)
    d.ellipse([x + 17 * s, y - 22 * s, x + 29 * s, y - 8 * s], fill=(0, 0, 0))


def ikon_lodde(d, x, y, s=1.0):
    d.line([(x, y + 110 * s), (x + 70 * s, y + 40 * s)], fill=(0, 0, 0), width=int(22 * s))
    d.line([(x + 70 * s, y + 40 * s), (x + 110 * s, y)], fill=(0, 0, 0), width=int(7 * s))
    for k in range(3):
        d.arc([x + 95 * s + k * 12 * s, y - 40 * s - k * 6 * s, x + 125 * s + k * 12 * s, y - 10 * s - k * 6 * s], 200, 320, fill=(0, 0, 0), width=4)


def ikon_pc(d, x, y, s=1.0):
    d.rounded_rectangle([x, y, x + 200 * s, y + 130 * s], 10 * s, outline=(0, 0, 0), width=6, fill=(255, 255, 255))
    d.polygon([(x - 25 * s, y + 150 * s), (x + 225 * s, y + 150 * s), (x + 205 * s, y + 132 * s), (x - 5 * s, y + 132 * s)], outline=(0, 0, 0), fill=(255, 255, 255), width=6)
    tekst(d, (x + 100 * s, y + 66 * s), "</>", int(54 * s), True, "mm")


def maal(d, a, b, a_ut, b_ut, t):
    for p, q in ((a, a_ut), (b, b_ut)):
        d.line([tuple(p), tuple(q)], fill=(0, 0, 0), width=3)
    pil(d, ((a_ut[0] + b_ut[0]) / 2, a_ut[1]), a_ut, w=5, hovud=24)
    pil(d, ((a_ut[0] + b_ut[0]) / 2, b_ut[1]), b_ut, w=5, hovud=24)
    tekst(d, ((a_ut[0] + b_ut[0]) / 2, a_ut[1] + 18), t, 64, True, "ma")


def ikon_snu(d, x, y):
    boge_pil(d, (x + 70, y + 70), 60, 200, 520, w=11)


def ikon_ok(d, x, y, s=1.0):
    d.ellipse([x, y, x + 120 * s, y + 120 * s], outline=(0, 0, 0), width=8)
    d.line([(x + 28 * s, y + 62 * s), (x + 52 * s, y + 88 * s), (x + 94 * s, y + 34 * s)], fill=(0, 0, 0), width=12, joint="curve")


def delboks(side, d, element, x=250, y=34, h=210):
    breidd = 30 + sum(min(int(e[0].width * (h - 70) / e[0].height), 230) + 30 for e in element)
    d.rounded_rectangle([x, y, x + breidd, y + h], 18, outline=(0, 0, 0), width=4, fill=(255, 255, 255))
    cx = x + 30
    for img, txt in element:
        th = h - 70
        tw = min(int(img.width * th / img.height), 230)
        th = int(img.height * tw / img.width)
        side.paste(img.resize((tw, th), Image.LANCZOS), (cx, y + 14 + (h - 70 - th) // 2))
        tekst(d, (cx + tw // 2, y + h - 18), txt, 34, True, "ms")
        cx += tw + 30


def utsnitt(side, d, img, senter, r, linje_til=None):
    k = img.resize((2 * r, 2 * r), Image.LANCZOS)
    maske = Image.new("L", (2 * r, 2 * r), 0)
    ImageDraw.Draw(maske).ellipse([0, 0, 2 * r - 1, 2 * r - 1], fill=255)
    if linje_til:
        d.line([tuple(linje_til), tuple(senter)], fill=(0, 0, 0), width=4)
        d.ellipse([linje_til[0] - 40, linje_til[1] - 40, linje_til[0] + 40, linje_til[1] + 40], outline=(0, 0, 0), width=4)
    d.ellipse([senter[0] - r - 6, senter[1] - r - 6, senter[0] + r + 6, senter[1] + r + 6], fill=(255, 255, 255))
    side.paste(k, (senter[0] - r, senter[1] - r), maske)
    d.ellipse([senter[0] - r, senter[1] - r, senter[0] + r, senter[1] + r], outline=(0, 0, 0), width=6)


def ny_side():
    s = Image.new("RGB", (W, H), "white")
    return s, ImageDraw.Draw(s)


HOVUD_POS, HOVUD_STORLEIK = (127, 250), (1500, 980)


def plasser(side, img, ank, pos=HOVUD_POS):
    side.paste(img, pos)
    return [(a[0] + pos[0], a[1] + pos[1]) for a in ank]


THUMB = {}


def tommel_fit(namn, objekt, dir=(1, -0.9, 0.8), up=(0, 0, 1)):
    if namn not in THUMB:
        spec_obj = objekt
        TELJAR[0] += 1
        out = TMP / f"t{TELJAR[0]:03d}.png"
        spec = {"size": [900, 700], "dir": list(dir), "up": list(up), "out": str(out), "outline": 0.3, "objects": spec_obj}
        sp = TMP / f"t{TELJAR[0]:03d}.json"
        sp.write_text(json.dumps(spec))
        subprocess.run(["node", str(HER / "scene.mjs"), str(sp)], check=True, capture_output=True, timeout=900)
        THUMB[namn] = beskjer(Image.open(out).convert("RGB"))
    return THUMB[namn]


T = {
    "kropp": lambda: tommel_fit("kropp", [o(DEL["kropp"], crease=55), o(DEL["utloysar"]), o(DEL["usb-lokk"])]),
    "luke": lambda: tommel_fit("luke", [o(DEL["luke"])], dir=(0.6, -0.8, 1.0)),
    "haldar": lambda: tommel_fit("haldar", [o(DEL["stabelhaldar"])]),
    "knapp": lambda: tommel_fit("knapp", [o(DEL["utloysar"])]),
    "lokk": lambda: tommel_fit("lokk", [o(DEL["usb-lokk"])], dir=(0.5, 1, 0.6)),
    "cam": lambda: tommel_fit("cam", [o(PX[n], crease=30, outline=0.25) for n in CAM], dir=(1, -0.5, 0.6)),
    "mb": lambda: tommel_fit("mb", [o(PX[n], crease=30, outline=0.25) for n in MB], dir=(1, -0.5, 0.6)),
    "brytar": lambda: tommel_fit("brytar", [o(PX["brytar6x6"], outline=0.15)], dir=(1, -0.8, 0.9)),
    "magnet": lambda: tommel_fit("magnet", [o(mag[0], outline=0.2)], dir=(1, -0.8, 0.9)),
    "leidning": lambda: tommel_fit("leidning", [o(LEID_KORT, color=0x222222, outline=0.15)], dir=(1, -0.5, 0.6)),
    "sd": lambda: tommel_fit("sd", [o(PX["sd_kort"], outline=0.2)], dir=(1, -0.6, 0.5)),
    "kabel": lambda: tommel_fit("kabel", [o(PX["usb_plugg"]), o(KABEL, color=0x222222, outline=0.2)], dir=(1, 0.4, 0.6)),
}

SIDER = []
VEKT = (0.95, -0.85, 0.75)
UNDER = (0.95, -0.85, -0.75)
OPP_NED = (0, 0, -1)
MIDT = (45, 60, 40)

# 0 Framside
s, d = ny_side()
img, _ = render([o(DEL["kropp"], crease=55), o(DEL["utloysar"]), o(DEL["usb-lokk"])], VEKT, span=70, target=MIDT)
s.paste(beskjer(img).resize((1100, int(1100 * beskjer(img).height / beskjer(img).width)), Image.LANCZOS), (330, 300))
tekst(d, (90, 80), "A3", 150, True)
tekst(d, (330, 105), "ENTROPI", 110, True)
tekst(d, (336, 228), "Kamerahus · ESP32-CAM · Bambu Lab P1S", 40)
SIDER.append(("00-framside", s))

# 1 Delar
s, d = ny_side()
tekst(d, (60, 40), "Delar", 90, True)
rad = [("kropp", "1x"), ("luke", "1x"), ("haldar", "1x"), ("knapp", "1x"), ("lokk", "1x")]
rad2 = [("cam", "1x"), ("mb", "1x"), ("sd", "1x"), ("brytar", "1x"), ("magnet", "8x Ø6×3"), ("leidning", "2x"), ("kabel", "1x")]
for yy, rk, hh, mx in ((230, rad, 330, 300), (720, rad2, 210, 190)):
    xx = 70
    for k, n in rk:
        im = T[k]()
        th = hh
        tw = int(im.width * th / im.height)
        if tw > mx:
            tw, th = mx, int(im.height * mx / im.width)
        s.paste(im.resize((tw, th), Image.LANCZOS), (xx, yy + (hh - th) // 2))
        tekst(d, (xx + tw // 2, yy + hh + 55), n, 46, True, "ms")
        xx += max(tw, 150) + 45
tekst(d, (70, 1085), "ESP32-CAM + ESP32-CAM-MB · microSD · 6×6 mm trykknapp · magnet Ø6×3 mm · 2 leidningar 26–30 AWG, ca. 15 cm", 30)
tekst(d, (70, 1135), "CA-lim (gel) · loddebolt og tinn · avbitar · skyvelære · micro-USB-kabel", 30)
d.line([(60, 660), (W - 60, 660)], fill=(0, 0, 0), width=3)
SIDER.append(("01-delar", s))

# Mål stabelen
s, d = ny_side()
stegnummer(d, 1)
delboks(s, d, [(T["cam"](), "1x"), (T["mb"](), "1x")])
ob = [o(PX[n], crease=30, outline=0.25) for n in CAM + MB]
zl = R["stabel_z"][0] - 7
img, a2 = render(ob, (0, -1, 0.12), span=30, target=(52, 75, 30), anchors=[[sx["tappar"], 60, 19.5], [sx["cam_front"], 60, 18.5], [sx["tappar"], 60, zl], [sx["cam_front"], 60, zl]], size=(1500, 760))
A = plasser(s, img, a2, (127, 260))
maal(d, A[0], A[1], A[2], A[3], "D")
dn = R["stabel_d_nominell"]
for i, (t, b_) in enumerate([(f"D = {dn - 0.25:.1f} – {dn + 0.25:.1f} mm:  A3-Entropi-P1S.gcode.3mf".replace(".", ",", 2), True),
                             ("Anna D:  A3-Entropi-P1S-utan-haldar.gcode.3mf", True),
                             ("+ haldar-p1s/stabelhaldar-D14.0 … D18.0.gcode.3mf (næraste D)", False)]):
    tekst(d, (180, 1020 + i * 58), t, 38 if i < 2 else 32, b_)
tekst(d, (180, 1185), "D: frå tappane bak på MB til framsida av kamerakortet (ikkje linsa)", 30)
SIDER.append(("02-maal-stabel", s))

# Print
s, d = ny_side()
stegnummer(d, 2)
PL = {"kropp": (10, 10), "luke": (112, 10), "stabelhaldar": (170, 10), "utloysar": (112, 72), "usb-lokk": (140, 72)}
ob = [o(BORD, color=0xF2F2F2, crease=80, outline=0.3)]
for n, (px, py) in PL.items():
    ob.append(o(str(P / "printretning" / f"{n}.stl"), pos=[px, py, 0], crease=55))
img, _ = render(ob, (0.75, -1.0, 1.15), span=150, target=(128, 100, 30))
b = beskjer(img)
plasser(s, b.resize((1000, int(1000 * b.height / b.width)), Image.LANCZOS), [], (700, 230))
sl = json.loads((P / "bambu" / "slicing.json").read_text())
t_ = sl["tid"].replace("h", " t").replace("m", " min").split(" min")[0] + " min"
linjer = ["Bambu Studio · Bambu Lab P1S", "0,4 mm dyse · 0,20 mm Standard", "Bambu PLA Basic", "Textured PEI-plate", "3 veggar · 15 % fyll", "Trestøtte berre frå plata", f"ca. {t_} · {round(sl['vekt_g'])} g", "A3-Entropi-P1S.gcode.3mf", "", "Fjern støtta gjennom luka", "Prøv stabel, haldar og luke utan lim"]
for i, t in enumerate(linjer):
    tekst(d, (70, 300 + i * 68), t, 36, i in (0, 6, 9, 10))
SIDER.append(("03-print", s))

# 3 Magnetar i kroppen
s, d = ny_side()
stegnummer(d, 3)
delboks(s, d, [(T["magnet"](), "4x"), (Image.new("RGB", (60, 100), "white"), "")])
tekst(d, (900, 110), "same pol ut (merk sida)", 40, True)
ikon_lim(d, 700, 60)
ank = []
ob = [o(DEL["kropp"], crease=55)]
for i, m in enumerate(mag):
    lyft = -20 - 7 * i
    ob.append(o(m, pos=[0, 0, lyft], outline=0.25))
    x, y = K["magnetar"]["pos"][i]
    ank += [[x, y, golv + lyft + 1.5 - 2.5], [x, y, golv + 1]]
img, a2 = render(ob, UNDER, OPP_NED, span=62, target=(40, 70, 25), anchors=ank)
A = plasser(s, img, a2)
for i in range(4):
    pil(d, A[2 * i], A[2 * i + 1], w=9, hovud=30)
ikon_snu(d, 1560, 60)
SIDER.append(("04-magnetar-kropp", s))

# 4 Magnetar i luka (polaritet via kroppen)
s, d = ny_side()
stegnummer(d, 4)
delboks(s, d, [(T["magnet"](), "4x"), (T["luke"](), "1x")])
ikon_lim(d, 900, 60)
ob = [o(DEL["kropp"], crease=55)] + [o(m) for m in mag] + [o(m, pos=[0, 0, -3.0]) for m in mag]
ob.append(o(DEL["luke"], pos=[0, 0, -40], crease=40))
img, a2 = render(ob, UNDER, OPP_NED, span=74, target=(40, 70, 10), anchors=[[40, 76, -36], [40, 76, -6], [22.5, 58, -3], [22.5, 58, -40 + 7]])
A = plasser(s, img, a2)
pil(d, A[0], A[1])
utsnitt_img, _ = render([o(DEL["kropp"], crease=55)] + [o(m) for m in mag] + [o(m, pos=[0, 0, -3.0]) for m in mag], UNDER, OPP_NED, span=12, target=(22.5, 77, 6))
utsnitt(s, d, utsnitt_img, (1480, 380), 190, linje_til=A[2])
tekst(d, (1480, 610), "N – S", 40, True, "ma")
tekst(d, (W - 60, 1100), "Litt lim på kvar magnet. Press luka på,", 34, True, "rs")
tekst(d, (W - 60, 1145), "la limet herde, og ta så av luka.", 34, True, "rs")
SIDER.append(("05-magnetar-luke", s))

# 5 Lodd leidningar til ESP32-CAM
s, d = ny_side()
stegnummer(d, 5)
delboks(s, d, [(T["cam"](), "1x"), (T["leidning"](), "2x")])
ikon_lodde(d, 820, 90)
ob = [o(PX[n], crease=30, outline=0.25) for n in CAM] + [o(LEID_KORT, color=0x222222, outline=0.15)]
img, a2 = render(ob, (1, -0.25, 0.55), span=28, target=(sx["cam_front"], 68, 30), anchors=[[x_pin, GND_Y, z_pin], [x_pin, IO13_Y, z_pin]])
A = plasser(s, img, a2)
for (px, py), t, dx in zip(A, ("GND (2)", "IO13 (4)"), (-1, 1)):
    d.ellipse([px - 24, py - 24, px + 24, py + 24], outline=(0, 0, 0), width=5)
    d.line([(px + dx * 20, py + 20), (px + dx * 120, py + 130)], fill=(0, 0, 0), width=4)
    tekst(d, (px + dx * 128, py + 150), t, 48, True, "rs" if dx < 0 else "ls")
tekst(d, (W - 60, 300), "5V-rekkja: 5V · GND · IO12 · IO13 · …", 36, True, "rs")
tekst(d, (1200, 1150), "ca. 15 cm", 46, True)
SIDER.append(("06-lodd-cam", s))

# 6 CAM på MB
s, d = ny_side()
stegnummer(d, 6)
delboks(s, d, [(T["cam"](), "1x"), (T["mb"](), "1x"), (T["sd"](), "1x"), (T["kabel"](), "1x")])
ob = [o(PX[n], pos=[22, 0, 0], crease=30, outline=0.25) for n in CAM] + [o(PX["sd_kort"], pos=[22, -16, 0], outline=0.25)] + [o(LEID_KORT, pos=[22, 0, 0], color=0x222222, outline=0.15)]
ob += [o(PX[n], crease=30, outline=0.25) for n in MB] + [o(PX["usb_plugg"], pos=[0, 30, 0]), o(KABEL, pos=[0, 30, 0], color=0x222222, outline=0.2)]
img, a2 = render(ob, (0.7, -1, 0.6), span=62, target=(60, 98, 32),
                 anchors=[[sx["cam_bak"] + 21, 76, 47], [sx["cam_bak"] + 3, 76, 47], [x_pin + 22.5, sy["sd_ende"] - 20, az + 9], [x_pin + 22.5, sy["sd_ende"] - 5, az + 9],
                          [R["usb_akse_x"], sy["usb_munn"] + 28, az], [R["usb_akse_x"], sy["usb_munn"] + 3, az], [R["usb_akse_x"], sy["usb_munn"] + 105, az + 12]])
A = plasser(s, img, a2)
pil(d, A[0], A[1])
pil(d, A[2], A[3])
pil(d, A[4], A[5])
ikon_pc(d, min(A[6][0], W - 300), max(A[6][1] - 260, 280), 1.0)
tekst(d, (W - 60, 1100), "Firmware: SD i 1-bit-modus, IO13 som knapp, blitz (IO4) av.", 32, True, "rs")
tekst(d, (W - 60, 1150), "Test kamera og utløysar (IO13 mot GND) før montering. SD-kortet sit fast etterpå.", 32, True, "rs")
SIDER.append(("07-cam-mb-sd-firmware", s))

# 7 Tre leidningane gjennom tunnelen
s, d = ny_side()
stegnummer(d, 7)
ikon_snu(d, 1560, 60)
ob = [o(DEL["kropp"], crease=55, opacity=0.22, noOutline=True)] + stabel(UTE) + [o(LEID_UTE, color=0x222222, outline=0.15)]
img, a2 = render(ob, UNDER, OPP_NED, span=70, target=(45, 60, 22), anchors=[[46.5, 54.8, 8], [46.5, 54.8, 30], [bx, by, 62], [bx, by, 80]])
A = plasser(s, img, a2)
pil(d, A[0], A[1], w=9)
pil(d, A[2], A[3], w=9)
SIDER.append(("08-leidning-tunnel", s))
BRYTAR_SIDE = len(SIDER)

# 8 Stabelen inn og fram
s, d = ny_side()
stegnummer(d, 9)
ikon_snu(d, 1560, 60)
ob = [o(DEL["kropp"], crease=55, opacity=0.22, noOutline=True)] + stabel(UTE) + [o(LEID_UTE_B, color=0x222222, outline=0.15), o(PX["brytar6x6"], outline=0.15)]
img, a2 = render(ob, UNDER, OPP_NED, span=70, target=(45, 70, 22),
                 anchors=[[sx["mb_botn"] - skyv + 8, 80, -42 + 18], [sx["mb_botn"] - skyv + 8, 80, 14], [sx["mb_botn"] - skyv + 8, 100.5, 32], [sx["mb_botn"] + 8, 100.5, 32]])
A = plasser(s, img, a2)
pil(d, A[0], A[1])
pil(d, A[2], A[3])
tekst(d, ((A[2][0] + A[3][0]) / 2, (A[2][1] + A[3][1]) / 2 + 60), f"{R['stabel_innsetjing']['skyv_fram_mm']:.1f} mm".replace(".", ","), 40, True, "ma", 6)
tekst(d, (127, 1150), "La ca. 3 cm slakk på leidningane liggje i holrommet.", 34, True)
ui, _ = render([o(DEL["kropp"], crease=55)] + stabel((0, 0, 0)), (1, -0.15, 0.1), span=22, target=(80, ay, az))
utsnitt(s, d, ui, (1460, 900), 210)
SIDER.append(("10-stabel-inn", s))

# 9 Haldar
s, d = ny_side()
stegnummer(d, 10)
delboks(s, d, [(T["haldar"](), "1x (D)")])
ob = [o(DEL["kropp"], crease=55, opacity=0.22, noOutline=True)] + stabel((0, 0, 0)) + [o(DEL["stabelhaldar"], pos=[0, 0, -45])]
img, a2 = render(ob, UNDER, OPP_NED, span=76, target=(45, 70, 10), anchors=[[36, 76, -40], [36, 76, 4]])
A = plasser(s, img, a2)
pil(d, A[0], A[1])
SIDER.append(("11-haldar", s))

# 10 Luka
s, d = ny_side()
stegnummer(d, 11)
ob = [o(DEL["kropp"], crease=55), o(DEL["luke"], pos=[0, 0, -40], crease=40)] + [o(m, pos=[0, 0, -40 - 3.0]) for m in mag]
img, a2 = render(ob, UNDER, OPP_NED, span=72, target=(42, 72, 8), anchors=[[40, 76, -36], [40, 76, -4]])
A = plasser(s, img, a2)
pil(d, A[0], A[1])
tekst(d, (A[0][0] + 70, A[0][1] + 40), "klikk", 46, True, "la", 6)
SIDER.append(("12-luke", s))

# 11 Brytaren
s, d = ny_side()
stegnummer(d, 8)
ikon_snu(d, 1560, 60)
delboks(s, d, [(T["brytar"](), "1x")])
ikon_lodde(d, 640, 90, 0.8)
ikon_lim(d, 820, 70, 0.9)
tekst(d, (980, 110), "Lodd på diagonale bein", 40, True)
ob = [o(DEL["kropp"], crease=55), o(PX["brytar6x6"], pos=[0, 0, 18], outline=0.15), o(LEID_BRYTAR, color=0x222222, outline=0.12)]
img, a2 = render(ob, VEKT, span=34, target=(45, 22, 62), anchors=[[bx, by, lomme_botn + 26], [bx, by, lomme_botn + 9]])
A = plasser(s, img, a2)
pil(d, A[0], A[1])
SIDER.insert(BRYTAR_SIDE, ("09-brytar", s))

# 12 Knappen
s, d = ny_side()
stegnummer(d, 12)
ikon_snu(d, 1560, 60)
delboks(s, d, [(T["knapp"](), "1x")])
ikon_lim(d, 640, 60, 0.9)
ob = [o(DEL["kropp"], crease=55), o(PX["brytar6x6"], outline=0.15), o(DEL["utloysar"], pos=[0, 0, 20])]
img, a2 = render(ob, VEKT, span=34, target=(45, 22, 62), anchors=[[ux, uy, kapp_z + 26], [ux, uy, kapp_z + 7]])
A = plasser(s, img, a2)
pil(d, A[0], A[1])
SIDER.append(("13-knapp", s))

# 13 USB
s, d = ny_side()
stegnummer(d, 13)
delboks(s, d, [(T["kabel"](), "1x"), (T["lokk"](), "1x")])
tekst(d, (900, 110), "kabel inn, eller lokket i når kabelen er ute", 36, True)
yut = R["usb_tunnel_ut_y"]
ob = [o(DEL["kropp"], crease=55), o(DEL["utloysar"]), o(DEL["usb-lokk"], pos=[0, 18, 22]), o(PX["usb_plugg"], pos=[0, 40, 0]), o(KABEL, pos=[0, 40, 0], color=0x222222, outline=0.2)]
img, a2 = render(ob, (0.55, 1.0, 0.45), span=72, target=(48, 105, 38),
                 anchors=[[R["usb_akse_x"], yut - 1, az + 4], [R["usb_akse_x"], yut + 12, az + 20], [R["usb_akse_x"], sy["usb_munn"] + 66, az - 6], [R["usb_akse_x"], yut + 4, az - 6]])
A = plasser(s, img, a2)
pil(d, A[1], A[0], w=10)
pil(d, A[2], A[3])
SIDER.append(("14-usb", s))

# 14 Ferdig
s, d = ny_side()
img, _ = render([o(DEL["kropp"], crease=55), o(DEL["utloysar"]), o(DEL["usb-lokk"])], VEKT, span=70, target=MIDT)
b = beskjer(img)
s.paste(b.resize((1150, int(1150 * b.height / b.width)), Image.LANCZOS), (300, 160))
ikon_ok(d, 1450, 1000)
tekst(d, (90, 70), "Test: kople til USB, trykk på knappen og sjekk at biletet blir lagra.", 34, True)
SIDER.append(("15-ferdig", s))

for i, (namn, side) in enumerate(SIDER):
    if i > 0:
        tekst(ImageDraw.Draw(side), (W - 50, H - 40), f"{i}/{len(SIDER) - 1}", 28, False, "rs")
    side.save(UT / f"{namn}.png")
SIDER[0][1].save(UT / "Entropi-A3-montering.pdf", save_all=True, append_images=[s for _, s in SIDER[1:]], resolution=150)
shutil.rmtree(TMP)
print("sider", len(SIDER))
