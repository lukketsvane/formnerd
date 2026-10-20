import glob
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import strek

M = "A2/print/montert"
UT = "A2/rettleiing"
KJELDE = "/usr/share/fonts/truetype/dejavu/"
SIDE = (1654, 2339)
TEIKN = 3000

MB_DELAR = ("mb", "usb", "hylse")
CAM_DELAR = ("cam", "esp32s", "list", "sd", "kamera", "linse", "blits")


def font(storleik, feit=False):
    return ImageFont.truetype(KJELDE + ("DejaVuSans-Bold.ttf" if feit else "DejaVuSans.ttf"), storleik)


def stabel(i, delar, flytt=(0, 0, 0)):
    ut = []
    for f in sorted(glob.glob(f"{M}/stabel_{i}_*.glb")):
        namn = os.path.basename(f)[len(f"stabel_{i}_"):-4].split("_")[0]
        if namn in delar:
            ut.append({"fil": f, "flytt": list(flytt)})
    return ut


def del_(namn, flytt=(0, 0, 0)):
    return [{"fil": f"{M}/{namn}.glb", "flytt": list(flytt)}]


def teikn(namn, objekt, retning, utheva_grupper=(), grå_grupper=(), ankre=(), zoom=1.08, opp=(0, 1, 0)):
    """objekt: liste av grupper (lister med objekt). Returnerer bilete og 2D-ankre."""
    flat, grupper = [], []
    for g, gruppe in enumerate(objekt):
        for o in gruppe:
            flat.append(o)
            grupper.append(g)
    mappe = f"/tmp/a2-rettleiing/{namn}"
    scene = {"storleik": TEIKN, "retning": list(retning), "zoom": zoom, "opp": list(opp), "objekt": flat, "ankre": [list(a) for a in ankre]}
    a2d = strek.render(scene, mappe)
    utheva = [i + 1 for i, g in enumerate(grupper) if g in utheva_grupper]
    grå = [i + 1 for i, g in enumerate(grupper) if g in grå_grupper]
    bilete = strek.strek(mappe, utheva=utheva, grå=grå, linje=3, skala=2)
    return bilete, [(x / 2, y / 2) for x, y in a2d]


def pil(dr, a, b, breidd=10, farge=(20, 20, 20)):
    a, b = np.array(a, float), np.array(b, float)
    v = b - a
    n = np.linalg.norm(v)
    if n < 1:
        return
    v /= n
    o = np.array([-v[1], v[0]])
    hode = b - v * 38
    dr.line([tuple(a), tuple(hode)], fill=farge, width=breidd)
    dr.polygon([tuple(b), tuple(hode + o * 22), tuple(hode - o * 22)], fill=farge)


def boks_med_tal(dr, x, y, w, h, tekst=None):
    dr.rounded_rectangle([x, y, x + w, y + h], radius=18, outline=(20, 20, 20), width=4)
    if tekst:
        dr.text((x + 18, y + 10), tekst, font=font(46, True), fill=(20, 20, 20))


def side(steg=None, tittel=None):
    im = Image.new("RGB", SIDE, "white")
    dr = ImageDraw.Draw(im)
    x = 90
    if steg is not None:
        dr.text((90, 70), str(steg), font=font(170, True), fill=(20, 20, 20))
        x = 90 + dr.textlength(str(steg), font=font(170, True)) + 50
    if tittel:
        dr.text((x, 130), tittel, font=font(44), fill=(70, 70, 70))
    dr.text((SIDE[0] - 260, SIDE[1] - 90), "A2 · FormNerd", font=font(30), fill=(140, 140, 140))
    return im, dr


def lim(im, teikning, x, y, maks_b, maks_h):
    t = teikning.copy()
    t.thumbnail((maks_b, maks_h), Image.LANCZOS)
    s = t.width / teikning.width
    im.paste(t, (int(x + (maks_b - t.width) / 2), int(y + (maks_h - t.height) / 2)))
    return lambda p: (x + (maks_b - t.width) / 2 + p[0] * s, y + (maks_h - t.height) / 2 + p[1] * s)


