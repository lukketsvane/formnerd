import json, sys, pathlib

BBL = pathlib.Path(sys.argv[1])
UT = pathlib.Path(sys.argv[2])
UT.mkdir(parents=True, exist_ok=True)
INDEKS = {}
for d in ("machine", "process", "filament"):
    for f in (BBL / d).glob("*.json"):
        try:
            INDEKS[(d, json.loads(f.read_text()).get("name", f.stem))] = f
        except Exception:
            pass


def flat(d, namn):
    data = json.loads(INDEKS[(d, namn)].read_text())
    arv = data.get("inherits")
    base = flat(d, arv) if arv else {}
    for inc in data.get("include", []):
        base.update({k: v for k, v in json.loads(INDEKS[(d, inc)].read_text()).items() if k not in ("name", "from", "type", "instantiation", "setting_id")})
    base.update({k: v for k, v in data.items() if k not in ("inherits", "include")})
    return base


ENDRINGAR = {
    "process": {"enable_support": "1", "support_type": "tree(auto)", "support_on_build_plate_only": "1", "wall_loops": "3", "wall_generator": "arachne", "curr_bed_type": "Textured PEI Plate"},
    "filament": {"filament_colour": ["#C8C8C8"], "default_filament_colour": ["#C8C8C8"]},
}
for d, namn, fil in (("machine", "Bambu Lab P1S 0.4 nozzle", "maskin.json"),
                     ("process", "0.20mm Standard @BBL X1C", "prosess.json"),
                     ("filament", "Bambu PLA Basic @BBL P1S 0.4 nozzle", "filament.json")):
    p = flat(d, namn)
    p.update(ENDRINGAR.get(d, {}))
    p["from"] = "system" if d != "process" else "User"
    if d == "process":
        p["name"] = "0.20mm Standard @BBL X1C + trestotte fraa plata"
        p["inherits"] = "0.20mm Standard @BBL X1C"
    (UT / fil).write_text(json.dumps(p, indent=1, ensure_ascii=False))
    print(fil, len(p), {k: p.get(k) for k in ("name", "layer_height", "wall_loops", "sparse_infill_density", "enable_support", "support_type", "support_on_build_plate_only", "printer_model", "filament_type") if k in p})
