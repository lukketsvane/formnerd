import json, subprocess, pathlib, tempfile

HER = pathlib.Path(__file__).resolve().parent
P = HER.parent / "print"
UT = HER.parent / "bilete"
UT.mkdir(exist_ok=True)
CMF = [{"ply": str(P / "cmf" / f"{n}.ply"), "style": "shaded", "rough": 0.55} for n in ("kropp", "luke", "utloysar", "usb-lokk")]
FARGE = {"cam_kort": 0x2F6F3E, "esp32s": 0x9A9A9A, "sd_og_fpc": 0x8A8A8A, "sd_kort": 0x1A3A7A, "kameramodul": 0x1E1E1E, "mb_kort": 0x2F6F3E, "mb_tappar": 0x222222,
         "usb_kontakt": 0xA0A0A0, "mb_knappar": 0x333333, "headerar": 0x1E1E1E, "brytar6x6": 0x2A2A2A}
SNITT = [0, 1, 0, -65.0]
INNMAT = [{"stl": str(P / "proxy" / f"{n}.stl"), "style": "shaded", "color": c} for n, c in FARGE.items()]
INNMAT.append({"stl": str(P / "stl" / "stabelhaldar.stl"), "style": "shaded", "color": 0xB8B8B8, "clip": SNITT})
for n in ("kropp", "luke", "utloysar", "usb-lokk"):
    INNMAT.append({"ply": str(P / "cmf" / f"{n}.ply"), "style": "shaded", "rough": 0.55, "clip": SNITT})
VISNINGAR = {
    "cmf": {"objects": CMF, "dir": [0.95, -0.85, 0.6], "target": [45, 60, 42], "span": 66},
    "snitt": {"objects": INNMAT, "dir": [0.35, -1, 0.3], "target": [50, 65, 40], "span": 62},
}
for namn, v in VISNINGAR.items():
    spec = {"size": [1800, 1400], "up": [0, 0, 1], "out": str(UT / f"{namn}.png"), "ground": 0, **v}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(spec, f)
    subprocess.run(["node", str(HER / "scene.mjs"), f.name], check=True, timeout=900)
    print(namn)
