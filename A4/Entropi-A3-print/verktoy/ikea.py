import json, subprocess, pathlib, shutil, re
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
SK = json.loads((P / "bambu" / "skal.json").read_text())
FB = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"
W, H = 1754, 1240
S = K["skal"]
ay, az = K["akse"]["y"], K["akse"]["z"]
dz = S["deling_z"]
ux, uy = K["utloysar"]["senter"]
bx, by = K["brytar"]["senter"]
kapp_z = K["utloysar"]["kapp_z"]
lomme_botn = kapp_z - K["brytar"]["hogd_med_bein"]
hx, hy = R["hjul"]["senter"]
ec_kapp = S["ec11"]["kapp_z"]
st = K["stabel"]
x_usb = st["cam_front_x"] - st["cam_pcb"] - st["header_gap"] + st["usb_akse_over_mb"]


def f(name, size):
    return ImageFont.truetype(FB if name == "b" else FR, size)


# --- ekstra illustrasjonsgeometri ----------------------------------------
def rør(punkt, r=0.55):
    deler = []
    for a, b in zip(punkt[:-1], punkt[1:]):
        if np.linalg.norm(np.subtract(b, a)) > 1e-6:
            deler.append(trimesh.creation.cylinder(r, segment=[a, b], sections=12))
    deler += [trimesh.creation.icosphere(1, r).apply_translation(p) for p in punkt]
    return trimesh.util.concatenate(deler)


def lagre(m, namn):
    p = TMP / f"{namn}.stl"
    m.export(p)
    return str(p)


# 5V-rekkja på ESP32-CAM ligg lågt (z ≈ 20,6); pinnane stikk ut på kamerasida
x_pin, z_pin = 61.4, 20.6
GND_Y, IO13_Y = 55.2 + 7.12, 55.2 + 12.20
PINNAR = ((GND_Y, -0.8), (IO13_Y, 0.8))


def leidningar(fn, namn, **kw):
    return lagre(trimesh.util.concatenate([rør(fn(y, dx, **kw)) for y, dx in PINNAR]), namn)


def l_kort(y, dx):
    return [[x_pin, y, z_pin], [x_pin + 2.5, y, z_pin], [x_pin + 3.5, y, z_pin - 6], [x_pin + 5, y + dx * 2.5, z_pin - 13]]


def l_heng(y, dx):  # med stabelen, laus ende opp
    return [[x_pin, y, z_pin], [63.2, y, z_pin], [63.2 + dx * 0.6, 50, z_pin + 1], [62 + dx, 44, 30], [60 + dx, 42, 44]]


T_OPP = 42.0     # toppskalet løfta over botnen i steg med leidning
B_OPP = 24.0     # brytaren løfta over lomma


def l_full(y, dx, til_brytar=True):
    p = [[x_pin, y, z_pin], [63.2, y, z_pin], [63.2 + dx * 0.6, 48, 21.5], [56, 28 + dx, 24], [bx + dx, by + 5, 28], [bx + dx, by, 36],
         [bx + dx, by, lomme_botn + T_OPP], [bx + dx, by, kapp_z + T_OPP + 6]]
    if til_brytar:
        d = -1 if dx < 0 else 1
        p += [[bx + d * 3.25, by + d * 2.25, lomme_botn + T_OPP + B_OPP - 0.3]]
    return p


LEID_KORT = leidningar(l_kort, "leidning_kort")
LEID_HENG = leidningar(l_heng, "leidning_heng")
LEID_FULL = leidningar(l_full, "leidning_full")


def magnetsett(z0, namn, merke=None):
    ob = []
    for i, (x, y) in enumerate(S["magnetar"]):
        m = trimesh.creation.cylinder(3.0, 3.0, sections=40).apply_translation([x, y, z0 + 1.5])
        ob.append(lagre(m, f"{namn}{i}"))
    mk = []
    if merke is not None:
        for i, (x, y) in enumerate(S["magnetar"]):
            mk.append(lagre(trimesh.creation.cylinder(3.05, 0.9, sections=40).apply_translation([x, y, merke]), f"{namn}_merke{i}"))
    return ob, mk


MAG_B, _ = magnetsett(dz - 3.0, "mag_b")
MAG_T, MERKE = magnetsett(dz, "mag_t", merke=dz + 3.0 - 0.3)
EIN_MAG = lagre(trimesh.creation.cylinder(3.0, 3.0, sections=40), "ein_magnet")
KABEL = lagre(rør([[x_usb, 121, az], [x_usb, 150, az], [x_usb, 168, az + 12]], r=1.8), "usb_kabel")

