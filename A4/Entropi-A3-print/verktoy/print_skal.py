import json, pathlib, trimesh

HER = pathlib.Path(__file__).resolve().parent
UT = HER / "../print"
RETNING = {"botn": [0, 0, -1], "topp": [0, 0, -1], "utloysar": [0, 0, -1], "usb-lokk": [0, -1, 0], "hjulaksel": [0, 0, -1]}
(UT / "printretning").mkdir(parents=True, exist_ok=True)
info = {}
for namn, ned in RETNING.items():
    m = trimesh.load(UT / "stl" / f"{namn}.stl")
    m.apply_transform(trimesh.geometry.align_vectors(ned, [0, 0, -1]))
    m.apply_translation(-m.bounds[0])
    m.export(UT / "printretning" / f"{namn}.stl")
    info[namn] = {"botn_mot_bordet": ned, "storleik_mm": [round(v, 1) for v in m.extents], "volum_cm3": round(m.volume / 1000, 2)}
(UT / "printretning" / "retningar.json").write_text(json.dumps(info, indent=2, ensure_ascii=False))
print(json.dumps(info, ensure_ascii=False))
