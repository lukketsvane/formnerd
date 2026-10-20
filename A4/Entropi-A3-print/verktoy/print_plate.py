import json, pathlib, numpy as np, trimesh

HER = pathlib.Path(__file__).resolve().parent
UT = HER / "../print"
RETNING = {
    "kropp": [0, 0, -1],
    "luke": [0, 0, 1],
    "utloysar": [0, 0, -1],
    "stabelhaldar": [0, 0, -1],
    "usb-lokk": [0, -1, 0],
}
(UT / "printretning" / "haldar-variantar").mkdir(parents=True, exist_ok=True)
info = {}
for namn, ned in RETNING.items():
    m = trimesh.load(UT / "stl" / f"{namn}.stl")
    R = trimesh.geometry.align_vectors(ned, [0, 0, -1])
    m.apply_transform(R)
    m.apply_translation([-m.bounds[0][0], -m.bounds[0][1], -m.bounds[0][2]])
    m.export(UT / "printretning" / f"{namn}.stl")
    info[namn] = {"botn_mot_bordet": ned, "storleik_mm": [round(v, 1) for v in m.extents], "vasstett": bool(m.is_watertight), "volum_cm3": round(m.volume / 1000, 2)}
for f in sorted((UT / "stl" / "haldar-variantar").glob("*.stl")):
    m = trimesh.load(f)
    m.apply_transform(trimesh.geometry.align_vectors(RETNING["stabelhaldar"], [0, 0, -1]))
    m.apply_translation(-m.bounds[0])
    m.export(UT / "printretning" / "haldar-variantar" / f.name)
(UT / "printretning" / "retningar.json").write_text(json.dumps(info, indent=2, ensure_ascii=False))
print(json.dumps(info, indent=1, ensure_ascii=False))

PLASS = {"kropp": (10, 10), "luke": (112, 10), "stabelhaldar": (170, 10), "utloysar": (112, 72), "usb-lokk": (140, 72)}
scene = trimesh.Scene()
for namn, (px, py) in PLASS.items():
    m = trimesh.load(UT / "printretning" / f"{namn}.stl")
    m.apply_translation([px, py, 0])
    assert m.bounds[1][0] <= 246 and m.bounds[1][1] <= 246
    scene.add_geometry(m, node_name=namn, geom_name=namn)
scene.export(UT / "A3-Entropi-alle-delar.3mf")
print("3mf ok")