PX = {n: str(P / "proxy" / f"{n}.stl") for n in ["mb_kort", "mb_tappar", "usb_kontakt", "mb_knappar", "headerar", "esp32s", "cam_kort", "sd_og_fpc",
                                                   "kameramodul", "pinnetappar", "brytar6x6", "usb_plugg", "sd_kort", "ec11"]}
DEL = {n: str(P / "stl" / f"{n}.stl") for n in ["botn", "topp", "utloysar", "usb-lokk", "hjulaksel"]}
PR = {n: str(P / "printretning" / f"{n}.stl") for n in ["botn", "topp", "utloysar", "usb-lokk", "hjulaksel", "hjul-A17-V1", "hjul-A17-V2", "hjul-A17-V3", "hjul-A17-V4"]}
HJUL = str(P / "printretning" / "hjul-A17-V4.stl")
HJUL_POS = [hx - 12.0, hy - 12.0, 80.5]
CAM = ["cam_kort", "esp32s", "sd_og_fpc", "kameramodul", "pinnetappar"]
MB = ["mb_kort", "mb_tappar", "usb_kontakt", "mb_knappar", "headerar"]
SVART = 0x222222


def o(stl, **kw):
    d = {"stl": stl, "style": "ikea"}
    d.update(kw)
    return d


def v(p, dz_=0.0):
    return [p[0], p[1], p[2] + dz_]


def stabel(pos=(0, 0, 0), leidning=None):
    ob = [o(PX[n], pos=list(pos), crease=30, outline=0.25) for n in CAM + ["sd_kort"] + MB]
    if leidning:
        ob.append(o(leidning, pos=list(pos), color=SVART, outline=0.15))
    return ob


def botn(**kw):
    return o(DEL["botn"], crease=55, **kw)


def topp(**kw):
    return o(DEL["topp"], crease=55, **kw)


def hjul(dz_=0.0):
    return o(HJUL, pos=v(HJUL_POS, dz_), crease=50, outline=0.2)


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
    v_ = b - a
    L = np.linalg.norm(v_)
    if L < 1:
        return
    u = v_ / L
    n = np.array([-u[1], u[0]])
    spiss = b
    base = b - u * hovud
    tri = [tuple(spiss), tuple(base + n * hovud * 0.55), tuple(base - n * hovud * 0.55)]
    for (lw, c) in ((w + 10, (255, 255, 255)), (w, farge)):
        d.line([tuple(a), tuple(base + u * 2)], fill=c, width=lw)
    d.polygon([tuple(spiss + u * 6), tuple(base + n * (hovud * 0.55 + 6) - u * 4), tuple(base - n * (hovud * 0.55 + 6) - u * 4)], fill=(255, 255, 255))
    d.polygon(tri, fill=farge)


def kort_pil(d, a, b, frå=0.12, til=0.9, **kw):
    a, b = np.array(a, float), np.array(b, float)
    pil(d, a + (b - a) * frå, a + (b - a) * til, **kw)


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


def ikon_penn(d, x, y, s=1.0):
    a, b = (x + 30 * s, y + 95 * s), (x + 120 * s, y + 5 * s)
    d.line([a, b], fill=(0, 0, 0), width=int(34 * s))
    d.line([(a[0] + 12 * s, a[1] - 12 * s), (b[0] - 6 * s, b[1] + 6 * s)], fill=(255, 255, 255), width=int(20 * s))
    d.polygon([(a[0] - 14 * s, a[1] - 10 * s), (a[0] + 10 * s, a[1] + 14 * s), (x, y + 125 * s)], fill=(0, 0, 0))


def ikon_klokke(d, x, y, r=50):
    d.ellipse([x - r, y - r, x + r, y + r], outline=(0, 0, 0), width=7)
    d.line([(x, y), (x, y - r * 0.7)], fill=(0, 0, 0), width=7)
    d.line([(x, y), (x + r * 0.5, y + r * 0.2)], fill=(0, 0, 0), width=7)


def ikon_snu(d, x=1560, y=60):
    boge_pil(d, (x + 70, y + 70), 60, 200, 520, w=11)