def sider():
    k = json.load(open("A2/print/kontroll.json"))
    s1, s2 = k["stablar"]
    xs = k["x_skøyt"]
    ly = (s1["y0"] + s1["y1"]) / 2
    mid = lambda s: np.array([(s["xb"] + s["xL"]) / 2, ly, (s["za"] + s["zb"]) / 2])
    FR = (1.0, 0.72, 0.62)
    sidene = []

    im, dr = side()
    t, _ = teikn("framside", [del_("fremre_skal"), del_("bakre_skal")], FR, zoom=1.0)
    lim(im, t, 80, 420, 1500, 1500)
    dr.text((90, 110), "A2", font=font(220, True), fill=(20, 20, 20))
    dr.text((95, 360), "Stereokamera for to ESP32-CAM", font=font(52), fill=(60, 60, 60))
    dr.text((95, 2080), "Monteringsrettleiing · utkast før prøveprint", font=font(38), fill=(120, 120, 120))
    sidene.append(im)

    im, dr = side(tittel="Delar")
    ruter = [
        ("1x", "fremre skal", [del_("fremre_skal")], FR),
        ("1x", "bakre skal", [del_("bakre_skal")], (-1.0, 0.7, 0.6)),
        ("1x", "innmatsramme", [del_("innmatsramme")], (1.0, 0.8, 0.5)),
        ("2x", "ESP32-CAM", [stabel(1, CAM_DELAR)], FR),
        ("2x", "ESP32-CAM-MB", [stabel(1, MB_DELAR)], FR),
        ("2x", "micro-USB-kabel", [[{"fil": f"{M}/kabel_1.glb"}]], (0.7, 0.8, 1.0)),
    ]
    for n, (tal, namn, obj, retn) in enumerate(ruter):
        x, y = 90 + (n % 2) * 760, 300 + (n // 2) * 560
        boks_med_tal(dr, x, y, 720, 520, tal)
        t, _ = teikn(f"del_{n}", obj, retn, zoom=1.15)
        lim(im, t, x + 40, y + 70, 640, 400)
        dr.text((x + 30, y + 470), namn, font=font(34), fill=(60, 60, 60))
    dr.text((90, 2000), "+ 2x USB-ladar 5 V, 1–2 A    + 2x microSD (valfritt)    + litt tape", font=font(34), fill=(60, 60, 60))
    dr.text((90, 2060), "Tape, kablar og ladarar står ikkje på utstyrslista.", font=font(30), fill=(150, 60, 60))
    sidene.append(im)

    im, dr = side(1, "Print delane")
    for n, (namn, retn) in enumerate((("fremre_skal", (1, 0.9, 0.7)), ("bakre_skal", (1, 0.9, 0.7)), ("innmatsramme", (1, 0.9, 0.7)))):
        t, _ = teikn(f"print_{n}", [[{"fil": f"/tmp/a2-print/{namn}.glb"}], [{"fil": f"/tmp/a2-print/seng_{namn}.glb"}]], retn, grå_grupper=(1,), zoom=0.95, opp=(0, 0, 1))
        lim(im, t, 90 + (n % 2) * 760, 330 + (n // 2) * 700, 720, 660)
    dr.text((900, 1100), "PLA · 0,4 mm dyse", font=font(36), fill=(60, 60, 60))
    dr.text((900, 1160), "skal: tre-støtte", font=font(36), fill=(60, 60, 60))
    dr.text((900, 1220), "ramme: utan støtte", font=font(36), fill=(60, 60, 60))
    dr.text((900, 1280), "flat side ned på plata", font=font(36), fill=(60, 60, 60))
    sidene.append(im)

    im, dr = side(2, "Print prøvebitane først")
    t, _ = teikn("prove", [[{"fil": "/tmp/a2-print/prove_skoyt_framme.glb", "flytt": [0, 0, 0]}], [{"fil": "/tmp/a2-print/prove_skoyt_bak.glb", "flytt": [80, 0, 0]}], [{"fil": "/tmp/a2-print/prove_holdar.glb", "flytt": [0, 90, 0]}], [{"fil": "/tmp/a2-print/prove_linse_usb.glb", "flytt": [80, 90, 0]}]], (1, 0.9, 0.9), opp=(0, 0, 1))
    lim(im, t, 90, 320, 1480, 1300)
    dr.text((90, 1700), "Kontroller før du printar heile huset:", font=font(40, True), fill=(20, 20, 20))
    for n, linje in enumerate(("skøyten klikkar saman og sit fast", "kortet går ned mellom styrebena utan press", "linseløpet går gjennom holet", "USB-pluggen går heilt inn i kontakten")):
        dr.text((110, 1780 + n * 64), "□  " + linje, font=font(38), fill=(40, 40, 40))
    sidene.append(im)

    im, dr = side(3, "Last opp program før montering")
    t, a = teikn("program", [stabel(1, MB_DELAR + CAM_DELAR), [{"fil": f"{M}/kabel_1.glb", "flytt": [0, 0, 25]}]], FR, utheva_grupper=(1,), ankre=[s1 and (s1["xb"] + 3, ly, s1["z_usb"] + 45), (s1["xb"] + 3, ly, s1["z_usb"] + 30)])
    p = lim(im, t, 90, 380, 1100, 1100)
    pil(dr, p(a[0]), p(a[1]))
    dr.rounded_rectangle([1230, 820, 1560, 1040], radius=12, outline=(20, 20, 20), width=5)
    dr.polygon([(1180, 1040), (1610, 1040), (1640, 1090), (1150, 1090)], outline=(20, 20, 20), width=5)
    dr.text((1300, 1110), "PC", font=font(44, True), fill=(20, 20, 20))
    boks_med_tal(dr, 90, 1600, 260, 120, "2x")
    sidene.append(im)

    im, dr = side(4, "Kameraet midt på SD-sokkelen")
    t, a = teikn("kamera", [stabel(1, ("cam", "sd", "list", "esp32s", "blits")), stabel(1, ("kamera", "linse"), (8, 0, 0))], FR, utheva_grupper=(1,), ankre=[mid(s1) + (14, 0, 0) + (0, 0, s1["lz"] - mid(s1)[2]), mid(s1) + (5, 0, 0) + (0, 0, s1["lz"] - mid(s1)[2])], zoom=0.9)
    p = lim(im, t, 90, 360, 1480, 1400)
    pil(dr, p(a[0]), p(a[1]))
    dr.text((90, 1820), "Legg linsa midt på sokkelen og fest med tape.", font=font(40), fill=(40, 40, 40))
    boks_med_tal(dr, 90, 1920, 260, 120, "2x")
    sidene.append(im)

    im, dr = side(5, "Set ESP32-CAM på MB-kortet")
    t, a = teikn("stabel", [stabel(1, MB_DELAR), stabel(1, CAM_DELAR, (22, 0, 0))], FR, utheva_grupper=(1,), ankre=[mid(s1) + (30, 0, 0), mid(s1) + (14, 0, 0)])
    p = lim(im, t, 90, 360, 1480, 1400)
    pil(dr, p(a[0]), p(a[1]))
    dr.text((90, 1820), "Kameraet vender bort frå MB-kortet.", font=font(40), fill=(40, 40, 40))
    boks_med_tal(dr, 90, 1920, 260, 120, "2x")
    sidene.append(im)

    for n, (s, i, tekst) in enumerate(((s1, 1, "USB-enden mot grepet"), (s2, 2, "USB-enden mot den andre enden"))):
        im, dr = side(6 + n, f"Stabel {i} i ramma")
        andre = [stabel(1, MB_DELAR + CAM_DELAR)] if i == 2 else []
        t, a = teikn(f"ramme_{i}", [del_("innmatsramme")] + andre + [stabel(i, MB_DELAR + CAM_DELAR, (30, 0, 0))], FR, grå_grupper=(0,), utheva_grupper=(len(andre) + 1,), ankre=[mid(s) + (44, 0, 0), mid(s) + (22, 0, 0)])
        p = lim(im, t, 90, 360, 1480, 1400)
        pil(dr, p(a[0]), p(a[1]))
        dr.text((90, 1820), tekst + ". Ned mellom styrebena.", font=font(40), fill=(40, 40, 40))
        sidene.append(im)

    alle = [stabel(1, MB_DELAR + CAM_DELAR), stabel(2, MB_DELAR + CAM_DELAR)]
    im, dr = side(8, "Ramma ned i bakre skal")
    t, a = teikn("bak", [del_("bakre_skal")] + [del_("innmatsramme", (30, 0, 0)) + stabel(1, MB_DELAR + CAM_DELAR, (30, 0, 0)) + stabel(2, MB_DELAR + CAM_DELAR, (30, 0, 0))], FR, grå_grupper=(0,), utheva_grupper=(1,), ankre=[(xs + 40, ly + 20, 57), (xs + 12, ly + 20, 57)])
    p = lim(im, t, 90, 360, 1480, 1400)
    pil(dr, p(a[0]), p(a[1]))
    sidene.append(im)

    im, dr = side(9, "Fremre skal på – klikk")
    t, a = teikn("front", [del_("bakre_skal"), del_("innmatsramme")] + alle + [del_("fremre_skal", (45, 0, 0))], FR, grå_grupper=(0,), utheva_grupper=(4,), ankre=[(xs + 75, 70, 57), (xs + 45, 70, 57)])
    p = lim(im, t, 90, 360, 1480, 1400)
    pil(dr, p(a[0]), p(a[1]))
    dr.text((90, 1820), "Linsene i hola, USB-kontaktane mot tunnelane. Trykk til det klikkar.", font=font(36), fill=(40, 40, 40))
    sidene.append(im)

    im, dr = side(10, "Kople til straum")
    t, a = teikn("usb", [del_("fremre_skal"), del_("bakre_skal"), [{"fil": f"{M}/kabel_1.glb", "flytt": [0, 0, 18]}], [{"fil": f"{M}/kabel_2.glb", "flytt": [0, 0, -18]}]], FR, utheva_grupper=(2, 3), ankre=[(s1["xb"] + 3, ly, s1["z_usb"] + 38), (s1["xb"] + 3, ly, s1["z_usb"] + 20), (s2["xb"] + 3, ly, s2["z_usb"] - 38), (s2["xb"] + 3, ly, s2["z_usb"] - 20)])
    p = lim(im, t, 90, 360, 1480, 1400)
    pil(dr, p(a[0]), p(a[1]))
    pil(dr, p(a[2]), p(a[3]))
    dr.text((90, 1820), "Ein ladar per kamera (5 V, 1–2 A). Utløysaren er i WiFi-appen.", font=font(36), fill=(40, 40, 40))
    boks_med_tal(dr, 90, 1920, 260, 120, "2x")
    sidene.append(im)

    im, dr = side(11, "Opne for SD-kort")
    t, a = teikn("opne", [del_("bakre_skal"), del_("fremre_skal", (35, 0, 0))], FR, utheva_grupper=(1,), ankre=[(xs + 40, 70, 57), (xs + 70, 70, 57)])
    p = lim(im, t, 90, 360, 1480, 1400)
    pil(dr, p(a[0]), p(a[1]))
    dr.text((90, 1820), "Trekk skala rett frå kvarandre.", font=font(40), fill=(40, 40, 40))
    sidene.append(im)
    return sidene


def print_glb():
    import trimesh
    os.makedirs("/tmp/a2-print", exist_ok=True)
    for f in glob.glob("A2/print/*.stl") + glob.glob("A2/print/provebitar/*.stl"):
        trimesh.load(f).export(f"/tmp/a2-print/{os.path.basename(f)[:-4]}.glb")
    for f in glob.glob("A2/print/*.stl"):
        b = trimesh.load(f).bounds
        e = b[1] - b[0] + 24
        trimesh.creation.box(extents=(e[0], e[1], 1.0), transform=trimesh.transformations.translation_matrix(((b[0][0] + b[1][0]) / 2, (b[0][1] + b[1][1]) / 2, -0.5))).export(f"/tmp/a2-print/seng_{os.path.basename(f)[:-4]}.glb")


if __name__ == "__main__":
    print_glb()
    os.makedirs(UT, exist_ok=True)
    s = sider()
    for i, im in enumerate(s):
        im.save(f"{UT}/side-{i:02d}.png")
    s[0].save(f"{UT}/A2-monteringsrettleiing.pdf", save_all=True, append_images=s[1:], resolution=200)
    print(len(s), "sider")
