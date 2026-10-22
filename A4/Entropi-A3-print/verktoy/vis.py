import json, subprocess, pathlib, tempfile

HER = pathlib.Path(__file__).resolve().parent
P = HER.parent / "print"
UT = HER.parent / "bilete"
UT.mkdir(exist_ok=True)
SKAL = ("botn", "topp", "utloysar", "usb-lokk")
FARGE = {"cam_kort": 0x2F6F3E, "esp32s": 0x9A9A9A, "sd_og_fpc": 0x8A8A8A, "sd_kort": 0x1A3A7A, "kameramodul": 0x1E1E1E, "mb_kort": 0x2F6F3E, "mb_tappar": 0x222222,
         "usb_kontakt": 0xA0A0A0, "mb_knappar": 0x333333, "headerar": 0x1E1E1E, "pinnetappar": 0x777777, "brytar6x6": 0x2A2A2A, "ec11": 0x9A9A9A, "magnetar": 0x8899AA}
HJUL = {"stl": str(P / "printretning" / "hjul-A17-V4.stl"), "style": "shaded", "color": 0x424749, "rough": 0.5}
SNITT = [0, 1, 0, -65.0]


def cmf(n, pos=(0, 0, 0), clip=None):
    o = {"ply": str(P / "cmf" / f"{n}.ply"), "style": "shaded", "rough": 0.55, "pos": list(pos)}
    if clip:
        o["clip"] = clip
    return o


def innmat(pos=(0, 0, 0)):
    return [{"stl": str(P / "proxy" / f"{n}.stl"), "style": "shaded", "color": c, "pos": list(pos)} for n, c in FARGE.items()]


kontroll = json.loads((P / "kontroll.json").read_text())
hx, hy = kontroll["hjul"]["senter"]
hjul_pos = [hx - 12.0, hy - 12.0, 80.5]
VISNINGAR = {
    "cmf": {"objects": [cmf(n) for n in SKAL] + [dict(HJUL, pos=hjul_pos)], "dir": [0.95, -0.85, 0.6], "target": [45, 60, 45], "span": 70},
    "sprengd": {"objects": [cmf("botn")] + innmat((0, 0, 14)) + [cmf("topp", (0, 0, 46)), cmf("utloysar", (0, 0, 62)), cmf("usb-lokk", (0, 22, 46)),
                                                                   dict(HJUL, pos=[hjul_pos[0], hjul_pos[1], hjul_pos[2] + 62])], "dir": [0.95, -0.85, 0.45], "target": [45, 60, 75], "span": 105},
    "snitt": {"objects": innmat() + [cmf(n, clip=SNITT) for n in SKAL] + [dict(HJUL, pos=hjul_pos)], "dir": [0.35, -1, 0.3], "target": [48, 65, 42], "span": 64},
}
for namn, v in VISNINGAR.items():
    spec = {"size": [1800, 1400], "up": [0, 0, 1], "out": str(UT / f"{namn}.png"), "ground": 0, **v}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(spec, f)
    subprocess.run(["node", str(HER / "scene.mjs"), f.name], check=True, timeout=900)
    print(namn)