def ikon_ok(d, x, y, s=1.0):
    d.ellipse([x, y, x + 120 * s, y + 120 * s], outline=(0, 0, 0), width=8)
    d.line([(x + 28 * s, y + 62 * s), (x + 52 * s, y + 88 * s), (x + 94 * s, y + 34 * s)], fill=(0, 0, 0), width=12, joint="curve")


def ikon_bilete(d, x, y, s=1.0):
    d.rounded_rectangle([x, y, x + 150 * s, y + 110 * s], 8, outline=(0, 0, 0), width=6, fill=(255, 255, 255))
    d.polygon([(x + 12 * s, y + 96 * s), (x + 60 * s, y + 40 * s), (x + 92 * s, y + 76 * s), (x + 110 * s, y + 58 * s), (x + 140 * s, y + 96 * s)], fill=(0, 0, 0))
    d.ellipse([x + 104 * s, y + 18 * s, x + 126 * s, y + 40 * s], fill=(0, 0, 0))


def vmaal(d, lo, hi, x_ut, t, s=44):
    """Loddrett mål mellom to skjermpunkt (lo nedst, hi øvst)."""
    for p in (lo, hi):
        d.line([tuple(p), (x_ut + 16, p[1])], fill=(0, 0, 0), width=3)
    pil(d, (x_ut, hi[1] - 70), (x_ut, hi[1]), w=5, hovud=22)
    pil(d, (x_ut, lo[1] + 70), (x_ut, lo[1]), w=5, hovud=22)
    tekst(d, (x_ut + 30, (lo[1] + hi[1]) / 2), t, s, True, "lm", 6)


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
    return x + breidd


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
    return lambda a: (senter[0] - r + a[0] * 2 * r / img.width, senter[1] - r + a[1] * 2 * r / img.height)


def ny_side():
    s = Image.new("RGB", (W, H), "white")
    return s, ImageDraw.Draw(s)


HOVUD_POS = (127, 250)


def plasser(side, img, ank, pos=HOVUD_POS):
    side.paste(img, pos)
    return [(a[0] + pos[0], a[1] + pos[1]) for a in ank]


def lim_inn(side, img, boks):
    """Skaler eit beskore bilete inn i boks (x0, y0, x1, y1), sentrert."""
    x0, y0, x1, y1 = boks
    s_ = min((x1 - x0) / img.width, (y1 - y0) / img.height)
    im = img.resize((int(img.width * s_), int(img.height * s_)), Image.LANCZOS)
    ox, oy = x0 + (x1 - x0 - im.width) // 2, y0 + (y1 - y0 - im.height) // 2
    side.paste(im, (ox, oy))
    return lambda a: (ox + a[0] * s_, oy + a[1] * s_)


THUMB = {}


def tommel_fit(namn, objekt, dir=(1, -0.9, 0.8), up=(0, 0, 1)):
    if namn not in THUMB:
        TELJAR[0] += 1
        out = TMP / f"t{TELJAR[0]:03d}.png"
        spec = {"size": [900, 700], "dir": list(dir), "up": list(up), "out": str(out), "outline": 0.3, "objects": objekt}
        sp = TMP / f"t{TELJAR[0]:03d}.json"
        sp.write_text(json.dumps(spec))
        subprocess.run(["node", str(HER / "scene.mjs"), str(sp)], check=True, capture_output=True, timeout=900)
        THUMB[namn] = beskjer(Image.open(out).convert("RGB"))
    return THUMB[namn]


def rekkje(namn, filer, gap=6.0, **kw):
    ob, x = [], 0.0
    for fil in filer:
        m = trimesh.load(fil)
        ob.append(o(fil, pos=[x - m.bounds[0][0], -m.bounds[0][1], 0], crease=50))
        x += m.extents[0] + gap
    return tommel_fit(namn, ob, **kw)


T = {
    "botn": lambda: tommel_fit("botn", [botn()]),
    "topp": lambda: tommel_fit("topp", [topp()]),
    "knapp": lambda: tommel_fit("knapp", [o(DEL["utloysar"])]),
    "lokk": lambda: tommel_fit("lokk", [o(DEL["usb-lokk"])], dir=(0.5, 1, 0.6)),
    "aksel": lambda: tommel_fit("aksel", [o(DEL["hjulaksel"])]),
    "hjul": lambda: tommel_fit("hjul", [o(HJUL, crease=50, outline=0.2)], dir=(1, -0.9, 0.9)),
    "cam": lambda: tommel_fit("cam", [o(PX[n], crease=30, outline=0.25) for n in CAM], dir=(1, -0.5, 0.6)),
    "mb": lambda: tommel_fit("mb", [o(PX[n], crease=30, outline=0.25) for n in MB], dir=(1, -0.5, 0.6)),
    "brytar": lambda: tommel_fit("brytar", [o(PX["brytar6x6"], outline=0.15)], dir=(1, -0.8, 0.9)),
    "ec11": lambda: tommel_fit("ec11", [o(PX["ec11"], outline=0.2)], dir=(1, -0.8, 0.6)),
    "magnet": lambda: tommel_fit("magnet", [o(EIN_MAG, outline=0.2)], dir=(1, -0.8, 0.9)),
    "magnet_m": lambda: tommel_fit("magnet_m", [o(MAG_T[0], outline=0.2), o(MERKE[0], color=SVART, outline=0.1)], dir=(1, -0.8, 0.5)),
    "leidning": lambda: tommel_fit("leidning", [o(LEID_KORT, color=SVART, outline=0.15)], dir=(1, -0.5, 0.6)),
    "sd": lambda: tommel_fit("sd", [o(PX["sd_kort"], outline=0.2)], dir=(1, -0.6, 0.5)),
    "kabel": lambda: tommel_fit("kabel", [o(PX["usb_plugg"]), o(KABEL, color=SVART, outline=0.2)], dir=(1, 0.4, 0.6)),
}


def tid(t):
    h = re.search(r"(\d+)h", t)
    m = re.search(r"(\d+)m", t)
    s_ = re.search(r"(\d+)s", t)
    mn = (int(h.group(1)) if h else 0) * 60 + (int(m.group(1)) if m else 0) + (1 if s_ and int(s_.group(1)) >= 30 else 0)
    return f"{mn // 60} t {mn % 60} min" if mn >= 60 else f"{mn} min"


SIDER = []
VEKT = (0.95, -0.85, 0.75)
UNDER = (0.95, -0.85, -0.75)
OPP_NED = (0, 0, -1)
MIDT = (48, 60, 42)


def ferdig(med_lokk=True, dz_hjul=0.0):
    ob = [botn(), topp(), o(DEL["utloysar"]), o(PX["brytar6x6"], outline=0.15), hjul(dz_hjul)]
    if med_lokk:
        ob.append(o(DEL["usb-lokk"]))
    return ob


# 0 Framside
s, d = ny_side()
img, _ = render(ferdig(), VEKT, span=72, target=MIDT)
lim_inn(s, beskjer(img), (300, 300, 1460, 1180))
tekst(d, (90, 80), "A3", 150, True)
tekst(d, (330, 105), "ENTROPI", 110, True)
tekst(d, (336, 228), "Kamerahus · ESP32-CAM · Bambu Lab P1S", 40)
SIDER.append(("00-framside", s))

# 1 Delar
s, d = ny_side()
tekst(d, (60, 40), "Delar", 90, True)
rad = [("botn", "1x", 300), ("topp", "1x", 300), ("knapp", "1x", 90), ("lokk", "1x", 120), ("aksel", "1x", 130), ("hjul", "1x", 110)]
rad2 = [("cam", "1x", 190), ("mb", "1x", 190), ("sd", "1x", 110), ("brytar", "1x", 110), ("ec11", "(1x)", 190), ("magnet", "12x", 70), ("leidning", "2x", 150), ("kabel", "1x", 110)]
for yy, rk, hh, mx in ((200, rad, 300, 340), (720, rad2, 190, 170)):
    xx = 70
    for k, n, th in rk:
        im = T[k]()
        tw = int(im.width * th / im.height)
        if tw > mx:
            tw, th = mx, int(im.height * mx / im.width)
        s.paste(im.resize((tw, th), Image.LANCZOS), (xx, yy + (hh - th) // 2))
        tekst(d, (xx + tw // 2, yy + hh + 55), n, 46, True, "ms")
        xx += max(tw, 120) + 40
tekst(d, (70, 1085), "ESP32-CAM + ESP32-CAM-MB · microSD · trykknapp 6×6 mm · magnet Ø6×3 mm · 2 leidningar ca. 15 cm · EC11 (valfri)", 30)
tekst(d, (70, 1135), "CA-lim (gel) · loddebolt og tinn · avbitar · tusj · micro-USB-kabel", 30)
d.line([(60, 650), (W - 60, 650)], fill=(0, 0, 0), width=3)
SIDER.append(("01-delar", s))

# 2 Print
s, d = ny_side()
stegnummer(d, 1)
PLATER = [("botn", "A3-Entropi-botn-P1S.gcode.3mf", lambda: rekkje("p_botn", [PR["botn"]])),
          ("topp", "A3-Entropi-topp-P1S.gcode.3mf", lambda: rekkje("p_topp", [PR["topp"]])),
          ("smådelar", "A3-Entropi-smaadelar-P1S.gcode.3mf", lambda: rekkje("p_smaa", [PR["utloysar"], PR["usb-lokk"], PR["hjulaksel"]], gap=5)),
          ("A17-hjul", "A3-Entropi-hjul-A17-P1S.gcode.3mf", lambda: rekkje("p_hjul", [PR[f"hjul-A17-V{i}"] for i in range(1, 5)], gap=5))]
for i, (namn, fil, fn) in enumerate(PLATER):
    cx = 120 + i * 390
    d.rounded_rectangle([cx, 250, cx + 360, 940], 18, outline=(0, 0, 0), width=4)
    lim_inn(s, fn(), (cx + 25, 280, cx + 335, 640))
    tekst(d, (cx + 180, 700), namn, 52, True, "ma")
    tekst(d, (cx + 180, 790), tid(SK[fil]["tid"]), 40, True, "ma")
    tekst(d, (cx + 180, 850), f"{round(SK[fil]['vekt_g'])} g", 40, False, "ma")
tekst(d, (120, 1000), "Bambu Lab P1S · PLA · 0,4 mm dyse · 0,20 mm · Textured PEI", 34)
tekst(d, (120, 1060), "Fjern all støtte.", 40, True)
tekst(d, (120, 1120), "A17-hjulet: fire variantar på plata, vel eitt.", 32)
SIDER.append(("02-print", s))

# 3 Magnetar i botnskalet
s, d = ny_side()
stegnummer(d, 2)
xe = delboks(s, d, [(T["magnet"](), "6x")])
ikon_lim(d, xe + 60, 70)
tekst(d, (xe + 160, 140), "same pol opp", 46, True, "lm")
ob, ank = [botn()], []
for i, m in enumerate(MAG_B):
    lyft = 14 + 3 * (i % 3)
    ob.append(o(m, pos=[0, 0, lyft], outline=0.25))
    x, y = S["magnetar"][i]
    ank += [[x, y, dz + lyft - 3.6], [x, y, dz + 0.6]]
img, a2 = render(ob, VEKT, span=66, target=(48, 60, 22), anchors=ank)
A = plasser(s, img, a2)
for i in range(len(MAG_B)):
    kort_pil(d, A[2 * i], A[2 * i + 1], frå=0.0, til=1.0, w=8, hovud=26)
SIDER.append(("03-magnetar-botn", s))

# 4 Ein magnet på kvar, merk oversida
s, d = ny_side()
stegnummer(d, 3)
xe = delboks(s, d, [(T["magnet"](), "6x")])
ikon_penn(d, xe + 60, 60)
tekst(d, (xe + 220, 140), "merk oversida", 46, True, "lm")
ob, ank = [botn()] + [o(m, outline=0.25) for m in MAG_B], []
for i, (m, mk) in enumerate(zip(MAG_T, MERKE)):
    lyft = 14
    ob += [o(m, pos=[0, 0, lyft], outline=0.25), o(mk, pos=[0, 0, lyft], color=SVART, outline=0.1)]
    x, y = S["magnetar"][i]
    ank += [[x, y, dz + lyft - 0.6], [x, y, dz + 3.4]]
img, a2 = render(ob, VEKT, span=66, target=(48, 60, 22), anchors=ank)
A = plasser(s, img, a2)
for i in range(len(MAG_T)):
    kort_pil(d, A[2 * i], A[2 * i + 1], frå=0.0, til=1.0, w=7, hovud=22)
ui, _ = render([botn(opacity=0.25, noOutline=True), o(MAG_B[0], outline=0.25), o(MAG_T[0], outline=0.25), o(MERKE[0], color=SVART, outline=0.1)],
               (1, -0.6, 0.35), span=8, target=(S["magnetar"][0][0], S["magnetar"][0][1], dz + 0.5), size=(800, 800))
utsnitt(s, d, ui, (1430, 860), 200)
SIDER.append(("04-magnetar-merk", s))

# 5 Merka magnetar i toppskalet (snudd)
s, d = ny_side()
stegnummer(d, 4)
ikon_snu(d)
xe = delboks(s, d, [(T["magnet_m"](), "6x"), (T["topp"](), "1x")])
ikon_lim(d, xe + 60, 70)
tekst(d, (xe + 160, 140), "merket ned", 46, True, "lm")
ob, ank = [topp()], []
for i, (m, mk) in enumerate(zip(MAG_T, MERKE)):
    lyft = -16
    ob += [o(m, pos=[0, 0, lyft], outline=0.25), o(mk, pos=[0, 0, lyft], color=SVART, outline=0.1)]
    x, y = S["magnetar"][i]
    ank += [[x, y, dz + lyft + 3.6], [x, y, dz - 0.4]]
img, a2 = render(ob, UNDER, OPP_NED, span=68, target=(46, 60, 46), anchors=ank)
A = plasser(s, img, a2)
for i in range(len(MAG_T)):
    kort_pil(d, A[2 * i], A[2 * i + 1], frå=0.0, til=1.0, w=8, hovud=26)
ikon_klokke(d, 1580, 1080, 55)
tekst(d, (1500, 1080), "la limet herde", 36, True, "rm")
SIDER.append(("05-magnetar-topp", s))

# 6 Lodd leidningar til ESP32-CAM
s, d = ny_side()
stegnummer(d, 5)
xe = delboks(s, d, [(T["cam"](), "1x"), (T["leidning"](), "2x")])
ikon_lodde(d, xe + 60, 90)
ob = [o(PX[n], crease=30, outline=0.25) for n in CAM] + [o(LEID_KORT, color=SVART, outline=0.15)]
img, a2 = render(ob, (1, -0.3, 0.25), span=26, target=(61, 72, 28), anchors=[[x_pin, GND_Y, z_pin], [x_pin, IO13_Y, z_pin]])
A = plasser(s, img, a2)
for (px, py), t, dx in zip(A, ("GND (2)", "IO13 (4)"), (-1, 1)):
    d.ellipse([px - 26, py - 26, px + 26, py + 26], outline=(0, 0, 0), width=5)
    d.line([(px + dx * 26, py), (px + dx * 230, py - 90)], fill=(0, 0, 0), width=4)
    tekst(d, (px + dx * 240, py - 90), t, 48, True, "rm" if dx < 0 else "lm", 6)
tekst(d, (W - 60, 300), "5V-rekkja: 5V · GND · IO12 · IO13 · …", 36, True, "rs")
SIDER.append(("06-lodd-cam", s))

# 7 CAM på MB, SD-kort, firmware
s, d = ny_side()
stegnummer(d, 6)
xe = delboks(s, d, [(T["mb"](), "1x"), (T["sd"](), "1x"), (T["kabel"](), "1x")])
CX = 24
ob = [o(PX[n], pos=[CX, 0, 0], crease=30, outline=0.25) for n in CAM] + [o(LEID_KORT, pos=[CX, 0, 0], color=SVART, outline=0.15)]
ob += [o(PX[n], crease=30, outline=0.25) for n in MB]
img, a2 = render(ob, (0.45, -1, 0.5), span=33, target=(58 + CX / 2, 76, 27), size=(1050, 820), anchors=[[57 + CX, 76, 50], [61, 76, 50]])
A = plasser(s, img, a2, (40, 300))
pil(d, A[0], A[1])
# SD-kortet inn
ui, ua = render([o(PX[n], crease=30, outline=0.25) for n in CAM] + [o(PX["sd_kort"], pos=[0, -16, 0], outline=0.25)], (1, -0.25, 0.3), span=15,
                target=(61, 60, 32), size=(800, 800), anchors=[[62.5, 50.5, 39.5], [62.5, 60, 39.5]])
tu = utsnitt(s, d, ui, (1450, 420), 175)
pil(d, tu(ua[0]), tu(ua[1]), w=9, hovud=28)
# USB og firmware
UP6 = 22
ui2, ub = render(stabel() + [o(PX["usb_plugg"], pos=[0, UP6, 0]), o(KABEL, pos=[0, UP6, 0], color=SVART, outline=0.2)], (0.8, 0.6, 0.5), span=50,
                 target=(55, 118, 40), size=(720, 480), anchors=[[x_usb, 121.6 + UP6, az + 7.5], [x_usb, 98, az + 7.5]])
B = plasser(s, ui2, ub, (990, 690))
pil(d, B[0], B[1])
ikon_pc(d, 1490, 640, 0.85)
ikon_ok(d, 1000, 1060, 0.8)
tekst(d, (1110, 1108), "test", 40, True, "lm")
SIDER.append(("07-cam-mb-sd-firmware", s))

# 8 Stabelen ned i botnskalet
s, d = ny_side()
stegnummer(d, 7)
SL = 40
ob = [botn()] + [o(m, outline=0.2) for m in MAG_B] + stabel((0, 0, SL), LEID_HENG)
img, a2 = render(ob, VEKT, span=70, target=(50, 62, 38), anchors=[[54, 80, SL + 47], [54, 80, 49], [42, 92, SL + 47], [42, 92, 49]])
A = plasser(s, img, a2)
pil(d, A[0], A[1])
ui, _ = render([botn()] + stabel(), (1, -0.35, 0.55), span=16, target=(66, ay, az - 3), size=(800, 800))
utsnitt(s, d, ui, (1430, 860), 210)
SIDER.append(("08-stabel-ned", s))

# 9 Leidningane opp gjennom trakta, brytaren
s, d = ny_side()
stegnummer(d, 8)
ikon_snu(d)
xe = delboks(s, d, [(T["brytar"](), "1x")])
ikon_lodde(d, xe + 50, 90, 0.8)
ikon_lim(d, xe + 220, 70, 0.9)
ob = [botn()] + stabel() + [o(LEID_FULL, color=SVART, outline=0.15), topp(pos=[0, 0, T_OPP], opacity=0.4, noOutline=True),
                             o(PX["brytar6x6"], pos=[0, 0, T_OPP + B_OPP], outline=0.15)]
img, a2 = render(ob, VEKT, span=90, target=(46, 48, 70),
                 anchors=[[bx - 6, by, 30], [bx - 6, by, 30 + T_OPP + 22], [bx + 7, by, lomme_botn + T_OPP + B_OPP + 4], [bx + 7, by, lomme_botn + T_OPP + 5]])
A = plasser(s, img, a2)
pil(d, A[0], A[1], w=9)
pil(d, A[2], A[3])
ui, _ = render([o(PX["brytar6x6"], outline=0.15), o(LEID_FULL, pos=[0, 0, -T_OPP - B_OPP], color=SVART, outline=0.12)], (1, -0.7, 0.35), span=9,
               target=(bx, by, lomme_botn + 2), size=(800, 800))
utsnitt(s, d, ui, (1440, 840), 200, linje_til=A[2])
tekst(d, (1440, 1090), "diagonale bein", 38, True, "ma")
SIDER.append(("09-leidning-brytar", s))

# 10 EC11 opp gjennom pipa
s, d = ny_side()
stegnummer(d, 9)
xe = delboks(s, d, [(T["ec11"](), "1x")])
tekst(d, (xe + 40, 95), "+ M7-mutter i forsenkinga", 40, True)
EL = -32
ob = [topp(), o(PX["brytar6x6"], outline=0.15), o(PX["ec11"], pos=[0, 0, EL], outline=0.2)]
img, a2 = render(ob, (0.9, -0.8, -0.45), span=62, target=(44, 66, 40), anchors=[[hx + 10, hy - 8, 34], [hx + 10, hy - 8, 58]])
A = plasser(s, img, a2, (20, 250))
pil(d, A[0], A[1])
ui, ua = render([topp(), o(PX["ec11"], outline=0.2)], (0, -1, 0.15), span=12, target=(hx, hy, 80), size=(800, 800),
                anchors=[[hx + 3, hy, ec_kapp], [hx + 3, hy, ec_kapp + 5.5]])
tu = utsnitt(s, d, ui, (1320, 540), 200)
lo, hi = tu(ua[0]), tu(ua[1])
vmaal(d, lo, hi, hi[0] + 60, "", 40)
tekst(d, (1540, (lo[1] + hi[1]) / 2), "5,5 mm", 44, True, "lm")
# alternativ: hjulaksel
d.rounded_rectangle([1150, 810, 1700, 1150], 18, outline=(0, 0, 0), width=4)
tekst(d, (1180, 830), "eller", 44, True)
ai, aa = render([topp(), o(DEL["hjulaksel"], pos=[0, 0, 20])], (0.95, -0.85, 0.55), span=20, target=(hx, hy, 88), size=(800, 700),
                anchors=[[hx + 6, hy - 6, 104], [hx + 6, hy - 6, 88]])
ta = lim_inn(s, ai, (1320, 822, 1690, 1140))
pil(d, ta(aa[0]), ta(aa[1]), w=8, hovud=26)
ikon_lim(d, 1200, 950, 0.9)
SIDER.append(("10-ec11", s))

# 11 Toppskalet på
s, d = ny_side()
stegnummer(d, 10)
TL = 40
ob = [botn()] + [o(m, outline=0.2) for m in MAG_B] + stabel() + [topp(pos=[0, 0, TL]), o(PX["brytar6x6"], pos=[0, 0, TL], outline=0.15)]
ank = []
for x, y in S["pinnar"][:2]:
    ank += [[x, y, dz + TL - 2], [x, y, dz + 6]]
img, a2 = render(ob, VEKT, span=92, target=(48, 60, 56), anchors=ank)
A = plasser(s, img, a2)
for i in range(2):
    pil(d, A[2 * i], A[2 * i + 1], w=10)
tekst(d, (W - 120, 1120), "klikk", 56, True, "rs", 6)
SIDER.append(("11-topp-paa", s))

# 12 Utløysar og A17-hjul
s, d = ny_side()
stegnummer(d, 11)
xe = delboks(s, d, [(T["knapp"](), "1x"), (T["hjul"](), "1x")])
ikon_lim(d, xe + 50, 70)
UL, HL = 22, 26
ob = [botn(), topp(), o(DEL["utloysar"], pos=[0, 0, UL]), hjul(HL)]
img, a2 = render(ob, VEKT, span=76, target=(48, 62, 64),
                 anchors=[[ux, uy, kapp_z + UL - 1], [ux, uy, kapp_z + 9], [hx, hy, 80.5 + HL - 1], [hx, hy, 87]])
A = plasser(s, img, a2)
pil(d, A[0], A[1])
pil(d, A[2], A[3])
SIDER.append(("12-utloysar-hjul", s))

# 13 USB
s, d = ny_side()
stegnummer(d, 12)
xe = delboks(s, d, [(T["kabel"](), "1x"), (T["lokk"](), "1x")])
UP = 46
ob = ferdig(med_lokk=False) + [o(PX["usb_plugg"], pos=[0, UP, 0]), o(KABEL, pos=[0, UP, 0], color=SVART, outline=0.2)]
img, a2 = render(ob, (0.55, 1.0, 0.45), span=70, target=(48, 100, 42), anchors=[[x_usb, 121 + UP, az + 9], [x_usb, 122, az + 9]])
A = plasser(s, img, a2, (40, 250))
pil(d, A[0], A[1])
li, la = render(ferdig(med_lokk=False) + [o(DEL["usb-lokk"], pos=[0, 18, 0])], (0.55, 1.0, 0.45), span=18, target=(x_usb, 118, az + 2), size=(800, 800),
                anchors=[[x_usb, 118 + 18 + 2, az + 12], [x_usb, 118 + 1, az + 12]])
tl = utsnitt(s, d, li, (1430, 830), 220)
pil(d, tl(la[0]), tl(la[1]), w=9, hovud=30)
tekst(d, (1430, 560), "eller", 48, True, "ms")
SIDER.append(("13-usb", s))

# 14 Ferdig + test
s, d = ny_side()
ob = ferdig(med_lokk=False) + [o(PX["usb_plugg"]), o(KABEL, color=SVART, outline=0.2)]
img, a2 = render(ob, VEKT, span=80, target=(52, 75, 45), anchors=[[ux, uy, kapp_z + 22], [ux, uy, 66]])
A = plasser(s, img, a2, (60, 220))
pil(d, A[0], A[1], w=12)
ikon_bilete(d, 1380, 520)
ikon_ok(d, 1395, 700, 1.0)
tekst(d, (90, 70), "Test: USB inn, trykk på knappen, biletet blir lagra på SD-kortet.", 36, True)
SIDER.append(("14-ferdig", s))

for p in UT.glob("*.png"):
    p.unlink()
for i, (namn, side) in enumerate(SIDER):
    if i > 0:
        tekst(ImageDraw.Draw(side), (W - 50, H - 40), f"{i}/{len(SIDER) - 1}", 28, False, "rs")
    side.save(UT / f"{namn}.png")
SIDER[0][1].save(UT / "Entropi-A3-montering.pdf", save_all=True, append_images=[s for _, s in SIDER[1:]], resolution=150)
shutil.rmtree(TMP)
print("sider", len(SIDER))
